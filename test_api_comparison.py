#!/usr/bin/env python3
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adset import AdSet
import os

load_dotenv()

FacebookAdsApi.init(
    access_token=os.getenv('META_ACCESS_TOKEN'),
    api_version='v21.0'
)

# All adset IDs
adsets = [
    ('Retargeting', '120232176000230525'),
    ('Brooklyn', '120232009098430525'),
    ('Miami', '120232008849250525'),
    ('Houston', '120232007790420525'),
    ('Chicago', '120232007448100525'),
    ('LA', '120232006608680525')
]

print('RAW API DATA vs FACEBOOK UI:')
print('=' * 80)
print(f'{'City':15} | {'API Raw':>10} | {'API/100':>10} | {'FB UI':>10} | {'Match?':>8}')
print('-' * 80)

total_api = 0
total_fb_ui = [52.91, 384.87, 317.29, 286.12, 242.79, 336.10]

for i, (name, adset_id) in enumerate(adsets):
    adset = AdSet(adset_id)
    insights = adset.get_insights(
        params={'date_preset': 'maximum'},
        fields=['spend']
    )
    
    if insights:
        raw_spend = insights[0].get('spend')
        api_value = float(raw_spend)
        api_div_100 = api_value / 100
        fb_ui_value = total_fb_ui[i]
        
        match = 'YES' if abs(api_value - fb_ui_value) < 0.01 else 'NO'
        
        print(f'{name:15} | ${api_value:9.2f} | ${api_div_100:9.2f} | ${fb_ui_value:9.2f} | {match:>8}')
        total_api += api_value

print('-' * 80)
print(f'{'TOTAL':15} | ${total_api:9.2f} | ${total_api/100:9.2f} | ${1620.08:9.2f}')

print('\nCONCLUSION:')
if abs(total_api - 1620.08) < 1:
    print('✅ API returns values in DOLLARS (no conversion needed)')
elif abs(total_api/100 - 1620.08) < 1:
    print('❌ API returns values in CENTS (need to divide by 100)')
else:
    print('⚠️ API values do not match Facebook UI!')