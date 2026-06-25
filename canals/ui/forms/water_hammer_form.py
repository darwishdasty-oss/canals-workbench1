"""
Water Hammer Analysis Form — MDI sub-window wrapping canals.water_hammer.

Computes water hammer pressure rise, wave speed (Korteweg), critical time
(Joukowsky), hoop stress, and safety factor for sudden valve closure or
pump trip. Provides engineering mitigation recommendations.

All inputs are free-form with no min/max constraints.
"""
from __future__ import annotations
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from canals.water_hammer import (
    PipeMaterial, PipeParameters, FluidProperties, WaterHammerAnalyzer
)

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea,
                                QWidget, QLabel, QSplitter)
from PySide6.QtCore import Qt
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ._widgets import LabeledInput, SectionFrame, ResultTable


class WaterHammerForm(QtWidgets.QMdiSubWindow):
    """Water hammer analysis — fully user-fillable inputs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Water Hammer Analyzer (Canals)")
        self.resize(1500, 950)
        self.analyzer = WaterHammerAnalyzer()
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
                      "Computes wave speed (Korteweg), Joukowsky pressure rise,\n"
                      "critical closure time, hoop stress, and safety factor.")
        note.setStyleSheet("color: #1A3A6C; font-style: italic; padding: 6px; background: #E8F0F8; border-radius: 3px;")
        note.setWordWrap(True)
        left_layout.addWidget(note)

        # --- Pipe material selector ---
        mat_section = SectionFrame("1. Pipe Material")
        mat_lbl = QLabel("Material preset:")
        mat_lbl.setStyleSheet("font-weight: bold;")
        mat_section.addWidget(mat_lbl)
        self.cbo_material = QtWidgets.QComboBox()
        self.cbo_material.addItems(["Steel", "Cast Iron", "PVC", "HDPE", "Concrete", "Copper", "Custom"])
        self.cbo_material.setCurrentText("Steel")
        self.cbo_material.currentTextChanged.connect(self._on_material_changed)
        mat_section.addWidget(self.cbo_material)

        self.lbl_mat_props = QLabel("E = 200 GPa, ν = 0.30, σ_y = 400 MPa")
        self.lbl_mat_props.setStyleSheet("color: #555; font-size: 9pt;")
        self.lbl_mat_props.setWordWrap(True)
        mat_section.addWidget(self.lbl_mat_props)

        left_layout.addWidget(mat_section)

        # --- Pipe geometry ---
        geom_section = SectionFrame("2. Pipe Geometry")
        self.inp_length = LabeledInput("Length (L)", default=1000.0, unit="m",
                                       tooltip="Total pipe length from reservoir/pump to valve.")
        self.inp_length.setValue(1000.0)
        geom_section.addWidget(self.inp_length)

        self.inp_diameter = LabeledInput("Diameter (D)", default=0.5, unit="m",
                                        tooltip="Inside diameter of the pipe.")
        self.inp_diameter.setValue(0.5)
        geom_section.addWidget(self.inp_diameter)

        self.inp_thickness = LabeledInput("Wall thickness (e)", default=0.01, unit="m",
                                           tooltip="Wall thickness. D/e ratio typically 20-200.")
        self.inp_thickness.setValue(0.01)
        geom_section.addWidget(self.inp_thickness)

        self.inp_E = LabeledInput("Elastic modulus (E)", default=200e9, unit="Pa",
                                  tooltip="Young's modulus of the pipe material. Use 2e11 for steel, 1e11 for CI, 3e9 for PVC.")
        self.inp_E.setValue(200e9)
        geom_section.addWidget(self.inp_E)

        self.inp_nu = LabeledInput("Poisson ratio (ν)", default=0.30, unit="",
                                   tooltip="Poisson's ratio (0.3 for metals, 0.45 for HDPE).")
        self.inp_nu.setValue(0.30)
        geom_section.addWidget(self.inp_nu)

        self.inp_yield = LabeledInput("Yield strength (σ_y)", default=400e6, unit="Pa",
                                       tooltip="Yield strength of the pipe material.")
        self.inp_yield.setValue(400e6)
        geom_section.addWidget(self.inp_yield)

        left_layout.addWidget(geom_section)

        # --- Fluid properties ---
        fluid_section = SectionFrame("3. Fluid Properties")
        self.inp_density = LabeledInput("Density (ρ)", default=1000.0, unit="kg/m³",
                                         tooltip="Fluid density (1000 for water, ~850 for light oil).")
        self.inp_density.setValue(1000.0)
        fluid_section.addWidget(self.inp_density)

        self.inp_K = LabeledInput("Bulk modulus (K)", default=2.2e9, unit="Pa",
                                  tooltip="Bulk modulus (2.2e9 for water at 20°C, 1.6e9 at 80°C).")
        self.inp_K.setValue(2.2e9)
        fluid_section.addWidget(self.inp_K)

        self.inp_temp = LabeledInput("Temperature", default=20.0, unit="°C",
                                     tooltip="Fluid temperature (affects bulk modulus; informational).")
        self.inp_temp.setValue(20.0)
        fluid_section.addWidget(self.inp_temp)

        left_layout.addWidget(fluid_section)

        # --- Operating conditions ---
        op_section = SectionFrame("4. Operating Conditions")
        self.inp_velocity = LabeledInput("Flow velocity (V)", default=2.0, unit="m/s",
                                          tooltip="Steady-state flow velocity before the transient event.")
        self.inp_velocity.setValue(2.0)
        op_section.addWidget(self.inp_velocity)

        self.inp_closure = LabeledInput("Valve closure time (t_c)", default=0.1, unit="s",
                                         tooltip="Time to close the valve. If < critical time, full water hammer occurs.")
        self.inp_closure.setValue(0.1)
        op_section.addWidget(self.inp_closure)

        self.inp_op_pressure = LabeledInput("Operating pressure", default=10.0, unit="bar",
                                             tooltip="Steady-state operating pressure (for total max pressure calculation).")
        self.inp_op_pressure.setValue(10.0)
        op_section.addWidget(self.inp_op_pressure)

        left_layout.addWidget(op_section)

        # --- Action buttons ---
        btn_section = SectionFrame("5. Run Analysis")
        self.btn_run = QPushButton("▶  Analyze Water Hammer")
        self.btn_run.setStyleSheet("QPushButton { background: #1A3A6C; color: white; padding: 10px; font-weight: bold; font-size: 11pt; } QPushButton:hover { background: #2A5A8C; }")
        self.btn_run.clicked.connect(self._on_run)
        btn_section.addWidget(self.btn_run)

        self.btn_wave_only = QPushButton("📐  Wave Speed Only")
        self.btn_wave_only.setStyleSheet("QPushButton { background: #4A6FA5; color: white; padding: 6px; } QPushButton:hover { background: #5A7FB5; }")
        self.btn_wave_only.clicked.connect(self._on_wave_only)
        btn_section.addWidget(self.btn_wave_only)

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

        self.result_table = ResultTable()
        right_splitter.addWidget(self.result_table)

        self.fig = Figure(figsize=(10, 5))
        self.canvas = FigureCanvas(self.fig)
        right_splitter.addWidget(self.canvas)

        root_layout.addWidget(right_splitter, 1)

    # ----------------------------------------------------------------- Wiring
    def _on_material_changed(self, name: str) -> None:
        presets = {
            "Steel": (200e9, 0.30, 400e6, "Carbon steel: most common for high-pressure pipelines"),
            "Cast Iron": (100e9, 0.26, 200e6, "Cast iron: older water mains"),
            "PVC": (3.0e9, 0.38, 50e6, "PVC: low-pressure water systems"),
            "HDPE": (1.0e9, 0.45, 25e6, "HDPE: flexible pipe, low modulus"),
            "Concrete": (30e9, 0.20, 40e6, "Concrete: large diameter penstocks"),
            "Copper": (110e9, 0.34, 210e6, "Copper: domestic plumbing"),
        }
        if name in presets:
            E, nu, sy, desc = presets[name]
            self.inp_E.setValue(E)
            self.inp_nu.setValue(nu)
            self.inp_yield.setValue(sy)
            self.lbl_mat_props.setText(f"E = {E/1e9:.1f} GPa, ν = {nu:.2f}, σ_y = {sy/1e6:.0f} MPa. {desc}.")
        else:
            self.lbl_mat_props.setText("Custom: enter E, ν, σ_y below.")

    def _build_pipe_fluid(self):
        pipe = PipeParameters(
            length=self.inp_length.value(),
            diameter=self.inp_diameter.value(),
            wall_thickness=self.inp_thickness.value(),
            elastic_modulus=self.inp_E.value(),
            poisson_ratio=self.inp_nu.value(),
            yield_strength=self.inp_yield.value(),
        )
        fluid = FluidProperties(
            density=self.inp_density.value(),
            bulk_modulus=self.inp_K.value(),
            temperature=self.inp_temp.value(),
        )
        return pipe, fluid

    # ----------------------------------------------------------------- Buttons
    def _on_run(self):
        try:
            pipe, fluid = self._build_pipe_fluid()
            flow_velocity = self.inp_velocity.value()
            closure_time = self.inp_closure.value()
            op_pressure = self.inp_op_pressure.value()
            results = self.analyzer.analyze_valve_closure(pipe, fluid, flow_velocity, closure_time)
            recs = self.analyzer.get_mitigation_recommendations(results, operating_pressure_bar=op_pressure)
            total = {
                "inputs": {
                    "L_m": pipe.length,
                    "D_m": pipe.diameter,
                    "e_m": pipe.wall_thickness,
                    "E_GPa": pipe.elastic_modulus / 1e9,
                    "nu": pipe.poisson_ratio,
                    "sigma_y_MPa": pipe.yield_strength / 1e6,
                    "rho_kgm3": fluid.density,
                    "K_GPa": fluid.bulk_modulus / 1e9,
                    "T_C": fluid.temperature,
                    "V_mps": flow_velocity,
                    "t_close_s": closure_time,
                    "operating_pressure_bar": op_pressure,
                },
                "results": {
                    "wave_speed_mps": results["wave_speed"],
                    "critical_time_s": results["critical_time"],
                    "pressure_rise_time_s": results["pressure_rise_time"],
                    "closure_type": results["closure_type"],
                    "delta_pressure_bar": results["delta_pressure_bar"],
                    "delta_pressure_psi": results["delta_pressure_psi"],
                    "hoop_stress_MPa": results["hoop_stress"] / 1e6,
                    "safety_factor": results["safety_factor"],
                    "total_max_pressure_bar": op_pressure + results["delta_pressure_bar"],
                },
                "recommendations": {f"r{i+1}": r for i, r in enumerate(recs)},
            }
            self.result_table.populate(total)
            self._plot_results(pipe, fluid, results, op_pressure)
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Water Hammer", f"{e}\n\n{traceback.format_exc()}")

    def _on_wave_only(self):
        try:
            pipe, fluid = self._build_pipe_fluid()
            wave_speed = self.analyzer.calculate_wave_speed(pipe, fluid)
            sonic_v = fluid.sonic_velocity_unconfined
            critical_time = self.analyzer.calculate_critical_time(pipe.length, wave_speed)
            pressure_rise_time = self.analyzer.calculate_pressure_rise_time(pipe.length, wave_speed)
            results = {
                "wave_speed_in_pipe_mps": wave_speed,
                "sonic_velocity_unconfined_mps": sonic_v,
                "wave_speed_reduction_factor": wave_speed / sonic_v,
                "critical_closure_time_s": critical_time,
                "pressure_rise_time_s": pressure_rise_time,
                "D_over_e": pipe.diameter_to_thickness_ratio,
            }
            self.result_table.populate(results)
        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(self, "Error in Wave Speed Calculation", f"{e}\n\n{traceback.format_exc()}")

    def _on_clear(self):
        self.result_table.setRowCount(0)
        self.fig.clear()
        self.canvas.draw()

    # ----------------------------------------------------------------- Charts
    def _plot_results(self, pipe, fluid, results, op_pressure):
        self.fig.clear()

        # Top panel: pressure history
        ax1 = self.fig.add_subplot(211)
        L = pipe.length
        a = results["wave_speed"]
        t = np.linspace(0, 2 * L / a, 500)  # two-way travel time

        # Simplified pressure history: step at t_c, then exponential decay
        delta_p = results["delta_pressure_pa"] / 1e5  # bar
        op = op_pressure
        pressure = np.full_like(t, op)
        pressure[t >= 0] = op + delta_p * np.exp(-(t) / (L / a))
        ax1.plot(t, pressure, 'b-', lw=2, label='Total pressure (op + hammer)')
        ax1.axhline(op, color='g', ls='--', lw=1, label=f'Operating pressure = {op:.1f} bar')
        ax1.axhline(op + delta_p, color='r', ls=':', lw=1, label=f'Peak pressure = {op + delta_p:.1f} bar')
        ax1.fill_between(t, op, pressure, where=(pressure > op), color='red', alpha=0.2, label='Hammer surge')
        ax1.set_xlabel("Time (s)", fontsize=10)
        ax1.set_ylabel("Pressure (bar)", fontsize=10)
        ax1.set_title("Pressure History at Valve (Joukowsky surge)", fontsize=10, fontweight='bold')
        ax1.legend(loc='upper right', fontsize=8)
        ax1.grid(alpha=0.3)

        # Bottom panel: safety factor gauge
        ax2 = self.fig.add_subplot(212)
        sf = results["safety_factor"]
        ax2.barh(["Safety factor"], [sf], color=['#4CAF50' if sf > 2 else '#FFA500' if sf > 1.5 else '#B8500A'])
        ax2.axvline(1.0, color='red', ls='--', lw=2, label='Yield (SF=1.0)')
        ax2.axvline(1.5, color='orange', ls='--', lw=1, label='Minimum safe (SF=1.5)')
        ax2.axvline(2.0, color='green', ls='--', lw=1, label='Recommended (SF=2.0)')
        ax2.set_xlim(0, max(5, sf * 1.2))
        ax2.set_xlabel("Safety factor", fontsize=10)
        ax2.set_title(f"Hoop stress = {results['hoop_stress']/1e6:.1f} MPa vs Yield = {pipe.yield_strength/1e6:.0f} MPa (SF = {sf:.2f})",
                      fontsize=10, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=8)
        ax2.grid(alpha=0.3, axis='x')

        # Add a text annotation with the closure type
        ax2.text(0.5, 0.4, results['closure_type'], transform=ax2.transAxes,
                 ha='center', va='center', fontsize=10,
                 bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', edgecolor='gray'))

        self.fig.tight_layout()
        self.canvas.draw()
