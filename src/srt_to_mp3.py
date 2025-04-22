# -*- coding: utf-8 -*-
"""
Experimenting with Google Text-to-Speech (gTTS) library to convert subtitles
to speech following time intervals.
"""

import os.path
import re
import sys

from io import BytesIO

# Google Text-to-Speech library.
# https://gtts.readthedocs.io/en/latest/index.html
from gtts import gTTS

# Pydub - Manipulate audio with a simple and easy high level interface.
# https://pypi.org/project/pydub/
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

    # Copy voices
    counter = 0
    filename = data.mp3_filename.lower().replace(".mp3", "")
    output_dir = data.mp3_path.replace(data.mp3_filename, "")
    if output_dir == "":
        output_dir = "./"
    elif not output_dir.endswith("/"):
        output_dir += "/"

    try:

        for part in data.lines:
            part = part.strip()
            if re.fullmatch("^" + data.token + ".+", part):
                wait = round(float(part.replace(data.token, "")), 2)
                print(f"Creating silence for {wait} ms ...")
                audio_parts.append(AudioSegment.silent(duration=wait))
            else:
                print(f"Generating speech for: {part}")
                tts = gTTS(text=part, lang=data.language, slow=False)
                tts_fp = BytesIO()
                tts.write_to_fp(tts_fp)
                tts_fp.seek(0)
                audio_parts.append(AudioSegment.from_file(tts_fp, format="mp3"))
                if data.mp3_voices:
                    tts.save(f"{output_dir}{filename}_part_{counter}.mp3")
                    counter += 1

        if audio_parts:
            final_audio = sum(audio_parts)
            final_audio.export(data.mp3_path, format="mp3")
            return True

    except Exception as e:
        print(f"An error occurred: {type(e).__name__} - {e}")

    return False


def load(filename: str, text_coding='UTF-8') -> list:
    try:
        if os.path.exists(filename):
            with open(filename, encoding=text_coding) as f:
                return [line.strip() for line in f if line.strip()]
        print(f"{filename} not found!")
    except Exception as e:
        print("Unexpected error:", e)
    return []


def kdenlive_format(lines: list, token: str) -> list:

    # Template
    # example.kdenlive.srt
    # 1
    # 00: 00:00, 000 --> 00: 05:00, 000
    # Texto
    #
    # 2
    # 00: 10:00, 000 --> 00: 15:00, 000
    # Texto

    result: list = []
    if len(lines) < 3:
        return result

    # Wait regex.
    rgx = r"^\d{2}:\d{2}:\d{2},\d{3}.-->.\d{2}:\d{2}:\d{2},\d{3}$"
    last_ms: float = 0.0

    def convert(value: str):
        h, m, s = value.split(":")
        s, ms = s.split(",")
        return float(h) * 3600000 + float(m) * 60000 + float(s) * 1000 + float(ms)

    # Read lines.
    for i in range(0, len(lines), 3):
        # Line 1 : Number.
        line = lines[i].replace("\n", "").strip()
        if line.isdigit():
            # Line 2 : Time (00:00:00,000 --> 00:00:00,000)
            line = lines[i + 1].replace("\n", "").strip()
            if re.fullmatch(rgx, line):
                values = line.split(" --> ")
                if len(values) == 2:
                    ms = convert(values[0])
                    result += [f"{token}{ms - last_ms}"]
                    last_ms = ms
                # Line 3 : Text.
                line = lines[i + 2].replace("\n", "").strip()
                if line != "":
                    result += [line]

    # print(result)
    return result


def prepare(data: Data) -> list:

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
            "  python3 script.py srt=<input.srt> mp3=<output.mp3> format=<kdenlive>"
            "  python3 script.py srt=<input.srt> mp3=<output.mp3> format=<kdenlive>"
            "To copy voices also use the --voices command:"
            "  python3 script.py srt=<input.srt> mp3=<output.mp3> format=<kdenlive> --voices"
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
        print(f"Success: '{data.mp3_filename}' generated from '{data.srt_filename}'.")
    else:
        print("Error: Failed to generate MP3 file.")


if __name__ == '__main__':
    # Example
    # main(['srt="./example.kdenlive.srt"', 'format=kdenlive' , 'mp3="./output.mp3"', "--voices"])

    # Command line
    main(sys.argv[1:])
