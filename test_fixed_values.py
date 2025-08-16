#!/usr/bin/env python3
from dotenv import load_dotenv
from tools.meta_sdk import MetaAdsSDK

load_dotenv()
sdk = MetaAdsSDK()

print('TESTING UPDATED SDK - Should match Facebook UI')
print('=' * 70)

# Facebook UI values
fb_ui = {
    'Retargeting': 52.91,
    'Brooklyn': 384.87,
    'Miami': 317.29,
    'Houston': 286.12,
    'Chicago': 242.79,
    'LA': 336.10
}

campaigns = sdk.search_campaigns('Ryan')
if campaigns:
    adsets = sdk.get_adsets_for_campaign(campaigns[0]['id'])
    
    print(f'{"City":20} | {"SDK Value":>10} | {"FB UI":>10} | {"Match?":>8}')
    print('-' * 70)
    
    total_sdk = 0
    city_names = ['Retargeting', 'Brooklyn', 'Miami', 'Houston', 'Chicago', 'LA']
    
    for i, adset in enumerate(adsets):
        insights = sdk.get_adset_insights(adset['id'], date_preset='maximum')
        if isinstance(insights, dict) and 'error' not in insights:
            # Should now be in dollars, no division needed
            spend = insights.get('spend_dollars', 0)
            city = city_names[i]
            fb_value = fb_ui[city]
            
            match = 'YES ✅' if abs(spend - fb_value) < 0.01 else 'NO ❌'
            
            print(f'{city:20} | ${spend:9.2f} | ${fb_value:9.2f} | {match:>8}')
            total_sdk += spend
    
    print('-' * 70)
    print(f'{"TOTAL":20} | ${total_sdk:9.2f} | ${1620.08:9.2f} | {"YES ✅" if abs(total_sdk - 1620.08) < 1 else "NO ❌":>8}')