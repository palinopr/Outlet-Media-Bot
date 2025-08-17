#!/usr/bin/env python3
"""Verify if the budget update actually works on Meta"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from tools.meta_sdk import MetaAdsSDK

def verify_update():
    sdk = MetaAdsSDK()
    
    print("=" * 70)
    print("VERIFYING BUDGET UPDATE ON META")
    print("=" * 70)
    
    # Step 1: Find Brooklyn adset
    print("\n1. Finding Brooklyn adset...")
    campaigns = sdk.search_campaigns("Ryan Castro")
    if not campaigns:
        print("ERROR: No Ryan Castro campaign found")
        return
    
    campaign_id = campaigns[0]['id']
    print(f"   Found campaign: {campaigns[0]['name']} (ID: {campaign_id})")
    
    # Step 2: Get adsets
    print("\n2. Getting adsets...")
    adsets = sdk.get_adsets_for_campaign(campaign_id)
    
    brooklyn_adset = None
    for adset in adsets:
        if "brooklyn" in adset['name'].lower():
            brooklyn_adset = adset
            break
    
    if not brooklyn_adset:
        print("ERROR: No Brooklyn adset found")
        return
    
    adset_id = brooklyn_adset['id']
    current_budget = brooklyn_adset.get('daily_budget', 0)
    
    # Convert cents to dollars for display
    current_budget_dollars = int(current_budget) / 100 if current_budget else 0
    
    print(f"   Brooklyn adset: {brooklyn_adset['name']}")
    print(f"   ID: {adset_id}")
    print(f"   Current budget: ${current_budget_dollars:.2f} (raw: {current_budget} cents)")
    
    # Step 3: Try to update to $200
    print("\n3. Attempting to update budget to $200...")
    result = sdk.update_adset_budget(adset_id, 200)
    
    print("\n   Update result:")
    print(f"   Success: {result.get('success', False)}")
    if 'error' in result:
        print(f"   ERROR: {result['error']}")
    else:
        print(f"   Message: {result.get('message', 'No message')}")
    
    # Step 4: Verify the change
    print("\n4. Fetching updated adset to verify...")
    updated_adsets = sdk.get_adsets_for_campaign(campaign_id)
    
    for adset in updated_adsets:
        if adset['id'] == adset_id:
            new_budget = adset.get('daily_budget', 0)
            new_budget_dollars = int(new_budget) / 100 if new_budget else 0
            
            print(f"   New budget: ${new_budget_dollars:.2f} (raw: {new_budget} cents)")
            
            if new_budget == "20000" or new_budget == 20000:  # $200 in cents
                print("\n   ✅ SUCCESS: Budget was updated to $200!")
            elif new_budget == current_budget:
                print("\n   ⚠️ WARNING: Budget unchanged")
                print("   Possible reasons:")
                print("   - API call succeeded but Meta didn't apply the change")
                print("   - Permission issues")
                print("   - Budget limits or restrictions")
            else:
                print(f"\n   ⚠️ Budget changed but not to $200 (now ${new_budget_dollars:.2f})")
            break
    
    # Step 5: Check account permissions
    print("\n5. Checking if this is a sandbox/test account...")
    print("   Note: Sandbox accounts may report success but not actually update")
    
    # Try to get account info
    try:
        account_info = sdk.account.api_get(fields=['name', 'account_status', 'disable_reason'])
        print(f"   Account name: {account_info.get('name', 'Unknown')}")
        print(f"   Account status: {account_info.get('account_status', 'Unknown')}")
        if account_info.get('disable_reason'):
            print(f"   Disable reason: {account_info['disable_reason']}")
    except Exception as e:
        print(f"   Could not fetch account info: {e}")

if __name__ == "__main__":
    verify_update()