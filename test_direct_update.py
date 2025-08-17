#!/usr/bin/env python3
"""Direct API test to debug the update issue"""
import os
import sys
import json
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from tools.meta_sdk import MetaAdsSDK as MetaSDK

def test_direct_update():
    """Test the exact same operation the bot is trying"""
    sdk = MetaSDK()
    
    print("=" * 70)
    print("DIRECT API TEST - Budget Update")
    print("=" * 70)
    
    # Step 1: Search for Ryan Castro campaign
    print("\n1. Searching for Ryan Castro campaign...")
    campaigns = sdk.search_campaigns("Ryan Castro")
    
    if not campaigns or len(campaigns) == 0:
        print("ERROR: No campaigns found for 'Ryan Castro'")
        return
    
    campaign = campaigns[0]
    campaign_id = campaign['id']
    print(f"   Found campaign: {campaign['name']} (ID: {campaign_id})")
    
    # Step 2: Get adsets for the campaign
    print(f"\n2. Getting adsets for campaign {campaign_id}...")
    adsets = sdk.get_adsets_for_campaign(campaign_id)
    
    if not adsets or len(adsets) == 0:
        print("ERROR: No adsets found for this campaign")
        return
    
    print(f"   Found {len(adsets)} adsets:")
    for adset in adsets:
        print(f"   - {adset['name']} (ID: {adset['id']})")
    
    # Find Brooklyn adset
    brooklyn_adset = None
    for adset in adsets:
        if "brooklyn" in adset['name'].lower():
            brooklyn_adset = adset
            break
    
    if not brooklyn_adset:
        print("   No Brooklyn adset found, using first adset")
        brooklyn_adset = adsets[0]
    
    print(f"\n3. Selected adset: {brooklyn_adset['name']} (ID: {brooklyn_adset['id']})")
    
    # Step 3: Update the budget
    print(f"\n4. Updating budget to $200 for adset {brooklyn_adset['id']}...")
    
    try:
        result = sdk.update_adset_budget(brooklyn_adset['id'], 200)
        
        print("\n   RAW API RESPONSE:")
        print("   " + "-" * 50)
        print(json.dumps(result, indent=2))
        print("   " + "-" * 50)
        
        # Check if update was successful
        if result and isinstance(result, dict):
            if result.get('success') == True:
                print("\n   ✅ SUCCESS: Budget updated successfully!")
            elif 'error' in result:
                print(f"\n   ❌ ERROR: {result['error']}")
            else:
                print("\n   ⚠️ UNKNOWN RESULT - Check raw response above")
        else:
            print(f"\n   ⚠️ Unexpected result type: {type(result)}")
            
    except Exception as e:
        print(f"\n   ❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("ANALYSIS:")
    print("If this shows success=True but bot reports error, the issue is in format_response")
    print("If this shows an actual error, the issue is in the API call")

if __name__ == "__main__":
    test_direct_update()