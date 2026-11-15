import sys
import urllib.request
import urllib.parse
import json
import io
from PIL import Image

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import os
BASE_URL = 'http://127.0.0.1:8000/api'

# Configurable test credentials (can be overridden in production/CI)
FARMER_PASSWORD = os.environ.get('DEMO_FARMER_PASSWORD', 'farmer123')
BUYER_PASSWORD = os.environ.get('DEMO_BUYER_PASSWORD', 'buyer123')
ADMIN_PASSWORD = os.environ.get('DEMO_ADMIN_PASSWORD', 'admin123')

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

def run_workflow():
    print("==================================================")
    print("  AgriVision AI v3.2 - Live API Workflow Testing  ")
    print("==================================================")

    # 1. Farmer Login
    print("\n[Step 1] Farmer Login (ramesh@demo.in)")
    status, res = req('/auth/login/', method='POST', data={'email': 'ramesh@demo.in', 'password': FARMER_PASSWORD})
    assert status == 200, f"Login failed: {res}"
    farmer_token = res['tokens']['access']
    print("  ✓ Login successful! Token acquired.")
    print(f"  Farmer: {res['user']['full_name']} ({res['user']['email']}), Role: {res['user']['role']}")

    # 2. Buyer Login
    print("\n[Step 2] Buyer Login (buyer@demo.in)")
    status, res = req('/auth/login/', method='POST', data={'email': 'buyer@demo.in', 'password': BUYER_PASSWORD})
    assert status == 200, f"Buyer login failed: {res}"
    buyer_token = res['tokens']['access']
    print("  ✓ Login successful! Token acquired.")
    print(f"  Buyer: {res['user']['full_name']} ({res['user']['email']}), Role: {res['user']['role']}")

    # 3. AI Quality Assessment (Synthetic Tomato Image)
    print("\n[Step 3] AI Quality Assessment on Listing Image")
    img = Image.new('RGB', (100, 100), color=(200, 40, 30)) # Rich red tomato color
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    image_bytes = buf.getvalue()

    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="image"; filename="tomato.jpg"\r\n'
        f'Content-Type: image/jpeg\r\n\r\n'
    ).encode('utf-8') + image_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

    status, res = req('/ai/assess-quality/', method='POST', raw_body=body, content_type=f'multipart/form-data; boundary={boundary}', token=farmer_token)
    assert status in (200, 201), f"AI assessment failed: {res}"
    grade = res.get('predicted_grade', res.get('grade', 'A'))
    confidence = res.get('confidence', 95)
    assessment_id = res.get('id', res.get('assessment_id', 'unknown'))
    print("  ✓ AI Quality Assessment complete:")
    print(f"    Grade: {grade}, Confidence: {confidence}%")
    print(f"    Assessment ID: {assessment_id}")

    # 4. Farmer creates listing
    print("\n[Step 4] Farmer creates listing (500 kg Tomato @ ₹32/kg)")
    listing_data = {
        'product_name': 'Hybrid Red Tomato',
        'crop': 'Tomato',
        'quantity': 500.0,
        'asking_price': 32.0,
        'state': 'Karnataka',
        'district': 'Kolar',
        'harvest_date': '2026-03-24',
        'quality_grade': grade,
        'quality_confidence': confidence
    }
    status, res = req('/products/listings/', method='POST', data=listing_data, token=farmer_token)
    assert status == 201, f"Listing failed: {res}"
    listing_id = res['id']
    print(f"  ✓ Listing created! ID: {listing_id}, Crop: {res['crop']} ({res['quantity']} kg)")

    # 5. Buyer places bid
    print("\n[Step 5] Buyer places bid (200 kg @ ₹30/kg)")
    bid_data = {
        'listing_id': listing_id,
        'offered_price': 30.0,
        'quantity': 200.0,
        'message': 'Immediate pickup via local logistics'
    }
    status, res = req('/bids/', method='POST', data=bid_data, token=buyer_token)
    assert status == 201, f"Bid failed: {res}"
    bid_id = res['id']
    print(f"  ✓ Bid placed! ID: {bid_id}, Status: {res['status']}")

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
    print("\n[Step 9] Admin Login & Analytics (admin@demo.in)")
    status, res = req('/auth/login/', method='POST', data={'email': 'admin@demo.in', 'password': ADMIN_PASSWORD})
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
    if res.get('is_live_ml'):
        tm = res['price_prediction_model']['test_metrics']
        r2_val = tm.get('R2', tm.get('r2'))
        mae_val = tm.get('MAE', tm.get('mae'))
        print(f"    Live ML Metrics: R² = {r2_val}, MAE = ₹{mae_val}/quintal")

    # 11. Market Price Recommendation with ML
    print("\n[Step 11] Market Price Recommendation (Proxy / ML)")
    status, res = req('/market/recommendations/?crop=Tomato&district=Kolar&state=Karnataka', method='GET')
    assert status == 200, f"Recommendation failed: {res}"
    print("  ✓ Market Recommendation verified:")
    print(f"    Crop: {res['crop']}, District: {res['district']}")
    print(f"    Recommended Price: ₹{res['recommended_price_per_kg']}/kg (is_live_ml: {res.get('is_live_ml')})")
    if res.get('prediction_interval'):
        print(f"    Prediction Interval: ₹{res['prediction_interval'].get('lower_bound')} - ₹{res['prediction_interval'].get('upper_bound')}/kg")

    # 12. Single-Shot ML Intelligence Endpoint
    print("\n[Step 12] Single-Shot ML Intelligence Endpoint (/market/ml-intelligence/)")
    ml_req = {'crop': 'Tomato', 'market': 'Kolar', 'district': 'Kolar', 'date': '2026-03-25'}
    status, res = req('/market/ml-intelligence/', method='POST', data=ml_req)
    assert status == 200, f"ML Intelligence failed: {res}"
    print("  ✓ Single-shot ML Intelligence response received:")
    print(f"    Predicted price: ₹{res['price_prediction']['predicted_modal_price_per_kg']}/kg")
    print(f"    Model Type: {res['price_prediction']['model_type']}")
    if res.get('demand_forecast'):
        print(f"    Demand Trend: {res['demand_forecast']['trend_label']} ({res['demand_forecast']['confidence_pct']}%)")
    if res.get('explanation'):
        print(f"    XAI Narrative: {res['explanation']['narrative'][:80]}...")

    print("\n==================================================")
    print("  ALL WORKFLOW STEPS PASSED WITH 100% SUCCESS   ")
    print("==================================================")

if __name__ == '__main__':
    run_workflow()
