"""Unit tests for the standalone Canals Workbench.
Run with: python -m unittest discover tests
or:        python -m pytest tests/
"""
import unittest
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))


class TestOpenChannel(unittest.TestCase):
    """Tests for canals.open_channel — optimal section + comprehensive flow analysis."""

    def test_optimal_trapezoidal(self):
        from canals import AdvancedChannelDesigner, ChannelType
        designer = AdvancedChannelDesigner()
        result = designer.design_optimal_section(
            10.0, 0.013, 0.001, channel_type=ChannelType.TRAPEZOIDAL)
        self.assertIsInstance(result, dict)
        self.assertIn('bottom_width', result)
        self.assertIn('depth', result)
        self.assertIn('side_slope', result)
        self.assertGreater(result['bottom_width'], 0)
        self.assertGreater(result['depth'], 0)

    def test_optimal_rectangular(self):
        from canals import AdvancedChannelDesigner, ChannelType
        designer = AdvancedChannelDesigner()
        result = designer.design_optimal_section(
            10.0, 0.013, 0.001, channel_type=ChannelType.RECTANGULAR)
        self.assertIsInstance(result, dict)
        self.assertIn('bottom_width', result)
        self.assertGreater(result['bottom_width'], 0)

    def test_comprehensive_flow_analysis(self):
        from canals import AdvancedChannelDesigner, ChannelGeometry, ChannelType
        designer = AdvancedChannelDesigner()
        geom = ChannelGeometry(channel_type=ChannelType.TRAPEZOIDAL,
                               bottom_width=3.0, side_slope=1.5, depth=2.0)
        try:
            result = designer.comprehensive_flow_analysis(geom, 10.0, 0.013, 0.001)
        except Exception:
            result = designer.comprehensive_flow_analysis(10.0, 0.013, 0.001)
        self.assertIsInstance(result, dict)


class TestStructures(unittest.TestCase):
    """Tests for canals.structures — gates, siphons, pressure breakers."""

    def test_sluice_gate(self):
        from canals import GateDesigner
        gd = GateDesigner()
        result = gd.design_sluice_gate(10.0, 5.0, 1.0, 3.0)
        self.assertIsInstance(result, dict)
        self.assertIn('discharge_coefficient', result)
        self.assertIn('hydrostatic_force', result)
        self.assertGreater(result['discharge_coefficient'], 0.5)
        self.assertLess(result['discharge_coefficient'], 1.0)

    def test_siphon(self):
        from canals import SiphonDesigner
        sd = SiphonDesigner()
        result = sd.design_siphon(5.0, 3.0, 20.0)
        self.assertIsInstance(result, dict)
        self.assertIn('head_losses', result)
        self.assertIn('cavitation_risk', result)

    def test_pressure_breaker(self):
        from canals import PressureBreakerDesigner
        pbd = PressureBreakerDesigner()
        result = pbd.design_optimal_breaker(5.0, 3.0, 15.0)
        self.assertIsInstance(result, dict)


class TestEarthCanal(unittest.TestCase):
    """Tests for canals.earth_canal — Lacey, Kennedy, Manning."""

    def test_lacey(self):
        from canals import EarthCanalDesigner
        ecd = EarthCanalDesigner()
        result = ecd.lacey_theory_design(5.0, 1.0, 0.5)
        self.assertIsInstance(result, dict)
        self.assertIn('depth', result)
        self.assertGreater(result['depth'], 0)

    def test_kennedy(self):
        from canals import EarthCanalDesigner
        ecd = EarthCanalDesigner()
        result = ecd.kennedy_theory_design(5.0, 0.0225, 0.0004)
        self.assertIsInstance(result, dict)

    def test_manning(self):
        from canals import EarthCanalDesigner
        ecd = EarthCanalDesigner()
        result = ecd.manning_design(Q=5.0, n=0.0225, S=0.0004, side_slope=0.5)
        self.assertIsInstance(result, dict)


class TestFlowProfile(unittest.TestCase):
    """Tests for canals.flow_profile — critical/normal depth + GVF."""

    def test_critical_depth_rectangular(self):
        from canals import OpenChannelFlow
        ch = OpenChannelFlow()
        ch.channel_type = 'rectangular'
        ch.channel_params = {'b': 5.0, 'z': 0}
        ch.flow_params = {'Q': 10.0, 'S0': 0.001, 'n': 0.015,
                          'y_initial': 2.0, 'L': 1000.0}
        yc = ch.calculate_critical_depth()
        q = 10.0 / 5.0
        expected = (q**2 / 9.81)**(1/3)
        self.assertAlmostEqual(yc, expected, places=2)

    def test_critical_depth_trapezoidal(self):
        from canals import OpenChannelFlow
        ch = OpenChannelFlow()
        ch.channel_type = 'trapezoidal'
        ch.channel_params = {'b': 3.0, 'z': 1.5}
        ch.flow_params = {'Q': 10.0, 'S0': 0.001, 'n': 0.015,
                          'y_initial': 2.0, 'L': 1000.0}
        yc = ch.calculate_critical_depth()
        self.assertGreater(yc, 0)
        self.assertLess(yc, 10.0)

    def test_normal_depth_horizontal(self):
        from canals import OpenChannelFlow
        ch = OpenChannelFlow()
        ch.channel_type = 'rectangular'
        ch.channel_params = {'b': 5.0, 'z': 0}
        ch.flow_params = {'Q': 10.0, 'S0': 0.0, 'n': 0.015,
                          'y_initial': 2.0, 'L': 1000.0}
        yn = ch.calculate_normal_depth()
        self.assertEqual(yn, float('inf'))


class TestHydraulicJump(unittest.TestCase):
    """Tests for canals.hydraulic_jump — Bélanger + USBR basin."""

    def test_basic_jump(self):
        from canals import HydraulicJumpInput, HydraulicJumpAnalyzer
        an = HydraulicJumpAnalyzer()
        # Use HydraulicJumpInput dataclass
        inp = HydraulicJumpInput(
            velocity_u1=8.0, depth_y1=0.5, width_b=5.0,
            slope=0.0, friction_coefficient=0.015, soil_type='rock',
        )
        jump, basin = an.analyze_and_design(inp)
        # jump is a HydraulicJumpResults object
        self.assertIsNotNone(jump)
        self.assertGreater(jump.depth_y2, 0.5)  # conjugate > upstream


class TestWaterHammer(unittest.TestCase):
    """Tests for canals.water_hammer — Korteweg + Joukowsky."""

    def test_wave_speed_steel(self):
        from canals import PipeParameters, FluidProperties, WaterHammerAnalyzer
        pipe = PipeParameters(
            length=1500, diameter=0.6, wall_thickness=0.012,
            elastic_modulus=200e9, poisson_ratio=0.30, yield_strength=400e6,
        )
        fluid = FluidProperties(density=1000.0, bulk_modulus=2.2e9)
        an = WaterHammerAnalyzer()
        a = an.calculate_wave_speed(pipe, fluid)
        # Wave speed in steel ~ 1200 m/s
        self.assertGreater(a, 1000)
        self.assertLess(a, 1300)

    def test_joukowsky_pressure(self):
        from canals import PipeParameters, FluidProperties, WaterHammerAnalyzer
        pipe = PipeParameters(
            length=1500, diameter=0.6, wall_thickness=0.012,
            elastic_modulus=200e9, poisson_ratio=0.30, yield_strength=400e6,
        )
        fluid = FluidProperties(density=1000.0, bulk_modulus=2.2e9)
        an = WaterHammerAnalyzer()
        a = an.calculate_wave_speed(pipe, fluid)
        delta_p = an.calculate_joukowsky_pressure(wave_speed=a, velocity_change=2.5, fluid_density=1000.0)
        # Joukowsky: delta_P = rho * a * delta_V
        # For rho=1000, a~1210, dV=2.5: ~3.0 MPa = 30 bar
        self.assertGreater(delta_p, 25e5)
        self.assertLess(delta_p, 35e5)


class TestForms(unittest.TestCase):
    """Tests that all 6 MDI forms import correctly."""

    def test_forms_import(self):
        from canals.ui.forms import (
            OpenChannelForm, StructuresForm, EarthCanalForm,
            FlowProfileForm, HydraulicJumpForm, WaterHammerForm,
        )
        for cls in (OpenChannelForm, StructuresForm, EarthCanalForm,
                    FlowProfileForm, HydraulicJumpForm, WaterHammerForm):
            self.assertIsNotNone(cls)


class TestCLI(unittest.TestCase):
    """Test the CLI module imports correctly."""

    def test_cli_imports(self):
        from canals import cli
        self.assertIsNotNone(cli)


if __name__ == "__main__":
    unittest.main()
