#!/usr/bin/env python3
"""Test Meta API directly to diagnose rate limit issue"""
from dotenv import load_dotenv
from tools.meta_sdk import MetaAdsSDK
import os

load_dotenv()

sdk = MetaAdsSDK()

print("Testing Meta API directly...")
print("=" * 70)

# Test 1: Get campaigns (this usually works)
print("\n1. Testing get_all_campaigns:")
campaigns = sdk.get_all_campaigns()
if isinstance(campaigns, list):
    print(f"   ✅ Success: Found {len(campaigns)} campaigns")
    for c in campaigns[:3]:
        print(f"      - {c.get('name', 'Unknown')}")
else:
    print(f"   ❌ Error: {campaigns}")

# Test 2: Search for Ryan Castro campaign
print("\n2. Testing search_campaigns('Ryan Castro'):")
ryan_campaigns = sdk.search_campaigns('Ryan Castro')
if isinstance(ryan_campaigns, list) and len(ryan_campaigns) > 0:
    print(f"   ✅ Success: Found campaign")
    campaign_id = ryan_campaigns[0]['id']
    print(f"      ID: {campaign_id}")
    print(f"      Name: {ryan_campaigns[0]['name']}")
    
    # Test 3: Get adsets for this specific campaign
    print(f"\n3. Testing get_adsets_for_campaign('{campaign_id}'):")
    adsets = sdk.get_adsets_for_campaign(campaign_id)
    if isinstance(adsets, dict) and 'error' in adsets:
        print(f"   ❌ Error: {adsets['error']}")
    elif isinstance(adsets, list):
        print(f"   ✅ Success: Found {len(adsets)} adsets")
        for adset in adsets:
            print(f"      - {adset.get('name', 'Unknown')} (ID: {adset.get('id')})")
            
        # Test 4: Try to update Brooklyn budget
        brooklyn = next((a for a in adsets if 'brooklyn' in a.get('name', '').lower()), None)
        if brooklyn:
            print(f"\n4. Testing update_adset_budget for Brooklyn:")
            print(f"   Adset: {brooklyn['name']}")
            print(f"   ID: {brooklyn['id']}")
            result = sdk.update_adset_budget(brooklyn['id'], daily_budget=200)
            if result.get('success'):
                print(f"   ✅ Success: {result.get('message')}")
            else:
                print(f"   ❌ Error: {result.get('error')}")
else:
    print(f"   ❌ Could not find Ryan Castro campaign")

# Test 5: Try getting account info
print("\n5. Testing account access:")
try:
    from facebook_business.adobjects.adaccount import AdAccount
    account = AdAccount(f"act_{os.getenv('META_AD_ACCOUNT_ID')}")
    info = account.api_get(fields=['name', 'account_status'])
    print(f"   ✅ Account Name: {info.get('name')}")
    print(f"   ✅ Account Status: {info.get('account_status')}")
except Exception as e:
    print(f"   ❌ Error: {e}")