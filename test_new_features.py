"""
test_new_features.py
Verifies all newly implemented features:
1. Blank startup idea by default with custom typing support
2. Target Industry (ONE combined searchable/selectable input with "Select industry or enter custom industry...")
3. Target Customers (ONE combined searchable/selectable input with "Select customer or enter custom customer...")
4. Location manual entry (Vizianagaram, Visakhapatnam, Hyderabad, Vijayawada, Bengaluru) with NO GPS
5. AI Blueprint engine takes all 4 inputs (Idea, Target Industry, Target Customers, Location)
6. Suitable Nearby Business Locations with Google Maps links
7. No AI buttons on inputs (AI is solely for the generation/summarisation section)
"""

import os
import sys
import json
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app import app, init, conn
from blueprint_engine import (
    PREDEFINED_INDUSTRIES,
    PREDEFINED_TARGET_CUSTOMERS
)

def test_all_new_features():
    init()
    client = app.test_client()

    print("=" * 70)
    print("VERIFYING COMBINED COMBOBOX INPUTS & BLUEPRINT ENGINE FEATURES")
    print("=" * 70)

    # 1. Predefined Lists Verification (Exact lists from prompt)
    print("\n[1] Checking Predefined Target Industries & Customers...")
    assert len(PREDEFINED_INDUSTRIES) == 24, f"Expected 24 industries, found {len(PREDEFINED_INDUSTRIES)}"
    assert "Technology" in PREDEFINED_INDUSTRIES
    assert "Food & Beverage" in PREDEFINED_INDUSTRIES
    assert "Artificial Intelligence" in PREDEFINED_INDUSTRIES
    assert "Agriculture" in PREDEFINED_INDUSTRIES
    assert "Transportation" in PREDEFINED_INDUSTRIES
    assert "Cyber Security" in PREDEFINED_INDUSTRIES
    assert "Other" in PREDEFINED_INDUSTRIES

    assert len(PREDEFINED_TARGET_CUSTOMERS) == 18, f"Expected 18 customer groups, found {len(PREDEFINED_TARGET_CUSTOMERS)}"
    assert "Students" in PREDEFINED_TARGET_CUSTOMERS
    assert "College Students" in PREDEFINED_TARGET_CUSTOMERS
    assert "Working Professionals" in PREDEFINED_TARGET_CUSTOMERS
    assert "Job Seekers" in PREDEFINED_TARGET_CUSTOMERS
    assert "Small Businesses" in PREDEFINED_TARGET_CUSTOMERS
    assert "Farmers" in PREDEFINED_TARGET_CUSTOMERS
    assert "Other" in PREDEFINED_TARGET_CUSTOMERS
    print(f"  [PASS] {len(PREDEFINED_INDUSTRIES)} Industries & {len(PREDEFINED_TARGET_CUSTOMERS)} Customer groups exactly matched prompt.")

    # 2. Generate Page GET (Checks ONE combined control for Industry & Customers, NO AI buttons on inputs)
    print("\n[2] Checking /generate GET form structure for single combined controls...")
    with client.session_transaction() as sess:
        sess["uid"] = 1
        sess["name"] = "Pavani"
        sess["email"] = "pavanibevara05@gmail.com"

    resp_get = client.get('/generate')
    assert resp_get.status_code == 200
    html_get = resp_get.data.decode('utf-8')
    assert 'name="idea"' in html_get
    assert 'placeholder="Enter your startup idea' in html_get
    # Ensure textarea does not have hardcoded default text inside it
    assert '>Smart irrigation service for farmers</textarea>' not in html_get

    # Verify ONE combined field for Industry
    assert 'placeholder="Select industry or enter custom industry..."' in html_get
    assert 'name="industry"' in html_get
    assert 'id="industry"' in html_get
    assert 'industry_select' not in html_get
    assert 'industry_custom' not in html_get

    # Verify ONE combined field for Target Customers
    assert 'placeholder="Select customer or enter custom customer..."' in html_get
    assert 'name="target_customers"' in html_get
    assert 'id="target_customers"' in html_get
    assert 'target_customers_select' not in html_get
    assert 'target_customers_custom' not in html_get

    # Verify NO AI buttons in inputs (AI is reserved for the summarisation/generation section)
    assert 'Suggest Target Industry with AI' not in html_get
    assert 'Generate Target Customers with AI' not in html_get

    # Verify Location has no GPS
    assert 'location-input' in html_get
    assert 'navigator.geolocation' not in html_get
    print("  [PASS] /generate form verified: Single combined controls, placeholders match prompt, zero GPS, no AI input buttons.")

    # 3. End-to-End Blueprint Generation with Predefined Selection
    # Startup Idea: Student Food Delivery, Target Customers: College Students, Industry: Food & Beverage, Location: Vizianagaram
    print("\n[3] Generating Blueprint with Selected Options: 'Student Food Delivery', College Students, Food & Beverage, Vizianagaram...")
    resp_gen = client.post('/generate', data={
        'idea': 'Student Food Delivery',
        'industry': 'Food & Beverage',
        'target_customers': 'College Students',
        'budget': '150000',
        'team_size': '2',
        'location': 'Vizianagaram',
        'location_details': ''
    }, follow_redirects=True)
    assert resp_gen.status_code == 200
    html_gen = resp_gen.data.decode('utf-8')

    # Verify database record
    c = conn()
    r = c.execute("SELECT * FROM blueprints ORDER BY id DESC LIMIT 1").fetchone()
    c.close()
    bid = r["id"]
    b = json.loads(r["data"])

    # Verifications
    assert b['idea'] == 'Student Food Delivery'
    assert b['target_customers'] == 'College Students'
    assert 'Food & Beverage' in b['industry']
    assert 'Vizianagaram' in b['location_summary']
    assert b['budget_allocation']['user_input_budget'] == 150000
    assert b['budget_allocation']['total_planned_investment'] <= 150000

    # Suitable Nearby Business Locations verification
    assert 'suitable_nearby_places' in b
    places = b['suitable_nearby_places']
    assert len(places) >= 3, f"Expected >= 3 nearby places, found {len(places)}"
    print("  Recommended Suitable Nearby Places:")
    for p in places:
        print(f"    - 📍 {p['place_type']}: {p['reason']}")
        print(f"      🗺️ Maps URL: {p['maps_url']}")
        assert 'https://www.google.com/maps/search/?api=1&query=' in p['maps_url']
        assert 'Vizianagaram' in p['maps_url'] or 'vizianagaram' in p['maps_url'].lower()

    # Executive Summary (Summarisation section powered by AI)
    exec_sum = b['executive_summary']
    assert 'Vizianagaram' in exec_sum
    assert 'College Students' in exec_sum or 'students' in exec_sum.lower()
    assert '150,000' in exec_sum

    # UI Verification
    assert 'Suitable Nearby Business Locations' in html_gen
    assert 'Open Google Maps' in html_gen
    assert 'College Students' in html_gen
    print("  [PASS] Blueprint successfully generated using single combined inputs.")

    # 4. TXT and PDF Downloads Verification
    print("\n[4] Verifying TXT and PDF downloads...")
    resp_txt = client.get(f"/download/{bid}")
    assert resp_txt.status_code == 200
    txt_content = resp_txt.data.decode('utf-8')
    assert "Target Customers: College Students" in txt_content
    assert "SUITABLE NEARBY BUSINESS LOCATIONS" in txt_content
    assert "https://www.google.com/maps/search/?api=1&query=" in txt_content
    print("  [PASS] TXT download contains Target Customers and Nearby Places.")

    resp_pdf = client.get(f"/download-pdf/{bid}")
    assert resp_pdf.status_code == 200
    assert resp_pdf.mimetype == "application/pdf"
    assert len(resp_pdf.data) > 1000
    print(f"  [PASS] PDF download generated successfully ({len(resp_pdf.data):,} bytes).")

    # 5. End-to-End Blueprint Generation with Completely CUSTOM Values
    # User types custom industry: "AI-powered Rural Supply Chain", custom customer: "Hostel Students in Urban Areas"
    print("\n[5] Generating Blueprint with Completely CUSTOM Industry & CUSTOM Customers...")
    resp_custom = client.post('/generate', data={
        'idea': 'Organic Farming Marketplace',
        'industry': 'AI-powered Rural Supply Chain',
        'target_customers': 'Hostel Students in Urban Areas',
        'budget': '300000',
        'team_size': '3',
        'location': 'Vijayawada, Andhra Pradesh',
        'location_details': ''
    }, follow_redirects=True)
    assert resp_custom.status_code == 200

    c = conn()
    r_cust = c.execute("SELECT * FROM blueprints ORDER BY id DESC LIMIT 1").fetchone()
    c.close()
    b_cust = json.loads(r_cust["data"])
    assert b_cust['industry'] == 'AI-powered Rural Supply Chain'
    assert b_cust['target_customers'] == 'Hostel Students in Urban Areas'
    assert 'Vijayawada' in b_cust['location_summary']
    print("  [PASS] Completely custom typed industry & custom customer correctly accepted and generated.")

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == '__main__':
    test_all_new_features()
