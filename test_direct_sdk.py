#!/usr/bin/env python3
"""
Direct SDK test to get real city-level metrics for Ryan's campaign
"""
import os
from dotenv import load_dotenv
from tools.meta_sdk import MetaAdsSDK
import json

# Load environment variables
load_dotenv()

def test_direct_sdk():
    sdk = MetaAdsSDK()
    
    # Step 1: Search for Ryan's campaign
    print('Step 1: Searching for Ryan campaign...')
    campaigns = sdk.search_campaigns('Ryan')
    if campaigns and len(campaigns) > 0:
        campaign = campaigns[0]
        print(f'Found campaign: {campaign["name"]} (ID: {campaign["id"]})')
        
        # Step 2: Get adsets for this campaign
        print('\nStep 2: Getting adsets for campaign...')
        adsets = sdk.get_adsets_for_campaign(campaign['id'])
        print(f'Found {len(adsets)} adsets/cities:')
        for adset in adsets:
            print(f'  - {adset["name"]} (ID: {adset["id"]})')
        
        # Step 3: Get insights for each adset
        print('\nStep 3: Getting insights for each city...')
        print('=' * 60)
        
        city_results = []
        for adset in adsets:
            print(f'\n📍 City: {adset["name"]}')
            insights = sdk.get_adset_insights(
                adset_id=adset['id'],
                date_preset='last_7d'
            )
            
            if isinstance(insights, dict) and 'error' not in insights:
                # Extract spend in dollars
                spend = insights.get('spend', 0)
                spend_dollars = float(spend) / 100 if spend else 0
                
                # Extract ROAS
                roas = 0
                if 'purchase_roas' in insights and insights['purchase_roas']:
                    if isinstance(insights['purchase_roas'], list) and len(insights['purchase_roas']) > 0:
                        roas = float(insights['purchase_roas'][0].get('value', 0))
                
                # Get other metrics
                impressions = insights.get('impressions', 0)
                clicks = insights.get('clicks', 0)
                
                city_results.append({
                    'city': adset["name"],
                    'spend': spend_dollars,
                    'roas': roas,
                    'impressions': impressions,
                    'clicks': clicks
                })
                
                print(f'  💰 Spend: ${spend_dollars:.2f}')
                print(f'  📈 ROAS: {roas:.2f}')
                print(f'  👁 Impressions: {impressions}')
                print(f'  🖱 Clicks: {clicks}')
            else:
                print(f'  ⚠️ No data available or error: {insights}')
                city_results.append({
                    'city': adset["name"],
                    'spend': 0,
                    'roas': 0,
                    'impressions': 0,
                    'clicks': 0,
                    'error': str(insights)
                })
        
        # Summary
        print('\n' + '=' * 60)
        print('SUMMARY - All Cities:')
        print('=' * 60)
        total_spend = sum(c['spend'] for c in city_results)
        print(f'Total Spend: ${total_spend:.2f}')
        print('\nPer City Breakdown:')
        for city in city_results:
            print(f"  {city['city']}: ${city['spend']:.2f} (ROAS: {city['roas']:.2f})")
            
    else:
        print('No campaigns found for "Ryan"')

if __name__ == '__main__':
    test_direct_sdk()