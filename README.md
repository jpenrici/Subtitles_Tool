# SRT to MP3 Converter (Subtitles_Tool)

Convert subtitle files (`.srt`) into MP3 audio using **Google Text-to-Speech (gTTS)**.
Pauses are automatically inserted based on subtitle timing.
A simple **PySide6** GUI is available to make the process easy!

---

## Features

- Converts `.srt` subtitle files into spoken `.mp3` files.
- Automatically inserts silent pauses matching the subtitle timing.
- Optionally saves each voice clip separately (`--voices` option).
- Generates a CSV history file with timings and texts.
- PySide6 GUI included (no need for command line).

---

## Requirements

- Python 3.12+
- Install required libraries:

```bash
pip install PySide6 gTTS pydub
```

You also need **ffmpeg** installed for audio processing:  
(On Ubuntu/Debian)
```bash
sudo apt install ffmpeg
```
(On Windows: [Download FFMPEG](https://ffmpeg.org/download.html))

---

## How to Use

### 1. Command Line Usage

```bash
python srt_to_mp3.py srt=<input_file.srt> mp3=<output_file.mp3> format=kdenlive
```

Optional: Save individual voice clips:

```bash
python srt_to_mp3.py srt=<input_file.srt> mp3=<output_file.mp3> format=kdenlive --voices
```

Example:
```bash
python srt_to_mp3.py srt="example.kdenlive.srt" mp3="output.mp3"
```

---

### 2. Graphical User Interface (GUI)

```bash
python srt_converter_gui.py
```

Through the GUI you can:
- Select your SRT file.
- Choose where to save the MP3.
- Enable "Save voice clips separately" if needed.
- Click **Convert** to start!

---

## Output Files

- The final **MP3** file with all speech and pauses combined.
- (Optional) Individual MP3 files for each subtitle line if `--voices` is selected.
- A **CSV file** listing:
  - Start time
  - Duration
  - Spoken text or silence

---

## Project Structure

```bash
🔹 srt_to_mp3.py        # Main converter script (command line)
🔹 srt_converter_gui.py # GUI application using PySide6
🔹 example.kdenlive.srt # Example input subtitle file
🔹 ouput.mp3            # Result of converting the example file
🔹 output_history.csv   # Conversion step by step
🔹 README.md            # Project documentation
```

---

## License

This project is released under the MIT License.
Feel free to use, modify, and distribute it!

---

