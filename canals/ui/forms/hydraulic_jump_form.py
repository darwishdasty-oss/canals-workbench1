"""
Hydraulic Jump Form — MDI sub-window wrapping canals.hydraulic_jump.

The user enters pre-jump conditions (V₁, y₁, b, slope, n, soil). The form
computes:
  - Froude number Fr1
  - Jump type (undular, weak, oscillating, steady, strong)
  - Conjugate depth y2 (Bélanger)
  - Energy loss ΔE and % loss
  - Jump length L_j
  - Recommended USBR stilling basin type (I, II, III, IV, or sloped)
  - Basin dimensions (length, width, depth)
  - Appurtenance heights (chute blocks, baffle blocks, end sill)

All inputs are free-form with no min/max constraints.
"""
from __future__ import annotations
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from canals.hydraulic_jump import (
    JumpType, BasinType, HydraulicJumpInput, HydraulicJumpResults,
    StillingBasinDesign, HydraulicJumpAnalyzer
)

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea,
                                QWidget, QLabel, QSplitter)
from PySide6.QtCore import Qt
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ._report_helper import ReportButton
from ._widgets import LabeledInput, SectionFrame, ResultTable


class HydraulicJumpForm(QtWidgets.QMdiSubWindow):
    """Hydraulic jump analyzer + USBR stilling basin designer — user-fillable inputs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hydraulic Jump Analyzer (Canals)")
        self.resize(1500, 950)
        self.analyzer = HydraulicJumpAnalyzer()
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
                      "Computes Froude number, jump type (undular/weak/oscillating/steady/strong),\n"
                      "conjugate depth (Bélanger), energy loss, jump length,\n"
                      "and USBR stilling basin design (Types I–IV, sloped).")
        note.setStyleSheet("color: #1A3A6C; font-style: italic; padding: 6px; background: #E8F0F8; border-radius: 3px;")
        note.setWordWrap(True)
        left_layout.addWidget(note)

        # --- Pre-jump conditions ---
        pre_section = SectionFrame("1. Pre-jump Conditions")
        self.inp_V1 = LabeledInput("Upstream velocity (V₁)", default=8.0, unit="m/s",
                                    tooltip="Flow velocity just before the hydraulic jump. Must be > 0.")
        self.inp_V1.setValue(8.0)
        pre_section.addWidget(self.inp_V1)

        self.inp_y1 = LabeledInput("Upstream depth (y₁)", default=0.6, unit="m",
                                    tooltip="Water depth just before the jump. Must be > 0.")
        self.inp_y1.setValue(0.6)
        pre_section.addWidget(self.inp_y1)

        self.inp_b = LabeledInput("Channel width (b)", default=5.0, unit="m",
                                   tooltip="Channel width (rectangular assumed for the basin design).")
        self.inp_b.setValue(5.0)
        pre_section.addWidget(self.inp_b)

        left_layout.addWidget(pre_section)

        # --- Channel & soil inputs ---
        chan_section = SectionFrame("2. Channel & Soil")
        self.inp_S = LabeledInput("Bed slope (S)", default=0.01, unit="m/m",
                                   tooltip="Channel bed slope. > 0.05 triggers Sloped basin selection.")
        self.inp_S.setValue(0.01)
        chan_section.addWidget(self.inp_S)

        self.inp_n = LabeledInput("Manning's n", default=0.015, unit="",
                                   tooltip="Roughness coefficient (informational; affects friction loss estimates).")
        self.inp_n.setValue(0.015)
        chan_section.addWidget(self.inp_n)

        soil_lbl = QLabel("Soil type:")
        soil_lbl.setStyleSheet("font-weight: bold;")
        chan_section.addWidget(soil_lbl)
        self.cbo_soil = QtWidgets.QComboBox()
        self.cbo_soil.addItems(["rock", "gravel", "sand", "silt", "clay"])
        self.cbo_soil.setCurrentText("rock")
        chan_section.addWidget(self.cbo_soil)

        left_layout.addWidget(chan_section)

        # --- Safety factor ---
        safety_section = SectionFrame("3. Safety Factor")
        self.inp_sf = LabeledInput("Safety factor", default=1.15, unit="",
                                    tooltip="Multiplier on basin length (typical: 1.0-1.25).")
        self.inp_sf.setValue(1.15)
        safety_section.addWidget(self.inp_sf)

        left_layout.addWidget(safety_section)

        # --- Action buttons ---
        btn_section = SectionFrame("4. Run Analysis")
        self.btn_run = QPushButton("▶  Analyze Jump & Design Basin")
        self.btn_run.setStyleSheet("QPushButton { background: #1A3A6C; color: white; padding: 10px; font-weight: bold; font-size: 11pt; } QPushButton:hover { background: #2A5A8C; }")
        self.btn_run.clicked.connect(self._on_run)
        btn_section.addWidget(self.btn_run)

        self.btn_jump_only = QPushButton("📐  Analyze Jump Only")
        self.btn_jump_only.setStyleSheet("QPushButton { background: #4A6FA5; color: white; padding: 6px; } QPushButton:hover { background: #5A7FB5; }")
        self.btn_jump_only.clicked.connect(self._on_jump_only)
        btn_section.addWidget(self.btn_jump_only)

        self.btn_basin_only = QPushButton("🏗️  Design Basin Only")
        self.btn_basin_only.setStyleSheet("QPushButton { background: #4A6FA5; color: white; padding: 6px; } QPushButton:hover { background: #5A7FB5; }")
        self.btn_basin_only.clicked.connect(self._on_basin_only)
        btn_section.addWidget(self.btn_basin_only)

        self.btn_clear = QPushButton("🗑  Clear Results")
        self.btn_clear.setStyleSheet("QPushButton { padding: 6px; }")
        self.btn_clear.clicked.connect(self._on_clear)
        btn_section.addWidget(self.btn_clear)

        self.btn_report = ReportButton(form_name='hydraulic_jump')
        btn_section.addWidget(self.btn_report)

        left_layout.addWidget(btn_section)
        left_layout.addStretch(1)
        left.setLayout(left_layout)
        left_scroll.setWidget(left)
        root_layout.addWidget(left_scroll)

        # === RIGHT: results + chart ===
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setSizes([500, 400])

        self.result_table = ResultTable()
        right_splitter.addWidget(self.result_table)

        self.fig = Figure(figsize=(10, 5))
        self.canvas = FigureCanvas(self.fig)
        right_splitter.addWidget(self.canvas)

        root_layout.addWidget(right_splitter, 1)

    # ----------------------------------------------------------------- Wiring
    def _build_input(self) -> HydraulicJumpInput:
        return HydraulicJumpInput(
            velocity_u1=self.inp_V1.value(),
            depth_y1=self.inp_y1.value(),
            width_b=self.inp_b.value(),
            slope=self.inp_S.value(),
            friction_coefficient=self.inp_n.value(),
            soil_type=self.cbo_soil.currentText(),
        )

    # ----------------------------------------------------------------- Buttons
    def _on_run(self):
        try:
            input_data = self._build_input()
            jump_results, basin_design = self.analyzer.analyze_and_design(input_data)
            results = {
                "inputs": {
                    "V1_mps": input_data.velocity_u1,
                    "y1_m": input_data.depth_y1,
                    "b_m": input_data.width_b,
                    "S": input_data.slope,
                    "n": input_data.friction_coefficient,
                    "soil_type": input_data.soil_type,
                },
                "hydraulic_jump": {
                    "Fr1": jump_results.froude_number_1,
                    "Fr2": jump_results.froude_number_2,
                    "conjugate_depth_y2_m": jump_results.depth_y2,
                    "conjugate_depth_ratio": jump_results.conjugate_depth_ratio,
                    "energy_loss_m": jump_results.energy_loss,
                    "energy_loss_percent": jump_results.energy_loss_percentage,
                    "jump_efficiency_percent": jump_results.jump_efficiency,
                    "jump_length_m": jump_results.jump_length,
                    "jump_type": jump_results.jump_type.value,
                },
                "stilling_basin": {
                    "basin_type": basin_design.basin_type.value,
                    "basin_length_m": basin_design.basin_length,
                    "basin_width_m": basin_design.basin_width,
                    "basin_depth_m": basin_design.basin_depth,
                    "appurtenances_height_m": basin_design.appurtenances_height,
                    "end_sill_height_m": basin_design.end_sill_height,
                    "baffle_blocks_height_m": basin_design.baffle_blocks_height,
                    "chute_blocks_height_m": basin_design.chute_blocks_height,
                    "water_volume_m3": basin_design.water_volume,
                    "energy_dissipation_capacity_W_per_m2": basin_design.energy_dissipation_capacity,
                },
            }
            self.result_table.populate(results)
            self._plot_jump(jump_results, basin_design)
            self.btn_report.set_result(
                inputs={'V1': input_data.velocity_u1,
                        'y1': input_data.depth_y1,
                        'b': input_data.width_b},
                result={'froude_number_1': jump_results.froude_number_1,
                        'froude_number_2': jump_results.froude_number_2,
                        'depth_y2': jump_results.depth_y2,
                        'energy_loss': jump_results.energy_loss,
                        'jump_efficiency': jump_results.jump_efficiency,
                        'jump_length': jump_results.jump_length,
                        'jump_type': jump_results.jump_type.value},
                extra={'basin_type': basin_design.basin_type.value,
                       'basin_length': basin_design.basin_length,
                       'basin_width': basin_design.basin_width,
                       'baffle_blocks_height': basin_design.baffle_blocks_height,
                       'end_sill_height': basin_design.end_sill_height,
                       'chute_blocks_height': basin_design.chute_blocks_height}
            )
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Hydraulic Jump Analysis", f"{e}\n\n{traceback.format_exc()}")

    def _on_jump_only(self):
        try:
            input_data = self._build_input()
            jump_results = self.analyzer.calculator.analyze_jump(input_data)
            results = {
                "Fr1": jump_results.froude_number_1,
                "Fr2": jump_results.froude_number_2,
                "conjugate_depth_y2_m": jump_results.depth_y2,
                "conjugate_depth_ratio": jump_results.conjugate_depth_ratio,
                "energy_loss_m": jump_results.energy_loss,
                "energy_loss_percent": jump_results.energy_loss_percentage,
                "jump_efficiency_percent": jump_results.jump_efficiency,
                "jump_length_m": jump_results.jump_length,
                "jump_type": jump_results.jump_type.value,
            }
            self.result_table.populate(results)
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Jump Analysis", f"{e}\n\n{traceback.format_exc()}")

    def _on_basin_only(self):
        try:
            input_data = self._build_input()
            jump_results = self.analyzer.calculator.analyze_jump(input_data)
            sf = self.inp_sf.value()
            basin_design = self.analyzer.designer.design_basin(input_data, jump_results, safety_factor=sf)
            results = {
                "basin_type": basin_design.basin_type.value,
                "basin_length_m": basin_design.basin_length,
                "basin_width_m": basin_design.basin_width,
                "basin_depth_m": basin_design.basin_depth,
                "appurtenances_height_m": basin_design.appurtenances_height,
                "end_sill_height_m": basin_design.end_sill_height,
                "baffle_blocks_height_m": basin_design.baffle_blocks_height,
                "chute_blocks_height_m": basin_design.chute_blocks_height,
                "water_volume_m3": basin_design.water_volume,
                "energy_dissipation_capacity_W_per_m2": basin_design.energy_dissipation_capacity,
            }
            self.result_table.populate(results)
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Basin Design", f"{e}\n\n{traceback.format_exc()}")

    def _on_clear(self):
        self.result_table.setRowCount(0)
        self.fig.clear()
        self.canvas.draw()

    # ----------------------------------------------------------------- Charts
    def _plot_jump(self, jr: HydraulicJumpResults, bd: StillingBasinDesign):
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        # Draw the jump profile
        y1 = self.inp_y1.value()
        y2 = jr.depth_y2
        L_j = jr.jump_length
        L_b = bd.basin_length
        b = self.inp_b.value()

        # x positions: pre-jump | jump rise | basin | post-basin
        x0 = 0
        x1_pre = 0
        x2_jump_start = 0
        x3_jump_end = L_j
        x4_basin_end = L_j + L_b
        x5_post_end = L_j + L_b + 2 * y2  # some post-basin distance

        # Bed elevation (constant)
        z = 0
        # Invert level
        invert_y = z

        # Pre-jump (subcritical → supercritical at jump start, depth y1)
        ax.plot([x0, x1_pre], [invert_y, invert_y], 'k-', lw=1.5)
        ax.plot([x0, x1_pre], [invert_y + y1, invert_y + y1], 'b-', lw=2, label=f'Pre-jump depth y₁ = {y1:.2f} m')

        # Jump rise (y1 → y2)
        x_jump = np.linspace(x2_jump_start, x3_jump_end, 50)
        y_jump = y1 + (y2 - y1) * (1 - np.cos(np.pi * (x_jump - x2_jump_start) / L_j)) / 2
        ax.plot(x_jump, invert_y + y_jump, 'b-', lw=2.5, label='Hydraulic jump')
        ax.fill_between(x_jump, invert_y, invert_y + y_jump, color='lightblue', alpha=0.4)

        # Basin (with chute blocks, baffle blocks, end sill)
        x_basin = np.linspace(x3_jump_end, x4_basin_end, 50)
        y_basin = y2 * np.ones_like(x_basin)
        ax.plot(x_basin, invert_y + y_basin, 'b-', lw=2)
        ax.fill_between(x_basin, invert_y, invert_y + y_basin, color='lightgreen', alpha=0.4,
                        label=f'Stilling basin ({bd.basin_type.value.split(" - ")[0]})')

        # Chute blocks at start of basin
        chute_h = bd.chute_blocks_height
        ax.bar([x3_jump_end + L_b * 0.1], [chute_h], width=L_b * 0.05, bottom=invert_y,
               color='gray', edgecolor='black', label=f'Chute blocks (h={chute_h:.2f} m)')

        # Baffle blocks at middle of basin
        baffle_h = bd.baffle_blocks_height
        ax.bar([x3_jump_end + L_b * 0.5], [baffle_h], width=L_b * 0.05, bottom=invert_y,
               color='dimgray', edgecolor='black', label=f'Baffle blocks (h={baffle_h:.2f} m)')

        # End sill at end of basin
        end_sill_h = bd.end_sill_height
        ax.bar([x4_basin_end - L_b * 0.05], [end_sill_h], width=L_b * 0.05, bottom=invert_y,
               color='darkgray', edgecolor='black', label=f'End sill (h={end_sill_h:.2f} m)')

        # Post-basin tailwater (depth y2 continues)
        ax.plot([x4_basin_end, x5_post_end], [invert_y + y2, invert_y + y2], 'b-', lw=1.5,
                label=f'Post-basin depth y₂ = {y2:.2f} m')

        # Annotations
        ax.axvline(x=x2_jump_start, color='red', ls=':', lw=1, alpha=0.6)
        ax.axvline(x=x3_jump_end, color='red', ls=':', lw=1, alpha=0.6)
        ax.annotate(f'L_j = {L_j:.2f} m\nFr1 = {jr.froude_number_1:.2f}',
                    xy=(L_j/2, invert_y + (y1+y2)/2), ha='center', fontsize=9,
                    color='red', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='red', alpha=0.9))
        ax.annotate(f'L_b = {L_b:.2f} m\n{bd.basin_type.value.split(" - ")[0]}',
                    xy=(x3_jump_end + L_b/2, invert_y + y2 + 0.3), ha='center', fontsize=9,
                    color='darkgreen', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='darkgreen', alpha=0.9))

        # EGL drop
        E1 = y1 + jr.froude_number_1**2 * y1 / 2
        E2 = y2 + jr.froude_number_1**2 * y1**2 / (2 * y2**2) * y2
        ax.plot([x0, x3_jump_end], [invert_y + E1, invert_y + E2], 'r--', lw=1.5, alpha=0.6,
                label=f'Energy grade line (ΔE = {jr.energy_loss:.2f} m)')

        ax.set_xlabel("x (m)", fontsize=10)
        ax.set_ylabel("Elevation (m)", fontsize=10)
        ax.set_title(f"Hydraulic Jump + Stilling Basin — {jr.jump_type.value}", fontsize=10, fontweight='bold')
        ax.legend(loc='upper right', fontsize=7, ncol=2)
        ax.grid(alpha=0.3)
        ax.set_ylim(-0.3, max(y2, E1) * 1.3)
        ax.set_xlim(-0.5, x5_post_end + 0.5)

        self.fig.tight_layout()
        self.canvas.draw()
