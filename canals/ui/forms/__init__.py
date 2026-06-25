"""canals.ui.forms — MDI form widgets."""
from .open_channel_form import OpenChannelForm
from .structures_form import StructuresForm
from .earth_canal_form import EarthCanalForm
from .flow_profile_form import FlowProfileForm
from .hydraulic_jump_form import HydraulicJumpForm
from .water_hammer_form import WaterHammerForm

__all__ = [
    "OpenChannelForm", "StructuresForm", "EarthCanalForm",
    "FlowProfileForm", "HydraulicJumpForm", "WaterHammerForm",
]
