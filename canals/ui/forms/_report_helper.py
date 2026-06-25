"""
_report_helper — adds "Export Report (PDF)" capability to any Canals form.

Usage in any form:
    from ._report_helper import ReportButton

    # In _build_ui:
    self.btn_report = ReportButton(form_name='open_channel',
                                    inputs_getter=lambda: self._get_inputs(),
                                    result_getter=lambda: self._get_result())
    layout.addWidget(self.btn_report)

    # In form, define:
    def _get_inputs(self): return {'Q': 15, 'n': 0.025, ...}
    def _get_result(self): return {'bottom_width': 2.88, 'depth': 2.55, ...}

The button stays disabled until a result is set (call self.btn_report.set_result(r)).
"""
from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QPushButton, QFileDialog, QMessageBox


class ReportButton(QPushButton):
    """A reusable 'Export Report (PDF)' button.

    Each form sets a form_name (one of: open_channel, sluice_gate,
    earth_canal_lacey, earth_canal_manning, flow_profile,
    hydraulic_jump, water_hammer) and provides getter functions for
    inputs and result. When clicked, opens a save dialog and writes
    the PDF report.
    """

    def __init__(self, form_name: str, inputs_getter=None, result_getter=None,
                 extra_getter=None, parent=None):
        super().__init__("📄  Export Report (PDF)", parent)
        self.form_name = form_name
        self._inputs_getter = inputs_getter or (lambda: {})
        self._result_getter = result_getter or (lambda: {})
        self._extra_getter = extra_getter  # for hydraulic_jump (basin dict)

        self.setStyleSheet(
            "QPushButton { background: #2E7D32; color: white; padding: 8px; "
            "font-weight: bold; border: none; border-radius: 3px; } "
            "QPushButton:hover { background: #3E8D42; } "
            "QPushButton:disabled { background: #aaaaaa; }"
        )
        self.setEnabled(False)
        self.clicked.connect(self._on_click)

    def set_result(self, inputs, result, extra=None):
        """Update the cached inputs/result and enable the button."""
        self._cached_inputs = inputs
        self._cached_result = result
        self._cached_extra = extra
        self.setEnabled(True)

    def _on_click(self):
        try:
            inputs = self._cached_inputs
            result = self._cached_result
            if not inputs or not result:
                QMessageBox.warning(self.parent(), "No Result",
                                    "Run an analysis first, then click Export.")
                return
            path, _ = QFileDialog.getSaveFileName(
                self.parent(), "Save Report",
                f"{self.form_name}_report.pdf", "PDF files (*.pdf)")
            if not path:
                return

            # Late import to avoid circular dependency
            from canals.reports import (
                report_open_channel, report_sluice_gate,
                report_earth_canal_lacey, report_earth_canal_manning,
                report_flow_profile, report_hydraulic_jump, report_water_hammer,
                report_generic,
            )

            if self.form_name == 'open_channel':
                report_open_channel(inputs, result, path)
            elif self.form_name == 'sluice_gate':
                report_sluice_gate(inputs, result, path)
            elif self.form_name == 'earth_canal_lacey':
                report_earth_canal_lacey(inputs, result, path)
            elif self.form_name == 'earth_canal_manning':
                report_earth_canal_manning(inputs, result, path)
            elif self.form_name == 'flow_profile':
                report_flow_profile(inputs, result, path)
            elif self.form_name == 'hydraulic_jump':
                report_hydraulic_jump(inputs, result, self._cached_extra or {}, path)
            elif self.form_name == 'water_hammer':
                report_water_hammer(inputs, result, path)
            else:
                report_generic(self.form_name, inputs, result, path)

            QMessageBox.information(self.parent(), "Report Saved",
                                    f"Report saved to:\n{path}\n\n"
                                    "Contains your inputs + step-by-step solution.")
        except Exception as e:
            QMessageBox.critical(self.parent(), "Report Error", str(e))
