#!/usr/bin/env python3
"""Debug the exact update call"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from tools.meta_sdk import MetaAdsSDK

sdk = MetaAdsSDK()

print("Testing update_adset_budget with explicit parameters...")
print("-" * 50)

# Test with Brooklyn adset ID from previous test
adset_id = "120232009098430525"
daily_budget = 200  # in dollars

print(f"Calling: sdk.update_adset_budget('{adset_id}', {daily_budget})")
result = sdk.update_adset_budget(adset_id, daily_budget)

print("\nResult:")
print(result)

print("\n" + "-" * 50)
print("Now testing with keyword arguments...")
print(f"Calling: sdk.update_adset_budget(id='{adset_id}', daily_budget={daily_budget})")
result2 = sdk.update_adset_budget(id=adset_id, daily_budget=daily_budget)

print("\nResult:")
print(result2)