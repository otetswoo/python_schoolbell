#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reusable volume slider widget for sound settings dialogs and the main window."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider, QWidget


class VolumeControl(QWidget):
    """Horizontal volume control with a text label, slider, and percent value."""

    value_changed = Signal(int)

    def __init__(self, title, value, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.title_label = QLabel(title)
        self.title_label.setMinimumWidth(100)
        layout.addWidget(self.title_label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setSingleStep(5)
        self.slider.setPageStep(10)
        self.slider.setValue(value)
        self.slider.setToolTip(title)
        layout.addWidget(self.slider, 1)

        self.value_label = QLabel()
        self.value_label.setMinimumWidth(42)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.value_label)

        self.slider.valueChanged.connect(self._on_slider_changed)
        self._set_value_label(value)

    def value(self):
        """Return the current volume value in percent."""
        return self.slider.value()

    def set_title(self, title):
        """Update visible label and tooltip text."""
        self.title_label.setText(title)
        self.slider.setToolTip(title)

    def _set_value_label(self, value):
        self.value_label.setText(f"{value}%")

    def _on_slider_changed(self, value):
        self._set_value_label(value)
        self.value_changed.emit(value)
