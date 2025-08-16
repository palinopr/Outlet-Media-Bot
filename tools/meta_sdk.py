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
    
    def get_campaigns_by_status(self, status: List[str] = None, statuses: List[str] = None) -> List[Dict]:
        """Get campaigns filtered by status"""
        try:
            # Handle both 'status' and 'statuses' parameter names
            status_list = status or statuses or []
            
            # If a single string was passed, convert to list
            if isinstance(status_list, str):
                status_list = [status_list]
            
            campaigns = self.get_all_campaigns()
            if isinstance(campaigns, dict) and "error" in campaigns:
                return campaigns
            
            return [c for c in campaigns if c.get('status') in status_list]
        except Exception as e:
            logger.error(f"Error filtering campaigns: {e}")
            return {"error": str(e)}
    
    def get_campaign_insights(
        self, 
        campaign_id: str = None,
        id: str = None,
        date_preset: str = "today",
        fields: List[str] = None
    ) -> Dict:
        """Get insights for a specific campaign"""
        try:
            # Accept both 'campaign_id' and 'id' parameters
            actual_campaign_id = campaign_id or id
            if not actual_campaign_id:
                return {"error": "Please provide a campaign_id or id"}
                
            if not fields:
                fields = [
                    'campaign_name', 'impressions', 'clicks', 'spend',
                    'ctr', 'cpc', 'cpm', 'conversions', 'purchase_roas'
                ]
            
            campaign = Campaign(actual_campaign_id)
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
    
    def search_campaigns(self, query: str = None, name: str = None) -> List[Dict]:
        """Search campaigns by name or query
        
        Args:
            query: Search query (for backward compatibility)
            name: Campaign name to search for (alternative parameter name)
        """
        try:
            # Accept both 'query' and 'name' parameters
            search_term = query or name
            if not search_term:
                return {"error": "Please provide a search query or name"}
                
            campaigns = self.get_all_campaigns()
            if isinstance(campaigns, dict) and "error" in campaigns:
                return campaigns
            
            search_lower = search_term.lower()
            return [
                c for c in campaigns 
                if search_lower in c.get('name', '').lower() or 
                   search_lower in c.get('id', '').lower()
            ]
        except Exception as e:
            logger.error(f"Error searching campaigns: {e}")
            return {"error": str(e)}
    
    def search_adsets(self, query: str = None, name: str = None, city: str = None) -> List[Dict]:
        """Search adsets by name, query, or city
        
        Args:
            query: Search query
            name: Adset name to search for
            city: City name (since adsets often represent cities in campaigns)
        """
        try:
            # Accept multiple parameter names
            search_term = query or name or city
            if not search_term:
                return {"error": "Please provide a search query, name, or city"}
                
            adsets = self._get_all_adsets()
            if isinstance(adsets, dict) and "error" in adsets:
                return adsets
            
            search_lower = search_term.lower()
            return [
                a for a in adsets 
                if search_lower in a.get('name', '').lower() or 
                   search_lower in a.get('id', '').lower()
            ]
        except Exception as e:
            logger.error(f"Error searching adsets: {e}")
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
    
    def _get_all_adsets(self) -> List[Dict]:
        """Get all ad sets from the account"""
        try:
            adsets = self.ad_account.get_ad_sets(fields=[
                'id', 'name', 'status', 'campaign_id', 'daily_budget'
            ])
            return [self._parse_object(adset) for adset in adsets]
        except Exception as e:
            logger.error(f"Error getting all adsets: {e}")
            return {"error": str(e)}
    
    def _get_all_ads(self) -> List[Dict]:
        """Get all ads from the account"""
        try:
            ads = self.ad_account.get_ads(fields=[
                'id', 'name', 'status', 'adset_id', 'creative'
            ])
            return [self._parse_object(ad) for ad in ads]
        except Exception as e:
            logger.error(f"Error getting all ads: {e}")
            return {"error": str(e)}
    
    def _get_audiences(self) -> List[Dict]:
        """Get custom audiences"""
        try:
            audiences = self.ad_account.get_custom_audiences(fields=[
                'id', 'name', 'description', 'approximate_count'
            ])
            return [self._parse_object(audience) for audience in audiences]
        except Exception as e:
            logger.error(f"Error getting audiences: {e}")
            return {"error": str(e)}
    
    def _get_creatives(self) -> List[Dict]:
        """Get ad creatives"""
        try:
            creatives = self.ad_account.get_ad_creatives(fields=[
                'id', 'name', 'title', 'body'
            ])
            return [self._parse_object(creative) for creative in creatives]
        except Exception as e:
            logger.error(f"Error getting creatives: {e}")
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
                "adsets": lambda: self._get_all_adsets() if not params or 'campaign_id' not in params else self.get_adsets_for_campaign(params.get('campaign_id')),
                "ads": lambda: self._get_all_ads() if not params or 'adset_id' not in params else self.get_ads_for_adset(params.get('adset_id')),
                "audiences": lambda: self._get_audiences(),
                "creatives": lambda: self._get_creatives(),
                "search": lambda: self.search_campaigns(params.get('query', '') if params else '')
            }
            
            if operation in operations:
                return operations[operation]()
            else:
                return {"error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Query error: {e}")
            return {"error": str(e)}