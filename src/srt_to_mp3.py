# -*- Mode: Python3; coding: utf-8; indent-tabs-methode: nil; tab-width: 4 +-*-
"""
Experimenting with Google Text-to-Speech (gTTS) library to convert subtitles
to speech following time intervals.
"""
import os.path
import re
import sys

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
        # gTTS
        self.lines: list = []
        self.language: str = "pt-br"
        self.srt_format: str = ""
        self.token: str = "#WAIT:"

    def __str__(self) -> str:
        return (
            f"srt_filename: \"{self.srt_filename}\" \n"
            f"srt_path    : \"{self.srt_path}\" \n"
            f"mp3_filename: \"{self.mp3_filename}\" \n"
            f"mp3_path    : \"{self.mp3_path}\" \n"
            f"lines       : {len(self.lines)} ({self.text_min(10)} ...) \n"
            f"language    : {self.language} \n"
        )

    def text(self) -> str:
        result = ""
        for line in self.lines:
            result += line + "\n"
        return result

    def text_min(self, characters: int = 5) -> str:
        out = self.text()
        if len(out) > characters:
            out = out[characters:]
        return out

    def validate(self):
        return (self.srt_path != "" and self.mp3_path != ""
                and self.srt_format != "" and len(self.lines) > 0)


def text_to_speech(data: Data) -> bool:

    if not data.validate():
        return False

    # Audio segments.
    audio_parts = []

    try:
        for i, part in enumerate(data.lines):
            part = part.strip()
            if re.fullmatch("^" + data.token + ".+", part):
                wait = round(float(part.replace(data.token, "")),2)
                print(f"Create a silence audio segment with {wait} milliseconds ...")
                silence = AudioSegment.silent(duration=wait)
                audio_parts.append(silence)
            else:
                print(f"Part: {part}")
                print("Create a gTTS object ...")
                tts = gTTS(text=part, lang=data.language, slow=False)
                print("Save the generated speech ...")
                temp_file = f"temp_part_{i}.mp3"
                tts.save(temp_file)
                audio_parts.append(AudioSegment.from_mp3(temp_file))
                os.remove(temp_file)
        if audio_parts:
            final_audio = sum(audio_parts)
            final_audio.export(data.mp3_path, format="mp3")
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    return True

def load(filename: str, text_coding='UTF-8') -> list:
    result = []
    try:
        if os.path.exists(filename):
            with open(filename, encoding=text_coding) as f:
                for line in f:
                    data = line.replace("\n", "")
                    if data != "":
                        result += [data]
        else:
            print(f"{filename} not found!")
    except Exception as e:
        print("Unexpected error: ", e)
        return []

    return result


def kdenlive_format(lines: list, token: str) -> list:

    # Template
    # example.kdenlive.srt
    # 1
    # 00: 03:00, 000 --> 00: 05:00, 000
    # Olá!
    #
    # 2
    # 00: 10:00, 000 --> 00: 15:00, 000
    # Estou falando em Português.

    result = []
    if len(lines) < 3:
        return result

    # Wait regex.
    rgx = r"^\d{2}:\d{2}:\d{2},\d{3}.-->.\d{2}:\d{2}:\d{2},\d{3}$"
    last_ms: float = 0.0

    def convert(value: str):
        n = value.split(":")
        n[-1] = n[-1].replace(",", ".")
        return float(n[0]) * 60 * 1000 + float(n[1]) * 1000 + float(n[2])

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
                    milliseconds = convert(values[0])
                    result += [f"{token}{milliseconds - last_ms}"]
                    nums = values[1].split(":")
                    nums[-1] = nums[-1].replace(",", ".")
                    last_ms = convert(values[1])
                # Line 3 : Text.
                line = lines[i + 2].replace("\n", "").strip()
                if line != "":
                    result += [line]

    # print(result)
    return result


def prepare(data: Data) -> list:

    # Load SRT file
    data.lines = load(data.srt_path)
    if not data.validate():
        print("Error: Empty SRT file.")
        return []

    prepared_lines = []
    if data.srt_format.lower() == "kdenlive":
        prepared_lines = kdenlive_format(data.lines, data.token)
    else:
        print("Undefined text reading format!")

    return prepared_lines


def check_file(path: str, extension: str) -> str:
    filename = ""
    extension = extension if extension[0] == '.' else "." + extension
    if path[-len(extension):].upper() == extension.upper():
        filename = os.path.basename(path)
    return filename


def main(args: list):

    inform = (
        "Convert SRT to Speech \n"
        "use:\n"
        "    script.py srt=<srt_input_file>\n"
        "    script.py srt=<srt_input_file> mp3=<mp3_output_file>\n"
        "    script.py srt=<srt_input_file> mp3=<mp3_output_file> format=<srt_format>\n"
    )

    # Check number of arguments.
    if len(args) < 1:
        print(inform)
        return

    # Step 1 : Initialize setup.
    data = Data()

    count = {'srt_args': 0, 'mp3_args': 0, 'format_args': 0}
    for arg in args:
        option = "srt="
        if arg[:len(option)] == option:
            count['srt_args'] += 1
            arg = arg.replace("\"", "")
            arg = arg.replace(option, "")
            data.srt_filename = check_file(arg, ".kdenlive.srt")
            data.srt_path = arg
            continue
        option = "mp3="
        if arg[:len(option)] == option:
            count['mp3_args'] += 1
            arg = arg.replace("\"", "")
            arg = arg.replace(option, "")
            data.mp3_filename = check_file(arg, ".mp3")
            data.mp3_path = arg
            continue
        option = "format="
        if arg[:len(option)] == option:
            count['format_args'] += 1
            arg = arg.replace("\"", "")
            arg = arg.replace(option, "")
            data.srt_format = arg

    print("Check data entry ...")
    if count['srt_args'] != 1:
        print("Error: Check SRT file input! \n")
        print(inform)
        return

    if count['mp3_args'] != 0 and count['mp3_args'] != 1:
        print("Error: Check MP3 file input! \n")
        print(inform)
        return

    if count['format_args'] == 0:
        data.srt_format = "kdenlive"
        print(f"Defining {data.srt_format} format for reading SRT file.")

    if count['format_args'] > 1:
        print("Error: Check SRT format input! \n")
        print(inform)
        return

    message = f"Input: \"{data.srt_path}\"\nOutput: \"{data.mp3_path}\"\nFormat: {data.srt_format}"
    print(message)

    # Step 2 : Analyze and Prepare files.
    print("Analyze and prepare SRT file ...")
    data.lines = prepare(data)

    # Step 3 : Convert text po speech.
    print("Convert text to speech ...")
    if text_to_speech(data):
        print(f"Text from '{data.srt_filename}' has been successfully converted to '{data.mp3_path}'.")
    else:
        print("Sorry! Something went wrong while generating MP3 file.")

    # Step 4: Terminate.
    print("Finished.")


if __name__ == '__main__':
    # Example
    main(['srt="./example.kdenlive.srt"', 'format=kdenlive' , 'mp3="./output.mp3"'])

    # Command line
    # main(sys.argv)
