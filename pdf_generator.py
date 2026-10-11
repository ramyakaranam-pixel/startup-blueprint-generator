"""
pdf_generator.py
Generates a professional, print-ready PDF for the Startup Business Blueprint
using ReportLab with clean styling, tables, page numbers, and exact blueprint structure.
Reflects:
- Business Category
- Target Audience
- Business Model Recommendation
- Suitable Potential Locations
- Budget & Investment Allocation (100% budget match)
- Market Opportunity, Operations, Roadmap, Risks, Opportunities, Success Metrics, Next Steps
Excludes:
- Estimated Revenue, Expenses, Profit/Loss
- Hybrid Strategy
- Technical dataset debug signals
"""

import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
FONT_OBLIQUE = 'Helvetica-Oblique'

try:
    font_paths = [
        ('C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/ariali.ttf'),
        ('C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/segoeuii.ttf'),
    ]
    for regular, bold, italic in font_paths:
        if os.path.exists(regular) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont('CustomFont', regular))
            pdfmetrics.registerFont(TTFont('CustomFont-Bold', bold))
            if os.path.exists(italic):
                pdfmetrics.registerFont(TTFont('CustomFont-Oblique', italic))
            else:
                pdfmetrics.registerFont(TTFont('CustomFont-Oblique', regular))
            FONT_NAME = 'CustomFont'
            FONT_BOLD = 'CustomFont-Bold'
            FONT_OBLIQUE = 'CustomFont-Oblique'
            break
except Exception:
    pass


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y' along with header/footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont(FONT_NAME, 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(36, 758, "STARTUP BUSINESS BLUEPRINT")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(36, 752, 576, 752)

        # Footer (All pages)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(36, 42, 576, 42)

        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 30, page_text)
        self.drawString(36, 30, "CONFIDENTIAL · STARTUP BUSINESS BLUEPRINT GENERATOR")
        self.restoreState()


def format_rupee(val):
    try:
        n = int(float(val))
        return f"₹{n:,}"
    except (ValueError, TypeError):
        return str(val or '₹0')


def build_blueprint_pdf(b, output_path_or_buffer):
    """Generates the complete PDF from blueprint dictionary 'b'."""
    doc = SimpleDocTemplate(
        output_path_or_buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=48,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#1e3a8a")     # Deep navy
    secondary_color = colors.HexColor("#0284c7")   # Bright sky blue
    dark_neutral = colors.HexColor("#0f172a")      # Slate 900
    text_color = colors.HexColor("#334155")        # Slate 700
    light_bg = colors.HexColor("#f8fafc")          # Slate 50
    border_color = colors.HexColor("#cbd5e1")      # Slate 300

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=15,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9,
        leading=13,
        textColor=secondary_color,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=8.5,
        leading=12,
        textColor=text_color,
        spaceAfter=4
    )

    body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName=FONT_BOLD,
        textColor=dark_neutral
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=8,
        leading=11,
        textColor=text_color
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName=FONT_BOLD,
        textColor=dark_neutral
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=8,
        leading=11,
        textColor=colors.white
    )

    story = []

    startup_name = str(b.get('startup_name', 'STARTUP VENTURE')).upper()
    category = str(b.get('business_category') or b.get('industry', 'Business'))
    idea = str(b.get('idea', ''))
    loc_summary = str(b.get('location_summary', 'Selected Location'))
    loc_details = b.get('location_details') or {}

    ba = b.get('budget_allocation') or {}
    user_budget = ba.get('user_input_budget') or b.get('budget', 500000)
    budget_str = format_rupee(user_budget)
    team_size = b.get('team_size', '2')

    bm = b.get('business_model_recommendation') or {}
    rec_approach = bm.get('recommendation') or b.get('recommended_approach', 'Online + Offline')
    
    raw_aud = b.get('target_audience') or b.get('target_customers') or 'Target Customers'
    if isinstance(raw_aud, list):
        aud_str = ", ".join([str(a) for a in raw_aud])
    else:
        aud_str = str(raw_aud)

    # Document Header Banner
    story.append(Paragraph(f"STARTUP BUSINESS BLUEPRINT: {startup_name}", title_style))
    story.append(Paragraph(
        f"<b>Business Category:</b> {category} &nbsp;|&nbsp; <b>Primary Budget:</b> {budget_str} &nbsp;|&nbsp; "
        f"<b>Model:</b> {rec_approach} &nbsp;|&nbsp; <b>Location:</b> {loc_summary}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=8))

    # 1. Startup Overview
    story.append(Paragraph("1. STARTUP OVERVIEW", h1_style))
    overview_data = [
        [Paragraph("<b>Startup Name:</b>", table_cell_bold), Paragraph(startup_name, table_cell_style),
         Paragraph("<b>Business Category:</b>", table_cell_bold), Paragraph(category, table_cell_style)],
        [Paragraph("<b>Primary Budget:</b>", table_cell_bold), Paragraph(budget_str, table_cell_style),
         Paragraph("<b>Core Team Size:</b>", table_cell_bold), Paragraph(f"{team_size} member(s)", table_cell_style)],
        [Paragraph("<b>Target Audience:</b>", table_cell_bold), Paragraph(aud_str, table_cell_style),
         Paragraph("<b>Business Model:</b>", table_cell_bold), Paragraph(rec_approach, table_cell_style)],
        [Paragraph("<b>Startup Idea:</b>", table_cell_bold), Paragraph(idea, table_cell_style),
         Paragraph("<b>Location:</b>", table_cell_bold), Paragraph(loc_summary, table_cell_style)]
    ]
    t_over = Table(overview_data, colWidths=[105, 165, 110, 160])
    t_over.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_over)
    story.append(Spacer(1, 6))

    # Executive Summary Snippet
    story.append(Paragraph(str(b.get('executive_summary', '-')), body_style))
    story.append(Spacer(1, 6))

    # 2 & 3. Problem Statement & Proposed Solution
    core_cards = [
        [Paragraph("<b>2. PROBLEM STATEMENT</b>", h2_style), Paragraph("<b>3. PROPOSED SOLUTION</b>", h2_style)],
        [Paragraph(str(b.get('problem', '-')), body_style), Paragraph(str(b.get('solution', '-')), body_style)]
    ]
    t_core = Table(core_cards, colWidths=[270, 270])
    t_core.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fdfdfd")),
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_core)
    story.append(Spacer(1, 6))

    # 4. Business Model Recommendation
    story.append(Paragraph(f"4. BUSINESS MODEL RECOMMENDATION: {rec_approach.upper()}", h1_style))
    story.append(Paragraph(f"<b>Strategic Fit:</b> {bm.get('why', '-')}", body_style))
    for op in bm.get('operational_structure', []):
        story.append(Paragraph(f"• {op}", bullet_style))
    story.append(Spacer(1, 6))

    # 5. Suitable Potential Locations
    story.append(Paragraph("5. SUITABLE POTENTIAL LOCATIONS", h1_style))
    story.append(Paragraph(
        "<i>Note: Locations are suggested based on geographical factors and customer presence. Profitability is not guaranteed; validate on-ground before committing capital.</i>",
        body_style
    ))
    suitable_locs = b.get('suitable_locations') or b.get('suggested_locations') or []
    for s in suitable_locs:
        s_data = [
            [Paragraph(f"<b>📍 {s.get('name')}</b>", table_cell_bold),
             Paragraph(f"<b>Customer Factors:</b> {s.get('customer_factors', '-')}", table_cell_style)],
            [Paragraph(f"<b>Suitability:</b> {s.get('why_suitable', '-')}", table_cell_style),
             Paragraph(f"<b>Explanation:</b> {s.get('simple_explanation', '-')}", table_cell_style)]
        ]
        t_s = Table(s_data, colWidths=[270, 270])
        t_s.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fafafa")),
            ('BOX', (0, 0), (-1, -1), 0.5, border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t_s)
        story.append(Spacer(1, 3))
    story.append(Spacer(1, 6))

    # 6. Budget & Investment Allocation
    story.append(Paragraph("6. BUDGET & INVESTMENT ALLOCATION", h1_style))
    cats = ba.get('categories') or {}
    tot_planned = ba.get('total_planned_investment') or sum(cats.values())

    budget_table_data = [
        [Paragraph("Relevant Startup Cost Category", table_header_style), Paragraph("Allocated Amount (INR)", table_header_style)]
    ]
    for c_name, c_amt in cats.items():
        budget_table_data.append([
            Paragraph(str(c_name), table_cell_style),
            Paragraph(format_rupee(c_amt), table_cell_style)
        ])
    budget_table_data.append([
        Paragraph("<b>Total Planned Investment (100% of Entered Budget)</b>", table_cell_bold),
        Paragraph(f"<b>{format_rupee(tot_planned)}</b>", table_cell_bold)
    ])

    t_bgt = Table(budget_table_data, colWidths=[370, 170])
    t_bgt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('BACKGROUND', (0, -1), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_bgt)
    story.append(Paragraph("<i>Note: These are estimated allocations, not guaranteed costs. Total allocation strictly equals the user-entered budget.</i>", subtitle_style))
    story.append(Spacer(1, 6))

    # 7. Market Opportunity
    story.append(Paragraph("7. MARKET & BUSINESS OPPORTUNITY", h1_style))
    story.append(Paragraph(str(b.get('market_opportunity', '-')), body_style))
    story.append(Spacer(1, 6))

    # 8 & 9. Go-To-Market & Operations Plan
    story.append(Paragraph("8. GO-TO-MARKET STRATEGY", h1_style))
    for g in b.get('go_to_market', []):
        story.append(Paragraph(f"• {g}", bullet_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("9. OPERATIONS PLAN", h1_style))
    for op in b.get('operations', []):
        story.append(Paragraph(f"• {op}", bullet_style))
    story.append(Spacer(1, 6))

    # 10. Implementation Roadmap
    story.append(Paragraph("10. IMPLEMENTATION ROADMAP", h1_style))
    for idx, s in enumerate(b.get('roadmap') or b.get('implementation_roadmap') or [], 1):
        story.append(Paragraph(f"{idx}. {s}", bullet_style))
    story.append(Spacer(1, 6))

    # 11 & 12. Growth Opportunities and Risks & Challenges
    story.append(Paragraph("11. GROWTH OPPORTUNITIES", h1_style))
    for opp in b.get('opportunities', []):
        story.append(Paragraph(f"• {opp}", bullet_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("12. RISKS & CHALLENGES", h1_style))
    for r in (b.get('risks') or b.get('risks_and_mitigation') or []):
        story.append(Paragraph(f"• {r}", bullet_style))
    story.append(Spacer(1, 6))

    # 13 & 14. Success Metrics & Immediate Next Steps
    story.append(Paragraph("13. SUCCESS METRICS (KPIS)", h1_style))
    for m in b.get('success_metrics', []):
        story.append(Paragraph(f"✓ {m}", bullet_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("14. IMMEDIATE NEXT STEPS", h1_style))
    for ns in b.get('next_steps', []):
        story.append(Paragraph(f"✓ {ns}", bullet_style))
    story.append(Spacer(1, 6))

    # 15. Final Summary
    story.append(Paragraph("15. FINAL SUMMARY", h1_style))
    story.append(Paragraph(str(b.get('final_summary', '-')), body_style))

    # Data Sources Note
    ds = b.get('data_sources') or {}
    if ds:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Data Sources:</b> User Inputs | {ds.get('dataset_information', '')} | {ds.get('verified_external_information', '')}", subtitle_style))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
