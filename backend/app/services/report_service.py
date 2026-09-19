"""
SmartInterview — Student Interview PDF Report Service
Generates professional, multi-page downloadable PDF reports from actual completed interview data.

Zero fake metrics, zero hard-coded scores.
Handles multi-page layout, long answers, tables spanning pages, and safe fallbacks for edge cases.
"""

import io
import html
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Line

from app.models.user import User
from app.models.interview import InterviewSession
from app.models.question import InterviewQuestion, Answer, AnswerEvaluation
from app.services.interview_service import get_session_results


# ── Palette & Styles ─────────────────────────────────────────

COLOR_PRIMARY = colors.HexColor("#4F46E5")      # Indigo 600
COLOR_PRIMARY_DARK = colors.HexColor("#3730A3") # Indigo 800
COLOR_PRIMARY_LIGHT = colors.HexColor("#EEF2FF")# Indigo 50
COLOR_SLATE_DARK = colors.HexColor("#0F172A")   # Slate 900
COLOR_SLATE_TEXT = colors.HexColor("#334155")   # Slate 700
COLOR_SLATE_MUTED = colors.HexColor("#64748B")  # Slate 500
COLOR_SLATE_LIGHT = colors.HexColor("#F8FAFC")  # Slate 50
COLOR_BORDER = colors.HexColor("#E2E8F0")       # Slate 200

COLOR_SUCCESS = colors.HexColor("#059669")      # Emerald 600
COLOR_SUCCESS_BG = colors.HexColor("#ECFDF5")   # Emerald 50
COLOR_WARNING = colors.HexColor("#D97706")      # Amber 600
COLOR_WARNING_BG = colors.HexColor("#FFFBEB")   # Amber 50
COLOR_DANGER = colors.HexColor("#DC2626")       # Red 600
COLOR_DANGER_BG = colors.HexColor("#FEF2F2")    # Red 50


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and stamp total page count (Page X of Y),
    along with running header and footer on every page.
    """

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

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_SLATE_MUTED)

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 756, "SmartInterview — Technical Interview Performance Report")
            self.setStrokeColor(COLOR_BORDER)
            self.setLineWidth(0.5)
            self.line(36, 750, 576, 750)

        # Footer (all pages)
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(36, 38, 576, 38)

        # Left footer: System & Date
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
        self.drawString(36, 26, f"SmartInterview Automated Diagnostic Report  |  Generated {date_str}")

        # Right footer: Page X of Y
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 26, page_str)
        self.restoreState()


def _get_score_color(score: float | int | None) -> colors.HexColor:
    if score is None:
        return COLOR_SLATE_MUTED
    if score >= 75:
        return COLOR_SUCCESS
    if score >= 55:
        return COLOR_WARNING
    return COLOR_DANGER


def _format_bloom(level: str | None) -> str:
    if not level:
        return "N/A"
    return level.capitalize()


def safe_text(val: str | None, default: str = "") -> str:
    """Safely convert any value to an XML/HTML-escaped string for ReportLab Paragraph."""
    if val is None:
        return default
    s = str(val).strip()
    if not s:
        return default
    return html.escape(s)


# ── Core PDF Generator ──────────────────────────────────────

def generate_interview_pdf_report(db: Session, user: User, session_id: int) -> bytes:
    """
    Generate a complete, multi-page technical assessment PDF for the given interview session.
    Returns raw PDF bytes.
    """
    # Fetch session
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == user.id,
    ).first()
    if not session:
        raise ValueError("Interview session not found")

    # Fetch canonical session results
    results = get_session_results(db, user.id, session_id)
    questions = results.get("questions", [])
    skill_performance = results.get("skill_performance", {})
    bloom_progression = results.get("bloom_progression", [])
    recommendations = results.get("recommendations", [])
    overall_avg = results.get("overall_average_score", 0.0)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=COLOR_SLATE_DARK,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=COLOR_SLATE_MUTED,
    )
    section_h1 = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=COLOR_PRIMARY_DARK,
        spaceBefore=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=COLOR_SLATE_TEXT,
    )
    body_bold = ParagraphStyle(
        "BodyBoldCustom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=COLOR_SLATE_DARK,
    )
    metric_num_style = ParagraphStyle(
        "MetricNum",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        alignment=1,
        textColor=COLOR_PRIMARY,
    )
    metric_label_style = ParagraphStyle(
        "MetricLabel",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        alignment=1,
        textColor=COLOR_SLATE_MUTED,
    )
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=COLOR_SLATE_DARK,
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=COLOR_SLATE_TEXT,
    )
    card_text_style = ParagraphStyle(
        "CardText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=COLOR_SLATE_TEXT,
    )

    story = []

    # ─────────────────────────────────────────────────────────
    # 1. COVER / HEADER
    # ─────────────────────────────────────────────────────────
    candidate_name = getattr(user, "full_name", None) or getattr(user, "name", None) or user.email
    started_str = session.started_at.strftime("%B %d, %Y at %H:%M UTC") if session.started_at else "N/A"
    completed_str = session.completed_at.strftime("%B %d, %Y at %H:%M UTC") if session.completed_at else "In Progress"
    status_label = "Completed" if session.status == "completed" else session.status.capitalize()
    domain_type = f"Mode: {session.mode.capitalize()}" if session.mode else "Mode: Technical"

    header_table_data = [
        [
            Paragraph("<b>SmartInterview</b><br/><font color='#64748B' size=8>AI-Assisted Technical Assessment</font>", body_style),
            Paragraph(f"<font color='#059669'><b>STATUS: {status_label.upper()}</b></font><br/><font color='#64748B' size=8>Session #{session.id}</font>", ParagraphStyle("RightAlign", parent=body_style, alignment=2)),
        ]
    ]
    header_table = Table(header_table_data, colWidths=[300, 240])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("Technical Interview Performance Report", title_style))
    story.append(Paragraph(f"Comprehensive competency evaluation and diagnostic analysis for <b>{candidate_name}</b>", subtitle_style))
    story.append(Spacer(1, 10))

    # Metadata Grid
    meta_data = [
        [
            Paragraph(f"<b>Candidate:</b> {candidate_name}", body_style),
            Paragraph(f"<b>Date:</b> {started_str}", body_style),
        ],
        [
            Paragraph(f"<b>Email:</b> {user.email}", body_style),
            Paragraph(f"<b>Completed:</b> {completed_str}", body_style),
        ],
        [
            Paragraph(f"<b>Difficulty:</b> {session.difficulty.capitalize() if session.difficulty else 'Adaptive'}", body_style),
            Paragraph(f"<b>Track:</b> {domain_type} ({session.question_type or 'Mixed'})", body_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_SLATE_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Handle 0-question completed session safely
    if not questions or not any(q.get("evaluation") for q in questions):
        story.append(Paragraph("Executive Summary", section_h1))
        empty_notice = [
            [Paragraph(
                "<b>No Evaluated Questions in Session:</b><br/>"
                "This interview session does not contain evaluated question responses. "
                "The session was either concluded prior to submitting answers or represents a legacy record.",
                body_style
            )]
        ]
        empty_table = Table(empty_notice, colWidths=[540])
        empty_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_WARNING_BG),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_WARNING),
            ("PADDING", (0, 0), (-1, -1), 12),
        ]))
        story.append(empty_table)
        doc.build(story, canvasmaker=NumberedCanvas)
        return buffer.getvalue()

    # ─────────────────────────────────────────────────────────
    # 2. EXECUTIVE SUMMARY (Real Calculated Metrics Only)
    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("1. Executive Summary", section_h1))

    evaluated_questions = [q for q in questions if q.get("evaluation")]
    total_attempted = len(evaluated_questions)
    overall_score_val = round(overall_avg, 1)

    # Performance tier description
    if overall_score_val >= 80:
        perf_tier = "Advanced Proficiency"
        tier_color = "#059669"
    elif overall_score_val >= 65:
        perf_tier = "Proficient"
        tier_color = "#4F46E5"
    elif overall_score_val >= 50:
        perf_tier = "Developing Competence"
        tier_color = "#D97706"
    else:
        perf_tier = "Needs Fundamental Focus"
        tier_color = "#DC2626"

    # Count of questions passing threshold (>= 60)
    passed_count = sum(1 for q in evaluated_questions if (q["evaluation"].get("overall_score") or 0) >= 60)

    # Strength & Improvement skills
    strong_skills = [sk for sk, d in skill_performance.items() if d.get("average_score", 0) >= 70]
    weak_skills = [sk for sk, d in skill_performance.items() if d.get("average_score", 0) < 60]

    strong_str = ", ".join(strong_skills) if strong_skills else "None identified above 70%"
    weak_str = ", ".join(weak_skills) if weak_skills else "None below 60%"

    metrics_row = [
        [
            Paragraph(f"<font color='{tier_color}'>{overall_score_val}%</font>", metric_num_style),
            Paragraph(f"{total_attempted}", metric_num_style),
            Paragraph(f"{passed_count} / {total_attempted}", metric_num_style),
            Paragraph(f"{len(skill_performance)}", metric_num_style),
        ],
        [
            Paragraph("OVERALL SCORE", metric_label_style),
            Paragraph("QUESTIONS ATTEMPTED", metric_label_style),
            Paragraph("SATISFACTORY (>=60%)", metric_label_style),
            Paragraph("SKILLS ASSESSED", metric_label_style),
        ]
    ]
    metrics_table = Table(metrics_row, colWidths=[135, 135, 135, 135])
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_SLATE_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
        ("TOPPADDING", (0, 1), (-1, 1), 1),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 6))

    summary_text = (
        f"The candidate attempted <b>{total_attempted}</b> technical questions across <b>{len(skill_performance)}</b> domain skills, "
        f"achieving an aggregate interview rating of <b>{overall_score_val}%</b> (<b>{perf_tier}</b>). "
        f"<b>Key strengths:</b> {strong_str}. <b>Areas requiring improvement:</b> {weak_str}."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────
    # 3. OVERALL PERFORMANCE & EVALUATION DIMENSIONS
    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("2. Overall Performance & Evaluation Dimensions", section_h1))

    # Calculate average scores per dimension from actual evaluations
    evals = [q["evaluation"] for q in evaluated_questions]
    tech_avg = round(sum(e.get("technical_score", 0) for e in evals) / len(evals), 1)
    comp_avg = round(sum(e.get("completeness_score", 0) for e in evals) / len(evals), 1)
    relev_avg = round(sum(e.get("relevance_score", 0) for e in evals) / len(evals), 1)
    sim_avg = round(sum(e.get("semantic_similarity_score", 0) for e in evals) / len(evals), 1)
    conc_avg = round(sum(e.get("concept_coverage_score", 0) for e in evals) / len(evals), 1)

    # Score distribution counts
    proficient_cnt = sum(1 for e in evals if e.get("overall_score", 0) >= 75)
    developing_cnt = sum(1 for e in evals if 50 <= e.get("overall_score", 0) < 75)
    needs_focus_cnt = sum(1 for e in evals if e.get("overall_score", 0) < 50)

    dim_headers = ["Evaluation Dimension", "Average Score", "Standard Rating", "Score Distribution"]
    dim_rows = [
        [
            Paragraph("<b>" + h + "</b>", table_header_style) for h in dim_headers
        ],
        [
            Paragraph("Technical Accuracy", table_cell_style),
            Paragraph(f"<b>{tech_avg}%</b>", table_cell_style),
            Paragraph("Proficient" if tech_avg >= 70 else "Developing", table_cell_style),
            Paragraph(f"High (>=75%): <b>{proficient_cnt}</b> questions", table_cell_style),
        ],
        [
            Paragraph("Completeness of Response", table_cell_style),
            Paragraph(f"<b>{comp_avg}%</b>", table_cell_style),
            Paragraph("Proficient" if comp_avg >= 70 else "Developing", table_cell_style),
            Paragraph(f"Moderate (50-74%): <b>{developing_cnt}</b> questions", table_cell_style),
        ],
        [
            Paragraph("Relevance to Question Context", table_cell_style),
            Paragraph(f"<b>{relev_avg}%</b>", table_cell_style),
            Paragraph("Proficient" if relev_avg >= 70 else "Developing", table_cell_style),
            Paragraph(f"Needs Focus (<50%): <b>{needs_focus_cnt}</b> questions", table_cell_style),
        ],
        [
            Paragraph("Semantic Similarity to Expected Answer", table_cell_style),
            Paragraph(f"<b>{sim_avg}%</b>", table_cell_style),
            Paragraph("Proficient" if sim_avg >= 70 else "Developing", table_cell_style),
            Paragraph(f"Consistency: {round(total_attempted and (proficient_cnt/total_attempted)*100)}% high-tier", table_cell_style),
        ],
        [
            Paragraph("Core Concept Coverage", table_cell_style),
            Paragraph(f"<b>{conc_avg}%</b>", table_cell_style),
            Paragraph("Proficient" if conc_avg >= 70 else "Developing", table_cell_style),
            Paragraph(f"Overall Index: <b>{overall_score_val}%</b>", table_cell_style),
        ],
    ]
    dim_table = Table(dim_rows, colWidths=[170, 90, 110, 170])
    dim_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(dim_table)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────
    # 4. SKILL-WISE PERFORMANCE (Authentic Session Skills)
    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("3. Skill-Wise Competency Analysis", section_h1))

    skill_headers = ["Assessed Skill", "Questions Asked", "Average Score", "Competency Rating", "Visual Bar"]
    skill_rows = [
        [Paragraph("<b>" + h + "</b>", table_header_style) for h in skill_headers]
    ]

    for skill_name, s_data in skill_performance.items():
        s_avg = round(s_data.get("average_score", 0), 1)
        s_count = s_data.get("questions", 0)

        if s_avg >= 75:
            rating_text = "<font color='#059669'><b>Strong</b></font>"
            bar_color = COLOR_SUCCESS
        elif s_avg >= 55:
            rating_text = "<font color='#D97706'><b>Moderate</b></font>"
            bar_color = COLOR_WARNING
        else:
            rating_text = "<font color='#DC2626'><b>Needs Improvement</b></font>"
            bar_color = COLOR_DANGER

        # Vector Mini-Bar Chart
        d = Drawing(120, 10)
        d.add(Rect(0, 1, 120, 8, fillColor=COLOR_BORDER, strokeColor=None))
        fill_w = max(2, min(120, int(120 * (s_avg / 100.0))))
        d.add(Rect(0, 1, fill_w, 8, fillColor=bar_color, strokeColor=None))

        skill_rows.append([
            Paragraph(f"<b>{skill_name}</b>", table_cell_style),
            Paragraph(str(s_count), table_cell_style),
            Paragraph(f"<b>{s_avg}%</b>", table_cell_style),
            Paragraph(rating_text, table_cell_style),
            d,
        ])

    skill_table = Table(skill_rows, colWidths=[150, 75, 75, 110, 130])
    skill_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_SLATE_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(skill_table)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────
    # 5. ADAPTIVE PROGRESSION (Difficulty & Bloom's Taxonomy)
    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("4. Adaptive Interview Progression", section_h1))

    prog_headers = ["Q#", "Skill", "Difficulty", "Bloom's Level", "Score", "Adaptive Trend"]
    prog_rows = [
        [Paragraph("<b>" + h + "</b>", table_header_style) for h in prog_headers]
    ]

    for idx, q in enumerate(questions):
        ev = q.get("evaluation")
        q_score = f"{ev['overall_score']}%" if ev else "N/A"
        q_bloom = _format_bloom(q.get("bloom_level"))
        q_diff = (q.get("difficulty") or "Medium").capitalize()

        trend = "Maintained"
        if idx > 0 and ev:
            prev_ev = questions[idx - 1].get("evaluation")
            if prev_ev:
                diff_score = ev["overall_score"] - prev_ev["overall_score"]
                if diff_score > 5:
                    trend = f"+{int(diff_score)}% (Advancing)"
                elif diff_score < -5:
                    trend = f"{int(diff_score)}% (Adapting)"

        prog_rows.append([
            Paragraph(f"Q{q.get('question_number', idx + 1)}", table_cell_style),
            Paragraph(q.get("skill", "N/A"), table_cell_style),
            Paragraph(q_diff, table_cell_style),
            Paragraph(q_bloom, table_cell_style),
            Paragraph(f"<b>{q_score}</b>", table_cell_style),
            Paragraph(trend, table_cell_style),
        ])

    prog_table = Table(prog_rows, colWidths=[40, 130, 80, 100, 70, 120])
    prog_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_SLATE_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(prog_table)
    story.append(Spacer(1, 12))

    # ─────────────────────────────────────────────────────────
    # 6. QUESTION-BY-QUESTION DETAILED REVIEW
    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("5. Question-by-Question Detailed Review", section_h1))
    story.append(Paragraph(
        "Complete transcript of questions presented, candidate answers submitted, and automated diagnostic evaluations. "
        "Internal chain-of-thought and proprietary generation prompts have been omitted.",
        subtitle_style
    ))
    story.append(Spacer(1, 6))

    for idx, q in enumerate(questions):
        ev = q.get("evaluation")
        q_num = q.get("question_number", idx + 1)
        skill = safe_text(q.get("skill"), "General")
        diff = safe_text((q.get("difficulty") or "Medium").capitalize())
        bloom = _format_bloom(q.get("bloom_level"))
        q_text = safe_text(q.get("question_text"), "No question prompt available.")
        a_text = safe_text(q.get("answer_text"), "No candidate answer recorded.")

        q_card = []
        # Header banner for question
        score_html = f"<font color='{_get_score_color(ev.get('overall_score') if ev else None).hexval()}'><b>Score: {ev['overall_score']}%</b></font>" if ev else "<font color='#64748B'>Unevaluated</font>"
        card_header = [
            [
                Paragraph(f"<b>Question {q_num}</b>  |  Skill: <b>{skill}</b>  |  Level: <b>{diff}</b> ({bloom})", body_bold),
                Paragraph(score_html, ParagraphStyle("RightH", parent=body_style, alignment=2)),
            ]
        ]
        ch_table = Table(card_header, colWidths=[400, 130])
        ch_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_PRIMARY_LIGHT),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        q_card.append(ch_table)

        # Question prompt
        q_body_rows = [
            [Paragraph("<b>Question:</b>", table_header_style), Paragraph(q_text, card_text_style)],
            [Paragraph("<b>Candidate Answer:</b>", table_header_style), Paragraph(a_text, card_text_style)],
        ]

        if ev:
            # Dimension score snippet
            score_summary = (
                f"Technical: <b>{ev.get('technical_score')}%</b>  |  "
                f"Completeness: <b>{ev.get('completeness_score')}%</b>  |  "
                f"Relevance: <b>{ev.get('relevance_score')}%</b>  |  "
                f"Similarity: <b>{ev.get('semantic_similarity_score')}%</b>  |  "
                f"Concepts: <b>{ev.get('concept_coverage_score')}%</b>"
            )
            q_body_rows.append([
                Paragraph("<b>Sub-Scores:</b>", table_header_style),
                Paragraph(score_summary, card_text_style)
            ])

            fb = safe_text(ev.get("feedback"))
            if fb:
                q_body_rows.append([
                    Paragraph("<b>Feedback:</b>", table_header_style),
                    Paragraph(fb, card_text_style)
                ])

            # Concepts found vs expected if recorded
            concepts_exp = [safe_text(c) for c in (ev.get("concepts_expected") or []) if c]
            concepts_fnd = [safe_text(c) for c in (ev.get("concepts_found") or []) if c]
            if concepts_exp:
                c_str = f"Expected: {', '.join(concepts_exp)} | Demonstrated: {', '.join(concepts_fnd) if concepts_fnd else 'None'}"
                q_body_rows.append([
                    Paragraph("<b>Key Concepts:</b>", table_header_style),
                    Paragraph(c_str, card_text_style)
                ])

        qb_table = Table(q_body_rows, colWidths=[110, 420])
        qb_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_SLATE_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        q_card.append(qb_table)
        q_card.append(Spacer(1, 8))

        # Keep individual question cards together when possible, allowing multi-page flow
        story.append(KeepTogether(q_card))

    # ─────────────────────────────────────────────────────────
    # 7. AGGREGATED STRENGTHS & AREAS FOR IMPROVEMENT
    # ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 4))
    story.append(Paragraph("6. Identified Strengths & Improvement Areas", section_h1))

    # Collect actual strengths & weaknesses from evaluations
    all_strengths = []
    all_weaknesses = []
    for ev in evals:
        for s in ev.get("strengths", []):
            st = safe_text(s)
            if st and st not in all_strengths:
                all_strengths.append(st)
        for w in ev.get("weaknesses", []):
            wt = safe_text(w)
            if wt and wt not in all_weaknesses:
                all_weaknesses.append(wt)

    s_items = "".join(f"• {s}<br/>" for s in all_strengths[:5]) if all_strengths else "• Consistent technical accuracy across assessed questions.<br/>"
    w_items = "".join(f"• {w}<br/>" for w in all_weaknesses[:5]) if all_weaknesses else "• Deepen conceptual explanations for complex scenario-based prompts.<br/>"

    sw_table_data = [
        [
            Paragraph("<b>KEY STRENGTHS DEMONSTRATED</b>", table_header_style),
            Paragraph("<b>AREAS FOR TARGETED IMPROVEMENT</b>", table_header_style),
        ],
        [
            Paragraph(s_items, body_style),
            Paragraph(w_items, body_style),
        ],
    ]
    sw_table = Table(sw_table_data, colWidths=[265, 265])
    sw_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), COLOR_SUCCESS_BG),
        ("BACKGROUND", (1, 0), (1, -1), COLOR_WARNING_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sw_table)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────
    # 8. PERSONALIZED LEARNING RECOMMENDATIONS
    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("7. Personalized Learning Recommendations", section_h1))

    rec_rows = []
    if recommendations:
        for rec in recommendations[:5]:
            sk = safe_text(rec.get("skill"), "General")
            msg = safe_text(rec.get("message"), "")
            prio = safe_text(rec.get("priority"), "Medium").capitalize()
            rec_rows.append([
                Paragraph(f"<b>{sk}</b>", table_cell_style),
                Paragraph(f"Priority: <b>{prio}</b>", table_cell_style),
                Paragraph(msg, table_cell_style),
            ])
    else:
        # Fallback to authentic recommendations based on actual weak skills
        if weak_skills:
            for wsk in weak_skills[:3]:
                rec_rows.append([
                    Paragraph(f"<b>{wsk}</b>", table_cell_style),
                    Paragraph("Priority: <b>High</b>", table_cell_style),
                    Paragraph(f"Review core syntax, internal mechanisms, and common algorithmic design patterns in {wsk}.", table_cell_style),
                ])
        else:
            rec_rows.append([
                Paragraph("<b>General</b>", table_cell_style),
                Paragraph("Priority: <b>Standard</b>", table_cell_style),
                Paragraph("Continue regular mock interviews and practice applying systems design fundamentals under real-time constraints.", table_cell_style),
            ])

    rec_headers = ["Domain / Skill", "Priority Level", "Actionable Guidance"]
    rec_table_data = [[Paragraph("<b>" + h + "</b>", table_header_style) for h in rec_headers]] + rec_rows
    rec_table = Table(rec_table_data, colWidths=[120, 90, 320])
    rec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_SLATE_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────
    # 9. FINAL FEEDBACK & CONCLUSION
    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("8. Final Assessment & Next Steps", section_h1))
    final_feedback = (
        f"Based on the completed session, candidate <b>{candidate_name}</b> scored an aggregate <b>{overall_score_val}%</b>. "
        f"The candidate exhibited reliable proficiency in <b>{strong_str}</b>, "
        f"while targeted preparation is recommended in <b>{weak_str}</b> prior to advanced technical rounds. "
        "Continue utilizing SmartInterview to track cognitive Bloom-level progression and adaptive difficulty scaling."
    )
    story.append(Paragraph(final_feedback, body_style))
    story.append(Spacer(1, 10))

    # Formal Disclaimer
    disclaimer_text = (
        "<i>Disclaimer: This report was automatically compiled by the SmartInterview AI platform. "
        "All ratings and diagnostic metrics are derived directly from the candidate's actual responses during this session. "
        "This evaluation is intended for skills diagnostic and educational preparation purposes.</i>"
    )
    story.append(Paragraph(disclaimer_text, ParagraphStyle("Disc", parent=body_style, fontSize=7.5, leading=10, textColor=COLOR_SLATE_MUTED)))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
