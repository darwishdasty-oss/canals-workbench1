"""
Earth Canal Design Form — Lacey, Kennedy, and Manning theories.

All inputs are free-form QLineEdits (no min/max constraints). The user
can enter any positive real number for Q, f, n, S, z.
"""
from __future__ import annotations
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from canals.earth_canal import EarthCanalDesigner

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea,
                                QWidget, QLabel, QComboBox)
from PySide6.QtCore import Qt
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from ._report_helper import ReportButton
from ._widgets import LabeledInput, SectionFrame, ResultTable


class EarthCanalForm(QtWidgets.QMdiSubWindow):
    """Earth canal design — Lacey + Kennedy + Manning + side-by-side comparison."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Earth Canal Design (Canals)")
        self.resize(1400, 900)
        self.designer = EarthCanalDesigner()
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
        note = QLabel("📝 All inputs are free-form. You can enter any value — no preset limits.")
        note.setStyleSheet("color: #1A3A6C; font-style: italic; padding: 4px; background: #E8F0F8; border-radius: 3px;")
        note.setWordWrap(True)
        left_layout.addWidget(note)

        # --- Discharge & soil inputs ---
        flow_section = SectionFrame("1. Flow & Soil Inputs")
        self.ec_Q = LabeledInput("Discharge (Q)", default=5.0, unit="m³/s",
                                  tooltip="Design discharge for the earth canal.")
        self.ec_Q.setValue(5.0)
        flow_section.addWidget(self.ec_Q)

        self.ec_f = LabeledInput("Lacey silt factor (f)", default=1.0, unit="",
                                  tooltip="Lacey's silt factor. Typical: 0.5-1.0 for fine silt, 1.0-1.5 for medium silt, 1.5-2.5 for coarse silt, 2.0+ for fine sand.")
        self.ec_f.setValue(1.0)
        flow_section.addWidget(self.ec_f)

        self.ec_n = LabeledInput("Manning's n", default=0.0225, unit="",
                                  tooltip="Manning's roughness coefficient for the canal. Typical: 0.018 (smooth earth), 0.0225 (ordinary earth), 0.030 (rough earth).")
        self.ec_n.setValue(0.0225)
        flow_section.addWidget(self.ec_n)

        self.ec_S = LabeledInput("Bed slope (S)", default=0.0004, unit="m/m",
                                  tooltip="Canal bed slope. Typical for irrigation canals: 0.0001 to 0.001.")
        self.ec_S.setValue(0.0004)
        flow_section.addWidget(self.ec_S)

        self.ec_z = LabeledInput("Side slope (z, H:V)", default=0.5, unit="",
                                  tooltip="Canal side slope as horizontal:vertical. Typical: 0.5 (stiff soil), 1.0 (medium), 1.5 (loose), 2.0 (very loose).")
        self.ec_z.setValue(0.5)
        flow_section.addWidget(self.ec_z)

        left_layout.addWidget(flow_section)

        # --- Soil type selector ---
        soil_section = SectionFrame("2. Soil Type (for comparison)")
        soil_lbl = QLabel("Soil type:")
        soil_lbl.setStyleSheet("font-weight: bold;")
        soil_section.addWidget(soil_lbl)
        self.ec_soil = QComboBox()
        self.ec_soil.addItems([
            "fine_silt", "medium_silt", "coarse_silt", "fine_sand", "medium_sand"
        ])
        self.ec_soil.setCurrentText("medium_silt")
        soil_section.addWidget(self.ec_soil)
        self.ec_soil.setToolTip("Affects the comprehensive side-by-side comparison.")

        left_layout.addWidget(soil_section)

        # --- Action buttons ---
        btn_section = SectionFrame("3. Run Analysis")
        self.btn_lacey = QPushButton("📐  Lacey Theory")
        self.btn_lacey.setStyleSheet("QPushButton { background: #1A3A6C; color: white; padding: 8px; font-weight: bold; } QPushButton:hover { background: #2A5A8C; }")
        self.btn_lacey.clicked.connect(self._on_lacey)
        btn_section.addWidget(self.btn_lacey)

        self.btn_kennedy = QPushButton("📐  Kennedy Theory (CVR)")
        self.btn_kennedy.setStyleSheet("QPushButton { background: #4A6FA5; color: white; padding: 8px; } QPushButton:hover { background: #5A7FB5; }")
        self.btn_kennedy.clicked.connect(self._on_kennedy)
        btn_section.addWidget(self.btn_kennedy)

        self.btn_manning = QPushButton("📐  Manning Theory")
        self.btn_manning.setStyleSheet("QPushButton { background: #6A8FC5; color: white; padding: 8px; } QPushButton:hover { background: #7A9FD5; }")
        self.btn_manning.clicked.connect(self._on_manning)
        btn_section.addWidget(self.btn_manning)

        self.btn_compare = QPushButton("📊  Side-by-Side Comparison")
        self.btn_compare.setStyleSheet("QPushButton { background: #1A6B2A; color: white; padding: 8px; font-weight: bold; } QPushButton:hover { background: #2A7B3A; }")
        self.btn_compare.clicked.connect(self._on_compare)
        btn_section.addWidget(self.btn_compare)

        self.btn_clear = QPushButton("🗑  Clear Results")
        self.btn_clear.setStyleSheet("QPushButton { padding: 6px; }")
        self.btn_clear.clicked.connect(self._on_clear)
        btn_section.addWidget(self.btn_clear)

        self.btn_report = ReportButton(form_name='earth_canal_manning')
        btn_section.addWidget(self.btn_report)

        left_layout.addWidget(btn_section)
        left_layout.addStretch(1)
        left.setLayout(left_layout)
        left_scroll.setWidget(left)
        root_layout.addWidget(left_scroll)

        # === RIGHT: results + chart ===
        right_splitter = QtWidgets.QSplitter(Qt.Vertical)
        right_splitter.setSizes([500, 400])

        self.result_table = ResultTable()
        right_splitter.addWidget(self.result_table)

        self.fig = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(self.fig)
        right_splitter.addWidget(self.canvas)

        root_layout.addWidget(right_splitter, 1)

    # ----------------------------------------------------------------- Buttons
    def _on_lacey(self):
        try:
            Q = self.ec_Q.value()
            f = self.ec_f.value()
            z = self.ec_z.value()
            res = self.designer.lacey_theory_design(Q, f, z)
            self.result_table.populate(res)
            self._plot_section(z, res.get('depth', 2.0), res.get('bottom_width', 1.5),
                               f"Lacey: Q={Q} m³/s, f={f}")
            self.btn_report.form_name = 'earth_canal_lacey'
            self.btn_report.set_result(
                inputs={'Q': Q, 'f': f, 'side_slope': z},
                result=dict(res)
            )
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Lacey Theory", f"{e}\n\n{traceback.format_exc()}")

    def _on_kennedy(self):
        try:
            Q = self.ec_Q.value()
            n = self.ec_n.value()
            S = self.ec_S.value()
            res = self.designer.kennedy_theory_design(Q, n, S)
            self.result_table.populate(res)
            self._plot_section(res.get('side_slope', 0.5), res.get('depth', 2.0),
                               res.get('bottom_width', 1.5),
                               f"Kennedy: Q={Q} m³/s, n={n}, S={S}")
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Kennedy Theory", f"{e}\n\n{traceback.format_exc()}")

    def _on_manning(self):
        try:
            Q = self.ec_Q.value()
            n = self.ec_n.value()
            S = self.ec_S.value()
            z = self.ec_z.value()
            res = self.designer.manning_design(Q, n, S, z)
            self.result_table.populate(res)
            self._plot_section(z, res.get('depth', 2.0), res.get('bottom_width', 1.5),
                               f"Manning: Q={Q} m³/s, n={n}, S={S}")
            self.btn_report.form_name = 'earth_canal_manning'
            self.btn_report.set_result(
                inputs={'Q': Q, 'n': n, 'S': S, 'side_slope': z},
                result=dict(res)
            )
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Manning Theory", f"{e}\n\n{traceback.format_exc()}")

    def _on_compare(self):
        try:
            Q = self.ec_Q.value()
            f = self.ec_f.value()
            n = self.ec_n.value()
            S = self.ec_S.value()
            soil = self.ec_soil.currentText()
            z = self.ec_z.value()
            res = self.designer.comprehensive_analysis(Q, soil, f, n, S, z)
            self.result_table.populate(res)
            self._plot_comparison(res)
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Side-by-Side Comparison", f"{e}\n\n{traceback.format_exc()}")

    def _on_clear(self):
        self.result_table.setRowCount(0)
        self.fig.clear()
        self.canvas.draw()

    # ----------------------------------------------------------------- Charts
    def _plot_section(self, z, y, b, title):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        try:
            ax.plot([-z * y, 0, b, b + z * y], [y, 0, 0, y], 'b-', lw=2)
            ax.fill([-z * y, 0, b, b + z * y], [y, 0, 0, y], color='lightblue', alpha=0.4)
            ax.set_title(f"{title}\nz={z}, y={y:.2f} m, b={b:.2f} m")
        except Exception as e:
            ax.text(0.5, 0.5, f"Plot error: {e}", ha='center', va='center', transform=ax.transAxes)
        ax.set_aspect('equal')
        ax.grid(alpha=0.3)
        self.canvas.draw()

    def _plot_comparison(self, res):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        try:
            theories = []
            depths = []
            widths = []
            for theory_name in ['lacey', 'kennedy', 'manning']:
                if theory_name in res:
                    t = res[theory_name]
                    if isinstance(t, dict):
                        theories.append(theory_name.capitalize())
                        depths.append(t.get('depth', 0))
                        widths.append(t.get('bottom_width', 0))
            if theories:
                x = np.arange(len(theories))
                width = 0.35
                ax.bar(x - width/2, depths, width, label='Depth y (m)', color='steelblue')
                ax.bar(x + width/2, widths, width, label='Bottom width b (m)', color='coral')
                ax.set_xticks(x)
                ax.set_xticklabels(theories)
                ax.set_ylabel('Dimension (m)')
                ax.set_title('Side-by-Side Comparison: Lacey vs Kennedy vs Manning')
                ax.legend()
                ax.grid(alpha=0.3, axis='y')
        except Exception as e:
            ax.text(0.5, 0.5, f"Plot error: {e}", ha='center', va='center', transform=ax.transAxes)
        self.canvas.draw()
