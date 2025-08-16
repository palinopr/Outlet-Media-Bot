#!/usr/bin/env python3
import os
import requests
import json
import re
import sys

# Get trace ID from command line or use default
trace_id = sys.argv[1] if len(sys.argv) > 1 else 'e644da71-7dff-41be-865b-9a850d2f85c5'

# Load from .env file
with open('.env', 'r') as f:
    for line in f:
        if 'LANGCHAIN_API_KEY' in line:
            api_key = line.split('=')[1].strip()
            break

headers = {'x-api-key': api_key}
url = f'https://api.smith.langchain.com/runs/{trace_id}'
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    
    print('=' * 70)
    print('TRACE ANALYSIS:', trace_id)
    print('=' * 70)
    
    # Basic info
    print(f'\nRun Name: {data.get("name", "N/A")}')
    print(f'Status: {data.get("status", "N/A")}')
    print(f'Error: {data.get("error", "None")}')
    
    # Get user request
    inputs = data.get('inputs', {})
    user_request = inputs.get('current_request', inputs.get('input', 'N/A'))
    print(f'\nUSER REQUEST: "{user_request}"')
    
    # Get outputs
    outputs = data.get('outputs', {})
    
    # Check SDK response
    if 'sdk_response' in outputs:
        sdk_resp = outputs['sdk_response']
        
        if isinstance(sdk_resp, dict):
            if 'error' in sdk_resp:
                print(f'\n❌ SDK ERROR: {sdk_resp["error"]}')
                
            if 'multi_step_results' in sdk_resp:
                results = sdk_resp['multi_step_results']
                print(f'\nMulti-step execution: {len(results)} operations')
                
                # Check each result
                for i, result in enumerate(results):
                    if isinstance(result, list):
                        print(f'  Step {i+1}: Returned {len(result)} items')
                    elif isinstance(result, dict) and 'error' in result:
                        print(f'  Step {i+1}: ERROR - {result["error"][:100]}')
                    elif isinstance(result, dict):
                        print(f'  Step {i+1}: Success')
    
    # Get final answer
    if 'final_answer' in outputs:
        answer = outputs['final_answer']
        print(f'\nFINAL DISCORD RESPONSE:')
        print('-' * 50)
        print(answer)
        
        # Validate data
        print('\n' + '=' * 70)
        print('DATA VALIDATION:')
        
        # Check for real values
        real_values = ['53.96', '388.08', '319.10', '288.87', '245.23', '338.30']
        found = [v for v in real_values if v in answer]
        
        if found:
            print(f'✅ REAL DATA FOUND: {found}')
        elif 'Unable to retrieve' in answer:
            print('✅ CORRECTLY REPORTED NO DATA (instead of hallucinating)')
        else:
            # Check if it has any dollar amounts
            amounts = re.findall(r'\$[\d,]+\.?\d*', answer)
            if amounts:
                print(f'⚠️ POSSIBLY HALLUCINATED VALUES: {amounts[:5]}')
            else:
                print('✅ No numeric values (correctly avoided hallucination)')
    
    # Get child runs
    child_url = f'https://api.smith.langchain.com/runs?filter=eq(parent_run_id, "{trace_id}")&limit=10'
    child_response = requests.get(child_url, headers=headers)
    
    if child_response.status_code == 200:
        child_data = child_response.json()
        runs = child_data.get('runs', [])
        print(f'\n\nCHILD RUNS: {len(runs)} found')
        
        for run in runs:
            name = run.get('name', '')
            status = run.get('status', '')
            error = run.get('error')
            
            if error:
                print(f'  ❌ {name}: {status} - ERROR: {error[:100]}')
            else:
                print(f'  ✅ {name}: {status}')
else:
    print(f'Error {response.status_code}: Could not fetch trace')