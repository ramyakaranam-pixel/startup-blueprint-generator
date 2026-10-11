import os, sys, json
import unittest
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "dataset", "startup_dataset.csv")

from blueprint_engine import generate, calculate_budget, calculate_profit_loss, extract_location_info
from app import app, init, conn

class BlueprintEngineTestCase(unittest.TestCase):
    def test_budget_enforcement_and_location(self):
        # TEST 1: Budget 1,00,000, Visakhapatnam
        data1 = {
            'industry': 'AgriTech',
            'idea': 'Smart irrigation service for small farmers',
            'budget': '100000',
            'team_size': '2',
            'location': 'MVP Colony, Visakhapatnam, Andhra Pradesh',
            'location_details': json.dumps({
                'area': 'MVP Colony',
                'village_town_city': 'Visakhapatnam',
                'mandal_subdistrict': 'Visakhapatnam Urban',
                'district': 'Visakhapatnam',
                'state': 'Andhra Pradesh',
                'pincode': '530017',
                'country': 'India',
                'lat': 17.738,
                'lon': 83.332,
                'display_name': 'MVP Colony, Visakhapatnam, Andhra Pradesh, India'
            })
        }
        b1 = generate(data1, DATA)

        # Budget assertions
        ba1 = b1['budget_allocation']
        self.assertEqual(ba1['user_input_budget'], 100000)
        self.assertLessEqual(ba1['total_planned_investment'], 100000)
        self.assertEqual(ba1['total_planned_investment'] + ba1['remaining_reserve'], 100000)
        self.assertEqual(sum(ba1['categories'].values()), ba1['total_planned_investment'])

        # Forbidden fields assertions
        self.assertNotIn('business_model', b1)
        self.assertNotIn('dataset_records_used', b1)
        self.assertNotIn('dataset_industry_matches', b1)
        self.assertNotIn('similar_startups', b1)
        self.assertNotIn('technology_stack', b1)
        self.assertNotIn('revenue_model', b1)

        # Target Customers & Suitable Nearby Places assertions
        self.assertIn('target_customers', b1)
        self.assertIn('suitable_nearby_places', b1)
        self.assertTrue(len(b1['suitable_nearby_places']) >= 3)
        self.assertIn('maps_url', b1['suitable_nearby_places'][0])
        self.assertIn('https://www.google.com/maps/search/?api=1&query=', b1['suitable_nearby_places'][0]['maps_url'])

        # Location assertions
        self.assertIn('Visakhapatnam', b1['executive_summary'])
        self.assertIn('₹100,000', b1['executive_summary'])
        self.assertTrue(any('Visakhapatnam' in x or 'MVP Colony' in x or 'Andhra Pradesh' in x for x in b1['local_market_analysis']))

        # TEST 2: Same idea, Budget 10,00,000
        data2 = {**data1, 'budget': '1000000'}
        b2 = generate(data2, DATA)
        ba2 = b2['budget_allocation']
        self.assertEqual(ba2['user_input_budget'], 1000000)
        self.assertLessEqual(ba2['total_planned_investment'], 1000000)
        self.assertEqual(ba2['total_planned_investment'] + ba2['remaining_reserve'], 1000000)
        self.assertNotEqual(ba1['total_planned_investment'], ba2['total_planned_investment'])
        self.assertNotEqual(b1['profit_loss_estimate']['monthly_expense_range'], b2['profit_loss_estimate']['monthly_expense_range'])

        # TEST 3: Vijayawada location
        data3 = {
            **data1,
            'location': 'Benz Circle, Vijayawada, Andhra Pradesh',
            'location_details': json.dumps({
                'area': 'Benz Circle',
                'village_town_city': 'Vijayawada',
                'mandal_subdistrict': 'Vijayawada Urban',
                'district': 'Krishna',
                'state': 'Andhra Pradesh',
                'pincode': '520010',
                'country': 'India',
                'lat': 16.506,
                'lon': 80.648,
                'display_name': 'Benz Circle, Vijayawada, Andhra Pradesh, India'
            })
        }
        b3 = generate(data3, DATA)
        self.assertIn('Vijayawada', b3['executive_summary'])
        self.assertTrue(any('Vijayawada' in x or 'Benz Circle' in x or 'Krishna' in x for x in b3['local_market_analysis']))
        self.assertNotEqual(b1['local_market_analysis'], b3['local_market_analysis'])

        # TEST 4: Different industry and idea
        data4 = {
            'industry': 'SaaS',
            'idea': 'Automated employee payroll software',
            'budget': '500000',
            'team_size': '4',
            'location': 'HITEC City, Hyderabad, Telangana',
            'location_details': json.dumps({
                'area': 'HITEC City',
                'village_town_city': 'Hyderabad',
                'district': 'Hyderabad',
                'state': 'Telangana',
                'pincode': '500081',
                'country': 'India',
                'lat': 17.443,
                'lon': 78.377,
                'display_name': 'HITEC City, Hyderabad, Telangana, India'
            })
        }
        b4 = generate(data4, DATA)
        self.assertNotEqual(b1['startup_name'], b4['startup_name'])
        self.assertEqual(b4['industry'], 'SaaS')
        self.assertEqual(b4['budget_allocation']['user_input_budget'], 500000)

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        init()
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_routes_and_validation(self):
        # 1. Register & Login
        email = f"testuser_{os.getpid()}@example.com"
        r = self.client.post("/register", data={"name": "Test User", "email": email, "password": "password123"}, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        r = self.client.post("/login", data={"email": email, "password": "password123"}, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        # 2. Generate without location - must reject (Requirement 15)
        r = self.client.post("/generate", data={
            "industry": "AgriTech",
            "idea": "Smart irrigation service",
            "budget": "100000",
            "team_size": "2",
            "location": "",
            "location_details": ""
        }, follow_redirects=True)
        self.assertIn("Please select a business location before generating the blueprint.".encode(), r.data)

        # 3. Generate with proper location
        loc_details = {
            "area": "MVP Colony",
            "village_town_city": "Visakhapatnam",
            "mandal_subdistrict": "Visakhapatnam Urban",
            "district": "Visakhapatnam",
            "state": "Andhra Pradesh",
            "pincode": "530017",
            "country": "India",
            "lat": 17.738,
            "lon": 83.332,
            "display_name": "MVP Colony, Visakhapatnam, Andhra Pradesh, India"
        }
        r = self.client.post("/generate", data={
            "industry": "AgriTech",
            "idea": "Smart irrigation service for small farmers",
            "budget": "100000",
            "team_size": "2",
            "location": "MVP Colony, Visakhapatnam, Andhra Pradesh, India",
            "latitude": "17.738",
            "longitude": "83.332",
            "location_details": json.dumps(loc_details)
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        html = r.data.decode('utf-8')
        # Ensure no "Business Model" or "Dataset Signals" in visible output
        self.assertNotIn("<h4>Business Model</h4>", html)
        self.assertNotIn("Business Model", html)
        self.assertNotIn("Dataset Signals", html)
        self.assertNotIn("records analyzed", html)

        # Ensure location and budget are in output
        self.assertIn("Visakhapatnam", html)
        self.assertIn("MVP Colony", html)
        self.assertIn("100,000", html)
        self.assertIn("Total Planned Investment", html)
        self.assertIn("Remaining / Contingency Reserve", html)

        # 4. View blueprint
        c = conn()
        row = c.execute("SELECT id FROM blueprints ORDER BY id DESC LIMIT 1").fetchone()
        c.close()
        self.assertIsNotNone(row)
        bid = row["id"]

        r_view = self.client.get(f"/view/{bid}")
        self.assertEqual(r_view.status_code, 200)

        # 5. Download TXT
        r_dl = self.client.get(f"/download/{bid}")
        self.assertEqual(r_dl.status_code, 200)
        txt = r_dl.data.decode('utf-8')
        self.assertIn("1. STARTUP OVERVIEW", txt)
        self.assertIn("2. EXECUTIVE SUMMARY", txt)
        self.assertIn("SELECTED BUSINESS LOCATION", txt)
        self.assertIn("BUDGET & INVESTMENT ALLOCATION", txt)
        self.assertIn("ESTIMATED REVENUE", txt)
        self.assertNotIn("Business Model", txt)
        self.assertNotIn("Dataset Signals", txt)
        self.assertNotIn("similar_startups", txt)
        self.assertIn("SUITABLE NEARBY BUSINESS LOCATIONS", txt)

        # 6. Download PDF
        r_pdf = self.client.get(f"/download-pdf/{bid}")
        self.assertEqual(r_pdf.status_code, 200)
        self.assertEqual(r_pdf.mimetype, "application/pdf")
        self.assertTrue(len(r_pdf.data) > 1000)

    def test_ai_suggestions_and_manual_location(self):
        # Register & Login
        email = f"suggest_{os.getpid()}@example.com"
        self.client.post("/register", data={"name": "Suggest User", "email": email, "password": "password123"}, follow_redirects=True)
        self.client.post("/login", data={"email": email, "password": "password123"}, follow_redirects=True)

        # 1. Test /api/suggest-industry
        r_ind = self.client.post("/api/suggest-industry", json={"idea": "Electric Bike Rental in Urban Areas"})
        self.assertEqual(r_ind.status_code, 200)
        data_ind = r_ind.get_json()
        self.assertTrue(data_ind["ok"])
        self.assertTrue(len(data_ind["suggestions"]) >= 3)
        self.assertTrue(any("Transport" in x or "Automobile" in x or "Renewable" in x or "Travel" in x for x in data_ind["suggestions"]))

        # 2. Test /api/suggest-customers
        r_cust = self.client.post("/api/suggest-customers", json={
            "idea": "Student Food Delivery",
            "industry": "Food & Beverage",
            "location": "Vizianagaram"
        })
        self.assertEqual(r_cust.status_code, 200)
        data_cust = r_cust.get_json()
        self.assertTrue(data_cust["ok"])
        self.assertTrue(len(data_cust["suggestions"]) >= 3)
        self.assertTrue(any("Student" in x or "Hostel" in x or "College" in x for x in data_cust["suggestions"]))

        # 3. Test Pure Manual Location Generation (e.g. Vizianagaram with single combobox fields)
        r_gen = self.client.post("/generate", data={
            "idea": "Student Food Delivery",
            "industry": "Food & Beverage",
            "target_customers": "Hostel Students in Urban Areas",
            "budget": "200000",
            "team_size": "2",
            "location": "Vizianagaram",
            "location_details": ""
        }, follow_redirects=True)
        self.assertEqual(r_gen.status_code, 200)
        html = r_gen.data.decode("utf-8")
        self.assertIn("Vizianagaram", html)
        self.assertIn("Hostel Students in Urban Areas", html)
        self.assertTrue("Food & Beverage" in html or "Food &amp; Beverage" in html)
        self.assertIn("Suitable Nearby Business Locations", html)
        self.assertIn("Open Google Maps", html)

if __name__ == '__main__':
    unittest.main()
