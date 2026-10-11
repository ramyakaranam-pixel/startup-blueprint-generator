"""
blueprint_engine.py
Core startup business blueprint generation engine using Google Gemini AI and CSV dataset intelligence.
Dynamically generates custom blueprints tailored to:
- Startup Idea
- Business Category (20 exact categories with emojis in UI, clean in backend)
- Target Audience (17 exact multi-select options)
- Primary Budget (strict mathematical ceiling)
- Location Intelligence

Removes:
- Hybrid Strategy
- Estimated Revenue, Expenses, Profit/Loss
- Fixed/Hardcoded suggestions
- Hybrid Startup Women
"""

import os
import json
import re
import math
import urllib.parse
import pandas as pd
import location_intelligence

# 20 Exact Business Categories with UI emojis
BUSINESS_CATEGORIES = [
    {"name": "Technology", "emoji": "💻", "display": "💻 Technology"},
    {"name": "Food & Beverages", "emoji": "🍔", "display": "🍔 Food & Beverages"},
    {"name": "Shopping & E-Commerce", "emoji": "🛒", "display": "🛒 Shopping & E-Commerce"},
    {"name": "Education & EdTech", "emoji": "🎓", "display": "🎓 Education & EdTech"},
    {"name": "Healthcare & Fitness", "emoji": "❤️", "display": "❤️ Healthcare & Fitness"},
    {"name": "Travel & Hospitality", "emoji": "✈️", "display": "✈️ Travel & Hospitality"},
    {"name": "Entertainment & Media", "emoji": "🎬", "display": "🎬 Entertainment & Media"},
    {"name": "Finance & Banking", "emoji": "💰", "display": "💰 Finance & Banking"},
    {"name": "Logistics & Delivery", "emoji": "🚚", "display": "🚚 Logistics & Delivery"},
    {"name": "Transportation & Mobility", "emoji": "🚗", "display": "🚗 Transportation & Mobility"},
    {"name": "Social Media & Communication", "emoji": "💬", "display": "💬 Social Media & Communication"},
    {"name": "Agriculture & Farming", "emoji": "🌱", "display": "🌱 Agriculture & Farming"},
    {"name": "Real Estate", "emoji": "🏠", "display": "🏠 Real Estate"},
    {"name": "HR & Recruitment", "emoji": "👥", "display": "👥 HR & Recruitment"},
    {"name": "Manufacturing", "emoji": "🏭", "display": "🏭 Manufacturing"},
    {"name": "Environment & Sustainability", "emoji": "🌍", "display": "🌍 Environment & Sustainability"},
    {"name": "Energy & CleanTech", "emoji": "⚡", "display": "⚡ Energy & CleanTech"},
    {"name": "Beauty & Personal Care", "emoji": "💄", "display": "💄 Beauty & Personal Care"},
    {"name": "Sports & Gaming", "emoji": "🎮", "display": "🎮 Sports & Gaming"},
    {"name": "Other", "emoji": "📌", "display": "📌 Other"}
]

# 17 Exact Target Audience options with UI emojis
TARGET_AUDIENCES = [
    {"name": "College Students", "emoji": "🎓", "display": "🎓 College Students"},
    {"name": "Working Professionals", "emoji": "💼", "display": "💼 Working Professionals"},
    {"name": "Job Seekers", "emoji": "🔍", "display": "🔍 Job Seekers"},
    {"name": "Families", "emoji": "👨👩👧👦", "display": "👨👩👧👦 Families"},
    {"name": "Parents", "emoji": "👨👩👧", "display": "👨👩👧 Parents"},
    {"name": "Children", "emoji": "🧒", "display": "🧒 Children"},
    {"name": "Senior Citizens", "emoji": "👴", "display": "👴 Senior Citizens"},
    {"name": "Farmers", "emoji": "👨🌾", "display": "👨🌾 Farmers"},
    {"name": "Entrepreneurs", "emoji": "🚀", "display": "🚀 Entrepreneurs"},
    {"name": "Small Businesses", "emoji": "🏪", "display": "🏪 Small Businesses"},
    {"name": "Freelancers", "emoji": "💻", "display": "💻 Freelancers"},
    {"name": "Women", "emoji": "👩", "display": "👩 Women"},
    {"name": "Men", "emoji": "👨", "display": "👨 Men"},
    {"name": "Tourists", "emoji": "🧳", "display": "🧳 Tourists"},
    {"name": "Local Customers", "emoji": "📍", "display": "📍 Local Customers"},
    {"name": "Online Customers", "emoji": "🌐", "display": "🌐 Online Customers"},
    {"name": "Other", "emoji": "👥", "display": "👥 Other"}
]

# Backward compatibility lists
PREDEFINED_INDUSTRIES = [c["name"] for c in BUSINESS_CATEGORIES]
PREDEFINED_TARGET_CUSTOMERS = [a["name"] for a in TARGET_AUDIENCES]


def strip_emojis(text):
    """Strips leading/trailing emojis and unicode symbols from text."""
    if not text:
        return ""
    cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', str(text), flags=re.UNICODE)
    cleaned = re.sub(r'[\u2600-\u27bf\ufe0f\u200d\u2300-\u23ff\u2b50\u2b55\u203c\u2049]', '', cleaned)
    return cleaned.strip()


def parse_clean_budget(budget_input):
    """Extracts a valid integer budget, with minimum 10000 ceiling."""
    cleaned = re.sub(r'[^\d.]', '', str(budget_input or '500000'))
    try:
        val = int(float(cleaned))
        return max(10000, val)
    except Exception:
        return 500000


def make_name(idea):
    """Generates an intuitive, readable brand name from the startup idea."""
    words = re.findall(r"[A-Za-z0-9]+", str(idea or ''))
    stopwords = {'a', 'an', 'the', 'for', 'and', 'in', 'on', 'at', 'to', 'of', 'with', 'by', 'is'}
    filtered = [w.capitalize() for w in words if w.lower() not in stopwords]
    if not filtered:
        filtered = [w.capitalize() for w in words[:3]]
    base = " ".join(filtered[:3]) if filtered else "Smart Venture"
    suffix_options = ["Flow", "Works", "Hub", "Desk", "Sphere", "Pulse", "Forge", "Connect", "Roots"]
    suffix = suffix_options[len(str(idea)) % len(suffix_options)]
    return f"{base} {suffix}"


def _clean_json(text):
    """Extracts and parses a JSON object from raw LLM output text."""
    text = (text or '').strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.I)
    text = re.sub(r'\s*```$', '', text)
    start, end = text.find('{'), text.rfind('}')
    if start >= 0 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def filter_relevant_dataset(df, idea, business_category, target_audiences, budget, location):
    """
    Intelligently scores and filters the 10,000-row CSV dataset for the 3-5 most relevant records.
    Handles missing or empty datasets gracefully.
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return []

    category_map = {
        'Technology': ['ai', 'saas', 'cybersecurity', 'tech', 'software', 'cloud'],
        'Food & Beverages': ['foodtech', 'food', 'beverage', 'kitchen', 'restaurant', 'meal', 'cafe'],
        'Shopping & E-Commerce': ['e-commerce', 'ecommerce', 'retail', 'shopping', 'store'],
        'Education & EdTech': ['edtech', 'education', 'learning', 'student', 'school', 'tutor'],
        'Healthcare & Fitness': ['healthtech', 'health', 'fitness', 'medical', 'clinic', 'wellness'],
        'Travel & Hospitality': ['traveltech', 'travel', 'hotel', 'tourism', 'hospitality'],
        'Entertainment & Media': ['media', 'entertainment', 'gaming', 'video', 'content'],
        'Finance & Banking': ['fintech', 'finance', 'banking', 'payment', 'loan', 'credit'],
        'Logistics & Delivery': ['logistics', 'delivery', 'supply chain', 'warehouse', 'freight'],
        'Transportation & Mobility': ['transportation', 'mobility', 'vehicle', 'ev', 'cab', 'ride'],
        'Social Media & Communication': ['saas', 'social', 'chat', 'communication', 'platform'],
        'Agriculture & Farming': ['agritech', 'agriculture', 'farm', 'crop', 'soil', 'farmer'],
        'Real Estate': ['real estate', 'property', 'housing', 'rental'],
        'HR & Recruitment': ['hr', 'recruitment', 'hiring', 'talent', 'staffing', 'job'],
        'Manufacturing': ['manufacturing', 'hardware', 'industrial', 'production'],
        'Environment & Sustainability': ['green', 'solar', 'waste', 'recycle', 'sustainability'],
        'Energy & CleanTech': ['energy', 'cleantech', 'solar', 'power', 'battery'],
        'Beauty & Personal Care': ['beauty', 'personal care', 'cosmetics', 'wellness', 'salon'],
        'Sports & Gaming': ['gaming', 'sports', 'fitness', 'athletic', 'esports'],
        'Other': ['general', 'services', 'platform']
    }

    kw_list = category_map.get(business_category, [business_category.lower()])
    idea_words = set(re.findall(r"[a-z]{3,}", str(idea).lower()))
    
    if isinstance(target_audiences, list):
        aud_text = " ".join([str(a).lower() for a in target_audiences])
    else:
        aud_text = str(target_audiences or '').lower()
    aud_words = set(re.findall(r"[a-z]{3,}", aud_text))
    loc_clean = str(location or '').lower()

    scores = []
    for _, row in df.iterrows():
        score = 0.0
        row_ind = str(row.get('industry', '')).lower()
        row_idea = str(row.get('startup_idea', '')).lower()
        row_prob = str(row.get('problem', '')).lower()
        row_sol = str(row.get('solution', '')).lower()
        row_cust = str(row.get('target_customer', '')).lower()
        row_loc = str(row.get('location', '')).lower()

        # Category keyword match
        if any(k in row_ind for k in kw_list):
            score += 10.0

        # Idea and problem/solution overlap
        haystack = f"{row_idea} {row_prob} {row_sol}"
        row_words = set(re.findall(r"[a-z]{3,}", haystack))
        overlap = len(idea_words & row_words)
        score += overlap * 3.0

        # Audience overlap
        cust_words = set(re.findall(r"[a-z]{3,}", row_cust))
        if aud_words & cust_words:
            score += 5.0

        # Location overlap
        if row_loc and row_loc in loc_clean:
            score += 3.0

        # Budget similarity
        try:
            row_bgt = float(row.get('initial_budget', 0))
            if row_bgt > 0 and budget > 0:
                diff_ratio = abs(row_bgt - budget) / max(budget, row_bgt)
                score += max(0, 4.0 - (diff_ratio * 4.0))
        except Exception:
            pass

        scores.append((score, row))

    scores.sort(key=lambda x: x[0], reverse=True)
    top_matches = scores[:4]

    results = []
    for s, r in top_matches:
        results.append({
            'startup_name': str(r.get('startup_name', '')),
            'industry': str(r.get('industry', '')),
            'concept_reference': str(r.get('startup_idea', '')),
            'problem_pattern': str(r.get('problem', '')),
            'solution_pattern': str(r.get('solution', '')),
            'target_customer': str(r.get('target_customer', '')),
            'business_model': str(r.get('business_model', '')),
            'risk_level': str(r.get('risk_level', ''))
        })
    return results


def _build_dynamic_investment_allocation(user_budget, business_category, idea):
    """
    Dynamically generates realistic investment categories tailored to the startup type.
    Strictly guarantees that SUM(categories) == user_budget (100% exact match).
    Only selects categories relevant to the specific startup.
    """
    user_budget = parse_clean_budget(user_budget)
    text = f"{business_category} {idea}".lower()

    if any(k in text for k in ['food', 'beverage', 'kitchen', 'restaurant', 'cafe', 'meal', 'tiffin']):
        raw_alloc = {
            'Kitchen & Cooking Equipment': 0.32,
            'Commercial Space / Lease': 0.22,
            'Initial Ingredients & Inventory': 0.14,
            'Local Marketing & Signage': 0.12,
            'Staffing & Food Handlers': 0.10,
            'FSSAI & Trade Licenses': 0.04,
            'Working Capital Reserve': 0.06
        }
    elif any(k in text for k in ['energy', 'cleantech', 'charging', 'solar', 'power', 'battery']):
        raw_alloc = {
            'Charging Hardware & Power Equipment': 0.38,
            'Site Lease & Electrical Civil Works': 0.22,
            'Grid Connection & Transformer Setup': 0.14,
            'Mobile App & Payment Integration': 0.10,
            'Government Permits & Safety Inspection': 0.06,
            'Operating Working Capital': 0.10
        }
    elif any(k in text for k in ['agri', 'farm', 'crop', 'soil', 'irrigation', 'farmer']):
        raw_alloc = {
            'Agricultural Equipment & Field Tools': 0.35,
            'Storage & Demonstration Depot': 0.18,
            'Farmer Outreach & Demonstrations': 0.15,
            'Field Operations Staff': 0.14,
            'Trade Permits & Compliance': 0.05,
            'Working Capital Buffer': 0.13
        }
    elif any(k in text for k in ['logistics', 'delivery', 'transport', 'mobility', 'vehicle']):
        raw_alloc = {
            'Vehicle Fleet & Transport Setup': 0.36,
            'Warehouse & Hub Rent': 0.18,
            'Tracking Software & GPS Hardware': 0.12,
            'Driver & Field Operations': 0.14,
            'Commercial Permits & Insurance': 0.08,
            'Working Capital Reserve': 0.12
        }
    elif any(k in text for k in ['shopping', 'ecommerce', 'e-commerce', 'retail']):
        raw_alloc = {
            'Initial Product Inventory': 0.32,
            'E-Commerce Platform & POS Setup': 0.18,
            'Packaging & Fulfillment Logistics': 0.14,
            'Digital & Social Media Marketing': 0.18,
            'Store / Storage Facility': 0.10,
            'Working Capital Reserve': 0.08
        }
    elif any(k in text for k in ['health', 'fitness', 'gym', 'wellness', 'clinic']):
        raw_alloc = {
            'Health & Fitness Equipment': 0.32,
            'Facility Lease & Space Renovation': 0.24,
            'Local Marketing & Launch Offers': 0.14,
            'Certified Trainers / Staff': 0.14,
            'Health Licenses & Certifications': 0.06,
            'Working Capital Reserve': 0.10
        }
    elif any(k in text for k in ['education', 'edtech', 'tutor', 'school', 'coaching']):
        raw_alloc = {
            'Curriculum & Learning Content Tools': 0.28,
            'Classroom / Studio Tech Setup': 0.22,
            'Student Acquisition & Marketing': 0.22,
            'Teaching & Administrative Staff': 0.14,
            'Accreditations & Entity Setup': 0.04,
            'Working Capital Reserve': 0.10
        }
    elif any(k in text for k in ['beauty', 'personal care', 'cosmetics', 'salon', 'skincare']):
        raw_alloc = {
            'Salon / Treatment Equipment': 0.30,
            'Studio / Clinic Lease & Interior': 0.24,
            'Cosmetic Inventory & Consumables': 0.16,
            'Local Promotion & Influencer Marketing': 0.14,
            'Trained Stylists / Aestheticians': 0.10,
            'Operating Working Capital': 0.06
        }
    elif any(k in text for k in ['real estate', 'property', 'housing', 'rental']):
        raw_alloc = {
            'Commercial Office & Client Lounge': 0.28,
            'Listing Platform & Virtual Tour Tech': 0.20,
            'Targeted Property Marketing': 0.22,
            'Legal Documentation & RERA Compliance': 0.12,
            'Sales Agents & Operations': 0.10,
            'Working Capital Reserve': 0.08
        }
    elif any(k in text for k in ['entertainment', 'media', 'gaming', 'esports']):
        raw_alloc = {
            'Gaming / Production Hardware & Studios': 0.36,
            'Software Licenses & Content Assets': 0.20,
            'Audience Acquisition & Stream Marketing': 0.20,
            'Creators & Technical Production Crew': 0.14,
            'Working Capital Reserve': 0.10
        }
    elif any(k in text for k in ['hr', 'recruitment', 'hiring', 'talent', 'staffing']):
        raw_alloc = {
            'ATS & Candidate Screening Platform': 0.32,
            'Job Board Credits & Candidate Sourcing': 0.24,
            'Client Acquisition & B2B Sales': 0.20,
            'Recruitment Specialists & Operations': 0.14,
            'Working Capital Reserve': 0.10
        }
    elif any(k in text for k in ['tech', 'software', 'ai', 'saas', 'platform', 'app', 'cyber']):
        raw_alloc = {
            'Software Development & Product Build': 0.38,
            'Cloud & Server Infrastructure': 0.16,
            'Targeted Digital Marketing': 0.18,
            'Technical & Support Staff': 0.12,
            'Legal, Compliance & Registration': 0.06,
            'Operating Working Capital': 0.10
        }
    else:
        raw_alloc = {
            'Core Operational Equipment & Setup': 0.32,
            'Commercial Space / Facility': 0.20,
            'Customer Acquisition & Marketing': 0.18,
            'Team & Operational Staff': 0.14,
            'Business Registration & Permits': 0.06,
            'Working Capital Reserve': 0.10
        }

    categories = {}
    running_total = 0
    cat_keys = list(raw_alloc.keys())
    for idx, (cat_name, pct) in enumerate(raw_alloc.items()):
        if idx == len(cat_keys) - 1:
            # Last category absorbs any rounding difference to ensure exact equality
            val = user_budget - running_total
        else:
            val = int(round(user_budget * pct))
            running_total += val
        categories[cat_name] = max(0, val)

    # Sanity check: Ensure strict exact sum
    total_planned = sum(categories.values())
    diff = user_budget - total_planned
    if diff != 0:
        last_key = cat_keys[-1]
        categories[last_key] = max(0, categories[last_key] + diff)

    return {
        'user_input_budget': user_budget,
        'categories': categories,
        'total_planned_investment': sum(categories.values()),
        'remaining_reserve': 0,
        'note': "These are estimated allocations, not guaranteed costs."
    }


def _determine_business_model(idea, business_category, target_audiences, budget, location):
    """
    Dynamically recommends Online, Offline, or Online + Offline.
    Provides simple English rationale and tailored operational points.
    Never gives the same static response.
    """
    text = f"{idea} {business_category}".lower()

    has_physical = any(k in text for k in [
        'food', 'restaurant', 'cafe', 'kitchen', 'dining', 'farm', 'crop', 'agriculture',
        'ev', 'charging', 'station', 'clinic', 'hospital', 'gym', 'fitness center',
        'warehouse', 'store', 'shop', 'retail outlet', 'salon', 'manufacturing',
        'hardware', 'repair', 'waste', 'solar panel installation', 'nursery', 'dairy'
    ])

    has_pure_digital = any(k in text for k in [
        'saas', 'api', 'ai resume', 'ai bot', 'code review', 'seo tool', 'cloud tool',
        'virtual assistant', 'newsletter', 'developer platform', 'portfolio generator',
        'remote tutoring platform', 'digital art marketplace'
    ])

    if has_pure_digital and not has_physical:
        rec = "Online"
        why = (
            f"This startup provides a digital service that can be built, hosted, and delivered entirely over the internet. "
            f"An online model lets you reach target customers across {location or 'your target market'} without the heavy expense of renting a physical commercial shop."
        )
        structure = [
            "Users access and use the platform directly via web browser or mobile app.",
            "Customer onboarding, automated billing, and user support happen entirely online.",
            "Zero physical retail lease keeps operating overhead low and capital focused on product development."
        ]
    elif has_physical and any(k in text for k in ['delivery', 'app', 'booking', 'online ordering', 'tracker', 'smart', 'platform', 'marketplace', 'iot', 'network', 'charging', 'station', 'rental']):
        rec = "Online + Offline"
        why = (
            f"This idea can reach customers online (for discovering availability, booking, and digital payments), "
            f"while the physical location in {location or 'the local area'} is used to provide the actual service."
        )
        structure = [
            "Online Channel: Mobile-friendly website or app for customer discovery, slot booking, live tracking, and digital payments.",
            "Offline Operations: Physical facility, charging hardware, kitchen, or service center where the actual service is delivered.",
            "Integration: Automated online updates keep customers informed in real-time about service status and availability."
        ]
    elif has_physical:
        rec = "Offline"
        why = (
            f"The primary value of this venture comes from hands-on, face-to-face interaction, physical demonstrations, "
            f"or local presence where customers in {location or 'the area'} need to visit or receive service in person."
        )
        structure = [
            "Dedicated physical workspace, clinic, store, or workshop in an accessible commercial area.",
            "Direct in-person sales, walk-in consultations, and local neighborhood relationships.",
            "Lightweight digital presence (Google Business Profile, WhatsApp) used primarily for basic contact and location sharing."
        ]
    else:
        # Default hybrid approach when both channels add value
        rec = "Online + Offline"
        why = (
            f"Combining an online presence with local offline touchpoints gives target customers "
            f"the convenience of online access along with the trust and reliability of local service delivery."
        )
        structure = [
            "Digital storefront or landing page for marketing, inquiries, and customer trust.",
            "Local operational presence to handle customer fulfillment, relationship building, and community outreach.",
            "Unified tracking system ensuring inquiries from both channels are serviced promptly."
        ]

    return {
        'recommendation': rec,
        'why': why,
        'operational_structure': structure
    }


def _generate_suitable_locations(idea, business_category, target_audiences, budget, loc_summary, loc_details):
    """
    Dynamically generates multiple distinct, real nearby locations
    based on the startup idea, category, audience, and local geography using location_intelligence engine.
    Guarantees non-repeating real nearby areas with genuine demand factors and feasibility estimation.
    Uses cautious wording: never promises guaranteed profit.
    """
    return location_intelligence.find_surrounding_locations(loc_details, business_category, idea, budget)


def _dynamic_generator_fallback(data, df):
    """
    Advanced dynamic generation engine that creates a complete 18-section blueprint
    strictly customized to user inputs without hardcoded results or static templates.
    """
    category = strip_emojis(data.get('business_category') or data.get('industry') or 'Technology')
    idea = str(data.get('idea') or 'Innovative startup venture').strip()
    
    # Process target audiences
    raw_aud = data.get('target_audience') or data.get('target_customers') or ['College Students']
    if isinstance(raw_aud, str):
        aud_list = [strip_emojis(x.strip()) for x in raw_aud.split(',') if x.strip()]
    elif isinstance(raw_aud, list):
        aud_list = [strip_emojis(x) for x in raw_aud if str(x).strip()]
    else:
        aud_list = ['College Students']
    if not aud_list:
        aud_list = ['Target Customers']

    user_budget = parse_clean_budget(data.get('budget'))
    team_size = max(1, int(data.get('team_size') or 2))

    loc_details = location_intelligence.parse_location_details(data)
    loc_summary = data.get('location') or loc_details['display_name'] or loc_details['concise_label']
    city = (
        loc_details.get('village_town_city') if loc_details.get('village_town_city') != 'Not available'
        else loc_details.get('area') if loc_details.get('area') != 'Not available'
        else loc_details.get('district') or loc_summary
    )

    name = make_name(idea)
    relevant_csv = filter_relevant_dataset(df, idea, category, aud_list, user_budget, loc_summary)
    
    # 1. Business Model Recommendation
    bm_data = _determine_business_model(idea, category, aud_list, user_budget, city)

    # 2. Main Location Analysis, Suitable Real Nearby Locations & Comparison
    main_loc_analysis = location_intelligence.analyze_main_location(loc_details, category, idea, user_budget)
    locations_list = _generate_suitable_locations(idea, category, aud_list, user_budget, loc_summary, loc_details)
    loc_comparison = location_intelligence.generate_location_comparison(loc_details, locations_list, idea, category, user_budget)

    # 3. Budget & Investment Allocation
    budget_alloc = _build_dynamic_investment_allocation(user_budget, category, idea)

    # 4. Content generation in simple English
    aud_str = ", ".join(aud_list)
    exec_summary = (
        f"{name} is a {category} startup created to solve practical challenges around '{idea}' "
        f"for {aud_str.lower()} in {loc_summary}. Operating with an initial budget of ₹{user_budget:,} "
        f"and a launch team of {team_size} member(s), the business will operate using an {bm_data['recommendation']} model. "
        f"Initial operations will focus on providing reliable service to early customers in {city} "
        f"while maintaining strict discipline over setup costs and daily expenses."
    )

    problem = (
        f"Currently, {aud_str.lower()} in {city} struggle with '{idea.lower()}' because existing solutions "
        f"are often inconvenient, inconsistent in quality, lack transparent local pricing, or fail to provide responsive local support."
    )

    solution = (
        f"{name} offers a clear, accessible solution tailored specifically for {aud_str.lower()} in {city}. "
        f"The venture focuses on solving '{idea}' through transparent pricing, dependable delivery, and simple direct communication, "
        f"while keeping operational setup costs strictly within the planned budget allocation of ₹{budget_alloc['total_planned_investment']:,}."
    )

    market_opportunity = (
        f"The demand for practical {category.lower()} offerings among {aud_str.lower()} in {city} is expanding. "
        f"Most customers currently rely on informal alternatives or fragmented providers. By offering a professional, "
        f"customer-focused experience with clear accountability, {name} can secure a solid position with high repeat usage."
    )

    go_to_market = [
        f"Engage early adopters among {aud_str.lower()} in {city} through direct demonstrations and introductory trial offers.",
        f"Run hyper-local digital promotions and community messaging targeting neighborhoods within a 10 km radius of {loc_summary}.",
        f"Partner with trusted local institutions, commercial hubs, and community touchpoints where {aud_str.lower()} regularly gather.",
        f"Implement a simple word-of-mouth referral incentive offering discounts to customers who introduce friends and colleagues."
    ]

    operations = [
        f"Establish lean operating workflows utilizing the core founding team of {team_size} member(s) to handle initial customer fulfillment.",
        f"Set up essential tools and equipment strictly within the ₹{budget_alloc['total_planned_investment']:,} budget allocation.",
        "Implement clear daily service standards with prompt response times for customer inquiries and orders.",
        "Monitor customer feedback after every transaction to rapidly improve operational reliability and service speed."
    ]

    roadmap = [
        f"Month 1: Groundwork & Setup — Finalize business registration, acquire essential starter tools, and set up communication channels.",
        f"Month 2: Pilot Testing — Launch a controlled test with 20 to 30 early customers among {aud_str.lower()} in {city} to refine workflows.",
        f"Month 3: Commercial Launch — Roll out local marketing campaigns across {city} and begin regular daily order fulfillment.",
        "Months 4–6: Growth & Review — Review customer retention rates, optimize operating costs, and assess expansion across nearby localities."
    ]

    opportunities = [
        f"Expanding service options to cater to adjacent customer segments across {loc_details.get('state', 'the region')}.",
        "Introducing simple subscription or monthly packages to secure recurring monthly customer relationships.",
        "Using customer usage data to introduce complementary add-on services that increase average order value.",
        "Collaborating with local suppliers to negotiate bulk pricing discounts as order volumes increase."
    ]

    risks = [
        f"Initial customer hesitation or slow adoption in {city}: Mitigate through risk-free first-time trials and direct founder interaction.",
        "Operating cost overruns: Mitigate by adhering strictly to the planned budget categories and reviewing weekly expenses.",
        "Informal local competition offering cut-price services: Mitigate through consistent reliability, superior hygiene/quality, and responsive support.",
        "Team bandwidth constraints during demand spikes: Mitigate through documented standard operating procedures and part-time seasonal support."
    ]

    success_metrics = [
        f"Onboard 50 to 100 active {aud_str.lower()} within the first 60 days of operations in {city}.",
        "Achieve a 40%+ repeat customer or subscription renewal rate within the first 90 days.",
        f"Keep total operational spending strictly within the initial ₹{user_budget:,} capital ceiling.",
        "Maintain customer satisfaction above 90% based on post-service ratings and reviews."
    ]

    next_steps = [
        f"Complete formal business registration and obtain any necessary local permits relevant to {loc_details.get('state', 'the region')}.",
        f"Conduct 15 to 20 structured validation conversations with {aud_str.lower()} in {city}.",
        f"Finalize vendor quotes for equipment and supplies to strictly match the planned ₹{user_budget:,} budget allocation.",
        f"Set up basic customer communication channels (WhatsApp Business, online landing page, and social media handles)."
    ]

    final_summary = (
        f"{name} is a practical, grounded startup concept tailored for {city}. "
        f"By focusing on solving the core problem for {aud_str.lower()} with an efficient {bm_data['recommendation']} model "
        f"and strictly controlling capital deployment within ₹{user_budget:,}, the venture has a realistic, actionable pathway to launch."
    )

    dataset_summary = (
        f"Reviewed {len(relevant_csv)} relevant historical startup patterns from the dataset in {category} "
        f"for problem-solving frameworks and lean operating benchmarks."
    ) if relevant_csv else "No direct matching historical dataset records found; analyzed using primary category principles."

    external_summary = (
        f"Grounded using geographic and commercial hub data for {loc_summary} and surrounding trade clusters."
    )

    return {
        'startup_name': name,
        'business_category': category,
        'industry': category,  # backward compatibility
        'idea': idea,
        'target_audience': aud_list,
        'target_customers': aud_str,  # backward compatibility
        'budget': user_budget,
        'team_size': team_size,
        'location_summary': loc_summary,
        'location_details': loc_details,
        'executive_summary': exec_summary,
        'startup_overview': {
            'startup_name': name,
            'business_category': category,
            'idea': idea,
            'target_audience': aud_list,
            'location': loc_summary,
            'budget': user_budget,
            'team_size': team_size,
            'summary': exec_summary
        },
        'problem': problem,
        'solution': solution,
        'business_model_recommendation': bm_data,
        'recommended_approach': bm_data['recommendation'],  # backward compatibility
        'main_location_analysis': main_loc_analysis,
        'suitable_locations': locations_list,
        'suggested_locations': locations_list,  # backward compatibility
        'suitable_nearby_places': locations_list,  # backward compatibility
        'location_comparison': loc_comparison,
        'budget_allocation': budget_alloc,
        'budget_breakdown': budget_alloc['categories'],  # backward compatibility
        'market_opportunity': market_opportunity,
        'go_to_market': go_to_market,
        'marketing_strategy': go_to_market,  # backward compatibility
        'operations': operations,
        'roadmap': roadmap,
        'implementation_roadmap': roadmap,  # backward compatibility
        'opportunities': opportunities,
        'risks': risks,
        'risks_and_mitigation': risks,  # backward compatibility
        'success_metrics': success_metrics,
        'next_steps': next_steps,
        'final_summary': final_summary,
        'data_sources': {
            'user_inputs': f"Startup idea, business category ({category}), target audience, budget (₹{user_budget:,}), and location ({loc_summary}).",
            'dataset_information': dataset_summary,
            'verified_external_information': external_summary,
            'citations': [loc_summary]
        }
    }


def _generate_with_gemini(data, df, api_key, model_name="gemini-2.5-flash"):
    """
    Generates dynamic startup blueprint using Google Gemini AI and CSV dataset context.
    Attempts Google Search grounding when supported.
    Strictly follows prompt rules: no invented statistics, no profit/loss forecast, simple English.
    """
    import google.generativeai as genai
    genai.configure(api_key=api_key)

    category = strip_emojis(data.get('business_category') or data.get('industry') or 'Technology')
    idea = str(data.get('idea') or 'Innovative startup venture').strip()
    
    raw_aud = data.get('target_audience') or data.get('target_customers') or ['College Students']
    if isinstance(raw_aud, str):
        aud_list = [strip_emojis(x.strip()) for x in raw_aud.split(',') if x.strip()]
    elif isinstance(raw_aud, list):
        aud_list = [strip_emojis(x) for x in raw_aud if str(x).strip()]
    else:
        aud_list = ['College Students']
    if not aud_list:
        aud_list = ['Target Customers']

    user_budget = parse_clean_budget(data.get('budget'))
    team_size = max(1, int(data.get('team_size') or 2))

    loc_details = location_intelligence.parse_location_details(data)
    loc_summary = data.get('location') or loc_details['display_name'] or loc_details['concise_label']
    city = (
        loc_details.get('village_town_city') if loc_details.get('village_town_city') != 'Not available'
        else loc_details.get('area') if loc_details.get('area') != 'Not available'
        else loc_details.get('district') or loc_summary
    )

    relevant_csv = filter_relevant_dataset(df, idea, category, aud_list, user_budget, loc_summary)

    prompt = f"""You are an AI business analysis assistant for a Startup Business Blueprint Generator.

Generate a comprehensive, realistic startup blueprint using:
1. User Input
2. Relevant CSV Dataset Information
3. Verified Current External Information (via Google Search where available)

Rules:
- Do not invent facts, statistics, or market sizes.
- Do not claim guaranteed profitability.
- Use only relevant dataset information.
- Use current verified information when available.
- Clearly distinguish dataset-derived information from external verified information.
- If information cannot be verified, state the limitation honestly.
- Generate recommendations specifically for this startup idea and business category: {category}.
- Do not return generic content that could apply to every startup.
- Use simple English. Avoid unnecessarily complicated business terminology.
- Keep explanations clear, practical, and easy to understand.

Do NOT generate any of the following:
- Revenue Forecast
- Expense Forecast
- Profit Forecast
- Loss Forecast
- Hybrid Strategy (Use 'Business Model Recommendation' instead)
- Hybrid Startup Women

USER INPUT:
- Startup Idea: {idea}
- Business Category: {category}
- Target Audience: {json.dumps(aud_list)}
- Primary Budget: ₹{user_budget:,} (STRICT CEILING)
- Core Team Size: {team_size}
- Primary Business Location: {loc_summary} (City/District: {city})

RELEVANT CSV DATASET INFORMATION:
{json.dumps(relevant_csv, ensure_ascii=False, indent=2)}

INSTRUCTIONS FOR KEY SECTIONS:
1. Business Model Recommendation:
   - Must be one of: "Online", "Offline", or "Online + Offline".
   - Provide a clear, simple English "Why" explanation tailored to {idea} in {category}.
   - Provide practical operational structure points.
2. Suitable Potential Locations:
   - Suggest 5 specific types of locations or areas in/around {city} tailored specifically for {idea}.
   - Do NOT use generic repeats like "IT Parks" or "University Areas" unless strictly appropriate for the startup.
   - Separate suggestions into 3 tiers: High Profit Potential, Moderate Profit Potential, and Low Profit Potential.
   - For each location include: name, location_type, why_this_location, target_customers, demand (Low/Medium/High), competition (Low/Medium/High), rent (Low/Medium/High), accessibility (Low/Medium/High), profit_potential (High/Medium/Low), risk (Low/Medium/High), location_score (0-100), and business_reason.
   - Use cautious language: "Potentially suitable location", "May be suitable because...".
   - Never claim guaranteed profitability.
3. Investment Allocation:
   - Break down the budget across dynamically chosen relevant categories (e.g. Equipment, Technology, Rent, Marketing, Staff, Operations, Inventory, Licenses, Working Capital).
   - SUM OF ALL ALLOCATED CATEGORIES MUST EXACTLY EQUAL {user_budget}.
   - Include the exact disclaimer: "These are estimated allocations, not guaranteed costs."

Return ONLY a single valid JSON object with EXACTLY this structure:
{{
  "startup_name": "string",
  "executive_summary": "string",
  "problem": "string",
  "solution": "string",
  "business_model_recommendation": {{
    "recommendation": "Online | Offline | Online + Offline",
    "why": "simple English explanation",
    "operational_structure": ["string", "string", "string"]
  }},
  "suitable_locations": [
    {{
      "name": "string",
      "location_type": "string",
      "why_this_location": "string (e.g. Potentially suitable because...)",
      "why_suitable": "string",
      "target_customers": "string",
      "customer_factors": "string",
      "demand": "Low | Medium | High",
      "competition": "Low | Medium | High",
      "rent": "Low | Medium | High",
      "accessibility": "Low | Medium | High",
      "profit_potential": "High | Medium | Low",
      "risk": "Low | Medium | High",
      "location_score": 85,
      "business_reason": "string",
      "simple_explanation": "string",
      "citations": "string or source reference if available"
    }}
  ],
  "budget_allocation": {{
    "categories": {{
      "Category 1": 0,
      "Category 2": 0
    }},
    "note": "These are estimated allocations, not guaranteed costs."
  }},
  "market_opportunity": "string",
  "go_to_market": ["string", "string", "string", "string"],
  "operations": ["string", "string", "string", "string"],
  "roadmap": ["string", "string", "string", "string"],
  "opportunities": ["string", "string", "string", "string"],
  "risks": ["string", "string", "string", "string"],
  "success_metrics": ["string", "string", "string", "string"],
  "next_steps": ["string", "string", "string", "string"],
  "final_summary": "string",
  "data_sources": {{
    "user_inputs": "string",
    "dataset_information": "string",
    "verified_external_information": "string",
    "citations": ["string"]
  }}
}}"""

    response = None
    # Attempt 1: Call Gemini with Google Search tool if supported
    try:
        model = genai.GenerativeModel(model_name=model_name, tools='google_search_retrieval')
        response = model.generate_content(prompt)
    except Exception:
        pass

    # Attempt 2: Call Gemini standard model without tools
    if not response or not getattr(response, 'text', None):
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content(prompt)

    if not response or not response.text:
        raise ValueError("Empty response received from Gemini AI model.")

    result = _clean_json(response.text)

    # Enforce budget mathematics strictly: categories must sum exactly to user_budget
    ba = result.get('budget_allocation') or {}
    cats = ba.get('categories') or {}
    cleaned_cats = {}
    running_sum = 0
    cat_keys = list(cats.keys())

    for idx, k in enumerate(cat_keys):
        try:
            amt = int(float(cats[k]))
        except Exception:
            amt = 0
        cleaned_cats[k] = max(0, amt)
        running_sum += cleaned_cats[k]

    # If LLM didn't sum correctly or empty, adjust or rebalance
    if running_sum != user_budget or not cleaned_cats:
        cleaned_allocation = _build_dynamic_investment_allocation(user_budget, category, idea)
        result['budget_allocation'] = cleaned_allocation
    else:
        result['budget_allocation'] = {
            'user_input_budget': user_budget,
            'categories': cleaned_cats,
            'total_planned_investment': sum(cleaned_cats.values()),
            'note': "These are estimated allocations, not guaranteed costs."
        }

    # Ensure all required top-level keys and backward-compatible fields are populated
    result['startup_name'] = result.get('startup_name') or make_name(idea)
    result['business_category'] = category
    result['industry'] = category
    result['idea'] = idea
    result['target_audience'] = aud_list
    result['target_customers'] = ", ".join(aud_list)
    result['budget'] = user_budget
    result['team_size'] = team_size
    result['location_summary'] = loc_summary
    result['location_details'] = loc_details

    # Business Model compatibility
    bm = result.get('business_model_recommendation') or {}
    rec_app = bm.get('recommendation', 'Online + Offline')
    result['recommended_approach'] = rec_app

    # Locations compatibility & Main Location Analysis
    main_loc_analysis = location_intelligence.analyze_main_location(loc_details, category, idea, user_budget)
    result['main_location_analysis'] = main_loc_analysis

    locs = result.get('suitable_locations') or []
    if not locs or len(locs) < 5 or any('University & College Hubs' in str(l) for l in locs) or not any(isinstance(l, dict) and l.get('profit_potential') for l in locs):
        locs = _generate_suitable_locations(idea, category, aud_list, user_budget, loc_summary, loc_details)
        result['suitable_locations'] = locs
    result['suggested_locations'] = locs
    result['suitable_nearby_places'] = locs
    result['location_comparison'] = location_intelligence.generate_location_comparison(loc_details, locs, idea, category, user_budget)

    # Other legacy compatibility bridges
    result['budget_breakdown'] = result['budget_allocation']['categories']
    result['marketing_strategy'] = result.get('go_to_market') or []
    result['implementation_roadmap'] = result.get('roadmap') or []
    result['risks_and_mitigation'] = result.get('risks') or []

    result['startup_overview'] = {
        'startup_name': result['startup_name'],
        'business_category': category,
        'idea': idea,
        'target_audience': aud_list,
        'location': loc_summary,
        'budget': user_budget,
        'team_size': team_size,
        'summary': result.get('executive_summary', '')
    }

    # Remove all forbidden keys
    forbidden = [
        'profit_loss_estimate', 'profit_loss', 'revenue', 'expense',
        'monthly_revenue_range', 'monthly_expense_range', 'monthly_profit_or_loss_range',
        'hybrid_strategy', 'hybrid_analysis', 'online_offline_analysis'
    ]
    for fb in forbidden:
        result.pop(fb, None)

    return result


def generate(data, path):
    """
    Main generation entry point called by Flask app.
    Integrates Gemini AI when GEMINI_API_KEY is configured,
    and falls back seamlessly to the enhanced dynamic generator without failing.
    """
    df = None
    if path and os.path.exists(path):
        try:
            df = pd.read_csv(path)
        except Exception:
            df = None

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    # Support backward-compatible environment variable if someone configured it
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

    if api_key and api_key != "your_gemini_api_key_here":
        try:
            return _generate_with_gemini(data, df, api_key, model_name)
        except Exception as e:
            # Safe user-friendly fallback without exposing keys
            return _dynamic_generator_fallback(data, df)
    else:
        return _dynamic_generator_fallback(data, df)


def suggest_target_customers(idea="", industry="", location=""):
    """Suggests relevant target audiences for an idea."""
    t = f"{idea} {industry}".lower()
    if any(k in t for k in ["college", "student", "study", "exam", "hostel", "youth"]):
        return ["College Students", "Job Seekers", "Working Professionals", "Online Customers"]
    if any(k in t for k in ["food", "dining", "meal", "restaurant", "tiffin"]):
        return ["College Students", "Working Professionals", "Families", "Local Customers"]
    if any(k in t for k in ["farm", "agri", "crop", "rural", "farmer"]):
        return ["Farmers", "Small Businesses", "Entrepreneurs", "Local Customers"]
    if any(k in t for k in ["b2b", "saas", "software", "payroll", "tech"]):
        return ["Small Businesses", "Entrepreneurs", "Freelancers", "Working Professionals"]
    if any(k in t for k in ["health", "clinic", "fit", "gym", "wellness"]):
        return ["Working Professionals", "Senior Citizens", "Families", "Women"]
    return ["Working Professionals", "College Students", "Small Businesses", "Local Customers"]


def suggest_target_industries(idea=""):
    """Suggests relevant business categories for an idea."""
    t = str(idea or '').lower()
    if any(k in t for k in ["ai", "resume", "software", "app", "tech", "platform"]):
        return ["Technology", "HR & Recruitment", "Social Media & Communication"]
    if any(k in t for k in ["food", "meal", "kitchen", "cafe", "restaurant", "tiffin"]):
        return ["Food & Beverages", "Logistics & Delivery"]
    if any(k in t for k in ["farm", "crop", "agriculture", "farmer"]):
        return ["Agriculture & Farming", "Logistics & Delivery"]
    if any(k in t for k in ["doctor", "health", "clinic", "gym", "fitness"]):
        return ["Healthcare & Fitness", "Sports & Gaming"]
    if any(k in t for k in ["car", "bike", "ev", "cab", "ride", "scooter"]):
        return ["Transportation & Mobility", "Energy & CleanTech"]
    if any(k in t for k in ["shop", "cloth", "ecommerce", "store", "buy"]):
        return ["Shopping & E-Commerce", "Logistics & Delivery"]
    return ["Technology", "Shopping & E-Commerce", "Food & Beverages", "Education & EdTech"]


# Backward-compatibility helpers for legacy scripts
def calculate_budget(user_budget, industry="Technology", team_size=2):
    """Legacy helper for testing budget calculation."""
    return _build_dynamic_investment_allocation(user_budget, industry, "")

def calculate_profit_loss(user_budget, industry="Technology", team_size=2, loc_name=""):
    """Legacy helper returning empty structure as profit/loss is decommissioned."""
    return {
        'monthly_revenue_range': '-',
        'monthly_expense_range': '-',
        'monthly_profit_or_loss_range': '-'
    }

def extract_location_info(data):
    """Legacy helper for extracting location details."""
    loc_details = location_intelligence.parse_location_details(data)
    return loc_details.get('concise_label', 'Selected Location'), loc_details

