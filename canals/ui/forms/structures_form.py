"""
Hydraulic Structures Form — gates, siphons, pressure breakers.

All inputs are free-form QLineEdits (no min/max constraints). The user
can enter any positive real number for Q, H, L, b, etc.
"""
from __future__ import annotations
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from canals.structures import (
    GateDesigner, SiphonDesigner, PressureBreakerDesigner, HydraulicStructuresSystem
)

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
                                QWidget, QLabel, QScrollArea)
from PySide6.QtCore import Qt
from ._widgets import LabeledInput, SectionFrame, ResultTable


class StructuresForm(QtWidgets.QMdiSubWindow):
    """Hydraulic structures — sluice gates, radial gates, siphons, pressure breakers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hydraulic Structures (Canals)")
        self.resize(1400, 900)
        self.gate_designer = GateDesigner()
        self.siphon_designer = SiphonDesigner()
        self.breaker_designer = PressureBreakerDesigner()
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setWidget(central)
        layout = QVBoxLayout(central)

        # Header note
        note = QLabel("📝 All inputs are free-form. You can enter any value — no preset limits.")
        note.setStyleSheet("color: #1A3A6C; font-style: italic; padding: 4px; background: #E8F0F8; border-radius: 3px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        tabs = QTabWidget()

        # ============== Tab 1: Gates ==============
        gates_tab = QWidget()
        gates_layout = QHBoxLayout(gates_tab)

        # Left: inputs
        gates_left_scroll = QScrollArea()
        gates_left_scroll.setWidgetResizable(True)
        gates_left_scroll.setMaximumWidth(440)
        gates_left_widget = QWidget()
        gates_left_layout = QVBoxLayout(gates_left_widget)

        gates_section = SectionFrame("Gate Design Inputs")
        gates_left_layout.addWidget(gates_section)

        # Gate type selector
        type_lbl = QLabel("Gate type:")
        type_lbl.setStyleSheet("font-weight: bold;")
        gates_section.addWidget(type_lbl)
        self.gate_type = QtWidgets.QComboBox()
        self.gate_type.addItems(["Sluice gate (vertical)", "Radial gate (Tainter)"])
        gates_section.addWidget(self.gate_type)

        self.gate_Q = LabeledInput("Discharge (Q)", default=10.0, unit="m³/s",
                                    tooltip="Design discharge through the gate.")
        self.gate_Q.setValue(10.0)
        gates_section.addWidget(self.gate_Q)

        self.gate_H_up = LabeledInput("Upstream head (H_up)", default=5.0, unit="m",
                                       tooltip="Water depth upstream of the gate.")
        self.gate_H_up.setValue(5.0)
        gates_section.addWidget(self.gate_H_up)

        self.gate_H_down = LabeledInput("Downstream head (H_down)", default=1.0, unit="m",
                                         tooltip="Water depth downstream of the gate. For free flow, leave as 0.")
        self.gate_H_down.setValue(1.0)
        gates_section.addWidget(self.gate_H_down)

        self.gate_b = LabeledInput("Gate width (b)", default=3.0, unit="m",
                                    tooltip="Width of the gate opening.")
        self.gate_b.setValue(3.0)
        gates_section.addWidget(self.gate_b)

        self.gate_a = LabeledInput("Gate opening (a, sluice)", default=0.5, unit="m",
                                    tooltip="Vertical opening of the sluice gate. Only used for sluice gates.")
        self.gate_a.setValue(0.5)
        gates_section.addWidget(self.gate_a)

        self.gate_radius = LabeledInput("Radius (R, radial)", default=5.0, unit="m",
                                         tooltip="Radius of the radial gate. Only used for radial gates.")
        self.gate_radius.setValue(5.0)
        gates_section.addWidget(self.gate_radius)

        self.btn_gate = QPushButton("🔧  Design Gate")
        self.btn_gate.setStyleSheet("QPushButton { background: #1A3A6C; color: white; padding: 8px; font-weight: bold; } QPushButton:hover { background: #2A5A8C; }")
        self.btn_gate.clicked.connect(self._on_gate)
        gates_section.addWidget(self.btn_gate)

        gates_left_layout.addWidget(gates_section)
        gates_left_layout.addStretch(1)
        gates_left_scroll.setWidget(gates_left_widget)
        gates_layout.addWidget(gates_left_scroll)

        # Right: result table
        self.gate_results = ResultTable()
        gates_layout.addWidget(self.gate_results, 1)
        tabs.addTab(gates_tab, "Gates")

        # ============== Tab 2: Siphons ==============
        siph_tab = QWidget()
        siph_layout = QHBoxLayout(siph_tab)

        siph_left_scroll = QScrollArea()
        siph_left_scroll.setWidgetResizable(True)
        siph_left_scroll.setMaximumWidth(440)
        siph_left_widget = QWidget()
        siph_left_layout = QVBoxLayout(siph_left_widget)

        siph_section = SectionFrame("Siphon Design Inputs")
        siph_left_layout.addWidget(siph_section)

        self.siph_Q = LabeledInput("Discharge (Q)", default=5.0, unit="m³/s",
                                    tooltip="Design discharge through the siphon.")
        self.siph_Q.setValue(5.0)
        siph_section.addWidget(self.siph_Q)

        self.siph_H = LabeledInput("Static head (H)", default=3.0, unit="m",
                                    tooltip="Static head difference driving the siphon flow.")
        self.siph_H.setValue(3.0)
        siph_section.addWidget(self.siph_H)

        self.siph_L = LabeledInput("Pipe length (L)", default=20.0, unit="m",
                                    tooltip="Total pipe length of the siphon.")
        self.siph_L.setValue(20.0)
        siph_section.addWidget(self.siph_L)

        self.siph_D = LabeledInput("Pipe diameter (D)", default=0.5, unit="m",
                                    tooltip="Pipe diameter (computed by the algorithm if not given).")
        self.siph_D.setValue(0.5)
        siph_section.addWidget(self.siph_D)

        self.siph_n = LabeledInput("Manning's n", default=0.013, unit="",
                                    tooltip="Pipe roughness coefficient.")
        self.siph_n.setValue(0.013)
        siph_section.addWidget(self.siph_n)

        self.btn_siph = QPushButton("🔧  Design Siphon")
        self.btn_siph.setStyleSheet("QPushButton { background: #1A3A6C; color: white; padding: 8px; font-weight: bold; } QPushButton:hover { background: #2A5A8C; }")
        self.btn_siph.clicked.connect(self._on_siphon)
        siph_section.addWidget(self.btn_siph)

        siph_left_layout.addWidget(siph_section)
        siph_left_layout.addStretch(1)
        siph_left_scroll.setWidget(siph_left_widget)
        siph_layout.addWidget(siph_left_scroll)

        self.siph_results = ResultTable()
        siph_layout.addWidget(self.siph_results, 1)
        tabs.addTab(siph_tab, "Siphons")

        # ============== Tab 3: Pressure Breakers ==============
        brk_tab = QWidget()
        brk_layout = QHBoxLayout(brk_tab)

        brk_left_scroll = QScrollArea()
        brk_left_scroll.setWidgetResizable(True)
        brk_left_scroll.setMaximumWidth(440)
        brk_left_widget = QWidget()
        brk_left_layout = QVBoxLayout(brk_left_widget)

        brk_section = SectionFrame("Pressure Breaker Design Inputs")
        brk_left_layout.addWidget(brk_section)

        self.brk_Q = LabeledInput("Discharge (Q)", default=5.0, unit="m³/s",
                                   tooltip="Design discharge through the pressure breaker.")
        self.brk_Q.setValue(5.0)
        brk_section.addWidget(self.brk_Q)

        self.brk_H = LabeledInput("Total head (H_total)", default=3.0, unit="m",
                                   tooltip="Total head to be dissipated.")
        self.brk_H.setValue(3.0)
        brk_section.addWidget(self.brk_H)

        self.brk_L = LabeledInput("Total length (L)", default=15.0, unit="m",
                                   tooltip="Total available length for the breaker system.")
        self.brk_L.setValue(15.0)
        brk_section.addWidget(self.brk_L)

        self.brk_D = LabeledInput("Pipe diameter (D)", default=0.5, unit="m",
                                   tooltip="Pipe diameter at the inlet.")
        self.brk_D.setValue(0.5)
        brk_section.addWidget(self.brk_D)

        self.btn_brk = QPushButton("🔧  Design Optimal Breaker")
        self.btn_brk.setStyleSheet("QPushButton { background: #1A3A6C; color: white; padding: 8px; font-weight: bold; } QPushButton:hover { background: #2A5A8C; }")
        self.btn_brk.clicked.connect(self._on_breaker)
        brk_section.addWidget(self.btn_brk)

        brk_left_layout.addWidget(brk_section)
        brk_left_layout.addStretch(1)
        brk_left_scroll.setWidget(brk_left_widget)
        brk_layout.addWidget(brk_left_scroll)

        self.brk_results = ResultTable()
        brk_layout.addWidget(self.brk_results, 1)
        tabs.addTab(brk_tab, "Pressure Breakers")

        layout.addWidget(tabs)

    # ----------------------------------------------------------------- Buttons
    def _on_gate(self):
        try:
            Q = self.gate_Q.value()
            H_up = self.gate_H_up.value()
            H_down = self.gate_H_down.value()
            b = self.gate_b.value()
            if self.gate_type.currentIndex() == 0:  # sluice
                a = self.gate_a.value()
                res = self.gate_designer.design_sluice_gate(Q, H_up, H_down, b, opening=a)
            else:  # radial
                radius = self.gate_radius.value()
                res = self.gate_designer.design_radial_gate(Q, H_up, b, radius=radius)
            self.gate_results.populate(res)
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Gate Design", f"{e}\n\n{traceback.format_exc()}")

    def _on_siphon(self):
        try:
            Q = self.siph_Q.value()
            H = self.siph_H.value()
            L = self.siph_L.value()
            D = self.siph_D.value()
            n = self.siph_n.value()
            res = self.siphon_designer.design_siphon(Q, H, L, D, n)
            self.siph_results.populate(res)
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Siphon Design", f"{e}\n\n{traceback.format_exc()}")

    def _on_breaker(self):
        try:
            Q = self.brk_Q.value()
            H = self.brk_H.value()
            L = self.brk_L.value()
            D = self.brk_D.value()
            res = self.breaker_designer.design_optimal_breaker(Q, H, L, D)
            self.brk_results.populate(res)
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Breaker Design", f"{e}\n\n{traceback.format_exc()}")
