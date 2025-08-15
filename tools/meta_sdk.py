"""
Meta Ads SDK - Simple wrapper for Facebook Business SDK
Direct access to Meta Ads API without complexity
"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.exceptions import FacebookRequestError

logger = logging.getLogger(__name__)


class MetaAdsSDK:
    """Simple Meta Ads SDK wrapper"""
    
    def __init__(self):
        """Initialize the SDK with credentials from environment"""
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
        
        if not self.access_token:
            raise ValueError("META_ACCESS_TOKEN not found in environment")
        if not self.ad_account_id:
            raise ValueError("META_AD_ACCOUNT_ID not found in environment")
        
        # Format account ID
        if not self.ad_account_id.startswith("act_"):
            self.ad_account_id = f"act_{self.ad_account_id}"
        
        # Initialize Facebook SDK
        FacebookAdsApi.init(
            access_token=self.access_token,
            api_version="v21.0"
        )
        
        # Get account object
        self.account = AdAccount(self.ad_account_id)
        logger.info(f"Meta SDK initialized for account: {self.ad_account_id}")
    
    def get_all_campaigns(self, fields: List[str] = None) -> List[Dict]:
        """Get all campaigns in the account"""
        try:
            if not fields:
                fields = [
                    'id', 'name', 'status', 'objective',
                    'daily_budget', 'lifetime_budget', 'spend_cap'
                ]
            
            campaigns = self.account.get_campaigns(fields=fields)
            return [campaign.export_all_data() for campaign in campaigns]
        except FacebookRequestError as e:
            logger.error(f"Facebook API error: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error getting campaigns: {e}")
            return {"error": str(e)}
    
    def get_campaigns_by_status(self, statuses: List[str]) -> List[Dict]:
        """Get campaigns filtered by status"""
        try:
            campaigns = self.get_all_campaigns()
            if isinstance(campaigns, dict) and "error" in campaigns:
                return campaigns
            
            return [c for c in campaigns if c.get('status') in statuses]
        except Exception as e:
            logger.error(f"Error filtering campaigns: {e}")
            return {"error": str(e)}
    
    def get_campaign_insights(
        self, 
        campaign_id: str,
        date_preset: str = "today",
        fields: List[str] = None
    ) -> Dict:
        """Get insights for a specific campaign"""
        try:
            if not fields:
                fields = [
                    'campaign_name', 'impressions', 'clicks', 'spend',
                    'ctr', 'cpc', 'cpm', 'conversions', 'purchase_roas'
                ]
            
            campaign = Campaign(campaign_id)
            insights = campaign.get_insights(
                fields=fields,
                params={'date_preset': date_preset}
            )
            
            if insights:
                return insights[0].export_all_data()
            return {"message": "No insights data available"}
            
        except FacebookRequestError as e:
            logger.error(f"Facebook API error: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error getting insights: {e}")
            return {"error": str(e)}
    
    def get_performance_metrics(self, date_preset: str = "today") -> Dict:
        """Get overall account performance metrics"""
        try:
            fields = [
                'spend', 'impressions', 'clicks', 'conversions',
                'ctr', 'cpc', 'cpm', 'purchase_roas'
            ]
            
            insights = self.account.get_insights(
                fields=fields,
                params={'date_preset': date_preset, 'level': 'account'}
            )
            
            if insights:
                data = insights[0].export_all_data()
                # Get campaign breakdown
                campaigns = self.get_campaigns_by_status(['ACTIVE'])
                
                return {
                    "account_metrics": data,
                    "active_campaigns": len(campaigns) if isinstance(campaigns, list) else 0,
                    "date_range": date_preset
                }
            return {"message": "No performance data available"}
            
        except Exception as e:
            logger.error(f"Error getting performance: {e}")
            return {"error": str(e)}
    
    def search_campaigns(self, query: str) -> List[Dict]:
        """Search campaigns by name"""
        try:
            campaigns = self.get_all_campaigns()
            if isinstance(campaigns, dict) and "error" in campaigns:
                return campaigns
            
            query_lower = query.lower()
            return [
                c for c in campaigns 
                if query_lower in c.get('name', '').lower() or 
                   query_lower in c.get('id', '').lower()
            ]
        except Exception as e:
            logger.error(f"Error searching campaigns: {e}")
            return {"error": str(e)}
    
    def get_adsets_for_campaign(self, campaign_id: str) -> List[Dict]:
        """Get all ad sets for a campaign"""
        try:
            campaign = Campaign(campaign_id)
            adsets = campaign.get_ad_sets(fields=[
                'id', 'name', 'status', 'daily_budget', 
                'lifetime_budget', 'targeting'
            ])
            return [adset.export_all_data() for adset in adsets]
        except Exception as e:
            logger.error(f"Error getting ad sets: {e}")
            return {"error": str(e)}
    
    def get_ads_for_adset(self, adset_id: str) -> List[Dict]:
        """Get all ads for an ad set"""
        try:
            adset = AdSet(adset_id)
            ads = adset.get_ads(fields=[
                'id', 'name', 'status', 'creative'
            ])
            return [ad.export_all_data() for ad in ads]
        except Exception as e:
            logger.error(f"Error getting ads: {e}")
            return {"error": str(e)}
    
    def query(self, operation: str, params: Dict = None) -> Any:
        """Generic query method for flexibility"""
        try:
            # Map operations to methods
            operations = {
                "campaigns": self.get_all_campaigns,
                "active_campaigns": lambda: self.get_campaigns_by_status(['ACTIVE']),
                "campaign_insights": lambda: self.get_campaign_insights(
                    params.get('campaign_id'),
                    params.get('date_preset', 'today')
                ),
                "performance": lambda: self.get_performance_metrics(
                    params.get('date_preset', 'today')
                ),
                "search": lambda: self.search_campaigns(params.get('query', '')),
                "adsets": lambda: self.get_adsets_for_campaign(params.get('campaign_id')),
                "ads": lambda: self.get_ads_for_adset(params.get('adset_id'))
            }
            
            if operation in operations:
                return operations[operation]()
            else:
                return {"error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Query error: {e}")
            return {"error": str(e)}