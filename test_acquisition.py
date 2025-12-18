import requests
import json
import time

# Wait for backend
time.sleep(2)

# Create test firm with unique name
import random
unique_id = random.randint(1000, 9999)
firm_name = f'TestAcquirer_{unique_id}'
user_name = f'Buyer_{unique_id}'

print(f"Creating test firm {firm_name}...")
r = requests.post('http://localhost:8000/api/firms', json={'firm_name': firm_name, 'user_name': user_name})
print(json.dumps(r.json(), indent=2))

if not r.json().get('success'):
    print("Failed to create firm, exiting")
    exit(1)

firm_id = r.json()['firm_id']

# Test acquisition cost
print(f"\nTesting acquisition cost for firm {firm_id} acquiring firm 1...")
r2 = requests.get(f'http://localhost:8000/api/firms/{firm_id}/acquisition-cost/1')
print(f'Status: {r2.status_code}')
if r2.status_code == 200:
    print(json.dumps(r2.json(), indent=2))
else:
    print(f'Error: {r2.text}')

# Try to acquire
print(f"\nAttempting to acquire firm 1...")
r3 = requests.post(f'http://localhost:8000/api/firms/{firm_id}/acquire/1')
print(f'Status: {r3.status_code}')
if r3.status_code == 200:
    result = r3.json()
    print("SUCCESS!")
    print(json.dumps(result, indent=2))
else:
    print(f'Error: {r3.text}')

# Check market overview
print(f"\nChecking market overview after acquisition...")
r4 = requests.get('http://localhost:8000/api/market')
if r4.status_code == 200:
    market = r4.json()
    print(f"Total firms: {len(market['firms'])}")
    for firm in market['firms'][:5]:
        print(f"  - {firm['name']}: Market Share {firm['market_share']}%, Cash €{firm['cash']:,.0f}")
else:
    print(f'Error: {r4.text}')
