import os, json, sqlite3, urllib.parse, urllib.request, io
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from blueprint_engine import (
    generate,
    strip_emojis,
    BUSINESS_CATEGORIES,
    TARGET_AUDIENCES,
    PREDEFINED_INDUSTRIES,
    PREDEFINED_TARGET_CUSTOMERS,
    suggest_target_customers,
    suggest_target_industries
)
import pdf_generator
from dotenv import load_dotenv

load_dotenv()
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "startup.db")
DATA = os.path.join(BASE, "dataset", "startup_dataset.csv")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "TRIPLESPARKLES-ramya-pavani-gayathri123456789")

# Dashboard is restricted to project team members.
raw_emails = os.getenv("TEAM_MEMBER_EMAILS") or os.getenv("TEAM_MEMEBERS_EMAILS") or ""
# Support both correct and typo variations if present
parsed_emails = {e.strip().lower() for e in raw_emails.split(",") if e.strip()}
cleaned_emails = set()
for e in parsed_emails:
    cleaned_emails.add(e)
    if e.endswith("s@gmail.com"):
        cleaned_emails.add(e.replace("s@gmail.com", "@gmail.com"))
    if e.endswith("@gamail.com"):
        cleaned_emails.add(e.replace("@gamail.com", "@gmail.com"))
    if e.endswith("@gmail.coms"):
        cleaned_emails.add(e.replace("@gmail.coms", "@gmail.com"))

TEAM_MEMBER_EMAILS = cleaned_emails

def is_team_member():
    if not TEAM_MEMBER_EMAILS:
        return True
    c = conn()
    u = c.execute("SELECT email FROM users WHERE id=?", (session.get("uid"),)).fetchone()
    c.close()
    if not u or not u["email"]:
        return False
    user_email = u["email"].strip().lower()
    return user_email in TEAM_MEMBER_EMAILS

def has_generated_output():
    c = conn()
    r = c.execute("SELECT COUNT(*) AS n FROM blueprints WHERE user_id=?", (session.get("uid"),)).fetchone()
    c.close()
    return bool(r and r["n"] > 0)

def team_only(f):
    @wraps(f)
    def x(*a, **k):
        if "uid" not in session:
            return redirect(url_for("login"))
        if not is_team_member():
            flash("Dashboard access is limited to registered project team members.")
            return redirect(url_for("generate_page"))
        if not has_generated_output():
            flash("Generate a blueprint first. The dashboard is available only after the output.")
            return redirect(url_for("generate_page"))
        return f(*a, **k)
    return x

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    c = conn()
    c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS blueprints(id INTEGER PRIMARY KEY, user_id INTEGER, industry TEXT, idea TEXT, location TEXT, data TEXT, created TEXT)")
    c.commit()
    c.close()

def auth(f):
    @wraps(f)
    def x(*a, **k):
        if "uid" not in session:
            return redirect(url_for("login"))
        return f(*a, **k)
    return x

@app.route("/")
def home():
    return redirect(url_for("generate_page") if "uid" in session else url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            c = conn()
            c.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",
                      (request.form["name"].strip(), request.form["email"].lower().strip(), generate_password_hash(request.form["password"])))
            c.commit()
            c.close()
            flash("Registration successful. Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        c = conn()
        u = c.execute("SELECT * FROM users WHERE email=?", (request.form["email"].lower().strip(),)).fetchone()
        c.close()
        if u and check_password_hash(u["password"], request.form["password"]):
            session["uid"] = u["id"]
            session["name"] = u["name"]
            session["email"] = u["email"]
            session.pop("generated_once", None)
            return redirect(url_for("generate_page"))
        flash("Invalid email or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return render_template("logout.html")

@app.route("/search-location")
def search_location():
    try:
        q = request.args.get("q", "").strip()
        if len(q) < 2:
            return jsonify({"ok": False, "error": "Enter at least 2 characters."}), 400
        params = urllib.parse.urlencode({"q": q, "format": "jsonv2", "addressdetails": 1, "limit": 8, "countrycodes": "in"})
        req = urllib.request.Request("https://nominatim.openstreetmap.org/search?" + params, headers={"User-Agent": "StartupBlueprintAgent/2.0 (student demo app)"})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = json.loads(r.read().decode("utf-8"))
        results = []
        for item in raw:
            a = item.get("address", {})
            results.append({
                "lat": float(item.get("lat")),
                "lon": float(item.get("lon")),
                "display_name": item.get("display_name") or q,
                "area": a.get("suburb") or a.get("neighbourhood") or a.get("quarter") or a.get("residential") or a.get("village") or a.get("town") or a.get("city") or "",
                "village_town_city": a.get("city") or a.get("town") or a.get("village") or a.get("municipality") or "",
                "mandal_subdistrict": a.get("subdistrict") or a.get("county") or a.get("tehsil") or a.get("mandal") or "",
                "district": a.get("district") or a.get("city_district") or a.get("state_district") or "",
                "state": a.get("state") or "",
                "pincode": a.get("postcode") or "",
                "country": a.get("country") or "India"
            })
        return jsonify({"ok": True, "results": results})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/suggest-customers", methods=["GET", "POST"])
def api_suggest_customers():
    try:
        if request.method == "POST":
            data = request.get_json(silent=True) or request.form
        else:
            data = request.args
        idea = data.get("idea", "").strip()
        industry = data.get("industry", "").strip()
        location = data.get("location", "").strip()
        suggestions = suggest_target_customers(idea=idea, industry=industry, location=location)
        return jsonify({"ok": True, "suggestions": suggestions})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/suggest-industry", methods=["GET", "POST"])
def api_suggest_industry():
    try:
        if request.method == "POST":
            data = request.get_json(silent=True) or request.form
        else:
            data = request.args
        idea = data.get("idea", "").strip()
        suggestions = suggest_target_industries(idea=idea)
        return jsonify({"ok": True, "suggestions": suggestions})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

def generate_blueprint_txt(b):
    lines = []
    lines.append("=" * 72)
    lines.append(f"STARTUP BUSINESS BLUEPRINT: {b.get('startup_name', 'STARTUP').upper()}")
    lines.append("=" * 72)
    lines.append("")

    # 1. Startup Overview
    lines.append("1. STARTUP OVERVIEW")
    lines.append("-" * 35)
    lines.append(f"Startup Name: {b.get('startup_name', '-')}")
    lines.append(f"Industry: {b.get('industry', '-')}")
    lines.append(f"Startup Idea: {b.get('idea', '-')}")
    lines.append(f"Target Customers: {b.get('target_customers', '-')}")
    lines.append(f"Selected Location: {b.get('location_summary', '-')}")
    ba = b.get('budget_allocation') or {}
    user_budget = ba.get('user_input_budget') or b.get('budget')
    if isinstance(user_budget, (int, float)):
        lines.append(f"User Input Budget: ₹{int(user_budget):,}")
    else:
        lines.append(f"User Input Budget: {user_budget}")
    lines.append(f"Core Team Size: {b.get('team_size', '-')}")
    lines.append(f"Recommended Approach: {b.get('recommended_approach', 'Hybrid Startup (Online + Offline)')}")
    lines.append("")

    # 2. Executive Summary
    lines.append("2. EXECUTIVE SUMMARY")
    lines.append("-" * 35)
    lines.append(b.get('executive_summary', '-'))
    lines.append("")

    # 3. Business Idea
    lines.append("3. BUSINESS IDEA")
    lines.append("-" * 35)
    lines.append(b.get('idea', '-'))
    lines.append("")

    # 4. Problem Statement
    lines.append("4. PROBLEM STATEMENT")
    lines.append("-" * 35)
    lines.append(b.get('problem', '-'))
    lines.append("")

    # 5. Proposed Solution
    lines.append("5. PROPOSED SOLUTION")
    lines.append("-" * 35)
    lines.append(b.get('solution', '-'))
    lines.append("")

    # 6. Value Proposition
    lines.append("6. VALUE PROPOSITION")
    lines.append("-" * 35)
    lines.append(b.get('value_proposition', '-'))
    lines.append("")

    # 7. Selected Business Location
    lines.append("7. USER-SELECTED BUSINESS LOCATION")
    lines.append("-" * 35)
    loc = b.get('location_details') or {}
    lines.append(f"Full Selected Location: {b.get('location_summary') or loc.get('display_name') or 'Not available'}")
    lines.append(f"Area / Locality: {loc.get('area') or 'Not available'}")
    lines.append(f"Village / Town / City: {loc.get('village_town_city') or 'Not available'}")
    lines.append(f"Mandal / Sub-district: {loc.get('mandal_subdistrict') or 'Not available'}")
    lines.append(f"District: {loc.get('district') or 'Not available'}")
    lines.append(f"State: {loc.get('state') or 'Not available'}")
    lines.append(f"Pincode: {loc.get('pincode') or 'Not available'}")
    lines.append(f"Country: {loc.get('country') or 'India'}")
    lat = loc.get('lat') or loc.get('latitude')
    lon = loc.get('lon') or loc.get('longitude')
    lines.append(f"Coordinates: {lat}, {lon}" if lat and lon else "Coordinates: Not available")
    lines.append("")

    # 8. Local Market Analysis
    lines.append("8. LOCAL MARKET ANALYSIS")
    lines.append("-" * 35)
    for p in b.get('local_market_analysis', []):
        lines.append(f"• {p}")
    lines.append("")

    # 9. Suggested Profitable-Potential Locations
    lines.append("9. SUGGESTED PROFITABLE-POTENTIAL LOCATIONS")
    lines.append("-" * 35)
    for s in (b.get('suggested_locations') or []):
        lines.append(f"• {s.get('name')} ({s.get('distance', 'Nearby')})")
        lines.append(f"  - Suitability: {s.get('suitability', '-')}")
        lines.append(f"  - Target Customer Segment: {s.get('customer_segment', '-')}")
        lines.append(f"  - Competition Context: {s.get('competition', '-')}")
        lines.append(f"  - Accessibility: {s.get('accessibility', '-')}")
        lines.append(f"  - Cost Considerations: {s.get('cost_considerations', '-')}")
        lines.append(f"  - Opportunities: {s.get('opportunities', '-')}")
        lines.append(f"  - Risks: {s.get('risks', '-')}")
    lines.append("")

    # 10. Location Comparison
    lines.append("10. LOCATION COMPARISON")
    lines.append("-" * 35)
    for r in (b.get('location_comparison') or []):
        is_p = " [SELECTED BASE]" if r.get('is_primary') else ""
        lines.append(f"• Location: {r.get('location')}{is_p}")
        lines.append(f"  Suitability: {r.get('suitability', '-')}")
        lines.append(f"  Customers: {r.get('customers', '-')}")
        lines.append(f"  Accessibility: {r.get('accessibility', '-')}")
        lines.append(f"  Costs: {r.get('costs', '-')}")
        lines.append(f"  Risks: {r.get('risks', '-')}")
    lines.append("")

    # 10b. Suitable Nearby Business Locations
    lines.append("SUITABLE NEARBY BUSINESS LOCATIONS (GOOGLE MAPS EXPLORATION)")
    lines.append("-" * 35)
    for p in (b.get('suitable_nearby_places') or []):
        lines.append(f"• {p.get('place_type', 'Location')}")
        lines.append(f"  - Why Suitable: {p.get('reason', '-')}")
        lines.append(f"  - Google Maps Search: {p.get('maps_url', '-')}")
    lines.append("")

    # 11, 12, 13, 14. Online vs Offline vs Hybrid
    lines.append("11. ONLINE VS OFFLINE VS HYBRID STARTUP RECOMMENDATION")
    lines.append("-" * 35)
    ooh = b.get('online_offline_analysis') or {}
    lines.append(f"Recommended Approach: {ooh.get('recommended_approach') or b.get('recommended_approach', 'Hybrid')}")
    lines.append(f"Reason: {ooh.get('reason_for_recommendation', '-')}")
    lines.append("")

    lines.append("12. ONLINE STARTUP ANALYSIS")
    lines.append("-" * 35)
    on_ana = ooh.get('online_analysis') or {}
    lines.append(f"• Why it works: {on_ana.get('why_it_works', '-')}")
    lines.append(f"• How to launch: {on_ana.get('how_to_launch', '-')}")
    lines.append(f"• Initial setup: {on_ana.get('initial_setup', '-')}")
    lines.append(f"• Customer acquisition: {on_ana.get('customer_acquisition', '-')}")
    lines.append(f"• Budget & Risks: {on_ana.get('budget_allocation', '-')} | Risk: {on_ana.get('potential_risks', '-')}")
    lines.append("")

    lines.append("13. OFFLINE STARTUP ANALYSIS")
    lines.append("-" * 35)
    off_ana = ooh.get('offline_analysis') or {}
    lines.append(f"• Why it works: {off_ana.get('why_it_works', '-')}")
    lines.append(f"• Suitable areas: {off_ana.get('suitable_areas', '-')}")
    lines.append(f"• Physical setup: {off_ana.get('physical_setup', '-')}")
    lines.append(f"• Customer acquisition: {off_ana.get('local_customer_acquisition', '-')}")
    lines.append(f"• Budget & Risks: {off_ana.get('budget_allocation', '-')} | Risk: {off_ana.get('potential_risks', '-')}")
    lines.append("")

    lines.append("14. HYBRID STRATEGY")
    lines.append("-" * 35)
    hyb_ana = ooh.get('hybrid_analysis') or {}
    lines.append(f"• Offline Scope: {hyb_ana.get('offline_operations', '-')}")
    lines.append(f"• Online Scope: {hyb_ana.get('online_operations', '-')}")
    lines.append(f"• Channel Integration: {hyb_ana.get('channel_integration', '-')}")
    lines.append(f"• Marketing & Risks: {hyb_ana.get('marketing_strategy', '-')} | {hyb_ana.get('benefits_and_risks', '-')}")
    lines.append("")

    # 15. Budget & Investment Allocation
    lines.append("15. BUDGET & INVESTMENT ALLOCATION")
    lines.append("-" * 35)
    u_b = ba.get('user_input_budget') or user_budget
    lines.append(f"User Input Budget: ₹{int(u_b):,}" if u_b else "User Input Budget: -")
    cats = ba.get('categories') or {}
    for c_name, c_amt in cats.items():
        lines.append(f"  - {c_name}: ₹{int(c_amt):,}")
    tot_plan = ba.get('total_planned_investment') or sum(cats.values())
    rem_res = ba.get('remaining_reserve', 0)
    lines.append(f"Total Planned Investment: ₹{int(tot_plan):,}")
    lines.append(f"Remaining / Contingency Reserve: ₹{int(rem_res):,}")
    lines.append("")

    # 16, 17, 18. Profit & Loss Estimates
    lines.append("16, 17, 18. ESTIMATED REVENUE, EXPENSES & PROFIT/LOSS")
    lines.append("-" * 35)
    pl = b.get('profit_loss_estimate') or {}
    lines.append(f"Estimated Monthly Revenue Range: {pl.get('monthly_revenue_range', '-')}")
    lines.append(f"Estimated Monthly Expenses Range: {pl.get('monthly_expense_range', '-')}")
    lines.append(f"Estimated Monthly Profit/Loss Range: {pl.get('monthly_profit_or_loss_range', '-')}")
    lines.append(f"Break-even Estimate: {pl.get('break_even_estimate', '-')}")
    assumptions = pl.get('key_assumptions') or []
    if isinstance(assumptions, list):
        lines.append("Key Assumptions:")
        for a in assumptions:
            lines.append(f"  • {a}")
    else:
        lines.append(f"Key Assumptions: {assumptions}")
    lines.append(f"Important Note: {pl.get('important_note') or pl.get('note', 'Estimates only; validate with local demand.')}")
    lines.append("")

    # 19. Marketing Strategy
    lines.append("19. MARKETING STRATEGY")
    lines.append("-" * 35)
    for m in b.get('marketing_strategy', []):
        lines.append(f"• {m}")
    lines.append("")

    # 20. Risks & Mitigation
    lines.append("20. RISKS & MITIGATION")
    lines.append("-" * 35)
    for r in (b.get('risks_and_mitigation') or b.get('risks') or []):
        lines.append(f"• {r}")
    lines.append("")

    # 21. Implementation Roadmap
    lines.append("21. IMPLEMENTATION ROADMAP")
    lines.append("-" * 35)
    for idx, s in enumerate(b.get('roadmap') or b.get('implementation_roadmap') or [], 1):
        lines.append(f"{idx}. {s}")
    lines.append("")

    # 22. Final Launch Suggestions & Next Steps
    lines.append("22. FINAL LAUNCH SUGGESTIONS & NEXT STEPS")
    lines.append("-" * 35)
    for st in b.get('next_steps', []):
        lines.append(f"• {st}")
    lines.append("")
    lines.append("=" * 72)
    lines.append("END OF BLUEPRINT")
    lines.append("=" * 72)
    return "\n".join(lines)

@app.route("/generate", methods=["GET", "POST"])
@auth
def generate_page():
    if request.method == "POST":
        idea = request.form.get("idea", "").strip()
        if not idea:
            flash("Please enter your startup idea.")
            return redirect(url_for("generate_page"))

        # Business Category: user-facing field, clean backend value without emojis
        raw_category = (
            request.form.get("business_category", "").strip()
            or request.form.get("industry", "").strip()
            or request.form.get("industry_custom", "").strip()
            or request.form.get("industry_select", "").strip()
        )
        business_category = strip_emojis(raw_category)
        if not business_category:
            flash("Please select a Business Category.")
            return redirect(url_for("generate_page"))

        # Target Audience: Multi-select support
        target_audience_list = request.form.getlist("target_audience")
        if not target_audience_list:
            raw_audience = request.form.get("target_audience") or request.form.get("target_customers", "")
            if raw_audience:
                target_audience_list = [strip_emojis(x.strip()) for x in raw_audience.split(",") if strip_emojis(x.strip())]
        else:
            target_audience_list = [strip_emojis(x) for x in target_audience_list if strip_emojis(x)]

        if not target_audience_list:
            target_audience_list = ["Local Customers"]

        loc_str = request.form.get("location", "").strip()
        if not loc_str:
            flash("Please enter a business location.")
            return redirect(url_for("generate_page"))

        loc_json = request.form.get("location_details", "").strip()
        location_details = {}
        if loc_json and loc_json != "{}" and loc_json != "null":
            try:
                location_details = json.loads(loc_json)
            except Exception:
                location_details = {}

        if not location_details or not location_details.get("display_name"):
            parts = [p.strip() for p in loc_str.split(",") if p.strip()]
            area_or_city = parts[0] if parts else loc_str
            district = parts[1] if len(parts) > 1 else area_or_city
            state = parts[-1] if len(parts) > 2 else "Not available"
            location_details = {
                "display_name": loc_str,
                "area": area_or_city,
                "village_town_city": area_or_city,
                "mandal_subdistrict": "Not available",
                "district": district,
                "state": state,
                "pincode": "Not available",
                "country": "India",
                "lat": request.form.get("latitude") or None,
                "lon": request.form.get("longitude") or None
            }

        budget = request.form.get("budget", "").strip() or "500000"
        team_size = request.form.get("team_size", "").strip() or "2"

        d = {
            "business_category": business_category,
            "industry": business_category,  # backward compatibility
            "idea": idea,
            "target_audience": target_audience_list,
            "target_customers": ", ".join(target_audience_list),  # backward compatibility
            "budget": budget,
            "team_size": team_size,
            "location": loc_str,
            "latitude": location_details.get("lat") or "",
            "longitude": location_details.get("lon") or "",
            "location_details": location_details
        }

        b = generate(d, DATA)
        c = conn()
        c.execute("INSERT INTO blueprints(user_id,industry,idea,location,data,created) VALUES(?,?,?,?,?,?)",
                  (session["uid"], d["industry"], d["idea"], d["location"], json.dumps(b, ensure_ascii=False), datetime.now().isoformat()))
        c.commit()
        bid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.close()
        session["generated_once"] = True
        return render_template("blueprint.html", b=b, bid=bid, can_dashboard=is_team_member() and has_generated_output())

    return render_template(
        "generate.html",
        business_categories=BUSINESS_CATEGORIES,
        target_audiences=TARGET_AUDIENCES,
        predefined_industries=PREDEFINED_INDUSTRIES,
        predefined_customers=PREDEFINED_TARGET_CUSTOMERS
    )

@app.route("/blueprint/delete/<int:bid>", methods=["POST"])
@auth
def delete_blueprint(bid):
    c = conn()
    r = c.execute("SELECT id FROM blueprints WHERE id=? AND user_id=?", (bid, session["uid"])).fetchone()
    if not r:
        c.close()
        flash("Blueprint not found or unauthorized.")
        return redirect(request.referrer or url_for("history"))
    c.execute("DELETE FROM blueprints WHERE id=? AND user_id=?", (bid, session["uid"]))
    c.commit()
    c.close()

    # Clean up generated files if any
    for ext in [".pdf", ".txt"]:
        file_p = os.path.join(BASE, "generated", f"blueprint_{bid}{ext}")
        if os.path.exists(file_p):
            try:
                os.remove(file_p)
            except Exception:
                pass

    flash("Blueprint deleted successfully.")
    return redirect(request.referrer or url_for("history"))

@app.route("/view/<int:bid>")
@auth
def view(bid):
    c = conn()
    r = c.execute("SELECT * FROM blueprints WHERE id=? AND user_id=?", (bid, session["uid"])).fetchone()
    c.close()
    if not r:
        return ("Not found", 404)
    b = json.loads(r["data"])
    return render_template("blueprint.html", b=b, bid=bid, can_dashboard=is_team_member() and has_generated_output())

@app.route("/history")
@auth
def history():
    c = conn()
    rows = c.execute("SELECT * FROM blueprints WHERE user_id=? ORDER BY id DESC", (session["uid"],)).fetchall()
    c.close()
    blueprints = []
    for r in rows:
        b_data = json.loads(r["data"])
        ba = b_data.get('budget_allocation') or {}
        user_budget = ba.get('user_input_budget') or b_data.get('budget')
        bm = b_data.get('business_model_recommendation') or {}
        approach = bm.get('recommendation') or b_data.get('recommended_approach') or 'Online + Offline'
        category = b_data.get('business_category') or r["industry"]
        target_audience = b_data.get('target_audience')
        if not target_audience:
            tc = b_data.get('target_customers', '')
            target_audience = [x.strip() for x in tc.split(',') if x.strip()] if tc else []
        blueprints.append({
            "id": r["id"],
            "startup_name": b_data.get('startup_name', 'Startup'),
            "idea": r["idea"],
            "business_category": category,
            "industry": category,
            "target_audience": target_audience,
            "target_customers": ", ".join(target_audience) if isinstance(target_audience, list) else str(target_audience),
            "location": r["location"],
            "budget": user_budget,
            "approach": approach,
            "created": r["created"]
        })
    return render_template("history.html", blueprints=blueprints)

@app.route("/overview")
@app.route("/overview/<int:bid>")
@auth
def overview(bid=None):
    c = conn()
    if bid:
        r = c.execute("SELECT * FROM blueprints WHERE id=? AND user_id=?", (bid, session["uid"])).fetchone()
    else:
        r = c.execute("SELECT * FROM blueprints WHERE user_id=? ORDER BY id DESC LIMIT 1", (session["uid"],)).fetchone()
    c.close()

    if not r:
        flash("Generate a blueprint first to view its overview.")
        return redirect(url_for("generate_page"))

    b = json.loads(r["data"])
    return render_template("overview.html", b=b, bid=r["id"])

@app.route("/dashboard")
@team_only
def dashboard():
    c = conn()
    rows = c.execute("SELECT * FROM blueprints WHERE user_id=? ORDER BY id DESC", (session["uid"],)).fetchall()
    c.close()
    blueprints = []
    categories = set()
    total_budget_planned = 0
    for r in rows:
        b_data = json.loads(r["data"])
        ba = b_data.get('budget_allocation') or {}
        user_budget = ba.get('user_input_budget') or b_data.get('budget') or 0
        if isinstance(user_budget, (int, float)):
            total_budget_planned += user_budget
        bm = b_data.get('business_model_recommendation') or {}
        approach = bm.get('recommendation') or b_data.get('recommended_approach') or 'Online + Offline'
        cat = b_data.get('business_category') or r["industry"]
        categories.add(cat)
        blueprints.append({
            "id": r["id"],
            "startup_name": b_data.get('startup_name', 'Startup'),
            "idea": r["idea"],
            "business_category": cat,
            "industry": cat,
            "location": r["location"],
            "budget": user_budget,
            "approach": approach,
            "created": r["created"]
        })
    return render_template("dashboard.html", blueprints=blueprints, total_blueprints=len(blueprints), unique_industries=len(categories), total_budget_planned=total_budget_planned)

@app.route("/download/<int:bid>")
@auth
def download(bid):
    # Requirement N: Remove TXT download, redirect to PDF download
    return redirect(url_for("download_pdf", bid=bid))

@app.route("/download-pdf/<int:bid>")
@auth
def download_pdf(bid):
    c = conn()
    r = c.execute("SELECT * FROM blueprints WHERE id=? AND user_id=?", (bid, session["uid"])).fetchone()
    c.close()
    if not r:
        return ("Not found", 404)
    b = json.loads(r["data"])
    os.makedirs(os.path.join(BASE, "generated"), exist_ok=True)
    pdf_path = os.path.join(BASE, "generated", f"blueprint_{bid}.pdf")
    pdf_generator.build_blueprint_pdf(b, pdf_path)
    return send_file(pdf_path, as_attachment=True, download_name=f"startup_blueprint_{bid}.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    init()
    app.run(debug=True)
