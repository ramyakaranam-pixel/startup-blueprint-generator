STARTUP BUSINESS BLUEPRINT - SETUP & USER GUIDE

APPLICATION USER FLOW
1. Open the app -> Login page appears first.
2. Login -> Generate Blueprint page (/generate).
3. Enter Industry, Startup Idea, Budget (₹), Team Size, and search/select a Business Location.
   (Device GPS/Current Location is completely disabled; only your selected location is used).
4. Generate -> Full 22-section Blueprint output appears.
5. Download PDF / Download TXT button -> Instantly generate and download the complete report.
6. History (/history) -> Browse and view all previously generated blueprints with PDF download.
7. Overview (/overview) -> View concise executive overview and switch between blueprints.
8. Dashboard (/dashboard) -> Central analytics portfolio and venture management.

KEY REQUIREMENTS IMPLEMENTED
- Strict User Budget Ceiling: The entered budget is treated as a hard primary input. The sum of all categories plus contingency reserve mathematically equals 100% of the user's budget.
- User-Selected Location Grounding: Selected location is preserved across all pages, database records, PDF, and TXT outputs.
- Suggested Profitable-Potential Locations: Analyzes and suggests 3–5 geographically viable surrounding hubs with distance, suitability, customer segments, competition, accessibility, costs, opportunities, and risks.
- Location Comparison Table: Direct side-by-side comparison of user-selected location against surrounding candidate hubs.
- Online vs Offline vs Hybrid Recommendation: Dynamic recommendation with deep-dive analyses for online, offline, and hybrid strategies.
- Executive Summary: Context-aware summary integrating startup idea, industry, budget, location, team size, and operational model.
- PDF Download: Built using ReportLab with clean typography, tables, page numbers, and custom styling.
- Complete Exclusion of Forbidden Fields: "Business Model" and "Dataset Signals" are completely excluded from the user-facing blueprint, PDF, TXT, History, Overview, and Dashboard.
- 10,000-Row Dataset: Kept intact and used strictly for internal conceptual patterns.

HOW TO RUN THE APPLICATION
1. Install dependencies:
   pip install -r requirements.txt
   (Note: reportlab is required for PDF generation).

2. (Optional) Set up .env file:
   Copy .env.example to .env
   Set SECRET_KEY, OPENAI_API_KEY (optional, fallback engine works fully offline), and TEAM_MEMBER_EMAILS.

3. Start the Flask application:
   python app.py
   Access the web app at: http://127.0.0.1:5000

4. Run the automated test suites:
   python test_suite.py
   python test_app.py
