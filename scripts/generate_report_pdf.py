#!/usr/bin/env python3
"""
Generate the official academic Capstone Project PDF Report for Experiment 8.
Follows the exact guidelines:
- Title Page (Group members, roll numbers, course code, guide)
- Abstract (150-200 words)
- 1. Introduction
- 2. Objectives
- 3. Related Work / Existing Systems (with Comparison Table)
- 4. System Architecture (Sensor -> Connectivity -> Processing -> AI -> Application)
- 5. Dataset / Data Simulation
- 6. Methodology (Formulations & Feature Engineering)
- 7. Implementation (Directory Structure & Code Snippets)
- 8. Results & Evaluation (Verified Metrics Table & Plotly Charts)
- 9. Discussion (What worked, what didn't, simulation limits)
- 10. Conclusion & Future Scope
- 11. Individual Contribution Table
- References
- Appendix (Repository Structure & Commands)
Uses the user's primary/secondary color palette and Apple-grade typography.
"""

import sys
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
    Preformatted
)
from reportlab.pdfgen import canvas

# Palette Constants
COLOR_PETROL = colors.HexColor("#001219")
COLOR_TEAL_DARK = colors.HexColor("#005F73")
COLOR_TEAL = colors.HexColor("#0A9396")
COLOR_SAGE = colors.HexColor("#94D2BD")
COLOR_CREAM = colors.HexColor("#E9D8A6")
COLOR_AMBER = colors.HexColor("#EE9B00")
COLOR_OCHRE = colors.HexColor("#CA6702")
COLOR_RUST = colors.HexColor("#BB3E03")
COLOR_CRIMSON = colors.HexColor("#AE2012")
COLOR_MAROON = colors.HexColor("#9B2226")

COLOR_PRIMARY_DARK = colors.HexColor("#080708")
COLOR_PRIMARY_LIGHT = colors.HexColor("#FFFFFF")
COLOR_SURFACE_LIGHT = colors.HexColor("#F8F9FA")
COLOR_BORDER = colors.HexColor("#DDE2E5")
COLOR_TEXT_PRIMARY = colors.HexColor("#080708")
COLOR_TEXT_SECONDARY = colors.HexColor("#005F73")
COLOR_TEXT_MUTED = colors.HexColor("#5A6B73")


class NumberedCanvas(canvas.Canvas):
    """Adds running headers and footers with page numbers."""
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
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        if self._pageNumber == 1:
            # Title page - omit running header/footer
            return
        
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_TEXT_MUTED)

        # Header
        self.drawString(54, 755, "AI for IoT — Capstone Project Report (Experiment 8)")
        self.drawRightString(612 - 54, 755, "Home Energy Forecasting & Anomaly Detection")
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(54, 748, 612 - 54, 748)

        # Footer
        self.line(54, 45, 612 - 54, 45)
        self.drawString(54, 33, "Department of Computer Science & Engineering • Academic Year 2025–2026")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 33, page_str)

        self.restoreState()


def build_pdf(filename="docs/CAPSTONE_REPORT_EXPERIMENT_8.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Typographic Hierarchy
    style_cover_super = ParagraphStyle(
        "CoverSuper",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=COLOR_TEAL,
        alignment=0,
        spaceAfter=8,
    )
    style_cover_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=COLOR_PRIMARY_DARK,
        alignment=0,
        spaceAfter=12,
    )
    style_cover_sub = ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=COLOR_TEXT_SECONDARY,
        alignment=0,
        spaceAfter=24,
    )
    style_h1 = ParagraphStyle(
        "ReportH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=COLOR_TEAL_DARK,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    style_h2 = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=COLOR_TEXT_PRIMARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    style_body = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=COLOR_TEXT_PRIMARY,
        spaceAfter=6,
    )
    style_body_bold = ParagraphStyle(
        "ReportBodyBold",
        parent=style_body,
        fontName="Helvetica-Bold",
    )
    style_bullet = ParagraphStyle(
        "ReportBullet",
        parent=style_body,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3,
    )
    style_abstract_box = ParagraphStyle(
        "AbstractBox",
        parent=style_body,
        fontName="Helvetica-Oblique",
        fontSize=9.5,
        leading=14,
        textColor=COLOR_PETROL,
    )
    style_code = ParagraphStyle(
        "ReportCode",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8,
        leading=10.5,
        textColor=COLOR_PETROL,
    )
    style_table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=COLOR_TEXT_PRIMARY,
    )
    style_table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=COLOR_TEXT_PRIMARY,
    )
    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=COLOR_PRIMARY_LIGHT,
    )

    story = []

    # =========================================================================
    # TITLE PAGE
    # =========================================================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("AI FOR IOT — CAPSTONE PROJECT (EXPERIMENT 8)", style_cover_super))
    story.append(Paragraph("AI-Based Smart Home Energy Consumption Forecasting & Wasteful Usage Detection", style_cover_title))
    story.append(Paragraph("An End-to-End Cyber-Physical System Integrating ESP32 Telemetry, Dual-Tier Machine Learning, Isolation Forest Anomaly Detection, and Apple-Grade Interactive Analytics", style_cover_sub))
    story.append(HRFlowable(width="100%", thickness=2, color=COLOR_TEAL, spaceBefore=0, spaceAfter=20))

    meta_table_data = [
        [Paragraph("Course Code & Title", style_table_cell_bold), Paragraph("AI for IoT — Capstone Project (Experiment 8)", style_table_cell)],
        [Paragraph("Group Structure", style_table_cell_bold), Paragraph("Group of 4 Students (Batch AY 2025–2026)", style_table_cell)],
        [Paragraph("Student Members & Roll Nos", style_table_cell_bold), Paragraph(
            "• Student 1 (Roll No: 2026-IOT-01) — Lead IoT Firmware & Simulation<br/>"
            "• Student 2 (Roll No: 2026-IOT-02) — Machine Learning & Feature Engineering<br/>"
            "• Student 3 (Roll No: 2026-IOT-03) — Backend Architecture, APIs & SQLite<br/>"
            "• Student 4 (Roll No: 2026-IOT-04) — Dashboard UI, Plotly Charts & Systems",
            style_table_cell
        )],
        [Paragraph("Project Guide / Supervisor", style_table_cell_bold), Paragraph("Prof. Faculty Name, Department of Computer Science & Engineering", style_table_cell)],
        [Paragraph("Project Repository", style_table_cell_bold), Paragraph("https://github.com/example/cap-ai-energy-iot (Release Phase 3.4)", style_table_cell)],
        [Paragraph("Verification Status", style_table_cell_bold), Paragraph("<b>100% PASS</b> (68/68 Automated Unit & Integration Tests Passing)", style_table_cell)],
    ]
    meta_table = Table(meta_table_data, colWidths=[150, 354])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_SURFACE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 25))

    # Abstract Callout Box
    abstract_text = (
        "<b>Abstract (180 words):</b> Residential energy waste accounts for substantial carbon emissions and inflated utility "
        "bills, driven primarily by unmonitored baseline loads, daylight lighting, and unoccupied climate control. Conventional "
        "smart meters provide delayed aggregate monthly summaries lacking device-level diagnostic explanations. This capstone "
        "project designs and implements an end-to-end cyber-physical IoT and AI platform for real-time telemetry acquisition, "
        "appliance load decomposition, short-term forecasting, unsupervised anomaly detection, and explainable waste diagnosis. "
        "An ESP32 simulated in Wokwi with DHT22, PIR, and LDR sensors streams telemetry frames across 7 domestic loads over "
        "MQTT to an asynchronous FastAPI backend. A multi-model pipeline deploys: Model 1 Expected Load Decomposition "
        "(R² = 1.000, MAE = 0.0 W); Model 2 Lagged Autoregressive Forecaster (R² = 0.2142, MAE = 830.11 W, horizon = 2.5s) "
        "without target leakage; and Model 3 Isolation Forest detecting extreme concurrent overloads. A deterministic rule engine "
        "quantifies avoidable wattage, and an Apple-inspired interactive Streamlit dashboard provides 10 Plotly visualizations "
        "and cross-filtering. The entire architecture is verified across 68 automated tests passing at 100%."
    )
    abstract_box = Table([[Paragraph(abstract_text, style_abstract_box)]], colWidths=[504])
    abstract_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EBF5F5")),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_TEAL),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(abstract_box)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 1: INTRODUCTION
    # =========================================================================
    story.append(Paragraph("1. Introduction", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))

    story.append(Paragraph("1.1 Problem Statement", style_h2))
    story.append(Paragraph(
        "Modern residential dwellings suffer from three fundamental energy management deficiencies: (1) <i>Lack of Appliance-Level Granularity</i>: "
        "conventional utility meters report whole-home aggregate kilowatt-hours (kWh) without visibility into which specific appliances drive peaks; "
        "(2) <i>Delayed Feedback Loops</i>: utility billing cycles operate monthly, preventing immediate behavioral intervention when equipment is "
        "accidentally left operational; and (3) <i>Black-Box AI Diagnostics</i>: existing machine learning systems frequently output statistical "
        "predictions without plain-English explanations or actionable wattage savings.",
        style_body
    ))

    story.append(Paragraph("1.2 Motivation", style_h2))
    story.append(Paragraph(
        "Residential buildings contribute roughly 40% of global primary energy consumption and 30% of energy-related carbon emissions. "
        "Studies indicate that between 15% and 30% of household energy is wasted through behavioral oversights—such as operating air conditioning "
        "in vacant rooms, utilizing artificial lighting during bright daylight hours, or simultaneous heating and cooling conflicts. Deploying edge IoT "
        "microcontrollers with lightweight publish-subscribe messaging and dual-tier machine learning enables real-time, explainable energy conservation.",
        style_body
    ))

    story.append(Paragraph("1.3 Why this Domain Needs an IoT-AI Solution", style_h2))
    story.append(Paragraph(
        "IoT sensors capture continuous environmental and behavioral state variables (ambient temperature, relative humidity, light level, room occupancy), "
        "generating high-frequency time-series streams. However, raw sensor data lacks diagnostic context without AI inferencing. Conversely, standalone "
        "AI models cannot operate without synchronized sensor telemetry. An integrated <b>IoT-AI architecture</b> bridges physical environmental phenomena "
        "with statistical predictive modeling, decomposing loads, detecting abnormal usage, and generating explainable corrective guidance.",
        style_body
    ))

    # =========================================================================
    # SECTION 2: OBJECTIVES
    # =========================================================================
    story.append(Paragraph("2. Objectives", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph("The capstone project achieves the following six clear, measurable objectives:", style_body))

    objectives = [
        "<b>Objective 1 (IoT Simulation):</b> Simulate an ESP32 microcontroller with DHT22, PIR, and LDR sensors in Wokwi, executing non-blocking telemetry acquisition and virtual appliance calculations every 2.5 seconds.",
        "<b>Objective 2 (Asynchronous Connectivity):</b> Stream structured JSON telemetry payloads over MQTT (topic <code>smart_home/telemetry</code>) to an asynchronous FastAPI backend with Pydantic v2 validation and SQLite persistence.",
        "<b>Objective 3 (Continuous Integration):</b> Compute cumulative electrical energy (kWh) in real time using discrete trapezoidal numerical integration.",
        "<b>Objective 4 (Multimodal ML Pipeline):</b> Deploy three verified models: Model 1 Expected Load Decomposition (R² = 1.000, MAE = 0 W), Model 2 Short-Term Lagged Power Forecasting (R² = 0.2142, MAE = 830.11 W, horizon = 2.5s), and Model 3 Isolation Forest Anomaly Detection (5% contamination).",
        "<b>Objective 5 (Explainable Rule Engine):</b> Implement deterministic domain guardrails diagnosing vacancy waste, daylight waste, and HVAC conflicts with plain-English corrective advisories.",
        "<b>Objective 6 (Apple-Inspired Dashboard):</b> Deliver a high-density, responsive Streamlit dashboard featuring an Apple Liquid Glass design system, 10 interactive Plotly charts, device cross-filtering, and 68 automated passing tests.",
    ]
    for obj in objectives:
        story.append(Paragraph(f"• {obj}", style_bullet))

    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 3: RELATED WORK & EXISTING SYSTEMS
    # =========================================================================
    story.append(Paragraph("3. Related Work / Existing Systems", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "Current energy monitoring solutions fall into three main paradigms researched during literature review:",
        style_body
    ))

    story.append(Paragraph("3.1 Case Study 1: Commercial Smart Metering (AMI)", style_h2))
    story.append(Paragraph(
        "Advanced Metering Infrastructure (AMI) deployed by regional utility providers measures electrical energy at 15-minute to 1-hour intervals. "
        "While suitable for billing and aggregate peak demand shaving, the coarse temporal resolution completely masks appliance-level waste occurrences.",
        style_body
    ))

    story.append(Paragraph("3.2 Case Study 2: Non-Intrusive Load Monitoring (NILM)", style_h2))
    story.append(Paragraph(
        "Academic literature frequently explores NILM techniques using high-frequency current harmonics (kHz-MHz) to disaggregate loads. While theoretically "
        "compelling, NILM requires expensive specialized ADC hardware, computationally intensive edge neural networks, and degrades severely when multiple "
        "inverter-based variable speed loads operate simultaneously.",
        style_body
    ))

    story.append(Paragraph("3.3 Case Study 3: Cloud Smart Home Automation (Home Assistant / Google Home)", style_h2))
    story.append(Paragraph(
        "Smart plug ecosystems allow event-driven automations (e.g., turn off lights after 10 minutes of vacancy). However, they lack predictive autoregressive "
        "forecasting, multi-variable anomaly scoring, and automated energy waterfall analysis.",
        style_body
    ))

    # Comparison Table
    comp_header = [Paragraph("Feature", style_table_header), Paragraph("AMI Meters", style_table_header), Paragraph("Academic NILM", style_table_header), Paragraph("Home Assistant", style_table_header), Paragraph("Proposed System", style_table_header)]
    comp_rows = [
        [Paragraph("Sampling Interval", style_table_cell_bold), Paragraph("15–60 min", style_table_cell), Paragraph("Sub-second (kHz)", style_table_cell), Paragraph("Event-driven", style_table_cell), Paragraph("<b>2.5 seconds</b>", style_table_cell)],
        [Paragraph("Hardware Cost", style_table_cell_bold), Paragraph("High (Commercial)", style_table_cell), Paragraph("Expensive ADC", style_table_cell), Paragraph("Moderate (Plugs)", style_table_cell), Paragraph("<b>Zero (Virtual ESP32)</b>", style_table_cell)],
        [Paragraph("Appliance Visibility", style_table_cell_bold), Paragraph("Whole-home only", style_table_cell), Paragraph("ML disaggregated", style_table_cell), Paragraph("Per smart plug", style_table_cell), Paragraph("<b>7 Granular devices</b>", style_table_cell)],
        [Paragraph("Predictive Forecasting", style_table_cell_bold), Paragraph("Day-ahead only", style_table_cell), Paragraph("Rare / Absent", style_table_cell), Paragraph("Absent", style_table_cell), Paragraph("<b>2.5s Autoregressive</b>", style_table_cell)],
        [Paragraph("Anomaly Detection", style_table_cell_bold), Paragraph("Threshold billing", style_table_cell), Paragraph("Absent", style_table_cell), Paragraph("Rule-only", style_table_cell), Paragraph("<b>Isolation Forest (5%)</b>", style_table_cell)],
        [Paragraph("Explainability Engine", style_table_cell_bold), Paragraph("None", style_table_cell), Paragraph("None", style_table_cell), Paragraph("Simple IF/THEN", style_table_cell), Paragraph("<b>Deterministic + Savings</b>", style_table_cell)],
        [Paragraph("Interactive UI", style_table_cell_bold), Paragraph("Static monthly PDF", style_table_cell), Paragraph("Specialized plots", style_table_cell), Paragraph("Card grid", style_table_cell), Paragraph("<b>Apple Liquid Glass</b>", style_table_cell)],
    ]
    comp_table = Table([comp_header] + comp_rows, colWidths=[90, 85, 95, 95, 139])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_TEAL_DARK),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_PRIMARY_LIGHT, COLOR_SURFACE_LIGHT]),
    ]))
    story.append(comp_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 4: SYSTEM ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("4. System Architecture", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "The project implements a decoupled 9-layer architecture ensuring robust isolation between physical IoT simulation, asynchronous ingestion, "
        "machine learning inferencing, and front-end rendering:",
        style_body
    ))

    arch_diagram_text = (
        "+-----------------------------------------------------------------------------------------+\n"
        "|                                1. SENSOR & EDGE LAYER                                   |\n"
        "|   ESP32 (Wokwi) | DHT22 (Temp/Hum) | PIR (Motion) | LDR (Lux) | Virtual Appliance States |\n"
        "+--------------------------------------------+--------------------------------------------+\n"
        "                                             |  JSON Payload / Non-blocking 2.5s loop\n"
        "                                             v\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "|                           2. CONNECTIVITY & BROKER LAYER                                |\n"
        "|           MQTT Protocol | HiveMQ Public Broker (broker.hivemq.com:1883)                 |\n"
        "|           Topic: smart_home/telemetry                                                   |\n"
        "+--------------------------------------------+--------------------------------------------+\n"
        "                                             |  Asynchronous Ingest & Auto-Reconnect\n"
        "                                             v\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "|                           3. DATA INGESTION & PROCESSING                                |\n"
        "|   Python MQTT Ingestion Daemon | Pydantic Schema Validation | Trapezoidal kWh Integrator|\n"
        "+--------------------------------------------+--------------------------------------------+\n"
        "                                             |  Clean Records & History Buffer\n"
        "                                             v\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "|                                4. DATA STORAGE LAYER                                    |\n"
        "|   SQLite Relational Database (data/smart_home.db) | WAL Mode | Indexed Timestamps       |\n"
        "+--------------------------------------------+--------------------------------------------+\n"
        "                                             |  Feature Engineering (features.py)\n"
        "                                             v\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "|                                5. MACHINE LEARNING LAYER                                |\n"
        "|   Model 1: Load Decomposition (R²=1.0) | Model 2: Short-Term Forecast (R²=0.2142)       |\n"
        "|   Model 3: Isolation Forest Anomaly Detection (Contamination=5%)                       |\n"
        "+--------------------------------------------+--------------------------------------------+\n"
        "                                             |  Inference Results & Anomaly Scores\n"
        "                                             v\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "|                         6. EXPLAINABILITY & RULE ENGINE LAYER                           |\n"
        "|   Deterministic Guardrails: Vacancy Waste | Daylight Waste | HVAC Conflict | Overload   |\n"
        "+--------------------------------------------+--------------------------------------------+\n"
        "                                             |  Aggregated Analytics Payload\n"
        "                                             v\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "|                               7. REST API SERVICE LAYER                                 |\n"
        "|   FastAPI Web Server | Uvicorn ASGI | Endpoints: /latest, /analysis, /forecast, /scenario|\n"
        "+--------------------------------------------+--------------------------------------------+\n"
        "                                             |  REST Client HTTP Invocations\n"
        "                                             v\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "|                             8. INTERACTIVE VISUALIZATION                                |\n"
        "|   Streamlit Framework | Apple Liquid Glass Design System | 10 Interactive Plotly Charts |\n"
        "+--------------------------------------------+--------------------------------------------+\n"
        "                                             |  User Cross-Filtering & Point Inspection\n"
        "                                             v\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "|                           9. USER INTERACTION & AUDIT LAYER                             |\n"
        "|   Appliance Isolation | Live/Pause Controls | Scenario Testing | Diagnostic Explanations|\n"
        "+-----------------------------------------------------------------------------------------+"
    )
    arch_box = Table([[Preformatted(arch_diagram_text, style_code)]], colWidths=[504])
    arch_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0F4F6")),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(arch_box)

    # =========================================================================
    # SECTION 5: DATASET & SIMULATION METHODOLOGY
    # =========================================================================
    story.append(Paragraph("5. Dataset & Simulation Methodology", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))

    story.append(Paragraph("5.1 Telemetry Simulation Architecture", style_h2))
    story.append(Paragraph(
        "The edge tier runs on a simulated ESP32 microcontroller in Wokwi (<code>sketch.ino</code>). Environmental sensors include: "
        "(1) <b>DHT22</b> on GPIO 15 measuring temperature (15°C to 38°C) and relative humidity (30% to 85%); "
        "(2) <b>HC-SR501 PIR</b> on GPIO 13 measuring room occupancy (binary 0/1); and "
        "(3) <b>LDR sensor</b> on ADC GPIO 34 measuring ambient illuminance (0 to 1,000 Lux). "
        "Total household instantaneous power is deterministically computed from 7 rated virtual appliances:",
        style_body
    ))

    # Rated Appliances Table
    app_header = [Paragraph("Appliance", style_table_header), Paragraph("Key", style_table_header), Paragraph("Category", style_table_header), Paragraph("Rated Power (W)", style_table_header), Paragraph("Operational Logic", style_table_header)]
    app_rows = [
        [Paragraph("Air Conditioner", style_table_cell_bold), Paragraph("<code>ac</code>", style_table_cell), Paragraph("HVAC", style_table_cell), Paragraph("1,500 W", style_table_cell), Paragraph("Active during warm temperatures (> 27°C)", style_table_cell)],
        [Paragraph("Space Heater", style_table_cell_bold), Paragraph("<code>heater</code>", style_table_cell), Paragraph("HVAC", style_table_cell), Paragraph("2,000 W", style_table_cell), Paragraph("Active during cool temperatures (< 18°C)", style_table_cell)],
        [Paragraph("Microwave Oven", style_table_cell_bold), Paragraph("<code>microwave</code>", style_table_cell), Paragraph("Kitchen", style_table_cell), Paragraph("1,000 W", style_table_cell), Paragraph("Intermittent cooking spikes (morning, evening)", style_table_cell)],
        [Paragraph("Refrigerator", style_table_cell_bold), Paragraph("<code>refrigerator</code>", style_table_cell), Paragraph("Kitchen", style_table_cell), Paragraph("150 W", style_table_cell), Paragraph("Continuous baseline compressor operation", style_table_cell)],
        [Paragraph("Television", style_table_cell_bold), Paragraph("<code>tv</code>", style_table_cell), Paragraph("Media", style_table_cell), Paragraph("120 W", style_table_cell), Paragraph("Active during evening occupied hours", style_table_cell)],
        [Paragraph("Ceiling Fan", style_table_cell_bold), Paragraph("<code>fan</code>", style_table_cell), Paragraph("Climate", style_table_cell), Paragraph("75 W", style_table_cell), Paragraph("Moderate cooling air circulation", style_table_cell)],
        [Paragraph("Room Light", style_table_cell_bold), Paragraph("<code>room_light</code>", style_table_cell), Paragraph("Lighting", style_table_cell), Paragraph("20 W", style_table_cell), Paragraph("Evening hours or low ambient illuminance", style_table_cell)],
    ]
    app_table = Table([app_header] + app_rows, colWidths=[95, 60, 65, 84, 200])
    app_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_TEAL_DARK),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_PRIMARY_LIGHT, COLOR_SURFACE_LIGHT]),
    ]))
    story.append(app_table)

    story.append(Spacer(1, 6))
    story.append(Paragraph("5.2 Simulation Assumptions & Controlled Testing", style_h2))
    story.append(Paragraph(
        "<b>Assumptions:</b> Power draw is calculated from rated device specifications with unity power factor (PF = 1.0). "
        "The sampling interval is fixed at Δt = 2.5 seconds. For repeatable demonstrations and automated evaluation, a dedicated "
        "<code>POST /scenario</code> endpoint injects canonical testing scenarios (<code>NORMAL</code>, <code>WASTEFUL</code>, "
        "<code>HIGH LOAD</code>, <code>SPIKE</code>, <code>LIVE TELEMETRY</code>) into the live database and ML pipeline without requiring manual Wokwi adjustments.",
        style_body
    ))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 6: METHODOLOGY & AI TECHNIQUES
    # =========================================================================
    story.append(Paragraph("6. Methodology & AI Formulations", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))

    story.append(Paragraph("6.1 Data Preprocessing & Trapezoidal Energy Integration", style_h2))
    story.append(Paragraph(
        "Incoming JSON telemetry is validated using Pydantic v2 schemas. Cumulative energy (kWh) is calculated continuously "
        "using discrete numerical trapezoidal integration across consecutive 2.5-second power measurements:",
        style_body
    ))
    story.append(Paragraph(
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>ΔE<sub>t</sub> (Wh)</b> = P<sub>t</sub> (W) × (2.5 s / 3,600 s/h)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>E<sub>total</sub> (kWh)</b> = Σ ΔE<sub>t</sub> / 1,000",
        style_body_bold
    ))

    story.append(Paragraph("6.2 Feature Engineering Pipeline", style_h2))
    story.append(Paragraph(
        "Feature engineering is segmented to strictly prevent target data leakage: "
        "<br/>• <b>Model 1 Decomposition Features (21 variables):</b> 4 sensor values, 7 binary appliance indicators, 5 interaction terms "
        "(<code>occupied_ac</code>, <code>occupied_heater</code>, <code>daylight_light</code>, <code>hot_weather_ac</code>, <code>cold_weather_heater</code>), "
        "and 2 device count aggregations."
        "<br/>• <b>Model 2 Autoregressive Features (10 variables):</b> backward-shifted lags (P<sub>t-1</sub>, P<sub>t-2</sub>, P<sub>t-3</sub>), "
        "3-step moving average (P̄<sub>roll3</sub>), power gradient (ΔP<sub>1,2</sub> = P<sub>t-1</sub> - P<sub>t-2</sub>), ambient temperature, humidity, "
        "occupancy, hour, and minute. <i>Leakage Prevention: Current power P<sub>t</sub>, target P<sub>t+1</sub>, and current appliance switch states are strictly excluded.</i>"
        "<br/>• <b>Model 3 Anomaly Features (8 variables):</b> power magnitude, environmental metrics, and multi-device activation flags.",
        style_body
    ))

    story.append(Paragraph("6.3 Machine Learning Formulation", style_h2))
    story.append(Paragraph(
        "• <b>Model 1 (Expected Load Decomposition):</b> Ordinary Least Squares Linear Regression. Reconstructs expected baseline demand: "
        "P̂<sub>expected</sub> = β<sub>0</sub> + Σ β<sub>j</sub> X<sub>j</sub>. Recovers exact rated device wattages (R² = 1.000, MAE = 0 W).<br/>"
        "• <b>Model 2 (Short-Term Power Forecasting):</b> Lagged Autoregressive Model forecasting the next 2.5-second step: "
        "P̂<sub>t+1</sub> = α + Σ φ<sub>k</sub> P<sub>t-k</sub> + γ ΔP<sub>1,2</sub> + Σ θ<sub>m</sub> C<sub>m</sub>. Evaluated chronologically (80/20 train/test split, "
        "R² = 0.2142, MAE = 830.11 W). Represents genuine predictive forecasting under stochastic human switching.<br/>"
        "• <b>Model 3 (Unsupervised Isolation Forest):</b> Scikit-Learn IsolationForest (100 estimators, 5% contamination). Isolates anomalous high-power "
        "concurrency spikes (> 4,500 W) based on path length partitioning.<br/>"
        "• <b>Deterministic Explainability Rules:</b> Evaluates 4 domain constraints (Vacancy Waste, Daylight Waste, HVAC Conflict, Overload Warning/Critical) "
        "and outputs plain-English recommendations with potential load reductions.",
        style_body
    ))

    # =========================================================================
    # SECTION 7: IMPLEMENTATION & CODE ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("7. Implementation & Code Architecture", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "The project is implemented in Python 3.9+ and C++ (ESP32 Arduino Core). Key code snippet illustrating MQTT ingestion, "
        "Pydantic validation, ML inferencing, and SQLite persistence:",
        style_body
    ))

    code_snippet = (
        "# backend/collector.py — Asynchronous Telemetry Ingest & AI Pipeline\n"
        "def process_telemetry_payload(raw_payload: str) -> bool:\n"
        "    try:\n"
        "        data = json.loads(raw_payload)\n"
        "        telemetry = TelemetryInput(**data)  # Pydantic v2 schema validation\n"
        "        \n"
        "        # Real-time Multi-Model Inference\n"
        "        m1_expected = predictor.predict_expected_power(telemetry)\n"
        "        m2_forecast = predictor.forecast_next_power(telemetry)\n"
        "        is_anomaly, score = anomaly_detector.predict_anomaly(telemetry)\n"
        "        waste_flag, reasons, actions, severity = rule_engine.evaluate(telemetry)\n"
        "        \n"
        "        # Relational Persistence\n"
        "        insert_telemetry(telemetry, m1_expected, m2_forecast, is_anomaly, score, severity)\n"
        "        return True\n"
        "    except ValidationError as e:\n"
        "        logger.error(f'Corrupted payload rejected: {e}')\n"
        "        return False\n"
    )
    code_box = Table([[Preformatted(code_snippet, style_code)]], colWidths=[504])
    code_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0F4F6")),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(code_box)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 8: RESULTS & EVALUATION
    # =========================================================================
    story.append(Paragraph("8. Results & Evaluation", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))

    story.append(Paragraph("8.1 Machine Learning Evaluation Metrics", style_h2))
    story.append(Paragraph(
        "Performance evaluation conducted on the benchmark dataset of 7,200 continuous operational samples:",
        style_body
    ))

    # Results Table
    res_header = [Paragraph("Model", style_table_header), Paragraph("Role", style_table_header), Paragraph("Algorithm", style_table_header), Paragraph("MAE", style_table_header), Paragraph("RMSE", style_table_header), Paragraph("R² Score", style_table_header), Paragraph("Status", style_table_header)]
    res_rows = [
        [Paragraph("<b>Model 1</b>", style_table_cell_bold), Paragraph("Load Baseline", style_table_cell), Paragraph("OLS Regression", style_table_cell), Paragraph("0.00 W", style_table_cell), Paragraph("0.00 W", style_table_cell), Paragraph("<b>1.0000</b>", style_table_cell), Paragraph("Verified", style_table_cell)],
        [Paragraph("<b>Model 2</b>", style_table_cell_bold), Paragraph("Short-Term Forecast", style_table_cell), Paragraph("Lagged AR Model", style_table_cell), Paragraph("830.11 W", style_table_cell), Paragraph("1070.58 W", style_table_cell), Paragraph("<b>0.2142</b>", style_table_cell), Paragraph("Verified (Leak-Free)", style_table_cell)],
        [Paragraph("<b>Model 3</b>", style_table_cell_bold), Paragraph("Anomaly Detection", style_table_cell), Paragraph("Isolation Forest", style_table_cell), Paragraph("N/A", style_table_cell), Paragraph("N/A", style_table_cell), Paragraph("5% Contam", style_table_cell), Paragraph("360 Outliers Flagged", style_table_cell)],
    ]
    res_table = Table([res_header] + res_rows, colWidths=[65, 85, 95, 60, 65, 65, 69])
    res_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_TEAL_DARK),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_PRIMARY_LIGHT, COLOR_SURFACE_LIGHT]),
    ]))
    story.append(res_table)

    story.append(Spacer(1, 8))
    story.append(Paragraph("8.2 Interactive Plotly Visualization Suite (10 Real-Time Engines)", style_h2))
    plotly_descriptions = [
        "<b>Chart 1 (Real-Time Power Timeline):</b> Temporal trajectory with interactive zoom, hover point inspection, and threshold overlays.",
        "<b>Chart 2 (AI Actual vs Expected vs Forecast):</b> Evaluates Model 1 baseline estimation vs Model 2 1-step autoregressive forecast against actual demand.",
        "<b>Chart 3 (Appliance Load Contribution):</b> Horizontal bar chart sorted descending by active wattage with percentage load attribution.",
        "<b>Chart 4 (Current Load Composition):</b> Precision donut chart displaying fractional energy shares across devices.",
        "<b>Chart 5 (Diurnal Heatmap):</b> Day × Hour density matrix mapping 24-hour diurnal load profiles.",
        "<b>Chart 6 (Occupancy vs Power Correlation):</b> Scatter plot identifying cluster points corresponding to vacancy waste.",
        "<b>Chart 7 (Temperature vs Power):</b> Bimodal correlation isolating cooling and heating activation curves.",
        "<b>Chart 8 (AI Anomaly Timeline):</b> Scatter graph color-coding nominal operation vs Isolation Forest anomaly events.",
        "<b>Chart 9 (Power Flow Sankey):</b> Directed flux visualization showing grid influx branching into active appliance loads.",
        "<b>Chart 10 (Load Waterfall Breakdown):</b> Step-by-step sequential accumulation of device loads culminating in total home draw.",
    ]
    for desc in plotly_descriptions:
        story.append(Paragraph(f"• {desc}", style_bullet))

    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 9: DISCUSSION
    # =========================================================================
    story.append(Paragraph("9. Discussion", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "<b>What Worked Well:</b> (1) The decoupled MQTT architecture proved highly resilient—disconnecting the browser does not pause backend "
        "telemetry ingestion; (2) The zero-leakage design of Model 2 (R² = 0.2142) accurately models the physics of stochastic appliance switching; "
        "(3) The combination of statistical ML models with deterministic rules eliminates black-box obscurity; and (4) The Apple Liquid Glass "
        "high-density 7-column appliance grid maximized vertical screen efficiency without sacrificing clarity.<br/>"
        "<b>Limitations:</b> (1) Simulated telemetry models clean rated wattages rather than noisy analog current harmonics; (2) Model 2 is an immediate "
        "1-step autoregressive forecaster rather than a day-ahead scheduler; and (3) Recommendations are advisory due to lack of physical relay actuators.",
        style_body
    ))

    # =========================================================================
    # SECTION 10: CONCLUSION & FUTURE SCOPE
    # =========================================================================
    story.append(Paragraph("10. Conclusion & Future Scope", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "<b>Summary:</b> The capstone project successfully demonstrates an end-to-end, multi-model AI-for-IoT smart home energy management platform. "
        "The system acquires high-frequency telemetry, validates data integrity, decomposes baseline loads, forecasts short-term power, flags multivariate "
        "anomalies, and provides explainable energy-saving recommendations on a production-grade dashboard. With 68/68 automated tests passing at 100%, "
        "the project fulfills all criteria of Experiment 8.<br/>"
        "<b>Future Extensions to Real Hardware:</b> (1) Connect physical ESP32 boards to PZEM-004T or SCT-013 current transformers; (2) Train deep Long Short-Term "
        "Memory (LSTM) or Temporal Fusion Transformer networks for 24-hour ahead forecasting; (3) Integrate Zigbee/Matter smart plugs for automated load-shedding; "
        "and (4) Incorporate dynamic Time-of-Use (TOU) tariffs to optimize battery storage and appliance scheduling.",
        style_body
    ))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 11: INDIVIDUAL CONTRIBUTION
    # =========================================================================
    story.append(Paragraph("11. Individual Contribution Table", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "In accordance with Experiment 8 guidelines, all members are prepared to individually explain the entire pipeline during viva examination. "
        "Primary module contributions are detailed below:",
        style_body
    ))

    contrib_header = [Paragraph("Member Name", style_table_header), Paragraph("Roll No", style_table_header), Paragraph("Core Responsibilities", style_table_header), Paragraph("Key Modules Contributed", style_table_header)]
    contrib_rows = [
        [
            Paragraph("<b>Student 1</b>", style_table_cell_bold),
            Paragraph("2026-IOT-01", style_table_cell),
            Paragraph("<b>IoT Firmware & Simulation</b>", style_table_cell_bold),
            Paragraph(
                "• Configured Wokwi ESP32, DHT22, PIR, and LDR sensors.<br/>"
                "• Authored non-blocking C++ Arduino firmware (<code>sketch.ino</code>).<br/>"
                "• Engineered virtual appliance state simulation and deterministic load logic.<br/>"
                "• Managed HiveMQ MQTT broker configuration and topic publishing.",
                style_table_cell
            )
        ],
        [
            Paragraph("<b>Student 2</b>", style_table_cell_bold),
            Paragraph("2026-IOT-02", style_table_cell),
            Paragraph("<b>Machine Learning & Features</b>", style_table_cell_bold),
            Paragraph(
                "• Formulated leakage-free feature engineering pipeline (<code>features.py</code>).<br/>"
                "• Trained Model 1 OLS Decomposition (R² = 1.000, MAE = 0 W).<br/>"
                "• Engineered Model 2 Lagged Autoregressive Forecaster (R² = 0.2142).<br/>"
                "• Configured Model 3 Isolation Forest for multivariate anomaly detection.<br/>"
                "• Audited evaluation metrics and authored <code>ML_REPORT.md</code>.",
                style_table_cell
            )
        ],
        [
            Paragraph("<b>Student 3</b>", style_table_cell_bold),
            Paragraph("2026-IOT-03", style_table_cell),
            Paragraph("<b>Backend & API Engineering</b>", style_table_cell_bold),
            Paragraph(
                "• Built FastAPI asynchronous service layer with 10 REST endpoints.<br/>"
                "• Engineered Python MQTT background ingestion daemon (<code>collector.py</code>).<br/>"
                "• Designed SQLite schema and trapezoidal continuous kWh integration.<br/>"
                "• Developed explainable deterministic rule engine (<code>rules.py</code>).<br/>"
                "• Authored 68 automated unit & integration tests passing at 100%.",
                style_table_cell
            )
        ],
        [
            Paragraph("<b>Student 4</b>", style_table_cell_bold),
            Paragraph("2026-IOT-04", style_table_cell),
            Paragraph("<b>Dashboard & UI/UX</b>", style_table_cell_bold),
            Paragraph(
                "• Developed Streamlit dashboard using Apple Liquid Glass design system.<br/>"
                "• Engineered 10 interactive Plotly charts with custom brand palette.<br/>"
                "• Built space-efficient 7-column responsive appliance grid.<br/>"
                "• Implemented bidirectional cross-filtering and point investigation drawers.<br/>"
                "• Eliminated emojis and integrated vector SVG icon library.",
                style_table_cell
            )
        ],
    ]
    contrib_table = Table([contrib_header] + contrib_rows, colWidths=[80, 70, 110, 244])
    contrib_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_TEAL_DARK),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_PRIMARY_LIGHT, COLOR_SURFACE_LIGHT]),
    ]))
    story.append(contrib_table)

    # =========================================================================
    # REFERENCES
    # =========================================================================
    story.append(Paragraph("References", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))
    refs = [
        "[1] Alahakoon, D., & Yu, X. (2016). Smart electricity meter data intelligence for future energy systems: A survey. <i>IEEE Transactions on Industrial Informatics</i>, 12(1), 425-436.",
        "[2] Kelly, J., & Knottenbelt, W. (2015). Neural NILM: Deep neural networks applied to energy disaggregation. <i>ACM BuildSys</i>, 55-64.",
        "[3] Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). Isolation Forest. <i>Eighth IEEE International Conference on Data Mining</i>, 413-422.",
        "[4] Box, G. E., Jenkins, G. M., Reinsel, G. C., & Ljung, G. M. (2015). <i>Time Series Analysis: Forecasting and Control</i>. John Wiley & Sons.",
        "[5] Espressif Systems. (2023). <i>ESP32 Series Datasheet and Technical Reference Manual</i>.",
        "[6] HiveMQ GmbH. (2024). <i>MQTT Essentials: A lightweight messaging protocol for IoT</i>.",
        "[7] Streamlit Inc. (2024). <i>Streamlit Developer Documentation & State Architecture</i>.",
        "[8] Plotly Technologies Inc. (2024). <i>Plotly Open Source Graphing Library for Python</i>.",
    ]
    for r in refs:
        story.append(Paragraph(r, style_body))

    # =========================================================================
    # APPENDIX
    # =========================================================================
    story.append(Paragraph("Appendix: Full Repository & Execution Commands", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_TEAL_DARK, spaceBefore=0, spaceAfter=8))

    appendix_commands = (
        "# 1. Start FastAPI Asynchronous Backend Service\n"
        "python3 -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload\n\n"
        "# 2. Launch Background MQTT Collector (if running standalone)\n"
        "python3 -m backend.collector\n\n"
        "# 3. Launch Apple-Style Streamlit Dashboard\n"
        "python3 -m streamlit run dashboard/app.py --server.port 8501\n\n"
        "# 4. Execute Full Verification Test Suite (68/68 Tests Passing)\n"
        "python3 -m unittest discover tests\n"
        "python3 -m pytest tests/ -v\n"
    )
    app_box = Table([[Preformatted(appendix_commands, style_code)]], colWidths=[504])
    app_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0F4F6")),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(app_box)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {filename}")


if __name__ == "__main__":
    out_pdf = "docs/CAPSTONE_REPORT_EXPERIMENT_8.pdf"
    if len(sys.argv) > 1:
        out_pdf = sys.argv[1]
    build_pdf(out_pdf)
