"""
Flow Profile Form — Open channel water surface profile analyzer.

Wraps the canals.flow_profile.OpenChannelFlow class (ported from the
user-supplied 24bf5a42__341431d8-3b25-4274-b9e0-488cf6e4e088.py).
The original was a console-based interactive analyzer; this form
replaces the input() prompts with Qt input fields, the print() with a
result table, and the plt.show() with an embedded matplotlib canvas.

Algorithms:
  - critical_depth via bisect on Fr=1
  - normal_depth via bisect on Manning Q
  - water_surface_profile via scipy.integrate.solve_ivp (RK45)
  - flow classification (subcritical / supercritical / critical; M1, M2, M3, S1, S2, S3, C1, C3)
  - Froude number, area, wetted perimeter, hydraulic radius, top width
"""
from __future__ import annotations
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from canals.flow_profile import OpenChannelFlow

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea,
                                QWidget, QLabel)
from PySide6.QtCore import Qt
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ._report_helper import ReportButton
from ._widgets import LabeledInput, ChannelTypeSelector, SectionFrame, ResultTable


class FlowProfileForm(QtWidgets.QMdiSubWindow):
    """Open-channel water surface profile analyzer — fully user-fillable inputs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Flow Profile Analyzer (Canals)")
        self.resize(1500, 950)
        self.channel = OpenChannelFlow()
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setWidget(central)
        root_layout = QHBoxLayout(central)

        # === LEFT: scrollable input panel ===
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMaximumWidth(440)
        left_scroll.setMinimumWidth(380)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        # Header note
        note = QLabel("📝 All inputs are free-form. You can enter any value — no preset limits.\n"
                      "Computes critical depth, normal depth, water surface profile,\n"
                      "Froude number, and flow classification (M1, M2, M3, S1-S3, C1, C3).")
        note.setStyleSheet("color: #1A3A6C; font-style: italic; padding: 6px; background: #E8F0F8; border-radius: 3px;")
        note.setWordWrap(True)
        left_layout.addWidget(note)

        # --- Channel geometry ---
        geom_section = SectionFrame("1. Channel Geometry")
        type_lbl = QLabel("Channel type:")
        type_lbl.setStyleSheet("font-weight: bold;")
        geom_section.addWidget(type_lbl)
        self.cbo_type = QtWidgets.QComboBox()
        self.cbo_type.addItems(["rectangular", "triangular", "trapezoidal"])
        geom_section.addWidget(self.cbo_type)
        self.cbo_type.currentTextChanged.connect(self._on_type_changed)

        self.inp_b = LabeledInput("Bottom width (b)", default=5.0, unit="m",
                                   tooltip="Bottom width for rectangular/trapezoidal channels. For triangular, set to 0.")
        self.inp_b.setValue(5.0)
        geom_section.addWidget(self.inp_b)

        self.inp_z = LabeledInput("Side slope (z, H:V)", default=0.0, unit="",
                                   tooltip="Side slope as horizontal:vertical. z=0 for rectangular.")
        self.inp_z.setValue(0.0)
        geom_section.addWidget(self.inp_z)

        left_layout.addWidget(geom_section)

        # --- Flow inputs ---
        flow_section = SectionFrame("2. Flow Conditions")
        self.inp_Q = LabeledInput("Discharge (Q)", default=10.0, unit="m³/s",
                                   tooltip="Design discharge. Enter any positive value.")
        self.inp_Q.setValue(10.0)
        flow_section.addWidget(self.inp_Q)

        self.inp_S = LabeledInput("Bed slope (S₀)", default=0.001, unit="m/m",
                                   tooltip="Channel bed slope. S=0 = horizontal (no normal depth).")
        self.inp_S.setValue(0.001)
        flow_section.addWidget(self.inp_S)

        self.inp_n = LabeledInput("Manning's n", default=0.015, unit="",
                                   tooltip="Manning's roughness coefficient. 0.013=concrete, 0.025=earth, etc.")
        self.inp_n.setValue(0.015)
        flow_section.addWidget(self.inp_n)

        self.inp_y_init = LabeledInput("Initial depth (y₀)", default=2.0, unit="m",
                                       tooltip="Water depth at x=0 (start of channel).")
        self.inp_y_init.setValue(2.0)
        flow_section.addWidget(self.inp_y_init)

        self.inp_L = LabeledInput("Channel length (L)", default=1000.0, unit="m",
                                   tooltip="Total reach length for the water surface profile.")
        self.inp_L.setValue(1000.0)
        flow_section.addWidget(self.inp_L)

        left_layout.addWidget(flow_section)

        # --- Solver controls ---
        solver_section = SectionFrame("3. Solver")
        self.inp_n_points = LabeledInput("Output points", default=500, unit="",
                                         tooltip="Number of points to compute along the profile (more = smoother).")
        self.inp_n_points.setValue(500)
        solver_section.addWidget(self.inp_n_points)

        left_layout.addWidget(solver_section)

        # --- Action buttons ---
        btn_section = SectionFrame("4. Run Analysis")
        self.btn_run = QPushButton("▶  Run Full Analysis")
        self.btn_run.setStyleSheet("QPushButton { background: #1A3A6C; color: white; padding: 10px; font-weight: bold; font-size: 11pt; } QPushButton:hover { background: #2A5A8C; }")
        self.btn_run.clicked.connect(self._on_run)
        btn_section.addWidget(self.btn_run)

        self.btn_critical = QPushButton("📐  Critical Depth Only")
        self.btn_critical.setStyleSheet("QPushButton { background: #4A6FA5; color: white; padding: 6px; } QPushButton:hover { background: #5A7FB5; }")
        self.btn_critical.clicked.connect(self._on_critical_only)
        btn_section.addWidget(self.btn_critical)

        self.btn_normal = QPushButton("📐  Normal Depth Only")
        self.btn_normal.setStyleSheet("QPushButton { background: #4A6FA5; color: white; padding: 6px; } QPushButton:hover { background: #5A7FB5; }")
        self.btn_normal.clicked.connect(self._on_normal_only)
        btn_section.addWidget(self.btn_normal)

        self.btn_clear = QPushButton("🗑  Clear Results")
        self.btn_clear.setStyleSheet("QPushButton { padding: 6px; }")
        self.btn_clear.clicked.connect(self._on_clear)
        btn_section.addWidget(self.btn_clear)

        self.btn_report = ReportButton(form_name='flow_profile')
        btn_section.addWidget(self.btn_report)

        left_layout.addWidget(btn_section)
        left_layout.addStretch(1)
        left.setLayout(left_layout)
        left_scroll.setWidget(left)
        root_layout.addWidget(left_scroll)

        # === RIGHT: results + chart ===
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setSizes([400, 500])

        self.result_table = ResultTable()
        right_splitter.addWidget(self.result_table)

        self.fig = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.fig)
        right_splitter.addWidget(self.canvas)

        root_layout.addWidget(right_splitter, 1)

    # ----------------------------------------------------------------- Wiring
    def _on_type_changed(self, t: str) -> None:
        if t == "triangular":
            self.inp_b.setValue(0.0)
            self.inp_z.setValue(1.0)
        elif t == "rectangular":
            self.inp_b.setValue(5.0)
            self.inp_z.setValue(0.0)
        else:  # trapezoidal
            self.inp_b.setValue(3.0)
            self.inp_z.setValue(1.5)

    def _load_into_channel(self) -> bool:
        """Load the form values into the OpenChannelFlow object."""
        ctype = self.cbo_type.currentText()
        b = self.inp_b.value()
        z = self.inp_z.value()
        if ctype == "rectangular":
            if b <= 0:
                QtWidgets.QMessageBox.warning(self, "Invalid input", "Bottom width must be > 0 for rectangular channel.")
                return False
            self.channel.channel_type = "rectangular"
            self.channel.channel_params = {"b": b, "z": 0.0}
        elif ctype == "triangular":
            if z <= 0:
                QtWidgets.QMessageBox.warning(self, "Invalid input", "Side slope must be > 0 for triangular channel.")
                return False
            self.channel.channel_type = "triangular"
            self.channel.channel_params = {"b": 0.0, "z": z}
        else:  # trapezoidal
            if b <= 0 or z <= 0:
                QtWidgets.QMessageBox.warning(self, "Invalid input", "Both b and z must be > 0 for trapezoidal channel.")
                return False
            self.channel.channel_type = "trapezoidal"
            self.channel.channel_params = {"b": b, "z": z}
        self.channel.flow_params = {
            "Q": self.inp_Q.value(),
            "S0": self.inp_S.value(),
            "n": self.inp_n.value(),
            "y_initial": self.inp_y_init.value(),
            "L": self.inp_L.value(),
        }
        return True

    # ----------------------------------------------------------------- Buttons
    def _on_run(self):
        try:
            if not self._load_into_channel():
                return
            yc = self.channel.calculate_critical_depth()
            yn = self.channel.calculate_normal_depth()
            n_pts = int(self.inp_n_points.value())
            # Force the channel's solver to use n_points
            original = self.channel.calculate_water_surface_profile
            def _with_n():
                import numpy as np
                y0 = self.channel.flow_params["y_initial"]
                L = self.channel.flow_params["L"]
                x_pts = np.linspace(0, L, n_pts)
                from scipy.integrate import solve_ivp
                sol = solve_ivp(
                    self.channel.water_surface_profile_equation,
                    [0, L], [y0], t_eval=x_pts, method="RK45", rtol=1e-8, atol=1e-10,
                )
                if sol.success:
                    return sol.t, sol.y[0]
                return None, None
            x, y = _with_n()
            if x is None or y is None:
                QtWidgets.QMessageBox.warning(self, "Solver failed",
                    "The water surface profile solver did not converge. Try a different initial depth or bed slope.")
                return

            # Build the results
            results = {
                "channel_type": self.channel.channel_type,
                "channel_params": self.channel.channel_params,
                "flow_params": self.channel.flow_params,
                "critical_depth_yc_m": yc,
                "normal_depth_yn_m": yn if yn and yn != float('inf') else "N/A (horizontal/adverse slope)",
                "profile_n_points": len(x),
                "y_start_m": float(y[0]),
                "y_end_m": float(y[-1]),
                "regime_at_start": self.channel.classify_flow(y[0], yc, yn)[0],
                "curve_at_start": self.channel.classify_flow(y[0], yc, yn)[1],
                "regime_at_end": self.channel.classify_flow(y[-1], yc, yn)[0],
                "curve_at_end": self.channel.classify_flow(y[-1], yc, yn)[1],
                "Froude_at_start": self.channel.calculate_froude_number(y[0]),
                "Froude_at_end": self.channel.calculate_froude_number(y[-1]),
            }
            self.result_table.populate(results)
            self._plot_profile(x, y, yc, yn)
            self.btn_report.set_result(
                inputs={'Q': self.channel.flow_params["Q"],
                        'b': self.channel.channel_params.get('b', 0),
                        'S': self.channel.flow_params.get('S0', 0),
                        'n': self.channel.flow_params['n'],
                        'L': self.channel.flow_params["L"],
                        'y_upstream': self.channel.flow_params["y_initial"]},
                result={'critical_depth': yc,
                        'normal_depth': yn if yn and yn != float('inf') else 0,
                        'profile_type': results["curve_at_start"]}
            )
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Flow Profile", f"{e}\n\n{traceback.format_exc()}")

    def _on_critical_only(self):
        try:
            if not self._load_into_channel():
                return
            yc = self.channel.calculate_critical_depth()
            A = self.channel.calculate_area(yc)
            T = self.channel.calculate_top_width(yc)
            Fr = self.channel.calculate_froude_number(yc)
            results = {
                "critical_depth_yc_m": yc,
                "area_at_yc_m2": A,
                "top_width_at_yc_m": T,
                "hydraulic_radius_at_yc_m": self.channel.calculate_hydraulic_radius(yc),
                "Froude_at_yc": Fr,
                "V_at_yc_mps": self.channel.flow_params["Q"] / A,
            }
            self.result_table.populate(results)
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Critical Depth", f"{e}\n\n{traceback.format_exc()}")

    def _on_normal_only(self):
        try:
            if not self._load_into_channel():
                return
            yn = self.channel.calculate_normal_depth()
            if yn is None or yn == float('inf'):
                results = {"normal_depth_yn_m": "N/A (S₀=0 = horizontal, no normal depth)"}
            else:
                A = self.channel.calculate_area(yn)
                T = self.channel.calculate_top_width(yn)
                Fr = self.channel.calculate_froude_number(yn)
                results = {
                    "normal_depth_yn_m": yn,
                    "area_at_yn_m2": A,
                    "top_width_at_yn_m": T,
                    "hydraulic_radius_at_yn_m": self.channel.calculate_hydraulic_radius(yn),
                    "Froude_at_yn": Fr,
                    "V_at_yn_mps": self.channel.flow_params["Q"] / A,
                }
            self.result_table.populate(results)
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Normal Depth", f"{e}\n\n{traceback.format_exc()}")

    def _on_clear(self):
        self.result_table.setRowCount(0)
        self.fig.clear()
        self.canvas.draw()

    # ----------------------------------------------------------------- Charts
    def _plot_profile(self, x, y, yc, yn):
        self.fig.clear()

        # Top panel: water surface profile
        ax1 = self.fig.add_subplot(211)
        ax1.plot(x, y, 'b-', lw=2, label='Water surface y(x)')
        if yc is not None:
            ax1.axhline(y=yc, color='r', ls='--', lw=1.5, label=f'Critical depth yc = {yc:.3f} m')
        if yn is not None and yn != float('inf'):
            ax1.axhline(y=yn, color='g', ls=':', lw=1.5, label=f'Normal depth yn = {yn:.3f} m')

        # Color zones
        if yc is not None and yn is not None and yn != float('inf'):
            ax1.fill_between(x, 0, y, where=(y > yn), color='lightblue', alpha=0.2, label='Zone 1 (M1)')
            ax1.fill_between(x, 0, y, where=((y > yc) & (y <= yn)), color='lightgreen', alpha=0.2, label='Zone 2 (M2)')

        ax1.set_xlabel("x (m)", fontsize=10)
        ax1.set_ylabel("Depth y (m)", fontsize=10)
        ax1.set_title("Water Surface Profile", fontsize=11, fontweight='bold')
        ax1.legend(loc='best', fontsize=8)
        ax1.grid(alpha=0.3)

        # Bottom panel: Froude number
        ax2 = self.fig.add_subplot(212)
        Fr = np.array([self.channel.calculate_froude_number(yi) for yi in y])
        ax2.plot(x, Fr, 'r-', lw=2, label='Froude number')
        ax2.axhline(y=1, color='k', ls='--', lw=1, label='Fr = 1 (critical)')
        ax2.fill_between(x, Fr, 1, where=(Fr > 1), color='red', alpha=0.2, label='Supercritical')
        ax2.fill_between(x, Fr, 1, where=(Fr < 1), color='blue', alpha=0.2, label='Subcritical')
        ax2.set_xlabel("x (m)", fontsize=10)
        ax2.set_ylabel("Froude number", fontsize=10)
        ax2.set_title("Froude Number Distribution", fontsize=11, fontweight='bold')
        ax2.legend(loc='best', fontsize=8)
        ax2.grid(alpha=0.3)

        self.fig.tight_layout()
        self.canvas.draw()


from PySide6.QtWidgets import QSplitter
