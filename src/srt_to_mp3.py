# -*- coding: utf-8 -*-
"""
Experimenting with Google Text-to-Speech (gTTS) library to convert subtitles
to speech following time intervals.
"""

import os.path
import re
import sys

from io import BytesIO
from typing import Tuple

# Google Text-to-Speech library.
# https://gtts.readthedocs.io/en/latest/index.html
from gtts import gTTS

# Pydub - Manipulate audio with a simple and easy high level interface.
# https://github.com/jiaaro/pydub
from pydub import AudioSegment


class Data:

    def __init__(self) -> None:
        # Files
        self.srt_filename: str = ""
        self.srt_path: str = ""
        self.mp3_filename: str = ""
        self.mp3_path: str = ""
        self.mp3_voices: bool = False
        # gTTS
        self.lines: list = []
        self.language: str = "pt-br"
        self.srt_format: str = ""
        self.token: str = "#WAIT:"

    def __str__(self) -> str:
        return (
            f"SRT Input  : \"{self.srt_filename}\" \n"
            f"SRT Path   : \"{self.srt_path}\" \n"
            f"MP3 Output : \"{self.mp3_filename}\" \n"
            f"MP3 Path   : \"{self.mp3_path}\" \n"
            f"Copy voices: {"Yes" if self.mp3_voices else "No"}"
        )

    def text(self) -> str:
        return "\n".join(self.lines)

    def text_min(self, characters: int = 5) -> str:
        return self.text()[:characters]

    def validate(self) -> bool:
        return all([
            self.srt_path,
            self.mp3_path,
            self.srt_format,
            len(self.lines) > 0
        ])


def text_to_speech(data: Data) -> bool:

    if not data.validate():
        return False

    # Audio segments.
    audio_parts = []

    # History and Copy voices
    history = "Time(ms);Duration(ms);Description\n"
    filename = data.mp3_filename.lower().replace(".mp3", "")
    output_dir = data.mp3_path.replace(data.mp3_filename, "")
    if output_dir == "":
        output_dir = "./"
    elif not output_dir.endswith("/"):
        output_dir += "/"

    def log_entry(start_ms: float, duration_ms: float, text: str) -> str:
        n1 = str(start_ms).replace(".", ",")
        n2 = str(duration_ms).replace(".", ",")
        return f"{n1}; {n2}; {text}\n"

    try:
        counter = 1
        total_ms = 0.0
        last_duration_ms : float = 0.0
        for part in data.lines:
            part = part.strip()
            if re.fullmatch("^" + data.token + ".+", part):
                wait = round(float(part.replace(data.token, "")) - last_duration_ms, 4)
                if wait > 0:
                    print(f"Creating silence for {wait} ms ...")
                    audio_parts.append(AudioSegment.silent(duration=wait))
                    # Record.
                    history += log_entry(total_ms, wait, "Silent.")
                    # Update.
                    total_ms += wait
            else:
                print(f"Generating speech for: {part}")
                # gTTS
                tts = gTTS(text=part, lang=data.language, slow=False)
                # Saves the audio to a BytesIO object.
                tts_fp = BytesIO()
                tts.write_to_fp(tts_fp)
                # Returns the cursor to the beginning of the buffer.
                tts_fp.seek(0)
                # Load audio from BytesIO using pydub.
                audio_part = AudioSegment.from_file(tts_fp, format="mp3")
                # Stores part.
                audio_parts.append(audio_part)
                # Get audio duration.
                last_duration_ms = len(audio_part)
                # Record.
                history += log_entry(total_ms, last_duration_ms, part)
                # Update.
                total_ms += last_duration_ms

                # Save copies.
                if data.mp3_voices:
                    tts.save(f"{output_dir}{filename}_part_{str(counter).zfill(3)}.mp3")
                    counter += 1

        # Save history.
        if history != "":
            save(f"{output_dir}{filename}_history.csv", history)

        # Finish conversion by joining muted parts and voices.
        if audio_parts:
            comments = f"Audio generated using the {data.srt_filename} file."
            final_audio = sum(audio_parts)
            final_audio.export(data.mp3_path, format="mp3", tags={'comments' : comments})
            return True

    except Exception as e:
        print(f"An error occurred: {type(e).__name__} - {e}")

    return False


def load(filename: str, text_coding: str ='UTF-8') -> list[str]:
    try:
        if os.path.exists(filename):
            with open(filename, encoding=text_coding) as f:
                return [line.strip() for line in f if line.strip()]
        print(f"{filename} not found!")
    except Exception as e:
        print("Unexpected error:", e)
    return []


def save(filename: str, text: str) -> bool:
    try:
        f = open(filename, "w")
        f.write(text)
        f.close()
    except Exception as e:
        print("Unexpected error:", e)
        return False
    return True


def kdenlive_format(lines: list, token: str) -> list[str]:
    """
    Parses an SRT file in Kdenlive format.

    Args:
    lines: List of lines in the SRT file.
    token: Token to indicate timeout.

    Returns:
    List of strings containing the text and timeouts.
    """

    # Template
    # example.kdenlive.srt
    # 1
    # 00: 00:00, 000 --> 00: 00:05, 000
    # Text

    result: list = []
    if len(lines) < 3:
        return result

    def parse_time(value: str):
        """Converts time string (HH:MM:SS,MS) to milliseconds."""
        h, m, s = value.split(":")
        s, ms = s.split(",")
        return float(h) * 3600000 + float(m) * 60000 + float(s) * 1000 + float(ms)

    def extract_time_range(line: str) -> Tuple[float, float] | None:
        """Extracts the time range from a line."""
        rgx = r"^\d{2}:\d{2}:\d{2},\d{3}.-->.\d{2}:\d{2}:\d{2},\d{3}$"
        if re.fullmatch(rgx, line):
            t = line.split(" --> ")
            if len(t) == 2:
                left = parse_time(t[0])
                right = parse_time(t[1])
                return left, right
        return None     

    # Read lines.
    last_ms: float = 0.0
    for i in range(0, len(lines), 3):
        # Check number.
        if not lines[i].strip().isdigit():
            continue  # Ignore if line is not a number.
        # Check time range.
        time_line = lines[i + 1].strip()
        time_range = extract_time_range(time_line)
        if time_range:
            start_time, _ = time_range
            result.append(f"{token}{start_time - last_ms}")
            last_ms = start_time
        # Check text.
        text_line = lines[i + 2].strip()
        if text_line:
            result.append(text_line)

    # print(result)
    return result


def prepare(data: Data) -> list[str]:

    # Load SRT file
    data.lines = load(data.srt_path)
    if not data.lines:
        print("Error: Empty or invalid SRT file.")
        return []

    format_loaders = {
        "kdenlive": kdenlive_format,
        # Other formats.
    }

    fmt = data.srt_format.lower()
    if fmt in format_loaders:
        return format_loaders[fmt](data.lines, data.token)

    print(f"Unsupported format '{fmt}'")
    return []


def check_file(path: str, extension: str) -> str:
    ext = extension if extension.startswith('.') else '.' + extension
    return os.path.basename(path) if path.lower().endswith(ext.lower()) else ""


def parse_arguments(args: list) -> Data | None:
    data = Data()
    count = {'srt_args': 0, 'mp3_args': 0, 'format_args': 0}

    for arg in args:
        if arg.startswith("srt="):
            count['srt_args'] += 1
            val = arg[4:].strip("\"")
            data.srt_filename = check_file(val, ".kdenlive.srt")
            data.srt_path = val
        elif arg.startswith("mp3="):
            count['mp3_args'] += 1
            val = arg[4:].strip("\"")
            data.mp3_filename = check_file(val, ".mp3")
            data.mp3_path = val
        elif arg.startswith("format="):
            count['format_args'] += 1
            data.srt_format = arg[7:].strip("\"")
        elif arg.startswith("--voices"):
            data.mp3_voices = True

    if count['srt_args'] != 1:
        print("Error: missing or multiple SRT arguments.")
        return None

    if count['mp3_args'] not in [0, 1]:
        print("Error: invalid number of MP3 arguments.")
        return None

    if count['format_args'] == 0:
        data.srt_format = "kdenlive"
        print(f"Default format set to '{data.srt_format}'.")

    if count['format_args'] > 1:
        print("Error: multiple format arguments.")
        return None

    return data


def main(args: list):
    print("Convert SRT to Speech")

    if len(args) < 1:
        print(
            "Usage:\n"
            "  python3 script.py srt=<input.srt>\n"
            "  python3 script.py srt=<input.srt> mp3=<output.mp3>\n"
            "  python3 script.py srt=<input.srt> mp3=<output.mp3> format=<kdenlive>\n"
            "To copy voices also use the --voices command:\n"
            "  python3 script.py srt=<input.srt> mp3=<output.mp3> format=<kdenlive> --voices\n"
        )
        return

    data = parse_arguments(args)
    if not data:
        return

    print(data)

    print("Analyzing and preparing subtitles ...")
    data.lines = prepare(data)

    print("Converting text to speech ...")
    if text_to_speech(data):
        complement = " and individual voice fills" if data.mp3_voices else ""
        print(f"Success: '{data.mp3_filename}'{complement} generated from '{data.srt_filename}'.")
    else:
        print("Error: Failed to generate MP3 file.")


if __name__ == '__main__':
    # Example
    # main(['srt="./example.kdenlive.srt"', 'format=kdenlive' , 'mp3="./output.mp3"', "--voices"])

    # Command line
    main(sys.argv[1:])
