"""Command-line interface for Canals Workbench."""
import argparse
import json
import sys


def cmd_open_channel(args):
    from canals import AdvancedChannelDesigner, ChannelType
    designer = AdvancedChannelDesigner()
    result = designer.design_optimal_section(
        args.Q, args.n, args.S,
        channel_type=ChannelType.TRAPEZOIDAL if args.type == "trapezoidal" else ChannelType.RECTANGULAR,
    )
    print(json.dumps(result, indent=2, default=str))


def cmd_earth_canal(args):
    from canals import EarthCanalDesigner
    designer = EarthCanalDesigner()
    if args.method == "lacey":
        result = designer.lacey_theory_design(args.Q, args.f, args.z)
    elif args.method == "kennedy":
        result = designer.kennedy_theory_design(args.Q, args.n, args.S)
    elif args.method == "manning":
        result = designer.manning_design(Q=args.Q, n=args.n, S=args.S, side_slope=args.z)
    else:
        print(f"Unknown method: {args.method}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, indent=2, default=str))


def cmd_flow_profile(args):
    from canals import OpenChannelFlow
    ch = OpenChannelFlow()
    ch.channel_type = args.type
    ch.channel_params = {"b": args.b, "z": args.z}
    ch.flow_params = {
        "Q": args.Q, "S0": args.S, "n": args.n,
        "y_initial": args.y0, "L": args.L,
    }
    yc = ch.calculate_critical_depth()
    yn = ch.calculate_normal_depth()
    # Try various solve_profile method names
    sol = None
    for m in ("solve_profile", "solve_gvf", "solve", "compute_profile"):
        try:
            sol = getattr(ch, m)()
            break
        except AttributeError:
            continue
    print(json.dumps({
        "y_critical": yc,
        "y_normal": yn if yn != float("inf") else None,
        
    }, indent=2, default=str))


def cmd_hydraulic_jump(args):
    from canals import HydraulicJumpAnalyzer, HydraulicJumpInput
    an = HydraulicJumpAnalyzer()
    inp = HydraulicJumpInput(
        velocity_u1=args.V1, depth_y1=args.y1, width_b=args.b,
        slope=args.S, friction_coefficient=args.n, soil_type=args.soil,
    )
    jump, basin = an.analyze_and_design(inp)
    res = {
        'Fr1': jump.froude_number_1,
        'y2': jump.depth_y2,
        'jump_type': jump.jump_type,
        'basin_type': basin.basin_type,
        'basin_length': basin.basin_length,
        'energy_loss': jump.energy_loss,
        'efficiency_pct': jump.jump_efficiency * 100,
    }
    print(json.dumps(res, indent=2, default=str))


def cmd_water_hammer(args):
    from canals import PipeMaterial, PipeParameters, FluidProperties, WaterHammerAnalyzer
    # Material properties
    E, nu, sigma_y = 200e9, 0.30, 400e6  # steel default
    if args.material == "DI":
        E, nu, sigma_y = 170e9, 0.28, 300e6
    elif args.material == "PVC":
        E, nu, sigma_y = 3e9, 0.40, 50e6
    elif args.material == "concrete":
        E, nu, sigma_y = 30e9, 0.20, 30e6
    pipe = PipeParameters(
        length=args.L, diameter=args.D, wall_thickness=args.e,
        elastic_modulus=E, poisson_ratio=nu, yield_strength=sigma_y,
    )
    fluid = FluidProperties(density=1000.0, bulk_modulus=2.2e9)
    an = WaterHammerAnalyzer()
    a = an.calculate_wave_speed(pipe, fluid)
    t_c = an.calculate_critical_time(args.L, a)
    delta_p = an.calculate_joukowsky_pressure(wave_speed=a, velocity_change=args.V, fluid_density=1000.0)
    sigma_h = args.P_op * args.D / (2 * args.e)  # thin-wall
    SF = sigma_y / sigma_h if sigma_h > 0 else float('inf')
    res = {
        'wave_speed_m_s': a,
        'critical_closure_time_s': t_c,
        'joukowsky_pressure_Pa': delta_p,
        'joukowsky_pressure_bar': delta_p / 1e5,
        'hoop_stress_Pa': sigma_h,
        'hoop_stress_MPa': sigma_h / 1e6,
        'safety_factor': SF,
    }
    print(json.dumps(res, indent=2, default=str))


def cmd_structures(args):
    from canals import GateDesigner, SiphonDesigner, PressureBreakerDesigner
    if args.struct_type == "sluice":
        gd = GateDesigner()
        result = gd.design_sluice_gate(args.Q, args.H_up, args.H_down, args.b, args.a)
    elif args.struct_type == "siphon":
        sd = SiphonDesigner()
        result = sd.design_siphon(args.Q, args.H, args.L)
    elif args.struct_type == "breaker":
        pbd = PressureBreakerDesigner()
        result = pbd.design_optimal_breaker(args.Q, args.H, args.L)
    else:
        print(f"Unknown structure type: {args.struct_type}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(
        prog="canals-cli",
        description="Canals Workbench — command-line interface for batch processing",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # open-channel
    p = sub.add_parser("open-channel", help="Optimal open-channel section design")
    p.add_argument("--Q", type=float, required=True, help="Discharge (m³/s)")
    p.add_argument("--n", type=float, required=True, help="Manning roughness")
    p.add_argument("--S", type=float, required=True, help="Bed slope (m/m)")
    p.add_argument("--type", default="trapezoidal", choices=["trapezoidal", "rectangular"])
    p.set_defaults(func=cmd_open_channel)

    # earth-canal
    p = sub.add_parser("earth-canal", help="Earth canal design")
    p.add_argument("--Q", type=float, required=True)
    p.add_argument("--method", choices=["lacey", "kennedy", "manning"], required=True)
    p.add_argument("--f", type=float, default=1.0, help="Lacey silt factor")
    p.add_argument("--z", type=float, default=0.5, help="Side slope")
    p.add_argument("--n", type=float, default=0.0225)
    p.add_argument("--S", type=float, default=0.0004)
    p.set_defaults(func=cmd_earth_canal)

    # flow-profile
    p = sub.add_parser("flow-profile", help="Water-surface profile")
    p.add_argument("--Q", type=float, required=True)
    p.add_argument("--type", default="rectangular", choices=["rectangular", "trapezoidal", "triangular"])
    p.add_argument("--b", type=float, default=5.0)
    p.add_argument("--z", type=float, default=0.0)
    p.add_argument("--S", type=float, default=0.001)
    p.add_argument("--n", type=float, default=0.015)
    p.add_argument("--y0", type=float, default=2.0)
    p.add_argument("--L", type=float, default=1000.0)
    p.set_defaults(func=cmd_flow_profile)

    # hydraulic-jump
    p = sub.add_parser("hydraulic-jump", help="Hydraulic jump analysis")
    p.add_argument("--V1", type=float, required=True, help="Upstream velocity (m/s)")
    p.add_argument("--y1", type=float, required=True, help="Upstream depth (m)")
    p.add_argument("--b", type=float, required=True, help="Channel width (m)")
    p.add_argument("--S", type=float, default=0.0)
    p.add_argument("--n", type=float, default=0.015)
    p.add_argument("--soil", default="medium_silt")
    p.set_defaults(func=cmd_hydraulic_jump)

    # water-hammer
    p = sub.add_parser("water-hammer", help="Water hammer analysis")
    p.add_argument("--L", type=float, required=True, help="Pipe length (m)")
    p.add_argument("--D", type=float, required=True, help="Diameter (m)")
    p.add_argument("--e", type=float, required=True, help="Wall thickness (m)")
    p.add_argument("--V", type=float, required=True, help="Flow velocity (m/s)")
    p.add_argument("--t_c", type=float, required=True, help="Closure time (s)")
    p.add_argument("--P_op", type=float, default=5e5, help="Operating pressure (Pa)")
    p.add_argument("--material", default="steel")
    p.set_defaults(func=cmd_water_hammer)

    # structures
    p = sub.add_parser("structures", help="Hydraulic structures")
    p.add_argument("--type", dest="struct_type", required=True, choices=["sluice", "siphon", "breaker"])
    p.add_argument("--Q", type=float, required=True)
    p.add_argument("--b", type=float, default=3.0)
    p.add_argument("--a", type=float, default=0.4, help="Gate opening (m)")
    p.add_argument("--H_up", type=float, default=4.0)
    p.add_argument("--H_down", type=float, default=1.0)
    p.add_argument("--H", type=float, default=3.0, help="Head (for siphon/breaker)")
    p.add_argument("--L", type=float, default=20.0, help="Length (for siphon/breaker)")
    p.set_defaults(func=cmd_structures)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
