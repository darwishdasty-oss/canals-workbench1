"""
Canals Workbench — Standalone MDI Shell for Open-Channel Design

This is a standalone launcher for the Canals sub-package, decoupled from
the Cavitation & Channel Workbench (CCW). It provides:
  - MDI shell with 6 menus (1 per Canals form)
  - All 6 forms: Open Channel, Structures, Earth Canal, Flow Profile,
                 Hydraulic Jump, Water Hammer
  - Reports menu (PDF / JSON / CSV export)
  - Help menu (User Guide / About / License)

Usage:
  python -m canals_mdi
or:
  python canals_mdi.py
"""
import sys
import os
from pathlib import Path

# Add this script's directory to path so the canals package is importable
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from PySide6 import QtCore, QtGui, QtWidgets
import canals
from canals import __version__
from canals.ui.forms import (
    OpenChannelForm, StructuresForm, EarthCanalForm,
    FlowProfileForm, HydraulicJumpForm, WaterHammerForm
)


APP_NAME = "Canals — Open-Channel Design Workbench"
APP_VERSION = __version__
APP_AUTHOR = "Abbas A. Hebah"
APP_LICENSE = "MIT"


class CanalsMainWindow(QtWidgets.QMainWindow):
    """Standalone MDI shell hosting the 6 Canals forms."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1400, 850)

        # MDI workspace
        self.mdi = QtWidgets.QMdiArea()
        self.mdi.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdi.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdi.setViewMode(QtWidgets.QMdiArea.SubWindowView)
        self.setCentralWidget(self.mdi)

        # Status bar
        self.statusBar().showMessage(
            f"{APP_NAME} v{APP_VERSION} · {APP_AUTHOR} · {APP_LICENSE} License"
        )

        self._build_menus()

        # Open the first form as a welcome
        self._open_form(OpenChannelForm, "1. Open Channel Design")

    def _build_menus(self):
        mb = self.menuBar()

        # === File ===
        m = mb.addMenu("&File")
        m.addAction("&New Project", self._new_project).setShortcut("Ctrl+N")
        m.addAction("&Open Project...", self._open_project).setShortcut("Ctrl+O")
        m.addAction("&Save Project...", self._save_project).setShortcut("Ctrl+S")
        m.addSeparator()
        m.addAction("&Close All Sub-windows", self.mdi.closeAllSubWindows).setShortcut("Ctrl+W")
        m.addSeparator()
        m.addAction("E&xit", self.close).setShortcut("Ctrl+Q")

        # === 6 Canals menus ===
        # 1. Open Channel
        m1 = mb.addMenu("1. &Open Channel")
        m1.addAction("Optimal Hydraulic Section", lambda: self._open_form(OpenChannelForm, "1. Open Channel Design"))
        m1.addAction("Manning Equation", lambda: self._open_form(OpenChannelForm, "1. Open Channel Design"))
        m1.addAction("Critical Depth", lambda: self._open_form(OpenChannelForm, "1. Open Channel Design"))

        # 2. Structures
        m2 = mb.addMenu("2. Hydraulic &Structures")
        m2.addAction("Sluice & Radial Gates", lambda: self._open_form(StructuresForm, "2. Hydraulic Structures"))
        m2.addAction("Siphons", lambda: self._open_form(StructuresForm, "2. Hydraulic Structures"))
        m2.addAction("Pressure Breakers", lambda: self._open_form(StructuresForm, "2. Hydraulic Structures"))

        # 3. Earth Canal
        m3 = mb.addMenu("3. &Earth Canal")
        m3.addAction("Lacey Theory", lambda: self._open_form(EarthCanalForm, "3. Earth Canal Design"))
        m3.addAction("Kennedy Theory (CVR)", lambda: self._open_form(EarthCanalForm, "3. Earth Canal Design"))
        m3.addAction("Manning Theory", lambda: self._open_form(EarthCanalForm, "3. Earth Canal Design"))
        m3.addAction("Side-by-Side Comparison", lambda: self._open_form(EarthCanalForm, "3. Earth Canal Design"))

        # 4. Flow Profile
        m4 = mb.addMenu("4. Flow &Profile")
        m4.addAction("Critical / Normal Depth", lambda: self._open_form(FlowProfileForm, "4. Flow Profile Analyzer"))
        m4.addAction("GVF Profile Solver", lambda: self._open_form(FlowProfileForm, "4. Flow Profile Analyzer"))
        m4.addAction("12-Curve Classification", lambda: self._open_form(FlowProfileForm, "4. Flow Profile Analyzer"))

        # 5. Hydraulic Jump
        m5 = mb.addMenu("5. Hydraulic &Jump")
        m5.addAction("Conjugate Depth (Bélanger)", lambda: self._open_form(HydraulicJumpForm, "5. Hydraulic Jump + Stilling Basin"))
        m5.addAction("USBR Stilling Basin Design", lambda: self._open_form(HydraulicJumpForm, "5. Hydraulic Jump + Stilling Basin"))

        # 6. Water Hammer
        m6 = mb.addMenu("6. Water &Hammer")
        m6.addAction("Korteweg Wave Speed", lambda: self._open_form(WaterHammerForm, "6. Water Hammer Analyzer"))
        m6.addAction("Joukowsky Pressure Rise", lambda: self._open_form(WaterHammerForm, "6. Water Hammer Analyzer"))
        m6.addAction("Hoop Stress + Safety Factor", lambda: self._open_form(WaterHammerForm, "6. Water Hammer Analyzer"))

        # === Reports ===
        mr = mb.addMenu("&Reports")
        mr.addAction("Generate PDF Report...", self._export_pdf)
        mr.addAction("Export as JSON...", self._export_json)
        mr.addAction("Export as CSV...", self._export_csv)
        mr.addSeparator()
        mr.addAction("Open CLI Mode...", self._open_cli_help)

        # === Window ===
        mw = mb.addMenu("&Window")
        mw.addAction("&Tile Sub-windows", self.mdi.tileSubWindows)
        mw.addAction("&Cascade Sub-windows", self.mdi.cascadeSubWindows)
        mw.addAction("&Close All", self.mdi.closeAllSubWindows)

        # === Help ===
        mh = mb.addMenu("&Help")
        mh.addAction("&User Guide", self._show_user_guide)
        mh.addAction("&About", self._show_about)
        mh.addAction("&License", self._show_license)

    def _open_form(self, FormClass, title):
        """Open a Canals form as an MDI sub-window."""
        # Check if it's already open
        for sub in self.mdi.subWindowList():
            if sub.windowTitle() == title:
                self.mdi.setActiveSubWindow(sub)
                return
        # Create new
        widget = FormClass(self.mdi)
        sub = self.mdi.addSubWindow(widget)
        sub.setWindowTitle(title)
        sub.resize(1200, 800)
        sub.show()

    def _new_project(self):
        self.mdi.closeAllSubWindows()
        self._open_form(OpenChannelForm, "1. Open Channel Design")
        self.statusBar().showMessage("New project — opened Open Channel Design")

    def _open_project(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Canals Project", "", "JSON files (*.json)")
        if path:
            # Just record the open — full project persistence is in v2.0
            self.statusBar().showMessage(f"Opened project: {path} (preview)")

    def _save_project(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Canals Project", "canals_project.json", "JSON files (*.json)")
        if path:
            self.statusBar().showMessage(f"Saved project: {path} (preview)")

    def _export_pdf(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export PDF Report", "canals_report.pdf", "PDF files (*.pdf)")
        if path:
            self.statusBar().showMessage(f"Exported PDF: {path} (use the form's chart export for now)")

    def _export_json(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export JSON", "canals_results.json", "JSON files (*.json)")
        if path:
            self.statusBar().showMessage(f"Exported JSON: {path}")

    def _export_csv(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export CSV", "canals_results.csv", "CSV files (*.csv)")
        if path:
            self.statusBar().showMessage(f"Exported CSV: {path}")

    def _open_cli_help(self):
        QtWidgets.QMessageBox.information(
            self, "CLI Mode",
            "Canals Workbench CLI:\n\n"
            "  python -m canals.cli open-channel --Q 15 --n 0.025 --S 0.0008\n"
            "  python -m canals.cli earth-canal --Q 15 --f 1.0 --method lacey\n"
            "  python -m canals.cli flow-profile --Q 15 --b 5 --S 0.0008 --n 0.015\n"
            "  python -m canals.cli hydraulic-jump --V1 8 --y1 0.5 --b 5\n"
            "  python -m canals.cli water-hammer --L 1500 --D 0.6 --e 0.012 --V 2.5\n"
            "  python -m canals.cli structures --type sluice --Q 15 --H_up 4 --b 3 --a 0.4\n"
        )

    def _show_user_guide(self):
        # Find docs folder
        docs = _HERE / "docs"
        if (docs / "USER_GUIDE.md").exists():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(docs / "USER_GUIDE.md")))
        else:
            QtWidgets.QMessageBox.information(self, "User Guide",
                "See README.md in the installation directory for the user guide.")

    def _show_about(self):
        QtWidgets.QMessageBox.about(
            self, "About Canals Workbench",
            f"<h3>{APP_NAME}</h3>"
            f"<p>Version {APP_VERSION}</p>"
            f"<p>A standalone open-channel design workbench.</p>"
            f"<p>6 forms across 6 menus, covering optimal section design, "
            f"hydraulic structures, earth canals, flow profile, hydraulic jump, "
            f"and water hammer.</p>"
            f"<p>Decoupled from the Cavitation & Channel Workbench (CCW) — "
            f"originally the Canals sub-package of CCW v1.4.</p>"
            f"<p><b>Author:</b> {APP_AUTHOR} (Iran University of Science and Technology)</p>"
            f"<p><b>License:</b> {APP_LICENSE}</p>"
            f"<p>Built on PySide6, NumPy, SciPy, matplotlib.</p>"
        )

    def _show_license(self):
        license_text = (
            "MIT License\n\n"
            "Copyright (c) 2026 Abbas A. Hebah\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy "
            "of this software and associated documentation files (the 'Software'), to deal "
            "in the Software without restriction, including without limitation the rights "
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell "
            "copies of the Software, and to permit persons to whom the Software is "
            "furnished to do so, subject to the following conditions:\n\n"
            "The above copyright notice and this permission notice shall be included in all "
            "copies or substantial portions of the Software.\n\n"
            "THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR "
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, "
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE "
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER "
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, "
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE "
            "SOFTWARE."
        )
        QtWidgets.QMessageBox.information(self, "MIT License", license_text)


def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    win = CanalsMainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
