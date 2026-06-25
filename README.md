# Canals — Open-Channel Design Workbench

A standalone Python 3 / PySide6 workbench for open-channel hydraulic design, decoupled from the Cavitation & Channel Workbench (CCW) v1.4.

This is the **Canals sub-package of CCW** extracted into its own installable, distributable program.

## Features

**6 forms, 6 menus** covering the full open-channel design workflow:

| # | Menu | Algorithm | Standards |
|---|---|---|---|
| 1 | Open Channel | Optimal trapezoidal/rectangular/triangular/circular sections, Manning, critical/normal depth, specific energy | Custom + Manning 1889 |
| 2 | Hydraulic Structures | Sluice + radial gates (Cd, force), siphons (with σ cavitation check), pressure breakers (auto-select) | USBR |
| 3 | Earth Canal | Lacey silt theory + Kennedy CVR + Manning + side-by-side compare | Lacey 1930, Kennedy 1895 |
| 4 | Flow Profile | GVF solver via `scipy.integrate.solve_ivp` (RK45), 12-curve M1/M2/M3/S1-S3/C1/C3/H2/H3/A2/A3 classification | Chow 1959 |
| 5 | Hydraulic Jump | Bélanger conjugate + USBR Type I-IV stilling basin selection + appurtenance dimensions | USBR Design of Small Dams 1987 |
| 6 | Water Hammer | Korteweg wave speed + Joukowsky pressure rise + hoop stress + safety factor + 4 engineering recommendations | Korteweg 1878, Joukowsky 1900 |

**Plus:** CLI mode (`canals-cli`), JSON/CSV/PDF export, 20+ unit tests.

## Installation

### Option 1 — pip install (recommended)

```bash
pip install canals-workbench
canals           # launches the GUI
canals-cli --help   # launches the CLI
```

### Option 2 — from source

```bash
git clone https://github.com/abbas-hebah/canals-workbench.git
cd canals-workbench
pip install -e .
canals
```

### Option 3 — standalone binary (no Python needed)

Download from the releases page:
- Linux:   `Canals-v1.4-linux-x86_64`     (~ 50 MB)
- Windows: `Canals-v1.4-windows-x64.exe`   (~ 50 MB)
- macOS:   `Canals-v1.4-macos-universal`   (~ 70 MB)

Just run the executable — no installation required.

## CLI usage

```bash
# Optimal open-channel section
canals-cli open-channel --Q 15 --n 0.025 --S 0.0008

# Earth canal — Lacey theory
canals-cli earth-canal --Q 15 --method lacey --f 1.0 --z 0.5

# Earth canal — Kennedy
canals-cli earth-canal --Q 15 --method kennedy --n 0.0225 --S 0.0004

# Flow profile (GVF)
canals-cli flow-profile --Q 15 --type rectangular --b 5 --S 0.0008 --n 0.015 --y0 2.5 --L 1000

# Hydraulic jump + stilling basin
canals-cli hydraulic-jump --V1 8 --y1 0.5 --b 5 --n 0.015

# Water hammer
canals-cli water-hammer --L 1500 --D 0.6 --e 0.012 --V 2.5 --t_c 0.2

# Hydraulic structures
canals-cli structures --type sluice --Q 15 --b 3 --a 0.4 --H_up 4 --H_down 1
canals-cli structures --type siphon --Q 5 --H 3 --L 20
canals-cli structures --type breaker --Q 5 --H 3 --L 15
```

All commands output structured JSON to stdout, suitable for piping into other tools.

## Quick start — the 6 standard test cases

These 6 cases are pre-validated against hand calculations and CCW v1.4:

| Form | Input | Expected |
|---|---|---|
| Open Channel | Q=15, n=0.025, S=0.0008 | Trapezoidal: b=2.88, z=0.61, y=2.55, A=11.3 |
| Structures (sluice) | Q=15, H_up=4, H_down=1, b=3, a=0.4 | Cd=0.58, F=573 kN |
| Earth Canal (Lacey) | Q=15, f=1, z=0.5 | y=5.21, b=4.32, A=49.7 |
| Flow Profile | Q=15, S=0.0008, b=5, y_0=2.5 | y_c=0.97, y_n=2.34, mild M1 |
| Hydraulic Jump | V=8, y=0.5, b=5 | Fr₁=3.61, y₂=2.32, USBR Type III |
| Water Hammer | L=1500, D=0.6, e=0.012, V=2.5, t_c=0.2 | a=1210.9 m/s, ΔP=30.3 bar, SF=3.30 |

## What's in this directory

```
canals_workbench/
├── pyproject.toml           # pip-installable package metadata
├── README.md                # this file
├── LICENSE                  # MIT
├── canals_mdi.py            # standalone launcher (entry point)
├── canals/
│   ├── __init__.py
│   ├── cli.py               # canals-cli command
│   ├── open_channel.py      # algorithm
│   ├── structures.py        # algorithm
│   ├── earth_canal.py       # algorithm
│   ├── flow_profile.py      # algorithm
│   ├── hydraulic_jump.py    # algorithm
│   ├── water_hammer.py      # algorithm
│   └── ui/
│       └── forms/           # PySide6 MDI forms (6 forms + shared widgets)
├── tests/
│   └── test_canals.py       # 20+ unit tests
├── docs/
│   └── USER_GUIDE.md
├── bin/                     # build scripts
│   ├── build_linux.sh
│   ├── build_windows.bat
│   └── build_macos.sh
└── figures/                 # documentation figures
```

## Relationship to CCW v1.4

CCW v1.4 = Cavitation & Channel Workbench = Cavicuspill + EM-Py + **Canals** + Bridge + MDI shell

This standalone package is just the **Canals** third of CCW, decoupled from the spillway-design and Falvey-analysis workflows. If you also need cavitation analysis, use CCW v1.4 (https://github.com/abbas-hebah/cavitation-channel-workbench).

## Author

**Abbas A. Hebah** — Ph.D. Candidate, Department of Civil Engineering, Iran University of Science and Technology. abbas74.hebah@gmail.com

## License

MIT — see LICENSE.
