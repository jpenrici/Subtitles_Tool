# -*- coding: utf-8 -*-
"""
Experimenting with Google Text-to-Speech (gTTS) library to convert subtitles
to speech following time intervals.
"""

import sys

# PySide6
# https://doc.qt.io/qtforpython-6/
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog, QLabel,
    QLineEdit, QVBoxLayout, QHBoxLayout, QTextEdit, QCheckBox
)

from srt_to_mp3 import parse_arguments, text_to_speech, prepare


class SRTConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SRT to MP3 Converter")
        self.setMinimumWidth(500)

        # UI elements
        self.srt_input = QLineEdit()
        self.srt_button = QPushButton("Select SRT File")

        self.mp3_output = QLineEdit()
        self.mp3_button = QPushButton("Choose MP3 Output")

        self.voices_checkbox = QCheckBox("Save voice clips separately.")
        self.convert_button = QPushButton("Convert")
        self.status = QTextEdit()
        self.status.setReadOnly(True)

        self.setup_layout()
        self.setup_events()

    def setup_layout(self):
        layout = QVBoxLayout()

        # Row for SRT input
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("SRT File:"))
        row1.addWidget(self.srt_input)
        row1.addWidget(self.srt_button)
        layout.addLayout(row1)

        # Row for MP3 output
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("MP3 Output:"))
        row2.addWidget(self.mp3_output)
        row2.addWidget(self.mp3_button)
        layout.addLayout(row2)

        layout.addWidget(self.voices_checkbox)
        layout.addWidget(self.convert_button)
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status)

        self.setLayout(layout)

    def setup_events(self):
        self.srt_button.clicked.connect(self.select_srt_file)
        self.mp3_button.clicked.connect(self.select_mp3_file)
        self.convert_button.clicked.connect(self.run_conversion)

    def select_srt_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select SRT File", "", "SRT Files (*.srt)")
        if file_path:
            self.srt_input.setText(file_path)

    def select_mp3_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save MP3 File", "", "MP3 Files (*.mp3)")
        if file_path:
            self.mp3_output.setText(file_path)

    def run_conversion(self):
        self.status.clear()
        srt = self.srt_input.text().strip()
        mp3 = self.mp3_output.text().strip()
        voices = self.voices_checkbox.isChecked()

        if not srt or not mp3:
            self.status.append("Error: Please provide both SRT and MP3 paths.")
            return

        args = [f"srt={srt}", f"mp3={mp3}", "format=kdenlive"]
        if voices:
            args.append("--voices")

        self.status.append("Starting conversion...")

        data = parse_arguments(args)
        if not data:
            self.status.append("Failed to parse arguments.")
            return

        self.status.append("Reading and preparing subtitles...")
        data.lines = prepare(data)

        self.status.append("Converting to speech...")
        if text_to_speech(data):
            extra = " and voice clips" if data.mp3_voices else ""
            self.status.append(f"Success! MP3{extra} created at:\n{mp3}")
        else:
            self.status.append("Error: Could not generate MP3.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SRTConverterApp()
    window.show()
    sys.exit(app.exec())
