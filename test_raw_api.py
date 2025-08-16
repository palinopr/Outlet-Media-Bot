#!/usr/bin/env python3
from dotenv import load_dotenv
from tools.meta_sdk import MetaAdsSDK
from facebook_business.adobjects.adset import AdSet
from facebook_business.api import FacebookAdsApi
import os

load_dotenv()

# Initialize API
FacebookAdsApi.init(
    access_token=os.getenv("META_ACCESS_TOKEN"),
    api_version="v21.0"
)

# Get raw insights without conversion
adset = AdSet('120232176000230525')  # Retargeting
insights = adset.get_insights(
    params={'date_preset': 'maximum'},
    fields=['spend', 'purchase_roas', 'actions', 'action_values']
)

if insights:
    data = insights[0].export_all_data()
    print('RAW API RESPONSE:')
    print('=' * 70)
    print(f'spend (raw): {data.get("spend")}')
    print(f'Type: {type(data.get("spend"))}')
    
    # Check if it's already in dollars or cents
    raw_spend = data.get('spend')
    print(f'\nIf cents → dollars: ${float(raw_spend)/100:.2f}')
    print(f'If already dollars: ${float(raw_spend):.2f}')
    print(f'\nFacebook UI shows: $52.91')
    print(f'So the API value of {raw_spend} is in CENTS')