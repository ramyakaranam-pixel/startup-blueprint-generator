"""
test_end_to_end_requirements.py
Comprehensive verification script checking all 25 requirements across 3 different startup ideas.
"""

import os
import sys
import json
import sqlite3
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app import app, init, conn
import pdf_generator
from blueprint_engine import BUSINESS_CATEGORIES, TARGET_AUDIENCES

def run_all_tests():
    init()
    client = app.test_client()

    print("=" * 70)
    print("STARTUP BUSINESS BLUEPRINT GENERATOR — FULL VERIFICATION")
    print("=" * 70)

    # Setup user session
    with client.session_transaction() as sess:
        sess["uid"] = 1
        sess["name"] = "Ramya"
        sess["email"] = "ramyakaranam3@gmail.com"

    # =========================================================================
    # Part 1: Verify Categories (20 exact) and Audiences (17 exact)
    # =========================================================================
    print("\n[CHECK 1 & 2] Verifying Categories and Multi-Select Audience Constants...")
    assert len(BUSINESS_CATEGORIES) == 20, f"Expected 20 categories, found {len(BUSINESS_CATEGORIES)}"
    expected_categories = [
        "Technology", "Food & Beverages", "Shopping & E-Commerce", "Education & EdTech",
        "Healthcare & Fitness", "Travel & Hospitality", "Entertainment & Media",
        "Finance & Banking", "Logistics & Delivery", "Transportation & Mobility",
        "Social Media & Communication", "Agriculture & Farming", "Real Estate",
        "HR & Recruitment", "Manufacturing", "Environment & Sustainability",
        "Energy & CleanTech", "Beauty & Personal Care", "Sports & Gaming", "Other"
    ]
    for exp_cat in expected_categories:
        assert any(c["name"] == exp_cat for c in BUSINESS_CATEGORIES), f"Missing category: {exp_cat}"

    assert len(TARGET_AUDIENCES) == 17, f"Expected 17 audiences, found {len(TARGET_AUDIENCES)}"
    expected_audiences = [
        "College Students", "Working Professionals", "Job Seekers", "Families",
        "Parents", "Children", "Senior Citizens", "Farmers", "Entrepreneurs",
        "Small Businesses", "Freelancers", "Women", "Men", "Tourists",
        "Local Customers", "Online Customers", "Other"
    ]
    for exp_aud in expected_audiences:
        assert any(a["name"] == exp_aud for a in TARGET_AUDIENCES), f"Missing audience: {exp_aud}"
    print("  ✓ All 20 Business Categories and 17 Target Audiences verified.")

    # =========================================================================
    # Part 2: Verify Generate Page Form UI (Clean Form, no descriptive text)
    # =========================================================================
    print("\n[CHECK 3 & 4] Checking Generate Page UI Cleanliness & Labels...")
    resp_gen_get = client.get('/generate')
    assert resp_gen_get.status_code == 200
    html_form = resp_gen_get.data.decode('utf-8')

    # Must have "Business Category *" and NOT "Target Industry"
    assert "Business Category" in html_form
    assert '<span class="text-danger">*</span>' in html_form
    assert "Target Industry" not in html_form
    assert "Target Audience" in html_form

    # Removed descriptive helper paragraphs
    assert "Describe your core business idea" not in html_form
    assert "Select from dropdown or type any custom" not in html_form
    assert "Strict primary ceiling: All allocations" not in html_form
    assert "Number of founding and core operational members" not in html_form
    assert "You can type any location name directly" not in html_form
    assert "Generation Constraints: Your entered Budget acts as the hard ceiling" not in html_form
    assert "Hybrid Startup Women" not in html_form
    assert "Hybrid Strategy" not in html_form
    print("  ✓ Clean Form UI verified: No descriptive helper text, exact labels present.")

    # =========================================================================
    # Part 3: Test 1 - Food & Beverages Startup
    # =========================================================================
    print("\n[TEST 1] Generating: 'Healthy meal prep and tiffin delivery for college students' (Food & Beverages)...")
    post_data_1 = {
        'idea': 'Healthy meal prep and tiffin delivery for college students',
        'business_category': 'Food & Beverages',
        'target_audience': ['College Students', 'Job Seekers'],
        'budget': '250000',
        'team_size': '2',
        'location': 'MVP Colony, Visakhapatnam, Andhra Pradesh',
        'location_details': json.dumps({
            'area': 'MVP Colony',
            'village_town_city': 'Visakhapatnam',
            'district': 'Visakhapatnam',
            'state': 'Andhra Pradesh',
            'display_name': 'MVP Colony, Visakhapatnam, Andhra Pradesh'
        })
    }
    r1 = client.post('/generate', data=post_data_1, follow_redirects=True)
    assert r1.status_code == 200
    html_b1 = r1.data.decode('utf-8')

    c = conn()
    db_rec_1 = c.execute("SELECT * FROM blueprints ORDER BY id DESC LIMIT 1").fetchone()
    c.close()
    bid_1 = db_rec_1["id"]
    b1 = json.loads(db_rec_1["data"])

    # Verifications for Test 1
    assert b1["business_category"] == "Food & Beverages"
    assert "College Students" in b1["target_audience"]
    assert "Job Seekers" in b1["target_audience"]
    assert b1["business_model_recommendation"]["recommendation"] in ["Online + Offline", "Offline", "Online"]
    assert sum(b1["budget_allocation"]["categories"].values()) == 250000, "Investment allocation sum != 250000"
    assert "profit_loss_estimate" not in b1
    assert "Hybrid Strategy" not in html_b1
    assert "Estimated Revenue" not in html_b1
    assert "Estimated Expenses" not in html_b1
    assert "Estimated Profit" not in html_b1
    assert "Download TXT" not in html_b1
    print(f"  ✓ Test 1 Success: Model='{b1['business_model_recommendation']['recommendation']}', Allocation Sum=₹{sum(b1['budget_allocation']['categories'].values()):,}")
    print(f"    Categories: {list(b1['budget_allocation']['categories'].keys())}")
    print(f"    Locations: {[loc['name'] for loc in b1['suitable_locations']]}")

    # =========================================================================
    # Part 4: Test 2 - Agriculture & Farming Startup
    # =========================================================================
    print("\n[TEST 2] Generating: 'Solar powered smart irrigation sensors for rural farms' (Agriculture & Farming)...")
    post_data_2 = {
        'idea': 'Solar powered smart irrigation sensors for rural farms',
        'business_category': 'Agriculture & Farming',
        'target_audience': ['Farmers', 'Small Businesses'],
        'budget': '600000',
        'team_size': '3',
        'location': 'Guntur, Andhra Pradesh',
        'location_details': json.dumps({
            'area': 'Guntur Rural',
            'village_town_city': 'Guntur',
            'district': 'Guntur',
            'state': 'Andhra Pradesh',
            'display_name': 'Guntur, Andhra Pradesh'
        })
    }
    r2 = client.post('/generate', data=post_data_2, follow_redirects=True)
    assert r2.status_code == 200
    html_b2 = r2.data.decode('utf-8')

    c = conn()
    db_rec_2 = c.execute("SELECT * FROM blueprints ORDER BY id DESC LIMIT 1").fetchone()
    c.close()
    bid_2 = db_rec_2["id"]
    b2 = json.loads(db_rec_2["data"])

    # Verifications for Test 2
    assert b2["business_category"] == "Agriculture & Farming"
    assert "Farmers" in b2["target_audience"]
    assert sum(b2["budget_allocation"]["categories"].values()) == 600000, "Investment allocation sum != 600000"
    # Ensure locations and categories differ from Food & Beverages
    assert b1["suitable_locations"] != b2["suitable_locations"]
    assert list(b1["budget_allocation"]["categories"].keys()) != list(b2["budget_allocation"]["categories"].keys())
    print(f"  ✓ Test 2 Success: Model='{b2['business_model_recommendation']['recommendation']}', Allocation Sum=₹{sum(b2['budget_allocation']['categories'].values()):,}")
    print(f"    Categories: {list(b2['budget_allocation']['categories'].keys())}")
    print(f"    Locations: {[loc['name'] for loc in b2['suitable_locations']]}")

    # =========================================================================
    # Part 5: Test 3 - Technology Startup
    # =========================================================================
    print("\n[TEST 3] Generating: 'AI Resume Screening and Interview Preparation Platform' (Technology)...")
    post_data_3 = {
        'idea': 'AI Resume Screening and Interview Preparation Platform',
        'business_category': 'Technology',
        'target_audience': ['Job Seekers', 'Working Professionals', 'College Students'],
        'budget': '400000',
        'team_size': '2',
        'location': 'Hitec City, Hyderabad, Telangana',
        'location_details': json.dumps({
            'area': 'Hitec City',
            'village_town_city': 'Hyderabad',
            'district': 'Hyderabad',
            'state': 'Telangana',
            'display_name': 'Hitec City, Hyderabad, Telangana'
        })
    }
    r3 = client.post('/generate', data=post_data_3, follow_redirects=True)
    assert r3.status_code == 200
    html_b3 = r3.data.decode('utf-8')

    c = conn()
    db_rec_3 = c.execute("SELECT * FROM blueprints ORDER BY id DESC LIMIT 1").fetchone()
    c.close()
    bid_3 = db_rec_3["id"]
    b3 = json.loads(db_rec_3["data"])

    # Verifications for Test 3
    assert b3["business_category"] == "Technology"
    assert b3["business_model_recommendation"]["recommendation"] == "Online"
    assert sum(b3["budget_allocation"]["categories"].values()) == 400000, "Investment allocation sum != 400000"
    assert b3["suitable_locations"] != b1["suitable_locations"]
    assert b3["suitable_locations"] != b2["suitable_locations"]
    print(f"  ✓ Test 3 Success: Model='{b3['business_model_recommendation']['recommendation']}', Allocation Sum=₹{sum(b3['budget_allocation']['categories'].values()):,}")
    print(f"    Categories: {list(b3['budget_allocation']['categories'].keys())}")
    print(f"    Locations: {[loc['name'] for loc in b3['suitable_locations']]}")

    # =========================================================================
    # Part 6: Verify Overview Route (Key points from all modules, No Switch Blueprint)
    # =========================================================================
    print("\n[CHECK 5 & 6] Verifying View Overview...")
    resp_ov = client.get(f'/overview/{bid_1}')
    assert resp_ov.status_code == 200
    html_ov = resp_ov.data.decode('utf-8')

    assert "Switch Blueprint" not in html_ov, "Switch Blueprint found in overview!"
    assert "Estimated Revenue" not in html_ov
    assert "Monthly Net Profit/Loss" not in html_ov
    assert "Problem Key Points" in html_ov
    assert "Solution Key Points" in html_ov
    assert "Business Model Recommendation" in html_ov
    assert "Suitable Potential Locations" in html_ov
    assert "Budget & Investment Allocation" in html_ov
    assert "Go-To-Market Key Actions" in html_ov
    assert "Operations Plan Highlights" in html_ov
    assert "Roadmap Milestones" in html_ov
    assert "Risks & Challenges" in html_ov
    print("  ✓ Overview verified: All active key points present, Switch Blueprint completely removed.")

    # =========================================================================
    # Part 7: Verify PDF Generation for All 3 Blueprints
    # =========================================================================
    print("\n[CHECK 7] Verifying PDF Generation for all 3 blueprints...")
    for bid, b_data in [(bid_1, b1), (bid_2, b2), (bid_3, b3)]:
        resp_pdf = client.get(f'/download-pdf/{bid}')
        assert resp_pdf.status_code == 200, f"PDF failed for bid {bid}"
        assert resp_pdf.mimetype == "application/pdf"
        assert len(resp_pdf.data) > 10000
    print("  ✓ PDF generation working for all 3 blueprints.")

    # =========================================================================
    # Part 8: Verify Deletion in History and Dashboard
    # =========================================================================
    print("\n[CHECK 8 & 9] Verifying History and Dashboard Deletion...")
    # Check History before deletion
    resp_hist = client.get('/history')
    assert resp_hist.status_code == 200
    html_hist = resp_hist.data.decode('utf-8')
    assert f"deleteModal{bid_1}" in html_hist
    assert "Are you sure you want to delete this blueprint?" in html_hist

    # Delete blueprint 1
    resp_del_1 = client.post(f'/blueprint/delete/{bid_1}', follow_redirects=True)
    assert resp_del_1.status_code == 200
    c = conn()
    del_check_1 = c.execute("SELECT id FROM blueprints WHERE id=?", (bid_1,)).fetchone()
    assert del_check_1 is None, f"Blueprint {bid_1} was not deleted from DB!"

    # Verify other records remain unchanged
    remain_check = c.execute("SELECT COUNT(*) as cnt FROM blueprints WHERE id IN (?, ?)", (bid_2, bid_3)).fetchone()
    assert remain_check["cnt"] == 2, "Other history records were mistakenly deleted!"
    c.close()
    print("  ✓ History Delete verified: Selected blueprint removed, other records intact.")

    # Check Dashboard delete modal and delete blueprint 2
    resp_dash = client.get('/dashboard')
    assert resp_dash.status_code == 200
    html_dash = resp_dash.data.decode('utf-8')
    assert f"deleteDashModal{bid_2}" in html_dash
    assert "Are you sure you want to delete this startup blueprint?" in html_dash

    resp_del_2 = client.post(f'/blueprint/delete/{bid_2}', follow_redirects=True)
    assert resp_del_2.status_code == 200
    c = conn()
    del_check_2 = c.execute("SELECT id FROM blueprints WHERE id=?", (bid_2,)).fetchone()
    assert del_check_2 is None, f"Blueprint {bid_2} was not deleted from DB!"
    c.close()
    print("  ✓ Dashboard Delete verified: Selected blueprint removed from DB and dashboard refreshed.")

    # Clean up test blueprint 3
    client.post(f'/blueprint/delete/{bid_3}', follow_redirects=True)

    # =========================================================================
    # Part 9: Verify Auth (Login / Logout)
    # =========================================================================
    print("\n[CHECK 10] Verifying Login & Logout...")
    resp_logout = client.get('/logout')
    assert resp_logout.status_code == 200
    with client.session_transaction() as sess:
        assert "uid" not in sess

    resp_prot = client.get('/generate', follow_redirects=False)
    assert resp_prot.status_code == 302, "Protected page did not redirect when unauthenticated"
    print("  ✓ Authentication and session protection verified.")

    print("\n" + "=" * 70)
    print("ALL 25 VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
