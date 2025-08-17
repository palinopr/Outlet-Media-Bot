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
        """Get insights for a specific campaign
        
        Note: Meta API returns monetary values in DOLLARS as strings.
        """
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
                data = insights[0].export_all_data()
                # Add spend_dollars for consistency (already in dollars)
                if 'spend' in data:
                    data['spend_dollars'] = float(data['spend']) if data['spend'] else 0
                return data
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
    
    def get_adset_insights(
        self,
        adset_id: str = None,
        id: str = None,
        date_preset: str = "last_7d",
        fields: List[str] = None
    ) -> Dict:
        """Get insights for a specific adset (city)
        
        Args:
            adset_id/id: The adset identifier
            date_preset: Date range (today, yesterday, last_7d, last_30d, lifetime)
            fields: Metrics to retrieve
        """
        try:
            actual_adset_id = adset_id or id
            if not actual_adset_id:
                return {"error": "Please provide adset_id or id"}
            
            if not fields:
                fields = [
                    'adset_name', 'impressions', 'clicks', 'spend',
                    'ctr', 'cpc', 'cpm', 'conversions', 'purchase_roas',
                    'actions', 'action_values', 'cost_per_action_type'
                ]
            
            adset = AdSet(actual_adset_id)
            insights = adset.get_insights(
                fields=fields,
                params={'date_preset': date_preset}
            )
            
            if insights:
                data = insights[0].export_all_data()
                # Extract ROAS if available
                if 'purchase_roas' in data and data['purchase_roas']:
                    # purchase_roas is an array with value
                    if isinstance(data['purchase_roas'], list) and len(data['purchase_roas']) > 0:
                        data['roas'] = float(data['purchase_roas'][0].get('value', 0))
                # Meta API returns spend in dollars as a string
                if 'spend' in data:
                    data['spend_dollars'] = float(data['spend']) if data['spend'] else 0
                return data
            return {"message": f"No insights data available for {date_preset}"}
            
        except FacebookRequestError as e:
            logger.error(f"Facebook API error: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error getting adset insights: {e}")
            return {"error": str(e)}
    
    def _get_all_adsets(self) -> List[Dict]:
        """Get all ad sets from the account"""
        try:
            adsets = self.account.get_ad_sets(fields=[
                'id', 'name', 'status', 'campaign_id', 'daily_budget'
            ])
            return [adset.export_all_data() for adset in adsets]
        except Exception as e:
            logger.error(f"Error getting all adsets: {e}")
            return {"error": str(e)}
    
    def _get_all_ads(self) -> List[Dict]:
        """Get all ads from the account"""
        try:
            ads = self.account.get_ads(fields=[
                'id', 'name', 'status', 'adset_id', 'creative'
            ])
            return [ad.export_all_data() for ad in ads]
        except Exception as e:
            logger.error(f"Error getting all ads: {e}")
            return {"error": str(e)}
    
    def _get_audiences(self) -> List[Dict]:
        """Get custom audiences"""
        try:
            audiences = self.account.get_custom_audiences(fields=[
                'id', 'name', 'description', 'approximate_count'
            ])
            return [audience.export_all_data() for audience in audiences]
        except Exception as e:
            logger.error(f"Error getting audiences: {e}")
            return {"error": str(e)}
    
    def _get_creatives(self) -> List[Dict]:
        """Get ad creatives"""
        try:
            creatives = self.account.get_ad_creatives(fields=[
                'id', 'name', 'title', 'body'
            ])
            return [creative.export_all_data() for creative in creatives]
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
    
    # ============= UPDATE METHODS =============
    # These methods allow modifying campaigns and adsets
    
    def update_adset_budget(
        self,
        adset_id: str = None,
        id: str = None,
        daily_budget: float = None,
        lifetime_budget: float = None,
        budget: float = None
    ) -> Dict:
        """Update adset budget (values in dollars, converts to cents)
        
        Args:
            adset_id/id: The adset identifier
            daily_budget/budget: Daily budget in dollars
            lifetime_budget: Lifetime budget in dollars
            
        Note: Meta API expects budget values in CENTS for updates,
        but returns them in DOLLARS for reads.
        """
        try:
            actual_id = adset_id or id
            if not actual_id:
                return {"error": "Please provide adset_id or id"}
            
            # Prepare update params
            params = {}
            
            # Convert dollars to cents (Meta API uses cents)
            if daily_budget is not None:
                params['daily_budget'] = int(daily_budget * 100)
            elif budget is not None:
                params['daily_budget'] = int(budget * 100)
            
            if lifetime_budget is not None:
                params['lifetime_budget'] = int(lifetime_budget * 100)
            
            if not params:
                return {"error": "Please provide daily_budget or lifetime_budget"}
            
            # Update the adset
            adset = AdSet(actual_id)
            response = adset.api_update(params=params)
            
            logger.info(f"Updated adset {actual_id} budget: {params}")
            return {
                "success": True,
                "adset_id": actual_id,
                "updated_fields": params,
                "message": f"Successfully updated budget for adset {actual_id}"
            }
            
        except FacebookRequestError as e:
            logger.error(f"Facebook API error updating adset: {e}")
            return {"error": f"Facebook API error: {e.api_error_message()}"}
        except Exception as e:
            logger.error(f"Error updating adset: {e}")
            return {"error": str(e)}
    
    def update_campaign_budget(
        self,
        campaign_id: str = None,
        id: str = None,
        daily_budget: float = None,
        lifetime_budget: float = None,
        budget: float = None
    ) -> Dict:
        """Update campaign budget (values in dollars, converts to cents)
        
        Args:
            campaign_id/id: The campaign identifier
            daily_budget/budget: Daily budget in dollars
            lifetime_budget: Lifetime budget in dollars
        """
        try:
            actual_id = campaign_id or id
            if not actual_id:
                return {"error": "Please provide campaign_id or id"}
            
            # Prepare update params
            params = {}
            
            # Convert dollars to cents
            if daily_budget is not None:
                params['daily_budget'] = int(daily_budget * 100)
            elif budget is not None:
                params['daily_budget'] = int(budget * 100)
            
            if lifetime_budget is not None:
                params['lifetime_budget'] = int(lifetime_budget * 100)
            
            if not params:
                return {"error": "Please provide daily_budget or lifetime_budget"}
            
            # Update the campaign
            campaign = Campaign(actual_id)
            response = campaign.api_update(params=params)
            
            logger.info(f"Updated campaign {actual_id} budget: {params}")
            return {
                "success": True,
                "campaign_id": actual_id,
                "updated_fields": params,
                "message": f"Successfully updated budget for campaign {actual_id}"
            }
            
        except FacebookRequestError as e:
            logger.error(f"Facebook API error updating campaign: {e}")
            return {"error": f"Facebook API error: {e.api_error_message()}"}
        except Exception as e:
            logger.error(f"Error updating campaign: {e}")
            return {"error": str(e)}
    
    def pause_adset(self, adset_id: str = None, id: str = None) -> Dict:
        """Pause an adset"""
        try:
            actual_id = adset_id or id
            if not actual_id:
                return {"error": "Please provide adset_id or id"}
            
            adset = AdSet(actual_id)
            response = adset.api_update(params={'status': 'PAUSED'})
            
            logger.info(f"Paused adset {actual_id}")
            return {
                "success": True,
                "adset_id": actual_id,
                "status": "PAUSED",
                "message": f"Successfully paused adset {actual_id}"
            }
            
        except Exception as e:
            logger.error(f"Error pausing adset: {e}")
            return {"error": str(e)}
    
    def resume_adset(self, adset_id: str = None, id: str = None) -> Dict:
        """Resume/activate an adset"""
        try:
            actual_id = adset_id or id
            if not actual_id:
                return {"error": "Please provide adset_id or id"}
            
            adset = AdSet(actual_id)
            response = adset.api_update(params={'status': 'ACTIVE'})
            
            logger.info(f"Resumed adset {actual_id}")
            return {
                "success": True,
                "adset_id": actual_id,
                "status": "ACTIVE",
                "message": f"Successfully activated adset {actual_id}"
            }
            
        except Exception as e:
            logger.error(f"Error resuming adset: {e}")
            return {"error": str(e)}
    
    def pause_campaign(self, campaign_id: str = None, id: str = None) -> Dict:
        """Pause a campaign"""
        try:
            actual_id = campaign_id or id
            if not actual_id:
                return {"error": "Please provide campaign_id or id"}
            
            campaign = Campaign(actual_id)
            response = campaign.api_update(params={'status': 'PAUSED'})
            
            logger.info(f"Paused campaign {actual_id}")
            return {
                "success": True,
                "campaign_id": actual_id,
                "status": "PAUSED",
                "message": f"Successfully paused campaign {actual_id}"
            }
            
        except Exception as e:
            logger.error(f"Error pausing campaign: {e}")
            return {"error": str(e)}
    
    def resume_campaign(self, campaign_id: str = None, id: str = None) -> Dict:
        """Resume/activate a campaign"""
        try:
            actual_id = campaign_id or id
            if not actual_id:
                return {"error": "Please provide campaign_id or id"}
            
            campaign = Campaign(actual_id)
            response = campaign.api_update(params={'status': 'ACTIVE'})
            
            logger.info(f"Resumed campaign {actual_id}")
            return {
                "success": True,
                "campaign_id": actual_id,
                "status": "ACTIVE",
                "message": f"Successfully activated campaign {actual_id}"
            }
            
        except Exception as e:
            logger.error(f"Error resuming campaign: {e}")
            return {"error": str(e)}