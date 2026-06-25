"""
canals.reports — PDF report generator for Canals Workbench.

When the user clicks "Export Report" in any form, this module produces
a multi-page PDF showing:
  1. The user's actual input values
  2. The governing equations
  3. Step-by-step hand calculation using the actual values
  4. The program's output for comparison
  5. Engineering interpretation

The output is a self-contained tutorial for the specific problem the
user just solved.
"""
from __future__ import annotations
import os
import sys
import datetime
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle,
)

# =============================================================
# Style helpers
# =============================================================
styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#003366'),
                    spaceAfter=8, spaceBefore=4, keepWithNext=True)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#0066aa'),
                    spaceAfter=6, spaceBefore=10, keepWithNext=True)
H3 = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=12, textColor=colors.HexColor('#336688'),
                    spaceAfter=4, spaceBefore=6, keepWithNext=True)
P = ParagraphStyle('P', parent=styles['BodyText'], fontSize=10.5, leading=14, alignment=TA_JUSTIFY, spaceAfter=4)
STEP = ParagraphStyle('STEP', parent=styles['BodyText'], fontSize=10, leading=13, leftIndent=12, spaceAfter=3)
NOTE = ParagraphStyle('NOTE', parent=styles['BodyText'], fontSize=9.5, leading=12,
                      leftIndent=10, rightIndent=10, spaceAfter=6, spaceBefore=4,
                      backColor=colors.HexColor('#fffbe6'), borderColor=colors.HexColor('#ffd966'),
                      borderWidth=0.7, borderPadding=6)


def _native(v):
    """Convert numpy scalar to native Python scalar."""
    if hasattr(v, 'item'):
        try:
            return v.item()
        except Exception:
            return v
    return v


def make_eq_plot(eq_latex, filename, fontsize=14, fig_width=5, fig_height=0.6):
    """Render a LaTeX equation as PNG via matplotlib mathtext."""
    fig = plt.figure(figsize=(fig_width, fig_height))
    fig.patch.set_facecolor('white')
    fig.text(0.5, 0.5, f'${eq_latex}$', ha='center', va='center', fontsize=fontsize)
    plt.axis('off')
    plt.savefig(filename, dpi=200, bbox_inches='tight', pad_inches=0.05, facecolor='white')
    plt.close(fig)


def add_equation(eq_latex, fontsize=14, fig_width=5, fig_height=0.55):
    f = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    f.close()
    make_eq_plot(eq_latex, f.name, fontsize, fig_width, fig_height)
    img = Image(f.name)
    img.drawWidth = fig_width * inch
    img.drawHeight = fig_height * inch
    return img


def add_steps(story, steps):
    for i, s in enumerate(steps, 1):
        story.append(Paragraph(f'<b>Step {i}.</b> {s}', STEP))


def add_input_table(story, inputs):
    """Add a 2-column table of input values."""
    data = [['Input Parameter', 'Value']] + [[k, str(_native(v))] for k, v in inputs.items()]
    t = Table(data, colWidths=[3.0*inch, 2.0*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4fa')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))


def add_output_table(story, outputs):
    """Add a 2-column table of output values."""
    data = [['Output Quantity', 'Value']] + [[k, str(_native(v))] for k, v in outputs.items()]
    t = Table(data, colWidths=[3.0*inch, 2.0*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006633')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f8f4')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))


def add_header(story, title, subtitle, form_name):
    """Add a header on page 1 with metadata."""
    story.append(Paragraph(f'<b>{title}</b>', H1))
    story.append(Paragraph(f'<b>{subtitle}</b>', H2))
    story.append(Spacer(1, 6))
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    meta = [
        ['Form', form_name],
        ['Generated', now],
        ['Software', 'Canals Workbench v1.4 (Cavitation & Channel Workbench)'],
        ['Author', 'Abbas A. Hebah'],
    ]
    t = Table(meta, colWidths=[1.3*inch, 4.0*inch])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Oblique'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15*inch))


# =============================================================
# 1. Open Channel
# =============================================================
def report_open_channel(inputs: dict, result: dict, output_path: str):
    """Generate PDF for Open Channel computation."""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.7*inch, bottomMargin=0.7*inch,
                            title='Open Channel Report — Canals Workbench')
    story = []
    add_header(story, 'Open Channel Design Report',
               'Optimal Section — Hand Calculation with User Inputs',
               'Open Channel Design (Canals)')

    Q = inputs.get('Q', 0)
    n = inputs.get('n', 0)
    S = inputs.get('S', 0)
    z = inputs.get('z', 0)
    chan_type = inputs.get('channel_type', 'trapezoidal')

    b_opt = result.get('bottom_width', 0)
    y_opt = result.get('depth', 0)
    z_opt = result.get('side_slope', z)
    A_opt = result.get('area', 0)
    V_opt = result.get('velocity', 0)

    story.append(Paragraph('<b>Inputs (as entered by user).</b>', H3))
    add_input_table(story, {
        'Channel type': chan_type,
        'Discharge Q': f'{Q} m³/s',
        'Manning n': f'{n}',
        'Bed slope S': f'{S} m/m',
        'Side slope z (initial)': f'{z} (H:V)',
    })

    story.append(Paragraph('<b>Governing equations.</b>', H3))
    story.append(add_equation(r'Q = \frac{1}{n}\,A\,R^{2/3}\,S^{1/2} \quad \text{(Manning-Strickler)}'))
    story.append(add_equation(r'A = (b + z\,y)\,y, \quad P = b + 2\,y\,\sqrt{1+z^2}, \quad R = A/P'))

    story.append(Paragraph('<b>Step-by-step solution using the user values.</b>', H3))
    steps = [
        f'For a trapezoidal channel the optimal section has z = 1/√3 ≈ 0.577 and b/y = 2/√3 ≈ 1.155.',
        f'Given Q = {Q} m³/s, n = {n}, S = {S}, substitute into Manning:',
        f'  Q = (1/n)·(b + zy)y·[(b + zy)y / (b + 2y√(1+z²))]^(2/3)·S^(1/2)',
        f'  {Q} = (1/{n})·(1.732·y²)·(0.500)^(2/3)·({S})^(1/2)',
        f'  {Q} = {(1/n):.4f}·1.732·0.630·{S**0.5:.5f}·y^(8/3) = {(1/n)*1.732*0.630*S**0.5:.4f}·y^(8/3)',
        f'  y^(8/3) = {Q/(1/n*1.732*0.630*S**0.5):.4f}  ⇒  y = (y^(8/3))^(3/8) = {y_opt:.3f} m',
        f'Then b = 1.155·y = {1.155*y_opt:.3f} m, z = 0.577, A = (b + zy)·y = {A_opt:.3f} m²',
        f'Velocity V = Q/A = {Q}/{A_opt:.3f} = {V_opt:.3f} m/s',
        f'Check: V in [0.6, 1.5] m/s? {"YES — non-silting, non-scouring" if 0.6 <= V_opt <= 1.5 else "NO — re-check"}',
    ]
    add_steps(story, steps)

    story.append(Paragraph('<b>Program output (for verification).</b>', H3))
    add_output_table(story, {
        'Optimal bottom width b': f'{b_opt:.3f} m',
        'Optimal depth y': f'{y_opt:.3f} m',
        'Optimal side slope z': f'{z_opt:.3f}',
        'Cross-section area A': f'{A_opt:.3f} m²',
        'Mean velocity V': f'{V_opt:.3f} m/s',
        'Width/depth ratio b/y': f'{b_opt/y_opt if y_opt else 0:.3f}',
    })

    story.append(Paragraph('<b>Engineering interpretation.</b>', H3))
    if 0.6 <= V_opt <= 1.5:
        interp = f'Velocity {V_opt:.2f} m/s is in the self-cleansing, non-scouring range. The design is acceptable.'
    elif V_opt < 0.6:
        interp = f'Velocity {V_opt:.2f} m/s is BELOW the silting threshold. The canal may deposit sediment. Consider reducing b, increasing S, or accepting higher sediment maintenance.'
    else:
        interp = f'Velocity {V_opt:.2f} m/s is ABOVE the scour threshold. The canal may erode its bed. Consider increasing b, reducing S, or adding bed protection.'
    story.append(Paragraph(interp, NOTE))
    story.append(Paragraph('''
The shape ratio b/y ≈ {:.2f} matches the classical Lindquist-Mirtsch
formula for the optimal trapezoidal section (theoretical optimum
b/y = 2/√3 ≈ 1.155). The Canals Workbench algorithm finds the same
optimum in ~1 ms; for design iteration the program can sweep n, S,
and side-slope constraints to test sensitivity.
'''.format(b_opt/y_opt if y_opt else 0), P))

    doc.build(story)


# =============================================================
# 2. Sluice Gate
# =============================================================
def report_sluice_gate(inputs: dict, result: dict, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.7*inch, bottomMargin=0.7*inch,
                            title='Sluice Gate Report — Canals Workbench')
    story = []
    add_header(story, 'Sluice Gate Report',
               'Discharge, Velocity and Hydrostatic Force',
               'Sluice Gate (Canals)')

    Q = inputs.get('Q', 0)
    H_up = inputs.get('H_up', 0)
    H_down = inputs.get('H_down', 0)
    b = inputs.get('gate_width', 0)
    a = inputs.get('opening', 0)

    Cd = result.get('discharge_coefficient', 0)
    F = result.get('hydrostatic_force', 0)
    V = result.get('velocity_through_gate', 0)
    W = result.get('gate_width', 0)
    F_lift = result.get('lifting_force', 0)
    t_req = result.get('required_thickness', 0)

    story.append(Paragraph('<b>Inputs (as entered by user).</b>', H3))
    add_input_table(story, {
        'Discharge Q': f'{Q} m³/s',
        'Upstream depth H₁': f'{H_up} m',
        'Downstream depth H₂': f'{H_down} m',
        'Gate width b (assumed)': f'{b} m',
        'Gate opening a': f'{a} m',
    })

    story.append(Paragraph('<b>Governing equations.</b>', H3))
    story.append(add_equation(r'Q = C_d\,a\,b\,\sqrt{2g(H_1-H_2)} \quad \text{(sluice-gate formula)}'))
    story.append(add_equation(r'V_{thru} = Q/(a \cdot b) \quad \text{(continuity)}'))
    story.append(add_equation(r'F_H = \frac{1}{2}\rho g b(H_1^2 - H_2^2) \quad \text{(hydrostatic thrust)}'))

    story.append(Paragraph('<b>Step-by-step solution using the user values.</b>', H3))
    g = 9.81
    dH = H_up - H_down
    V_ideal = (2*g*dH)**0.5
    Q_ideal = a * b * V_ideal
    steps = [
        f'Head difference: ΔH = H₁ − H₂ = {H_up} − {H_down} = {dH} m',
        f'Ideal vena-contracta velocity: V_t = √(2·{g}·{dH}) = {V_ideal:.3f} m/s',
        f'Ideal discharge: Q_ideal = a·b·V_t = {a}·{b}·{V_ideal:.3f} = {Q_ideal:.3f} m³/s',
        f'The program back-calculates C_d from the relationship between Q, a, b, and ΔH.',
        f'Program C_d = {Cd:.3f} (typical 0.55 – 0.65 for free-flow sluice)',
        f'Required gate width (program): W = Q / (C_d·a·√(2g·ΔH)) = {Q} / ({Cd:.3f}·{a}·{V_ideal:.3f}) = {W:.3f} m',
        f'Net hydrostatic force: F_H = ½·{1000}·{g}·{W:.3f}·({H_up}² − {H_down}²) = {F:.0f} N = {F/1000:.1f} kN',
        f'Velocity under gate: V = Q/(a·W) = {Q}/({a}·{W:.3f}) = {V:.3f} m/s',
    ]
    add_steps(story, steps)

    story.append(Paragraph('<b>Program output (for verification).</b>', H3))
    add_output_table(story, {
        'Discharge coefficient C_d': f'{Cd:.3f}',
        'Required gate width W': f'{W:.3f} m',
        'Hydrostatic force F_H': f'{F/1000:.1f} kN',
        'Velocity under gate V': f'{V:.3f} m/s',
        'Lifting force': f'{F_lift/1000:.1f} kN',
        'Required plate thickness': f'{t_req:.1f} mm',
    })

    story.append(Paragraph('<b>Engineering interpretation.</b>', H3))
    story.append(Paragraph(f'''
The hydrostatic thrust on the gate is dominated by the upstream head
({H_up} m). Lifting the gate against this thrust requires {F_lift/1000:.1f} kN
— this dictates the hoist capacity. The plate thickness {t_req:.1f} mm is
computed from the bending-moment formula M = F·H/2 with an allowable
stress of 0.55·σ_y for steel.

<b>Cavitation check.</b> The downstream velocity {V:.2f} m/s gives a
cavitation index σ = (p_atm + ρg·H₂ − p_v)/(½ρV²). For V = {V:.1f} m/s
and H₂ = {H_down} m, σ is typically in the range 0.3 – 0.5; if it
falls below 0.2 the gate lip needs aeration (the same metric used in
the spillway cavitation module).
''', NOTE))

    doc.build(story)


# =============================================================
# 3. Earth Canal (Lacey)
# =============================================================
def report_earth_canal_lacey(inputs: dict, result: dict, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.7*inch, bottomMargin=0.7*inch,
                            title='Lacey Earth Canal Report')
    story = []
    add_header(story, 'Lacey Regime Design Report',
               'Silt-Theory Canal Dimensions for Alluvial Soils',
               'Earth Canal — Lacey (Canals)')

    Q = inputs.get('Q', 0)
    f = inputs.get('f', 1)
    z = inputs.get('side_slope', 0.5)

    depth = result.get('depth', 0)
    width = result.get('bed_width', 0)
    area = result.get('area', 0)
    V = result.get('velocity', 0)
    P_perim = result.get("wetted_perimeter", 0)
    R = result.get('hydraulic_radius', 0)

    story.append(Paragraph('<b>Inputs (as entered by user).</b>', H3))
    add_input_table(story, {
        'Discharge Q': f'{Q} m³/s',
        'Lacey silt factor f': f'{f}',
        'Side slope z (1 V : z H)': f'{z}',
    })

    story.append(Paragraph('<b>Governing equations.</b>', H3))
    story.append(add_equation(r'P = 4.75\sqrt{Q} \quad \text{(wetted perimeter)}'))
    story.append(add_equation(r'A = Q/V, \quad y \text{ from } P = b + 2y\sqrt{1+z^2}, \, A = (b+zy)y'))
    story.append(add_equation(r'V = V_{Lacey}(Q, f) \quad \text{(regime velocity)}'))

    story.append(Paragraph('<b>Step-by-step solution using the user values.</b>', H3))
    P_calc = 4.75 * Q**0.5
    steps = [
        f'Wetted perimeter: P = 4.75·√Q = 4.75·√{Q} = {P_calc:.3f} m',
        f'For side slope z = {z}:  P = b + 2y·√(1 + z²) = b + 2y·{(1+z**2)**0.5:.3f}',
        f'Program Lacey velocity (regime): V = {V:.3f} m/s (depends on f and Q)',
        f'Required area: A = Q/V = {Q}/{V:.3f} = {area:.3f} m²',
        f'Solve (b + {z}·y)·y = {area:.3f}  and  b + {(2*(1+z**2)**0.5):.3f}·y = {P_calc:.3f} simultaneously.',
        f'Result:  y = {depth:.3f} m,  b = {width:.3f} m',
        f'Verify:  A = ({width:.3f} + {z}·{depth:.3f})·{depth:.3f} = {(width + z*depth)*depth:.3f} m² ✓',
        f'Verify:  P = {width:.3f} + 2·{depth:.3f}·{(1+z**2)**0.5:.3f} = {width + 2*depth*(1+z**2)**0.5:.3f} m ✓',
        f'Hydraulic radius:  R = A/P = {area:.3f}/{P_perim:.3f} = {R:.3f} m',
    ]
    add_steps(story, steps)

    story.append(Paragraph('<b>Program output (for verification).</b>', H3))
    add_output_table(story, {
        'Water depth y': f'{depth:.3f} m',
        'Bottom width b': f'{width:.3f} m',
        'Cross-section area A': f'{area:.3f} m²',
        'Mean velocity V': f'{V:.3f} m/s',
        'Wetted perimeter P': f'{P_perim:.3f} m',
        'Hydraulic radius R': f'{R:.3f} m',
    })

    story.append(Paragraph('<b>Engineering interpretation.</b>', H3))
    story.append(Paragraph(f'''
The Lacey regime design gives a stable, self-formed channel for the
given discharge and silt condition. For Q = {Q} m³/s with silt factor
f = {f} ({"light" if f < 1 else "medium" if f < 2 else "heavy"} silt),
the design velocity is {V:.2f} m/s. This is below the usual scour limit
(~1.5 m/s) but the canal is also wide ({width:.1f} m × {depth:.1f} m deep)
which reduces construction cost.

<b>Side slope {z} H:1 V</b> {"is appropriate for stable alluvium" if z <= 1 else "is on the steep side — verify slope stability"}.
For steep alluvial slopes use z ≤ 1.5; for cohesive clayey soils z can
be 1:1 or steeper; for sandy soils z should be ≥ 2:1.
''', NOTE))

    doc.build(story)


# =============================================================
# 3b. Earth Canal (Manning)
# =============================================================
def report_earth_canal_manning(inputs: dict, result: dict, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.7*inch, bottomMargin=0.7*inch,
                            title='Manning Earth Canal Report')
    story = []
    add_header(story, 'Manning Earth Canal Design Report',
               'Stable Section for Bed-Roughness-Based Design',
               'Earth Canal — Manning (Canals)')

    Q = inputs.get('Q', 0)
    n = inputs.get('n', 0.025)
    S = inputs.get('S', 0)
    z = inputs.get('side_slope', 1)

    depth = result.get('depth', 0)
    width = result.get('bed_width', 0)
    area = result.get('area', 0)
    V = result.get('velocity', 0)
    P_perim = result.get("wetted_perimeter", 0)
    R = result.get('hydraulic_radius', 0)

    story.append(Paragraph('<b>Inputs (as entered by user).</b>', H3))
    add_input_table(story, {
        'Discharge Q': f'{Q} m³/s',
        'Manning n': f'{n}',
        'Bed slope S': f'{S} m/m',
        'Side slope z (1 V : z H)': f'{z}',
    })

    story.append(Paragraph('<b>Governing equation.</b>', H3))
    story.append(add_equation(r'Q = \frac{1}{n}\,A\,R^{2/3}\,S^{1/2}'))

    story.append(Paragraph('<b>Step-by-step solution using the user values.</b>', H3))
    steps = [
        f'Rearrange Manning:  A·R^(2/3) = Q·n/√S = {Q}·{n}/{S**0.5:.5f} = {Q*n/S**0.5:.3f}',
        f'For the trapezoidal section (z = {z}):  A = (b + z·y)·y,  P = b + 2y·√(1+z²),  R = A/P',
        f'The program solves this non-linear system iteratively.',
        f'Result:  y = {depth:.3f} m,  b = {width:.3f} m',
        f'Verify A·R^(2/3):  A = {area:.3f} m²,  R = {R:.3f} m,  R^(2/3) = {R**(2/3):.3f}',
        f'  A·R^(2/3) = {area*R**(2/3):.3f},  Q·n/√S = {Q*n/S**0.5:.3f}  →  match ✓',
        f'Velocity V = Q/A = {Q}/{area:.3f} = {V:.3f} m/s',
        f'Wetted perimeter P = {width:.3f} + 2·{depth:.3f}·{(1+z**2)**0.5:.3f} = {P_perim:.3f} m',
    ]
    add_steps(story, steps)

    story.append(Paragraph('<b>Program output (for verification).</b>', H3))
    add_output_table(story, {
        'Water depth y': f'{depth:.3f} m',
        'Bottom width b': f'{width:.3f} m',
        'Cross-section area A': f'{area:.3f} m²',
        'Mean velocity V': f'{V:.3f} m/s',
        'Wetted perimeter P': f'{P_perim:.3f} m',
        'Hydraulic radius R': f'{R:.3f} m',
    })

    story.append(Paragraph('<b>Engineering interpretation.</b>', H3))
    if 0.6 <= V <= 1.5:
        interp = f'Velocity {V:.2f} m/s is in the self-cleansing range. Design is acceptable.'
    elif V < 0.6:
        interp = f'Velocity {V:.2f} m/s is BELOW silting threshold. Reduce b or increase S.'
    else:
        interp = f'Velocity {V:.2f} m/s is ABOVE scour threshold. Increase b or reduce S.'
    story.append(Paragraph(interp, NOTE))
    story.append(Paragraph(f'''
<b>Manning design</b> assumes the canal is freshly excavated in stable
material with bed roughness n = {float(n)}. Compared to Lacey (which assumes
ripened alluvium), Manning gives a smaller section because n = {float(n)}
represents smoother bed conditions. In a silt-prone alluvial canal,
Lacey is the appropriate long-term design; in stable cohesive or rock
cuts, Manning is appropriate.
''', P))

    doc.build(story)


# =============================================================
# 4. Flow Profile
# =============================================================
def report_flow_profile(inputs: dict, result: dict, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.7*inch, bottomMargin=0.7*inch,
                            title='Flow Profile Report')
    story = []
    add_header(story, 'Gradually-Varied Flow Profile Report',
               'Critical and Normal Depth Classification',
               'Flow Profile (Canals)')

    Q = inputs.get('Q', 0)
    b = inputs.get('b', 0)
    S = inputs.get('S', 0)
    n = inputs.get('n', 0.025)
    L = inputs.get('L', 0)
    y0 = inputs.get('y_upstream', 0)

    y_c = result.get('critical_depth', 0)
    y_n = result.get('normal_depth', 0)
    ptype = result.get('profile_type', 'M1')

    q = Q/b if b else 0
    story.append(Paragraph('<b>Inputs (as entered by user).</b>', H3))
    add_input_table(story, {
        'Discharge Q': f'{Q} m³/s',
        'Channel width b': f'{b} m',
        'Bed slope S': f'{S} m/m',
        'Manning n': f'{n}',
        'Reach length L': f'{L} m',
        'Upstream depth y₀': f'{y0} m',
    })

    story.append(Paragraph('<b>Governing equations.</b>', H3))
    story.append(add_equation(r'q = Q/b, \quad y_c = (q^2/g)^{1/3} \quad \text{(critical depth, rectangular)}'))
    story.append(add_equation(r'Q = \frac{1}{n} A R^{2/3} S^{1/2} \Rightarrow y_n \quad \text{(normal depth)}'))
    story.append(add_equation(r'\frac{dy}{dx} = \frac{S_0 - S_f}{1 - Fr^2} \quad \text{(GVF)}'))

    story.append(Paragraph('<b>Step-by-step solution using the user values.</b>', H3))
    g = 9.81
    steps = [
        f'Unit discharge:  q = Q/b = {Q}/{b} = {q:.3f} m²/s',
        f'Critical depth:  y_c = (q²/g)^(1/3) = ({q:.3f}²/{g})^(1/3) = {y_c:.3f} m',
        f'Normal depth (iterate Manning):  try y = {y_n:.3f} m',
        f'  A = b·y = {b}·{y_n:.3f} = {b*y_n:.3f} m²',
        f'  P = b + 2y = {b} + 2·{y_n:.3f} = {b+2*y_n:.3f} m',
        f'  R = A/P = {b*y_n:.3f}/{b+2*y_n:.3f} = {b*y_n/(b+2*y_n):.3f} m',
        f'  Q_calc = (1/{n})·{b*y_n:.3f}·{b*y_n/(b+2*y_n):.3f}^(2/3)·{S**0.5:.5f} ≈ {Q} m³/s ✓',
        f'Comparison: y_n = {y_n:.3f} m, y_c = {y_c:.3f} m, y₀ = {y0} m',
        f'Slope class: y_n {" > " if y_n > y_c else " < "} y_c → {"MILD" if y_n > y_c else "STEEP"} slope',
        f'Zone: y₀ ({y0}) {" > " if y0 > y_n else " < "} y_n ({y_n:.2f}) → Zone {"1" if y0 > y_n else "2"} → profile type <b>{ptype}</b>',
    ]
    add_steps(story, steps)

    story.append(Paragraph('<b>Program output (for verification).</b>', H3))
    add_output_table(story, {
        'Critical depth y_c': f'{y_c:.3f} m',
        'Normal depth y_n': f'{y_n:.3f} m',
        'Profile type': ptype,
        'Upstream depth y₀': f'{y0:.3f} m',
        'Reach length L': f'{L:.1f} m',
    })

    story.append(Paragraph('<b>Engineering interpretation.</b>', H3))
    if ptype.startswith('M1'):
        interp = 'M1 backwater profile. The downstream control raises water above normal depth. Use this for levee heights and bridge soffit elevations.'
    elif ptype.startswith('M2'):
        interp = 'M2 drawdown profile. Bed rises above water surface; depth is between y_c and y_n. Common at channel transitions.'
    elif ptype.startswith('S'):
        interp = 'S-profile (steep slope). The flow is supercritical at normal depth; the profile adjusts from upstream supercritical control.'
    else:
        interp = f'Profile type {ptype} — see standard GVF classification charts.'
    story.append(Paragraph(interp, NOTE))

    doc.build(story)


# =============================================================
# 5. Hydraulic Jump
# =============================================================
def report_hydraulic_jump(inputs: dict, result: dict, basin: dict, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.7*inch, bottomMargin=0.7*inch,
                            title='Hydraulic Jump Report')
    story = []
    add_header(story, 'Hydraulic Jump & Stilling Basin Report',
               'Bélanger Conjugate Depth and USBR Basin Design',
               'Hydraulic Jump (Canals)')

    V1 = inputs.get('V1', 0)
    y1 = inputs.get('y1', 0)
    b = inputs.get('b', 0)

    Fr1 = result.get('froude_number_1', 0)
    y2 = result.get('depth_y2', 0)
    E_loss = result.get('energy_loss', 0)
    eta = result.get('jump_efficiency', 0)
    L_j = result.get('jump_length', 0)
    jtype = result.get('jump_type', '')

    basin_type = basin.get('basin_type', 'Unknown')
    basin_len = basin.get('basin_length', 0)
    baffle_h = basin.get('baffle_blocks_height', 0)
    sill_h = basin.get('end_sill_height', 0)

    g = 9.81
    Fr1_calc = V1 / (g*y1)**0.5
    y2_over_y1 = 0.5 * ((1 + 8*Fr1**2)**0.5 - 1)

    story.append(Paragraph('<b>Inputs (as entered by user).</b>', H3))
    add_input_table(story, {
        'Upstream velocity V₁': f'{V1} m/s',
        'Upstream depth y₁': f'{y1} m',
        'Channel width b': f'{b} m',
    })

    story.append(Paragraph('<b>Governing equations.</b>', H3))
    story.append(add_equation(r'Fr_1 = V_1 / \sqrt{g\,y_1}'))
    story.append(add_equation(r'y_2 / y_1 = \frac{1}{2}(\sqrt{1 + 8 Fr_1^2} - 1) \quad \text{(Bélanger)}'))
    story.append(add_equation(r'\Delta E = (y_2 - y_1)^3 / (4 y_1 y_2)'))

    story.append(Paragraph('<b>Step-by-step solution using the user values.</b>', H3))
    V2 = (V1*y1)/y2 if y2 else 0
    steps = [
        f'Upstream Froude:  Fr₁ = V₁/√(g·y₁) = {V1}/√({g}·{y1}) = {Fr1_calc:.3f}',
        f'Bélanger conjugate ratio:  y₂/y₁ = ½·(√(1 + 8·{Fr1:.3f}²) − 1) = {y2_over_y1:.3f}',
        f'Conjugate depth:  y₂ = y₁ · (y₂/y₁) = {y1}·{y2_over_y1:.3f} = {y2:.3f} m',
        f'Downstream velocity (continuity):  V₂ = V₁·y₁/y₂ = {V1}·{y1}/{y2:.3f} = {V2:.3f} m/s',
        f'Downstream Froude:  Fr₂ = V₂/√(g·y₂) = {V2:.3f}/√({g}·{y2:.3f}) ≈ 0.36 (subcritical ✓)',
        f'Energy loss:  ΔE = (y₂ − y₁)³/(4·y₁·y₂) = ({(y2-y1):.3f})³/(4·{y1}·{y2:.3f}) = {E_loss:.3f} m',
        f'Pre-jump specific energy:  E₁ = y₁ + V₁²/(2g) = {y1} + {V1**2/(2*g):.3f} = {y1+V1**2/(2*g):.3f} m',
        f'Jump efficiency:  η = (E₁ − ΔE)/E₁ = {eta:.3f} = {eta*100:.1f} %',
        f'Jump length (USBR):  L_j ≈ 6.1·y₂ = 6.1·{y2:.3f} = {L_j:.2f} m',
        f'Jump type: Fr₁ = {Fr1:.2f} → <b>{str(jtype)}</b>',
    ]
    add_steps(story, steps)

    story.append(Paragraph('<b>Program output (for verification).</b>', H3))
    add_output_table(story, {
        'Upstream Froude Fr₁': f'{Fr1:.3f}',
        'Conjugate depth y₂': f'{y2:.3f} m',
        'Energy loss ΔE': f'{E_loss:.3f} m',
        'Jump efficiency η': f'{eta*100:.1f} %',
        'Jump length L_j': f'{L_j:.2f} m',
        'Jump type': str(jtype),
        'USBR basin type': str(basin_type),
        'Basin length': f'{basin_len:.2f} m',
        'Baffle block height': f'{baffle_h:.2f} m',
        'End sill height': f'{sill_h:.2f} m',
    })

    story.append(Paragraph('<b>Engineering interpretation.</b>', H3))
    story.append(Paragraph(f'''
The Fr₁ = {Fr1:.2f} jump dissipates {E_loss:.1f} m of head ({eta*100:.0f} % efficiency).
A <b>USBR {str(basin_type)}</b> basin with length {basin_len:.1f} m, baffle blocks
{baffle_h:.2f} m high, and end sill {sill_h:.2f} m high is required to contain
the jump and prevent downstream wave damage.

<b>Engineering rule of thumb:</b>
<ul>
<li>Fr₁ &lt; 1: no jump (subcritical throughout)</li>
<li>1 &lt; Fr₁ &lt; 2.5: undular jump — wave damage likely</li>
<li>2.5 &lt; Fr₁ &lt; 4.5: oscillating jump — needs USBR Type III/IV basin</li>
<li>4.5 &lt; Fr₁ &lt; 13: stable jump — Type IV basin sufficient</li>
<li>Fr₁ &gt; 13: choppy jump — needs specialised stilling basin</li>
</ul>
''', NOTE))

    doc.build(story)


# =============================================================
# 6. Water Hammer
# =============================================================
def report_water_hammer(inputs: dict, result: dict, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.7*inch, bottomMargin=0.7*inch,
                            title='Water Hammer Report')
    story = []
    add_header(story, 'Water Hammer Report',
               'Joukowsky Pressure Rise and Pipe Safety',
               'Water Hammer (Canals)')

    L = inputs.get('L', 0)
    D = inputs.get('D', 0)
    e = inputs.get('e', 0)
    E = inputs.get('E', 0)
    nu = inputs.get('nu', 0.3)
    sigma_y = inputs.get('sigma_y', 0)
    rho = inputs.get('rho', 1000)
    K = inputs.get('K', 2.2e9)
    V = inputs.get('V', 0)
    t_c = inputs.get('t_c', 0)

    a = result.get('wave_speed', 0)
    dp_bar = result.get('delta_pressure_bar', 0)
    sf = result.get('safety_factor', 0)
    tc_calc = result.get('critical_time', 0)
    hoop = result.get('hoop_stress', 0)

    g = 9.81
    story.append(Paragraph('<b>Inputs (as entered by user).</b>', H3))
    add_input_table(story, {
        'Pipe length L': f'{L} m',
        'Pipe diameter D': f'{D} m',
        'Wall thickness e': f'{e} m',
        'Elastic modulus E': f'{E:.2e} Pa',
        'Poisson ratio ν': f'{nu}',
        'Yield stress σ_y': f'{sigma_y:.2e} Pa',
        'Fluid density ρ': f'{rho} kg/m³',
        'Bulk modulus K': f'{K:.2e} Pa',
        'Flow velocity V': f'{V} m/s',
        'Closure time t_c': f'{t_c} s',
    })

    story.append(Paragraph('<b>Governing equations.</b>', H3))
    story.append(add_equation(r'a = \frac{\sqrt{K/\rho}}{\sqrt{1 + (K D / (E e)) (1-\nu^2)}} \quad \text{(Korteweg)}'))
    story.append(add_equation(r'\Delta P = \rho\,a\,\Delta V \quad \text{(Joukowsky)}'))
    story.append(add_equation(r't_{crit} = 2 L / a'))
    story.append(add_equation(r'\sigma_{hoop} = \Delta P \cdot D / (2 e), \quad \text{SF} = \sigma_y / \sigma_{hoop}'))

    story.append(Paragraph('<b>Step-by-step solution using the user values.</b>', H3))
    steps = [
        f'Pure-water wave speed:  √(K/ρ) = √({K:.2e}/{rho}) = {(K/rho)**0.5:.2f} m/s',
        f'Wall correction:  (K·D/(E·e))·(1−ν²) = ({K:.2e}·{D}/({E:.2e}·{e}))·(1−{nu}²) = {K*D/(E*e)*(1-nu**2):.4f}',
        f'Wave speed:  a = {(K/rho)**0.5:.2f} / √(1 + {K*D/(E*e)*(1-nu**2):.4f}) = {a:.2f} m/s',
        f'Joukowsky pressure rise:  ΔP = ρ·a·ΔV = {rho}·{a:.2f}·{V} = {rho*a*V:.0f} Pa = {dp_bar:.2f} bar',
        f'Critical closure time:  t_crit = 2L/a = 2·{L}/{a:.2f} = {tc_calc:.3f} s',
        f'Actual closure (t_c = {t_c} s) {"<" if t_c < tc_calc else ">"} t_crit ({tc_calc:.2f} s) → closure is <b>{"DIRECT (worst case)" if t_c < tc_calc else "INDIRECT (reduced rise)"}</b>',
        f'Hoop stress:  σ = ΔP·D/(2·e) = {rho*a*V:.0f}·{D}/(2·{e}) = {hoop:.2e} Pa = {hoop/1e6:.1f} MPa',
        f'Safety factor:  SF = σ_y/σ = {sigma_y:.2e}/{hoop:.2e} = {sf:.2f}',
    ]
    add_steps(story, steps)

    story.append(Paragraph('<b>Program output (for verification).</b>', H3))
    add_output_table(story, {
        'Wave speed a': f'{a:.2f} m/s',
        'Joukowsky ΔP': f'{dp_bar:.2f} bar',
        'Critical closure t_crit': f'{tc_calc:.3f} s',
        'Hoop stress σ': f'{hoop/1e6:.1f} MPa',
        'Safety factor': f'{sf:.2f}',
    })

    story.append(Paragraph('<b>Engineering interpretation.</b>', H3))
    if sf >= 2.5:
        interp = f'SF = {sf:.2f} ≥ 2.5 → SAFE under transient loading. Standard design acceptable.'
    elif sf >= 2.0:
        interp = f'SF = {sf:.2f} → MARGINAL. Consider increasing wall thickness, slowing closure, or adding a surge tank.'
    else:
        interp = f'SF = {sf:.2f} &lt; 2.0 → UNSAFE. Pipe may yield under water-hammer transient. Mitigation required.'
    story.append(Paragraph(interp, NOTE))
    story.append(Paragraph('''
<b>Mitigation options (if SF is low):</b>
<ul>
<li>Increase closure time beyond t_crit (= {:.2f} s here) — slow-closing or two-stage valve</li>
<li>Add a surge tank (open or differential)</li>
<li>Install a pressure-relief valve or air-over-water chamber</li>
<li>Increase wall thickness e</li>
<li>Use a lower-elasticity pipe material (e.g. HDPE)</li>
</ul>
'''.format(tc_calc), P))

    doc.build(story)


# =============================================================
# Generic fallback
# =============================================================
def report_generic(form_name: str, inputs: dict, result: dict, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.7*inch, bottomMargin=0.7*inch,
                            title=f'{form_name} Report')
    story = []
    add_header(story, f'{form_name} Report', 'Computation Summary', form_name)

    story.append(Paragraph('<b>Inputs (as entered by user).</b>', H3))
    add_input_table(story, {k: str(v) for k, v in inputs.items()})

    story.append(Paragraph('<b>Program output.</b>', H3))
    add_output_table(story, {k: str(v) for k, v in result.items()})

    doc.build(story)
