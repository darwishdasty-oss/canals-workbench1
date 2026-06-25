"""
canals — Hydraulic engineering design studio.

Five sub-modules:
  - open_channel: Trapezoidal/rectangular/triangular/circular/parabolic sections,
    Manning/Chezy/Bernoulli, critical/normal depth, specific-energy curve,
    gradually-varied flow, optimal hydraulic section
  - structures: Sluice & radial gates, siphons (with cavitation check),
    pressure breakers (stilling well / impact basin / cascade)
  - earth_canal: Lacey silt theory, Kennedy theory (CVR), side-by-side comparison
  - flow_profile: Open-channel water surface profile analyzer
    (critical/normal depth, GVF via solve_ivp, Froude number, M1/M2/M3/S1-S3/C1/C3 classification)
  - hydraulic_jump: Hydraulic jump analyzer + USBR stilling basin designer
    (Froude, jump type, Bélanger conjugate, energy loss, basin Types I-IV/sloped)
  - water_hammer: Water hammer pressure analysis (Korteweg wave speed, Joukowsky surge,
    critical closure time, hoop stress, safety factor, mitigation recommendations)

Original author:  خبير هندسة الموارد المائية (Water Resources Engineering Expert)
Original date:    2024
Original version: 3.0 Professional
Port: Abbas A. Hebah, 8 June 2026
"""
__version__ = "1.3.0"

from .open_channel import (
    ChannelType, FlowRegime, ChannelGeometry, FlowParameters,
    HydraulicTheories, AdvancedChannelDesigner
)
from .structures import (
    GateDesigner, SiphonDesigner, PressureBreakerDesigner,
    HydraulicStructuresSystem
)
from .earth_canal import EarthCanalDesigner
from .flow_profile import OpenChannelFlow
from .hydraulic_jump import (
    JumpType, BasinType, HydraulicJumpInput, HydraulicJumpResults,
    StillingBasinDesign, HydraulicJumpCalculator, StillingBasinDesigner,
    HydraulicJumpAnalyzer
)
from .water_hammer import (
    PipeMaterial, PipeParameters, FluidProperties, WaterHammerAnalyzer
)

__all__ = [
    "ChannelType", "FlowRegime", "ChannelGeometry", "FlowParameters",
    "HydraulicTheories", "AdvancedChannelDesigner",
    "GateDesigner", "SiphonDesigner", "PressureBreakerDesigner",
    "HydraulicStructuresSystem",
    "EarthCanalDesigner",
    "OpenChannelFlow",
    "JumpType", "BasinType", "HydraulicJumpInput", "HydraulicJumpResults",
    "StillingBasinDesign", "HydraulicJumpCalculator", "StillingBasinDesigner",
    "HydraulicJumpAnalyzer",
    "PipeMaterial", "PipeParameters", "FluidProperties", "WaterHammerAnalyzer",
]
