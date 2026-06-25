"""
Open Channel Design Form — MDI sub-window wrapping canals.open_channel.

User-fillable, no min/max limits on any input. The user can enter ANY
positive real number for Q, n, S, b, z, D, y, L. The form validates
inputs but never silently caps them.

Provides:
  - Channel type selection (trapezoidal/rectangular/triangular/circular)
  - All numeric inputs as free-form fields with engineering hints
  - Output: optimal section design, GVF profile, comprehensive analysis
  - Inline matplotlib chart for the section
"""
from __future__ import annotations
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
import numpy as np

# Make canals sub-package importable
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from canals.open_channel import (
    AdvancedChannelDesigner, ChannelType, ChannelGeometry, HydraulicTheories
)

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton,
                                QTextEdit, QSplitter, QScrollArea, QWidget, QLabel)
from PySide6.QtCore import Qt
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ._widgets import LabeledInput, ChannelTypeSelector, ResultTable, SectionFrame


class OpenChannelForm(QtWidgets.QMdiSubWindow):
    """Open Channel hydraulic design — fully user-fillable inputs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open Channel Design (Canals)")
        self.resize(1400, 900)
        self.designer = AdvancedChannelDesigner()
        self.theories = HydraulicTheories()
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

        # --- Channel geometry ---
        geom_section = SectionFrame("1. Channel Geometry")
        self.chan_type = ChannelTypeSelector()
        geom_section.addWidget(self.chan_type)

        self.inp_b = LabeledInput("Bottom width (b)", default=3.0, unit="m",
                                   tooltip="Bottom width of the channel. For rectangular channels, this is the channel width. For trapezoidal, this is the bottom width.")
        self.inp_b.setValue(3.0)
        geom_section.addWidget(self.inp_b)

        self.inp_z = LabeledInput("Side slope (z, H:V)", default=1.5, unit="",
                                   tooltip="Side slope as horizontal:vertical. e.g. z=1.5 means 1.5H:1V. z=0 = rectangular. Used for trapezoidal and triangular channels.")
        self.inp_z.setValue(1.5)
        geom_section.addWidget(self.inp_z)

        self.inp_D = LabeledInput("Diameter (D, circular only)", default=2.0, unit="m",
                                   tooltip="Diameter of the circular cross-section. Only used when channel type is 'circular'.")
        self.inp_D.setValue(2.0)
        geom_section.addWidget(self.inp_D)

        left_layout.addWidget(geom_section)

        # --- Flow inputs ---
        flow_section = SectionFrame("2. Flow Conditions")
        self.inp_Q = LabeledInput("Discharge (Q)", default=10.0, unit="m³/s",
                                   tooltip="Design discharge. Enter any positive value — no limit.")
        self.inp_Q.setValue(10.0)
        flow_section.addWidget(self.inp_Q)

        self.inp_n = LabeledInput("Manning's n (roughness)", default=0.013, unit="",
                                   tooltip="Manning's roughness coefficient. Typical values: 0.010 (smooth concrete), 0.013 (concrete), 0.025 (earth), 0.040 (rough earth).")
        self.inp_n.setValue(0.013)
        flow_section.addWidget(self.inp_n)

        self.inp_S = LabeledInput("Bed slope (S)", default=0.001, unit="m/m",
                                   tooltip="Channel bed slope. Enter any positive value. S=0.001 = 1 m drop per 1000 m.")
        self.inp_S.setValue(0.001)
        flow_section.addWidget(self.inp_S)

        left_layout.addWidget(flow_section)

        # --- GVF inputs (optional) ---
        gvf_section = SectionFrame("3. GVF Profile Inputs (optional)")
        self.inp_y_start = LabeledInput("Initial depth (y_start)", default=2.0, unit="m",
                                        tooltip="Starting depth for the gradually-varied flow computation. Leave default if you don't run GVF.")
        self.inp_y_start.setValue(2.0)
        gvf_section.addWidget(self.inp_y_start)

        self.inp_L_gvf = LabeledInput("Reach length (L)", default=500.0, unit="m",
                                       tooltip="Reach length for the GVF profile computation.")
        self.inp_L_gvf.setValue(500.0)
        gvf_section.addWidget(self.inp_L_gvf)

        left_layout.addWidget(gvf_section)

        # --- Action buttons ---
        btn_section = SectionFrame("4. Run Analysis")
        self.btn_optimal = QPushButton("🔧  Optimal Section Design")
        self.btn_optimal.setStyleSheet("QPushButton { background: #1A3A6C; color: white; padding: 8px; font-weight: bold; } QPushButton:hover { background: #2A5A8C; }")
        self.btn_optimal.clicked.connect(self._on_optimal)
        btn_section.addWidget(self.btn_optimal)

        self.btn_gvf = QPushButton("📈  GVF Profile (backwater M1)")
        self.btn_gvf.setStyleSheet("QPushButton { background: #4A6FA5; color: white; padding: 8px; } QPushButton:hover { background: #5A7FB5; }")
        self.btn_gvf.clicked.connect(self._on_gvf)
        btn_section.addWidget(self.btn_gvf)

        self.btn_comprehensive = QPushButton("📊  Comprehensive Analysis")
        self.btn_comprehensive.setStyleSheet("QPushButton { background: #6A8FC5; color: white; padding: 8px; } QPushButton:hover { background: #7A9FD5; }")
        self.btn_comprehensive.clicked.connect(self._on_comprehensive)
        btn_section.addWidget(self.btn_comprehensive)

        self.btn_clear = QPushButton("🗑  Clear Results")
        self.btn_clear.setStyleSheet("QPushButton { padding: 6px; }")
        self.btn_clear.clicked.connect(self._on_clear)
        btn_section.addWidget(self.btn_clear)

        left_layout.addWidget(btn_section)
        left_layout.addStretch(1)
        left.setLayout(left_layout)
        left_scroll.setWidget(left)
        root_layout.addWidget(left_scroll)

        # === RIGHT: results + chart ===
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setSizes([500, 400])

        # Result table
        self.result_table = ResultTable()
        right_splitter.addWidget(self.result_table)

        # Matplotlib chart
        self.fig = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(self.fig)
        right_splitter.addWidget(self.canvas)

        root_layout.addWidget(right_splitter, 1)

    # ------------------------------------------------------------------ Inputs
    def _build_geometry(self) -> ChannelGeometry:
        ctype = self.chan_type.value()
        b = self.inp_b.value()
        z = self.inp_z.value()
        D = self.inp_D.value()
        if ctype == "trapezoidal":
            return ChannelGeometry(channel_type=ChannelType.TRAPEZOIDAL, bottom_width=b, side_slope=z)
        elif ctype == "rectangular":
            return ChannelGeometry(channel_type=ChannelType.RECTANGULAR, bottom_width=b, side_slope=0.0)
        elif ctype == "triangular":
            return ChannelGeometry(channel_type=ChannelType.TRIANGULAR, bottom_width=0.0, side_slope=z)
        elif ctype == "circular":
            return ChannelGeometry(channel_type=ChannelType.CIRCULAR, diameter=D)
        return ChannelGeometry(channel_type=ChannelType.TRAPEZOIDAL, bottom_width=b, side_slope=z)

    # ----------------------------------------------------------------- Buttons
    def _on_optimal(self):
        try:
            Q = self.inp_Q.value()
            n = self.inp_n.value()
            S = self.inp_S.value()
            ctype = self.chan_type.value()
            ctype_enum = {
                "trapezoidal": ChannelType.TRAPEZOIDAL,
                "rectangular": ChannelType.RECTANGULAR,
                "triangular": ChannelType.TRIANGULAR,
                "circular": ChannelType.CIRCULAR,
            }[ctype]
            res = self.designer.design_optimal_section(Q, n, S, channel_type=ctype_enum)
            self.result_table.populate(res)
            self._plot_section(res)
        except Exception as e:
            import traceback
            self._show_error("Optimal Section Design", e, traceback.format_exc())

    def _on_gvf(self):
        try:
            geom = self._build_geometry()
            Q = self.inp_Q.value()
            n = self.inp_n.value()
            S = self.inp_S.value()
            y_start = self.inp_y_start.value()
            L = self.inp_L_gvf.value()
            res = self.designer.gradually_varied_flow(geom, Q, n, S, y_start, L, n_points=100)
            self.result_table.populate(res)
            self._plot_gvf(res)
        except Exception as e:
            import traceback
            self._show_error("GVF Profile", e, traceback.format_exc())

    def _on_comprehensive(self):
        try:
            geom = self._build_geometry()
            Q = self.inp_Q.value()
            n = self.inp_n.value()
            S = self.inp_S.value()
            res = self.designer.comprehensive_flow_analysis(geom, Q, n, S)
            self.result_table.populate(res)
        except Exception as e:
            import traceback
            self._show_error("Comprehensive Analysis", e, traceback.format_exc())

    def _on_clear(self):
        self.result_table.setRowCount(0)
        self.fig.clear()
        self.canvas.draw()

    def _show_error(self, title, exc, tb):
        QtWidgets.QMessageBox.critical(self, f"Error in {title}",
            f"<b>{type(exc).__name__}:</b> {exc}<br><br>"
            f"<pre style='font-size: 9pt'>{tb}</pre>")

    # ----------------------------------------------------------------- Charts
    def _plot_section(self, res):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        try:
            b = res.get('bottom_width', self.inp_b.value())
            z = res.get('side_slope', self.inp_z.value())
            y = res.get('depth', 1.0)
            D = res.get('diameter', self.inp_D.value())
            ctype = self.chan_type.value()
            if ctype == "trapezoidal":
                ax.plot([-z * y, 0], [y, 0], 'b-', lw=2)
                ax.plot([0, b], [0, 0], 'b-', lw=2)
                ax.plot([b, b + z * y], [0, y], 'b-', lw=2)
                ax.fill([-z * y, 0, b, b + z * y], [y, 0, 0, y], color='lightblue', alpha=0.4)
                ax.set_title(f"Optimal trapezoidal: b={b:.2f} m, z={z}, y={y:.2f} m")
            elif ctype == "rectangular":
                ax.plot([0, b, b, 0, 0], [0, 0, y, y, 0], 'b-', lw=2)
                ax.fill([0, b, b, 0], [0, 0, y, y], color='lightblue', alpha=0.4)
                ax.set_title(f"Optimal rectangular: b={b:.2f} m, y={y:.2f} m")
            elif ctype == "triangular":
                ax.plot([-z * y, 0, z * y, -z * y], [y, 0, y, y], 'b-', lw=2)
                ax.fill([-z * y, 0, z * y], [y, 0, y], color='lightblue', alpha=0.4)
                ax.set_title(f"Optimal triangular: z={z}, y={y:.2f} m")
            elif ctype == "circular":
                theta = np.linspace(0, 2 * np.pi, 100)
                ax.plot(D / 2 * np.cos(theta), D / 2 * np.sin(theta), 'b-', lw=2)
                ax.fill(D / 2 * np.cos(theta), D / 2 * np.sin(theta), color='lightblue', alpha=0.4)
                ax.set_title(f"Optimal circular: D={D:.2f} m")
        except Exception as e:
            ax.text(0.5, 0.5, f"Plot error: {e}", ha='center', va='center', transform=ax.transAxes)
        ax.set_aspect('equal')
        ax.grid(alpha=0.3)
        self.canvas.draw()

    def _plot_gvf(self, res):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        try:
            if 'x' in res and 'y' in res:
                ax.plot(res['x'], res['y'], 'b-', lw=2)
                ax.fill_between(res['x'], res['y'], alpha=0.2, color='blue')
                ax.set_xlabel("x (m)", fontsize=10)
                ax.set_ylabel("y (m)", fontsize=10)
                ax.set_title("Gradually Varied Flow (GVF) — backwater profile M1", fontsize=10)
                ax.grid(alpha=0.3)
            else:
                keys = list(res.keys())
                ax.text(0.5, 0.5, f"GVF result keys:\n{keys}", ha='center', va='center', transform=ax.transAxes, wrap=True)
        except Exception as e:
            ax.text(0.5, 0.5, f"Plot error: {e}", ha='center', va='center', transform=ax.transAxes)
        self.canvas.draw()
