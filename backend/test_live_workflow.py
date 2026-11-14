import urllib.request
import urllib.parse
import json
import io
from PIL import Image

BASE_URL = 'http://127.0.0.1:8000/api'

def req(path, method='GET', data=None, token=None, is_json=True, raw_body=None, content_type=None):
    url = BASE_URL + path
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    body = None
    if raw_body is not None:
        body = raw_body
        if content_type:
            headers['Content-Type'] = content_type
    elif data is not None:
        if is_json:
            body = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        else:
            body = urllib.parse.urlencode(data).encode('utf-8')
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as resp:
            content = resp.read().decode('utf-8')
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8')
        try:
            err_data = json.loads(content)
        except:
            err_data = content
        return e.code, err_data

print("==================================================")
print("  AgriVision AI v3.2 - Live API Workflow Testing  ")
print("==================================================")

# 1. Farmer Login
print("\n[Step 1] Farmer Login (ramesh@demo.in / farmer123)")
status, res = req('/auth/login/', method='POST', data={'email': 'ramesh@demo.in', 'password': 'farmer123'})
assert status == 200, f"Login failed: {res}"
farmer_token = res['tokens']['access']
print("  ✓ Login successful! Token acquired.")
print(f"  Farmer: {res['user']['full_name']} ({res['user']['email']}), Role: {res['user']['role']}")

# 2. Buyer Login
print("\n[Step 2] Buyer Login (buyer@demo.in / buyer123)")
status, res = req('/auth/login/', method='POST', data={'email': 'buyer@demo.in', 'password': 'buyer123'})
assert status == 200, f"Buyer login failed: {res}"
buyer_token = res['tokens']['access']
buyer_verified = res['user']['is_verified']
print("  ✓ Buyer Login successful! Token acquired.")
print(f"  Buyer: {res['user']['full_name']}, Verified: {buyer_verified}")

# 3. Farmer creates produce listing
print("\n[Step 3] Farmer creates listing (500 kg Tomato)")
status, res = req('/products/', method='POST', data={
    'product_name': 'Live Test Hybrid Tomato',
    'crop': 'Tomato',
    'quantity': 500.0,
    'unit': 'kg',
    'asking_price': 24.5,
    'quality_grade': 'A',
    'quality_confidence': 91,
    'harvest_date': '2026-11-13',
    'district': 'Kolar',
    'status': 'active'
}, token=farmer_token)
assert status == 201, f"Product creation failed: {res}"
listing_id = res['id']
print(f"  ✓ Listing created: {res['product_name']} (ID: {listing_id})")
print(f"  Quantity: {res['quantity']} {res['unit']}, Asking: ₹{res['asking_price']}/kg, Grade: {res['quality_grade']}")

# 4. Buyer browses products
print("\n[Step 4] Buyer browses products")
status, res = req('/products/?crop=Tomato', method='GET', token=buyer_token)
assert status == 200, f"Browse failed: {res}"
items = res if isinstance(res, list) else res.get('results', [])
print(f"  ✓ Found {len(items)} Tomato listings matching criteria.")

# 5. Verified Buyer places bid for 200 kg
print("\n[Step 5] Verified Buyer places bid (200 kg at ₹23.5/kg)")
status, res = req('/bids/', method='POST', data={
    'listing_id': listing_id,
    'offered_price': 23.5,
    'quantity': 200.0,
    'message': 'Fast dispatch requested'
}, token=buyer_token)
assert status == 201, f"Bid creation failed: {res}"
bid_id = res['id']
print(f"  ✓ Bid placed! Bid ID: {bid_id}")
print(f"  Offered: ₹{res['offered_price']}/kg for {res['quantity']} kg, Status: {res['status']}")

# 6. Farmer accepts bid
print("\n[Step 6] Farmer accepts bid (Partial quantity fulfillment)")
status, res = req(f'/bids/{bid_id}/accept/', method='POST', token=farmer_token)
assert status == 200, f"Accept failed: {res}"
order_id = res['order_id']
remaining_qty = res['remaining_quantity']
print("  ✓ Bid accepted!")
print(f"  Order ID: {order_id}")
print(f"  Remaining listing stock: {remaining_qty} kg (Status: {res['listing_status']})")
assert remaining_qty == 300.0, f"Expected 300.0 remaining, got {remaining_qty}"

# 7. Check Order details
print("\n[Step 7] Verify Order Details")
status, res = req(f'/orders/{order_id}/', method='GET', token=buyer_token)
assert status == 200, f"Order fetch failed: {res}"
print(f"  ✓ Order verified: Total ₹{res['total_amount']} ({res['quantity']} kg @ ₹{res['agreed_price']}/kg)")
print(f"  Delivery Status: {res['delivery_status']}, Payment Status: {res['payment_status']}")

# 8. Order Dispatch & Delivery Workflow
print("\n[Step 8] Farmer dispatches, then confirms delivery")
status, res = req(f'/orders/{order_id}/dispatch/', method='POST', token=farmer_token)
assert status == 200, f"Dispatch failed: {res}"
print(f"  ✓ Dispatched! Status: {res['order']['delivery_status']}")

status, res = req(f'/orders/{order_id}/deliver/', method='POST', token=buyer_token)
assert status == 200, f"Deliver failed: {res}"
print(f"  ✓ Delivered! Status: {res['order']['delivery_status']}")

# 9. Admin Login & Analytics
print("\n[Step 9] Admin Login & Analytics (admin@demo.in / admin123)")
status, res = req('/auth/login/', method='POST', data={'email': 'admin@demo.in', 'password': 'admin123'})
assert status == 200, f"Admin login failed: {res}"
admin_token = res['tokens']['access']

status, res = req('/admin/analytics/', method='GET', token=admin_token)
assert status == 200, f"Analytics failed: {res}"
print("  ✓ Admin Analytics successfully retrieved:")
print(f"    Users: {res['users']['total']} ({res['users']['farmers']} farmers, {res['users']['buyers']} buyers)")
print(f"    Listings: {res['listings']['total']} ({res['listings']['active']} active)")
print(f"    Orders: {res['orders']['total']}, GMV: ₹{res['orders']['total_gmv']}")

# 10. AI Model Transparency Endpoint
print("\n[Step 10] AI Model Transparency & Monitoring")
status, res = req('/admin/models/', method='GET', token=admin_token)
assert status == 200, f"Model monitoring failed: {res}"
print("  ✓ AI Model transparency endpoint verified:")
print(f"    Engine: {res['engine_name']}")
print(f"    Implementation: {res['implementation']}")
print(f"    Disclaimer: {res['certification_statement']}")

print("\n==================================================")
print("  ALL 10 WORKFLOW STEPS PASSED WITH 100% SUCCESS  ")
print("==================================================")
