#!/usr/bin/env python3
"""Trace agent execution to find where data is lost"""
from dotenv import load_dotenv
from agents.meta_ads_agent import MetaAdsAgent
from tools.meta_sdk import MetaAdsSDK
import asyncio
import json

load_dotenv()

async def trace_execution():
    agent = MetaAdsAgent()
    sdk = MetaAdsSDK()
    
    print('TRACING REAL EXECUTION')
    print('=' * 70)
    
    # Step 1: Search for campaign
    campaigns = sdk.search_campaigns('Ryan Castro')
    print(f'Step 1: Found campaign: {campaigns[0]["name"] if campaigns else "None"}')
    
    if campaigns:
        campaign_id = campaigns[0]['id']
        
        # Step 2: Get adsets
        adsets = sdk.get_adsets_for_campaign(campaign_id)
        print(f'Step 2: Found {len(adsets)} adsets')
        
        # Step 3: Get insights for each adset
        print('\nStep 3: Getting insights for each adset:')
        total = 0
        for adset in adsets:
            insights = sdk.get_adset_insights(adset['id'], date_preset='maximum')
            if isinstance(insights, dict) and 'error' not in insights:
                spend = insights.get('spend_dollars', 0)
                roas = insights.get('roas', 0)
                print(f'  - {adset["name"][:30]:30} : ${spend:7.2f} (ROAS: {roas:.2f})')
                total += spend
        
        print(f'\nTOTAL FROM SDK: ${total:.2f}')
    
    print('\n' + '=' * 70)
    print('Now testing agent with same request:')
    response = await agent.process_request('show me spend for Ryan Castro campaign by city')
    
    print('\nAgent response:')
    print(response)
    
    # Check if real values are in response
    real_values = ['52.91', '384.87', '317.29', '286.12', '242.79', '336.10']
    found = [v for v in real_values if v in response]
    
    if found:
        print(f'\n✅ Found {len(found)} real values')
    else:
        print('\n❌ No real values found - agent is hallucinating!')

if __name__ == "__main__":
    asyncio.run(trace_execution())