#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reusable volume slider widget for sound settings dialogs and the main window."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget


class VolumeControl(QWidget):
    """Reusable volume control with a text label, slider, and percent value."""

    value_changed = Signal(int)

    def __init__(
        self,
        title,
        value,
        parent=None,
        orientation=Qt.Horizontal,
        show_title=True,
    ):
        super().__init__(parent)

        self.orientation = orientation
        self._active = True
        if orientation == Qt.Vertical:
            layout = QVBoxLayout()
            label_alignment = Qt.AlignHCenter | Qt.AlignBottom
            value_alignment = Qt.AlignHCenter | Qt.AlignTop
        else:
            layout = QHBoxLayout()
            label_alignment = Qt.AlignLeft | Qt.AlignVCenter
            value_alignment = Qt.AlignRight | Qt.AlignVCenter

        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        self.setLayout(layout)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(label_alignment)
        if orientation == Qt.Vertical:
            self.title_label.setWordWrap(True)
            self.title_label.setMinimumWidth(58)
            self.title_label.setMaximumWidth(82)
        else:
            self.title_label.setMinimumWidth(100)
        self.title_label.setVisible(show_title)
        if show_title:
            layout.addWidget(self.title_label)

        self.slider = QSlider(orientation)
        self.slider.setRange(0, 100)
        self.slider.setSingleStep(5)
        self.slider.setPageStep(10)
        self.slider.setValue(value)
        self.slider.setToolTip(title)
        if orientation == Qt.Vertical:
            self.slider.setMinimumHeight(78)
            self.slider.setMaximumHeight(96)
        layout.addWidget(self.slider, 1)

        self.value_label = QLabel()
        self.value_label.setMinimumWidth(42)
        self.value_label.setAlignment(value_alignment)
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

    def set_value(self, value):
        """Set the current volume value in percent."""
        self.slider.setValue(value)

    def set_active(self, active):
        """Dim the control when playback is disabled without disabling the slider."""
        self._active = bool(active)
        if self._active:
            self.title_label.setStyleSheet("")
            self.value_label.setStyleSheet("")
            self.slider.setStyleSheet("")
            return

        muted_text = "color: #8a8f98;"
        self.title_label.setStyleSheet(muted_text)
        self.value_label.setStyleSheet(muted_text)
        if self.orientation == Qt.Vertical:
            groove = "QSlider::groove:vertical"
            handle = "QSlider::handle:vertical"
            add_page = "QSlider::add-page:vertical"
            sub_page = "QSlider::sub-page:vertical"
        else:
            groove = "QSlider::groove:horizontal"
            handle = "QSlider::handle:horizontal"
            add_page = "QSlider::add-page:horizontal"
            sub_page = "QSlider::sub-page:horizontal"
        self.slider.setStyleSheet(f"""
            {groove} {{ background: #d5d8dd; border-radius: 3px; }}
            {sub_page} {{ background: #c5c9d0; border-radius: 3px; }}
            {add_page} {{ background: #eceff3; border-radius: 3px; }}
            {handle} {{ background: #9aa1aa; border: 1px solid #858b94; border-radius: 6px; }}
        """)

    def _set_value_label(self, value):
        self.value_label.setText(f"{value}%")

    def _on_slider_changed(self, value):
        self._set_value_label(value)
        self.value_changed.emit(value)
