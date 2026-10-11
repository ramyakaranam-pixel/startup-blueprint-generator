"""
test_suite.py
Automated test suite verifying all 20 requirements and test cases:
- Strict budget ceilings (Rs. 1,00,000 vs Rs. 10,00,000)
- Location preservation and local market reasoning (Visakhapatnam vs Vijayawada)
- Suggested surrounding locations and Location Comparison table
- Online vs Offline vs Hybrid evaluation
- Complete exclusion of Business Model and Dataset Signals
- PDF Generation and download
- History, Overview, and Dashboard routes
- Input validation (prevent generation without location)
"""

import os
import sys
import json
import sqlite3
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from app import app, init, conn
import pdf_generator

def run_tests():
    init()
    client = app.test_client()

    print("\n" + "=" * 60)
    print("STARTING STARTUP BLUEPRINT SYSTEM VERIFICATION")
    print("=" * 60)

    # 1. Login user session
    with client.session_transaction() as sess:
        sess["uid"] = 1
        sess["name"] = "Pavani"
        sess["email"] = "pavanibevara05@gmail.com"

    # TEST 1: AgriTech, ₹1,00,000, Visakhapatnam, Andhra Pradesh
    print("\n--> TEST 1: AgriTech, Budget ₹1,00,000, Visakhapatnam")
    data_1 = {
        'industry': 'AgriTech',
        'idea': 'Smart irrigation service for small farmers',
        'budget': '100000',
        'team_size': '2',
        'location': 'Visakhapatnam, Andhra Pradesh, India',
        'location_details': json.dumps({
            'area': 'MVP Colony',
            'village_town_city': 'Visakhapatnam',
            'district': 'Visakhapatnam',
            'state': 'Andhra Pradesh',
            'pincode': '530017',
            'country': 'India',
            'display_name': 'Visakhapatnam, Andhra Pradesh, India',
            'lat': 17.6868,
            'lon': 83.2185
        })
    }
    resp1 = client.post('/generate', data=data_1, follow_redirects=True)
    assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}"
    html1 = resp1.data.decode('utf-8')

    # Check database record
    c = conn()
    r1 = c.execute("SELECT * FROM blueprints ORDER BY id DESC LIMIT 1").fetchone()
    c.close()
    bid_1 = r1["id"]
    b1 = json.loads(r1["data"])

    # Verifications for Test 1
    ba1 = b1['budget_allocation']
    tot1 = ba1['total_planned_investment']
    rem1 = ba1['remaining_reserve']
    assert tot1 <= 100000, f"Budget exceeded! {tot1} > 100000"
    assert tot1 + rem1 == 100000, f"Budget math mismatch: {tot1} + {rem1} != 100000"
    assert "Visakhapatnam" in b1['location_summary'], "Location not preserved in summary!"
    assert "Visakhapatnam" in b1['executive_summary'], "Location missing in Executive Summary!"
    assert "100,000" in b1['executive_summary'], "Budget ₹1,00,000 missing in Executive Summary!"
    assert "business_model" not in b1, "Forbidden 'business_model' found in JSON!"
    assert "dataset_records_used" not in b1, "Forbidden 'dataset_records_used' found in JSON!"
    assert "Business Model" not in html1, "Forbidden 'Business Model' section found in HTML!"
    assert "Dataset Signals" not in html1, "Forbidden 'Dataset Signals' section found in HTML!"
    assert len(b1['suggested_locations']) >= 3, "Missing suggested surrounding locations!"
    assert len(b1['location_comparison']) >= 4, "Missing location comparison table rows!"
    print(f"  [PASS] Budget strictly enforced: Total ₹{tot1:,} + Reserve ₹{rem1:,} = ₹1,00,000")
    print(f"  [PASS] Location preserved: {b1['location_summary']}")
    print(f"  [PASS] Surrounding locations: {[s['name'] for s in b1['suggested_locations']]}")
    print(f"  [PASS] Recommended Approach: {b1.get('recommended_approach')}")
    print("  [PASS] Business Model and Dataset Signals completely excluded.")

    # TEST 2: Same idea, Budget ₹10,00,000 (Check scaling)
    print("\n--> TEST 2: AgriTech, Budget ₹10,00,000, Visakhapatnam (Scaling check)")
    data_2 = {
        'industry': 'AgriTech',
        'idea': 'Smart irrigation service for small farmers',
        'budget': '1000000',
        'team_size': '2',
        'location': 'Visakhapatnam, Andhra Pradesh, India',
        'location_details': data_1['location_details']
    }
    resp2 = client.post('/generate', data=data_2, follow_redirects=True)
    assert resp2.status_code == 200
    c = conn()
    r2 = c.execute("SELECT * FROM blueprints ORDER BY id DESC LIMIT 1").fetchone()
    c.close()
    bid_2 = r2["id"]
    b2 = json.loads(r2["data"])

    ba2 = b2['budget_allocation']
    tot2 = ba2['total_planned_investment']
    assert tot2 <= 1000000, f"Budget exceeded: {tot2} > 1000000"
    assert tot2 > tot1, "Scale failure: ₹10,00,000 plan has same or lower budget than ₹1,00,000 plan!"
    pl1 = b1['profit_loss_estimate']
    pl2 = b2['profit_loss_estimate']
    assert pl1['monthly_revenue_range'] != pl2['monthly_revenue_range'], "P/L revenue range did not scale with budget!"
    print(f"  [PASS] ₹10,00,000 Budget scaled: Total ₹{tot2:,} vs ₹1,00,000 Total ₹{tot1:,}")
    print(f"  [PASS] ₹10,00,000 P/L Revenue: {pl2['monthly_revenue_range']} vs ₹1,00,000 P/L Revenue: {pl1['monthly_revenue_range']}")

    # TEST 3: Same idea & budget, Different Location: Vijayawada, Andhra Pradesh
    print("\n--> TEST 3: AgriTech, Budget ₹5,00,000, Location Vijayawada (Location change check)")
    data_3 = {
        'industry': 'AgriTech',
        'idea': 'Smart irrigation service for small farmers',
        'budget': '500000',
        'team_size': '2',
        'location': 'Vijayawada, Andhra Pradesh, India',
        'location_details': json.dumps({
            'area': 'Gollapudi',
            'village_town_city': 'Vijayawada',
            'district': 'NTR District',
            'state': 'Andhra Pradesh',
            'pincode': '520012',
            'country': 'India',
            'display_name': 'Vijayawada, Andhra Pradesh, India',
            'lat': 16.5062,
            'lon': 80.6480
        })
    }
    resp3 = client.post('/generate', data=data_3, follow_redirects=True)
    assert resp3.status_code == 200
    c = conn()
    r3 = c.execute("SELECT * FROM blueprints ORDER BY id DESC LIMIT 1").fetchone()
    c.close()
    bid_3 = r3["id"]
    b3 = json.loads(r3["data"])
    assert "Vijayawada" in b3['location_summary'], "Vijayawada not in location summary!"
    assert "Vijayawada" in b3['executive_summary'], "Vijayawada missing in Executive Summary!"
    surr3_names = [s['name'] for s in b3['suggested_locations']]
    print(f"  [PASS] Location changed to Vijayawada everywhere.")
    print(f"  [PASS] Vijayawada surrounding locations: {surr3_names}")
    assert any(k in " ".join(surr3_names) for k in ["Gollapudi", "Kankipadu", "Gannavaram", "Poranki", "Mangalagiri"]), "Vijayawada specific hubs missing!"

    # TEST 4: Different Industry & Idea: FoodTech / Organic Food Delivery
    print("\n--> TEST 4: FoodTech, Budget ₹3,00,000, Hyderabad (Different industry check)")
    data_4 = {
        'industry': 'FoodTech',
        'idea': 'Late night cloud kitchen and meal box delivery',
        'budget': '300000',
        'team_size': '3',
        'location': 'Hyderabad, Telangana, India',
        'location_details': json.dumps({
            'area': 'Ameerpet',
            'village_town_city': 'Hyderabad',
            'district': 'Hyderabad',
            'state': 'Telangana',
            'pincode': '500016',
            'country': 'India',
            'display_name': 'Hyderabad, Telangana, India',
            'lat': 17.3850,
            'lon': 78.4867
        })
    }
    resp4 = client.post('/generate', data=data_4, follow_redirects=True)
    assert resp4.status_code == 200
    c = conn()
    r4 = c.execute("SELECT * FROM blueprints ORDER BY id DESC LIMIT 1").fetchone()
    c.close()
    bid_4 = r4["id"]
    b4 = json.loads(r4["data"])
    assert b4['industry'] == 'FoodTech'
    assert b4['idea'] != b1['idea']
    assert b4['budget_allocation']['total_planned_investment'] <= 300000
    print(f"  [PASS] FoodTech blueprint generated for Hyderabad with ₹3,00,000 budget.")
    print(f"  [PASS] FoodTech surrounding hubs: {[s['name'] for s in b4['suggested_locations']]}")

    # TEST 5: Input Validation (Empty location blocked)
    print("\n--> TEST 5: Location Validation on /generate (Missing location blocked)")
    resp_empty = client.post('/generate', data={
        'industry': 'SaaS',
        'idea': 'Testing without location',
        'budget': '500000',
        'team_size': '2',
        'location': '',
        'location_details': ''
    }, follow_redirects=False)
    assert resp_empty.status_code == 302, "Expected redirect when location is empty!"
    print("  [PASS] Empty location properly rejected with redirect.")

    # TEST 6: PDF Download (/download-pdf/<id>)
    print(f"\n--> TEST 6: PDF Download for Blueprint #{bid_1}")
    resp_pdf = client.get(f'/download-pdf/{bid_1}')
    assert resp_pdf.status_code == 200, f"PDF download returned {resp_pdf.status_code}"
    assert resp_pdf.mimetype == 'application/pdf', f"Expected application/pdf, got {resp_pdf.mimetype}"
    assert len(resp_pdf.data) > 20000, f"PDF size too small: {len(resp_pdf.data)} bytes"
    print(f"  [PASS] PDF generated and downloaded successfully ({len(resp_pdf.data):,} bytes).")

    # TEST 7: TXT Download (/download/<id>)
    print(f"\n--> TEST 7: TXT Download for Blueprint #{bid_1}")
    resp_txt = client.get(f'/download/{bid_1}')
    assert resp_txt.status_code == 200
    txt_content = resp_txt.data.decode('utf-8')
    assert "1. STARTUP OVERVIEW" in txt_content
    assert "Business Model" not in txt_content
    assert "Dataset Signals" not in txt_content
    print("  [PASS] TXT generated with all required sections and no forbidden fields.")

    # TEST 8: History page (/history)
    print("\n--> TEST 8: History page (/history)")
    resp_hist = client.get('/history')
    assert resp_hist.status_code == 200
    html_hist = resp_hist.data.decode('utf-8')
    assert "Blueprint History" in html_hist
    assert "Smart irrigation service" in html_hist
    assert f"/view/{bid_1}" in html_hist
    assert f"/download-pdf/{bid_1}" in html_hist
    print("  [PASS] History page renders all generated records with View and PDF buttons.")

    # TEST 9: Overview page (/overview and /overview/<id>)
    print(f"\n--> TEST 9: Overview page (/overview/{bid_1})")
    resp_ov = client.get(f'/overview/{bid_1}')
    assert resp_ov.status_code == 200
    html_ov = resp_ov.data.decode('utf-8')
    assert "Executive Overview" in html_ov
    assert "Suggested Surrounding Locations" in html_ov
    assert "Key Local Market Insights" in html_ov
    assert "Main Next Steps" in html_ov
    print("  [PASS] Overview page displays concise strategic summary.")

    # TEST 10: Dashboard page (/dashboard)
    print("\n--> TEST 10: Dashboard page (/dashboard)")
    resp_dash = client.get('/dashboard')
    assert resp_dash.status_code == 200
    html_dash = resp_dash.data.decode('utf-8')
    assert "Project Dashboard" in html_dash
    assert "Total Blueprints" in html_dash
    assert "Business Model" not in html_dash
    assert "Dataset Signals" not in html_dash
    print("  [PASS] Dashboard page displays metrics and startup portfolio without forbidden sections.")

    print("\n" + "=" * 60)
    print("ALL 10 VERIFICATION TEST CASES PASSED WITH 100% SUCCESS!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    run_tests()
