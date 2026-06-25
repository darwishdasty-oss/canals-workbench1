"""
canals/ui/forms/_widgets.py - Reusable widgets for the Canals forms.

Provides:
  - LabeledInput: QLineEdit + label + unit + optional default value.
    Accepts any numeric value (no min/max constraints) with built-in
    validation. Falls back to the default if the input is empty or invalid.
  - ChannelTypeSelector: a tabbed selector for the 4 supported channel types.
  - ResultTable: a sortable, monospaced QTableWidget for displaying numeric results.

These widgets are designed so the user can enter any value, not constrained
to preset limits. Validation is permissive: a bad value just shows a red
border and uses the last-known good value.
"""
from __future__ import annotations
from typing import Optional, Callable, Any, List, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (QLineEdit, QLabel, QHBoxLayout, QVBoxLayout,
                                QFormLayout, QFrame, QSizePolicy, QToolButton)
from PySide6.QtCore import Qt, Signal


# ---------------------------------------------------------------------------
# Numeric line edit with validation
# ---------------------------------------------------------------------------

class NumericLineEdit(QLineEdit):
    """A QLineEdit that accepts any positive (or signed) numeric value.

    No min/max constraints are imposed. If the user enters an invalid value
    the field is highlighted in red, but the previous good value is kept
    internally so callers can fall back gracefully.
    """
    valueChanged = Signal(float)  # emitted whenever a valid value is entered

    def __init__(self, default: float = 1.0, allow_negative: bool = False,
                 decimals: int = 6, parent=None):
        super().__init__(parent)
        self._default = float(default)
        self._allow_negative = allow_negative
        self._decimals = decimals
        self._last_good = float(default)
        self.setText(self._format(default))
        self.setMaximumWidth(180)
        self.setMinimumWidth(120)
        font = QtGui.QFont("Courier", 10)
        self.setFont(font)
        self.setClearButtonEnabled(True)
        self.textChanged.connect(self._on_text_changed)

    def _format(self, v: float) -> str:
        return f"{v:.{self._decimals}g}"

    def value(self) -> float:
        """Return the current value (default if invalid)."""
        try:
            txt = self.text().strip()
            if not txt:
                return self._default
            v = float(txt)
            if not self._allow_negative and v < 0:
                return self._default
            return v
        except (ValueError, TypeError):
            return self._default

    def setValue(self, v: float) -> None:
        self._last_good = float(v)
        self.setText(self._format(v))

    def _on_text_changed(self, text: str) -> None:
        v = self._safe_parse(text)
        if v is not None:
            self._last_good = v
            self.setStyleSheet("")
            self.valueChanged.emit(v)
        else:
            # Highlight as invalid but don't overwrite the last good value
            self.setStyleSheet("QLineEdit { border: 2px solid #B8500A; background: #FFF5F5; }")

    def _safe_parse(self, text: str) -> Optional[float]:
        try:
            t = text.strip()
            if not t:
                return None
            v = float(t)
            if not self._allow_negative and v < 0:
                return None
            if v != v:  # NaN
                return None
            if v == float('inf') or v == float('-inf'):
                return None
            return v
        except (ValueError, TypeError):
            return None


# ---------------------------------------------------------------------------
# Labeled input: label + line edit + unit
# ---------------------------------------------------------------------------

class LabeledInput(QtWidgets.QWidget):
    """A label + numeric line edit + unit suffix, stacked horizontally.

    Used as the standard input widget in the Canals forms. No min/max
    constraints: the user can enter any positive real number.
    """
    valueChanged = Signal(float)

    def __init__(self, label: str, default: float = 1.0, unit: str = "",
                 tooltip: str = "", allow_negative: bool = False,
                 decimals: int = 6, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        self._lbl = QLabel(label)
        self._lbl.setMinimumWidth(140)
        self._lbl.setMaximumWidth(180)
        layout.addWidget(self._lbl)

        self._edit = NumericLineEdit(default=default, allow_negative=allow_negative,
                                      decimals=decimals)
        layout.addWidget(self._edit)

        if unit:
            self._unit = QLabel(unit)
            self._unit.setMinimumWidth(60)
            self._unit.setStyleSheet("color: #666;")
            layout.addWidget(self._unit)
        else:
            self._unit = None

        layout.addStretch(1)

        if tooltip:
            self.setToolTip(tooltip)
            self._edit.setToolTip(tooltip)

        self._edit.valueChanged.connect(self.valueChanged)

    def value(self) -> float:
        return self._edit.value()

    def setValue(self, v: float) -> None:
        self._edit.setValue(v)


# ---------------------------------------------------------------------------
# Channel type selector
# ---------------------------------------------------------------------------

class ChannelTypeSelector(QtWidgets.QWidget):
    """A radio-button group for the 4 supported channel types."""

    selectionChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self._group = QtWidgets.QButtonGroup(self)
        self._buttons = {}
        options = [
            ("trapezoidal", "Trapezoidal"),
            ("rectangular", "Rectangular"),
            ("triangular", "Triangular"),
            ("circular", "Circular"),
        ]
        for i, (key, label) in enumerate(options):
            btn = QtWidgets.QRadioButton(label)
            btn.setChecked(i == 0)
            layout.addWidget(btn)
            self._group.addButton(btn, i)
            self._buttons[key] = btn
        self._group.idClicked.connect(self._on_clicked)
        layout.addStretch(1)

    def _on_clicked(self, btn_id: int) -> None:
        for key, btn in self._buttons.items():
            if self._group.id(btn) == btn_id:
                self.selectionChanged.emit(key)
                return

    def value(self) -> str:
        for key, btn in self._buttons.items():
            if btn.isChecked():
                return key
        return "trapezoidal"


# ---------------------------------------------------------------------------
# Result table
# ---------------------------------------------------------------------------

class ResultTable(QtWidgets.QTableWidget):
    """A monospaced, read-only QTableWidget for showing computed results.

    Two-column layout by default: parameter name + value. Supports multi-column.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        font = QtGui.QFont("Courier", 9)
        self.setFont(font)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #F5F5F5;
                gridline-color: #DDD;
            }
            QHeaderView::section {
                background-color: #1A3A6C;
                color: white;
                padding: 4px;
                border: none;
                font-weight: bold;
            }
        """)

    def populate(self, results: dict) -> None:
        """Populate the table from a nested dict. Sub-dicts are flattened with a slash."""
        flat = self._flatten(results)
        self.setRowCount(len(flat))
        for row, (k, v) in enumerate(flat):
            self.setItem(row, 0, QtWidgets.QTableWidgetItem(str(k)))
            self.setItem(row, 1, QtWidgets.QTableWidgetItem(self._fmt(v)))
        self.resizeColumnsToContents()
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

    def _flatten(self, d: dict, prefix: str = "") -> List[Tuple[str, Any]]:
        out = []
        for k, v in d.items():
            key = f"{prefix}{k}" if not prefix else f"{prefix}/{k}"
            if isinstance(v, dict):
                out.extend(self._flatten(v, prefix=key))
            else:
                out.append((key, v))
        return out

    def _fmt(self, v: Any) -> str:
        if isinstance(v, float):
            if abs(v) < 1e-3 and v != 0:
                return f"{v:.4e}"
            return f"{v:.4f}"
        if isinstance(v, (list, tuple)) and len(v) > 8:
            return f"[{type(v).__name__}, len={len(v)}]"
        if isinstance(v, str) and len(v) > 80:
            return v[:77] + "..."
        return str(v)


# ---------------------------------------------------------------------------
# Section frame: a titled group box with a vertical layout
# ---------------------------------------------------------------------------

class SectionFrame(QtWidgets.QGroupBox):
    """A titled section frame with a vertical layout."""

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #CCC;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: #1A3A6C;
            }
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 12, 8, 8)
        self._layout.setSpacing(4)

    def addWidget(self, w: QtWidgets.QWidget) -> None:
        self._layout.addWidget(w)

    def addLayout(self, l) -> None:
        self._layout.addLayout(l)
