#!/usr/bin/env python3
"""AudioSpeechTextUnified for audio_speech_text.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (6):
  audio2text <- audio2text.py (109L): signal_handler() + 1 more
  audio2txt <- audio2txt.py (51L): m4a_to_text() + 0 more
  mp3play <- mp3play.py (33L): playsound() + 0 more
  tts_from_file <- tts_from_file.py (50L): speak_text() + 2 more
  txt2wav <- txt2wav.py (44L): speak_text() + 3 more
  whisper2txt <- whisper2txt.py (28L): m4a_to_text_whisper() + 0 more

Usage:
  python main.py --list
  python main.py --info <tool>
  python main.py <tool> [args ...]
  python main.py <tool> --help  (passthrough when supported)

Notes:
- Each subcommand execs the embedded original source with isolated globals,
  sys.argv patched to [source_file] + args, and __name__ == "__main__".
- Missing third-party deps (e.g. 'dh') or SyntaxErrors fail plainly at runtime;
  nothing is simulated or faked.
- Multi-tool folder: first arg must be a tool name; use --list to see names.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

_AUDIO2TEXT_SOURCE: str = (
    'import os\n'
    'import signal\n'
    'import sys\n'
    'import tempfile\n'
    'import time\n'
    'import speech_recognition as sr\n'
    'from pydub import AudioSegment\n'
    '\n'
    'interrupted = False\n'
    'output_file_global = "out.txt"\n'
    '\n'
    '\n'
    'def signal_handler(sig, frame):\n'
    '    global interrupted\n'
    '    print("\\n\\n⚠️  Interrupt received. Saving progress and exiting...")\n'
    '    interrupted = True\n'
    '\n'
    '\n'
    'def wav_to_text_chunked(input_file, output_file="out.txt", chunk_duration_ms=30000):\n'
    '    global output_file_global\n'
    '    output_file_global = output_file\n'
    '    signal.signal(signal.SIGINT, signal_handler)\n'
    '    if not os.path.exists(input_file):\n'
    '        print(f"Error: Input file \'{input_file}\' not found.")\n'
    '        sys.exit(1)\n'
    '    if not input_file.lower().endswith(".wav"):\n'
    '        print("Warning: Input file doesn\'t have .wav extension. Continuing anyway...")\n'
    '    print(f"Processing: {input_file}")\n'
    '    print(f"Chunk duration: {chunk_duration_ms / 1000} seconds")\n'
    '    print(f"Output file: {output_file}")\n'
    '    print("Press Ctrl+C to save progress and exit\\n")\n'
    '    try:\n'
    '        print("Loading audio file...")\n'
    '        audio = AudioSegment.from_file(input_file, format="wav")\n'
    '        total_duration_ms = len(audio)\n'
    '        total_duration_sec = total_duration_ms / 1000\n'
    '        print(f"Audio duration: {total_duration_sec:.2f} seconds")\n'
    '        num_chunks = (total_duration_ms + chunk_duration_ms - 1) // chunk_duration_ms\n'
    '        print(f"Processing in {num_chunks} chunk(s)\\n")\n'
    '        recognizer = sr.Recognizer()\n'
    '        with open(output_file, "w", encoding="utf-8") as f:\n'
    '            f.write("")\n'
    '        full_text = []\n'
    '        for i in range(num_chunks):\n'
    '            if interrupted:\n'
    '                print("\\nExiting due to interrupt...")\n'
    '                break\n'
    '            start_ms = i * chunk_duration_ms\n'
    '            end_ms = min((i + 1) * chunk_duration_ms, total_duration_ms)\n'
    '            chunk_start_sec = start_ms / 1000\n'
    '            chunk_end_sec = end_ms / 1000\n'
    '            print(f"Processing chunk {i + 1}/{num_chunks} ({chunk_start_sec:.1f}s - {chunk_end_sec:.1f}s)...")\n'
    '            try:\n'
    '                chunk = audio[start_ms:end_ms]\n'
    '                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:\n'
    '                    temp_wav_path = temp_wav.name\n'
    '                chunk.export(temp_wav_path, format="wav")\n'
    '                with sr.AudioFile(temp_wav_path) as source:\n'
    '                    audio_data = recognizer.record(source)\n'
    '                try:\n'
    '                    text = recognizer.recognize_google(audio_data)\n'
    '                    if text.strip():\n'
    '                        full_text.append(text)\n'
    '                        with open(output_file, "a", encoding="utf-8") as f:\n'
    '                            f.write(text + " ")\n'
    '                        print(\n'
    '                            f"  ✓ Chunk {i + 1} transcribed: {text[:100]}..."\n'
    '                            if len(text) > 100\n'
    '                            else f"  ✓ Chunk {i + 1} transcribed: {text}"\n'
    '                        )\n'
    '                    else:\n'
    '                        print(f"  - Chunk {i + 1}: No speech detected")\n'
    '                except sr.UnknownValueError:\n'
    '                    print(f"  - Chunk {i + 1}: Could not understand audio")\n'
    '                except sr.RequestError as e:\n'
    '                    print(f"  - Chunk {i + 1}: API error - {e}")\n'
    '            except Exception as e:\n'
    '                print(f"  ✗ Error processing chunk {i + 1}: {e}")\n'
    '            finally:\n'
    '                if "temp_wav_path" in locals() and os.path.exists(temp_wav_path):\n'
    '                    os.unlink(temp_wav_path)\n'
    '            if i < num_chunks - 1 and not interrupted:\n'
    '                time.sleep(1)\n'
    '        print(f"\\n{\'=\' * 40}")\n'
    '        if interrupted:\n'
    '            print(f"⚠️  Process interrupted. Progress saved to: {output_file}")\n'
    '            print(f"Completed: {i + 1}/{num_chunks} chunks")\n'
    '        else:\n'
    '            print(f"✓ Full transcription saved to: {output_file}")\n'
    '            print(f"Completed: {num_chunks}/{num_chunks} chunks")\n'
    '        if full_text:\n'
    '            combined_text = " ".join(full_text)\n'
    '            preview = combined_text[:300] + "..." if len(combined_text) > 300 else combined_text\n'
    '            print(f"\\nTranscription preview:\\n{preview}")\n'
    '    except Exception as e:\n'
    '        print(f"\\nError: {e}")\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) < 2 or len(sys.argv) > 4:\n'
    '        print("Usage: python wav_to_text.py <input_file.wav> [output_file.txt] [chunk_duration_seconds]")\n'
    '        print("Example: python wav_to_text.py recording.wav")\n'
    '        print("Example: python wav_to_text.py recording.wav output.txt 30")\n'
    '        sys.exit(1)\n'
    '    input_file = sys.argv[1]\n'
    '    output_file = sys.argv[2] if len(sys.argv) >= 3 else "out.txt"\n'
    '    chunk_duration = int(sys.argv[3]) * 400 if len(sys.argv) == 4 else 30000\n'
    '    wav_to_text_chunked(input_file, output_file, chunk_duration)\n'
)

_AUDIO2TXT_SOURCE: str = (
    'import os\n'
    'import sys\n'
    'import tempfile\n'
    'import speech_recognition as sr\n'
    'from pydub import AudioSegment\n'
    '\n'
    '\n'
    'def m4a_to_text(input_file, output_file="out.txt"):\n'
    '    if not os.path.exists(input_file):\n'
    '        print(f"Error: Input file \'{input_file}\' not found.")\n'
    '        sys.exit(1)\n'
    '    if not input_file.lower().endswith(".m4a"):\n'
    '        print("Warning: Input file doesn\'t have .m4a extension. Continuing anyway...")\n'
    '    print(f"Processing: {input_file}")\n'
    '    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:\n'
    '        temp_wav_path = temp_wav.name\n'
    '    try:\n'
    '        print("Converting M4A to WAV...")\n'
    '        audio = AudioSegment.from_file(input_file, format="m4a")\n'
    '        audio.export(temp_wav_path, format="wav")\n'
    '        recognizer = sr.Recognizer()\n'
    '        print("Loading audio file...")\n'
    '        with sr.AudioFile(temp_wav_path) as source:\n'
    '            print("Adjusting for ambient noise...")\n'
    '            recognizer.adjust_for_ambient_noise(source, duration=1)\n'
    '            audio_data = recognizer.record(source)\n'
    '        print("Transcribing audio to text...")\n'
    '        try:\n'
    '            text = recognizer.recognize_google(audio_data)\n'
    '            with open(output_file, "w", encoding="utf-8") as f:\n'
    '                f.write(text)\n'
    '            print(f"✓ Transcription saved to: {output_file}")\n'
    '            print(f"Transcribed text:\\n{text[:200]}..." if len(text) > 200 else f"Transcribed text:\\n{text}")\n'
    '        except sr.UnknownValueError:\n'
    '            print("Error: Speech recognition could not understand the audio")\n'
    '            sys.exit(1)\n'
    '        except sr.RequestError as e:\n'
    '            print(f"Error: Could not request results from speech recognition service; {e}")\n'
    '            sys.exit(1)\n'
    '    finally:\n'
    '        if os.path.exists(temp_wav_path):\n'
    '            os.unlink(temp_wav_path)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) != 2:\n'
    '        print("Usage: python m4a_to_text.py <input_file.m4a>")\n'
    '        print("Example: python m4a_to_text.py recording.m4a")\n'
    '        sys.exit(1)\n'
    '    input_file = sys.argv[1]\n'
    '    m4a_to_text(input_file)\n'
)

_MP3PLAY_SOURCE: str = (
    'class PlaysoundException(Exception):\n'
    '    pass\n'
    '\n'
    '\n'
    'def playsound(sound, block=True):\n'
    '    if not block:\n'
    '        raise NotImplementedError("block=False cannot be used on this platform yet")\n'
    '    import os\n'
    '    from urllib.request import pathname2url\n'
    '    import gi\n'
    '\n'
    '    gi.require_version("Gst", "1.0")\n'
    '    from gi.repository import Gst\n'
    '\n'
    '    Gst.init(None)\n'
    '    playbin = Gst.ElementFactory.make("playbin", "playbin")\n'
    '    if sound.startswith(("http://", "https://")):\n'
    '        playbin.props.uri = sound\n'
    '    else:\n'
    '        playbin.props.uri = "file://" + pathname2url(os.path.abspath(sound))\n'
    '    set_result = playbin.set_state(Gst.State.PLAYING)\n'
    '    if set_result != Gst.StateChangeReturn.ASYNC:\n'
    '        raise PlaysoundException("playbin.set_state returned " + repr(set_result))\n'
    '    bus = playbin.get_bus()\n'
    '    bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)\n'
    '    playbin.set_state(Gst.State.NULL)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    import sys\n'
    '\n'
    '    fn = sys.argv[1]\n'
    '    playsound(fn)\n'
)

_TTS_FROM_FILE_SOURCE: str = (
    'import subprocess\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def speak_text(text):\n'
    '    subprocess.run(["termux-tts-speak", text], check=True)\n'
    '\n'
    '\n'
    'def chunk_text(text, max_chars=3000):\n'
    '    lines = text.splitlines()\n'
    '    chunks = []\n'
    '    current = ""\n'
    '    for line in lines:\n'
    '        candidate = (current + "\\n" + line).strip() if current else line.strip()\n'
    '        if not candidate:\n'
    '            continue\n'
    '        if len(candidate) <= max_chars:\n'
    '            current = candidate\n'
    '        else:\n'
    '            if current:\n'
    '                chunks.append(current)\n'
    '            while len(line) > max_chars:\n'
    '                chunks.append(line[:max_chars])\n'
    '                line = line[max_chars:]\n'
    '            current = line.strip()\n'
    '    if current.strip():\n'
    '        chunks.append(current)\n'
    '    return chunks\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python tts_from_file.py /path/to/file.txt")\n'
    '        sys.exit(1)\n'
    '    path = sys.argv[1]\n'
    '    path = Path(path)\n'
    '    if not path.exists():\n'
    '        print(f"File not found: {path}")\n'
    '        sys.exit(1)\n'
    '    text = path.read_text(encoding="utf-8", errors="ignore")\n'
    '    chunks = chunk_text(text)\n'
    '    print(f"Loaded {path}. Total chunks: {len(chunks)}")\n'
    '    for i, chunk in enumerate(chunks, start=1):\n'
    '        print(f"Speaking chunk {i}/{len(chunks)} (chars={len(chunk)})...")\n'
    '        speak_text(chunk)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_TXT2WAV_SOURCE: str = (
    'import subprocess\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def speak_text(text):\n'
    '    subprocess.run(["termux-tts-speak", text], check=True)\n'
    '\n'
    '\n'
    'def read_text_file(path):\n'
    '    path = Path(path)\n'
    '    if not path.exists():\n'
    '        msg = "error: file not found"\n'
    '        raise FileNotFoundError(msg)\n'
    '    return path.read_text(encoding="utf-8")\n'
    '\n'
    '\n'
    'def chunk_text(text, max_chars=3000):\n'
    '    chunks = []\n'
    '    current = ""\n'
    '    for paragraph in text.splitlines():\n'
    '        if len(current) + len(paragraph) + 1 > max_chars:\n'
    '            if current:\n'
    '                chunks.append(current.strip())\n'
    '                current = paragraph\n'
    '            else:\n'
    '                chunks.append(paragraph[:max_chars])\n'
    '                current = paragraph[max_chars:]\n'
    '        else:\n'
    '            current += paragraph + "\\n"\n'
    '    if current.strip():\n'
    '        chunks.append(current.strip())\n'
    '    return chunks\n'
    '\n'
    '\n'
    'def text_file_to_speech(path):\n'
    '    text = read_text_file(path)\n'
    '    chunks = chunk_text(text)\n'
    '    for i, chunk in enumerate(chunks, start=1):\n'
    '        print(f"Speaking chunk {i}/{len(chunks)}...")\n'
    '        speak_text(chunk)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    text_file_to_speech("/sdcard/Download/sample.txt")\n'
)

_WHISPER2TXT_SOURCE: str = (
    'import os\n'
    'import sys\n'
    'import whisper\n'
    '\n'
    '\n'
    'def m4a_to_text_whisper(input_file, output_file="out.txt"):\n'
    '    if not os.path.exists(input_file):\n'
    '        print(f"Error: Input file \'{input_file}\' not found.")\n'
    '        sys.exit(1)\n'
    '    print("Loading Whisper model...")\n'
    '    model = whisper.load_model("base")\n'
    '    print(f"Processing: {input_file}")\n'
    '    result = model.transcribe(input_file)\n'
    '    with open(output_file, "w", encoding="utf-8") as f:\n'
    '        f.write(result["text"])\n'
    '    print(f"✓ Transcription saved to: {output_file}")\n'
    '    print(\n'
    '        f"Transcribed text:\\n{result[\'text\'][:200]}..."\n'
    '        if len(result["text"]) > 200\n'
    '        else f"Transcribed text:\\n{result[\'text\']}"\n'
    '    )\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) != 2:\n'
    '        print("Usage: python m4a_to_text.py <input_file.m4a>")\n'
    '        sys.exit(1)\n'
    '    m4a_to_text_whisper(sys.argv[1])\n'
)

class BaseTool:
    """Base class for embedded original-script tools."""

    name: str = "base"
    source_file: str = ""
    description: str = ""
    functions: list[str] = []
    notes: str = ""
    source: str = ""

    @classmethod
    def run(cls: type[BaseTool], argv: Sequence[str]) -> int:
        """Execute embedded original source with patched sys.argv."""
        old_argv: list[str] = sys.argv
        sys.argv = [cls.source_file] + list(argv)
        gbls: dict[str, object] = {"__name__": "__main__", "__file__": cls.source_file}
        try:
            code: object = compile(cls.source, cls.source_file, "exec")
            exec(code, gbls)  # noqa: S102 - intentional exec of embedded original
            return 0
        except SystemExit as e:
            c: object = e.code
            if c is None:
                return 0
            if isinstance(c, int):
                return c
            print(str(c), file=sys.stderr)
            return 1
        except SyntaxError as e:
            print(f"[{cls.name}] SyntaxError in {cls.source_file}: {e}", file=sys.stderr)
            return 2
        except ImportError as e:
            print(f"[{cls.name}] ImportError in {cls.source_file}: {e}", file=sys.stderr)
            return 3
        except Exception as e:
            print(f"[{cls.name}] error in {cls.source_file}: {e}", file=sys.stderr)
            return 1
        finally:
            sys.argv = old_argv

    @classmethod
    def info_text(cls: type[BaseTool]) -> str:
        """Return human-readable info for --info."""
        funcs: str = ", ".join(cls.functions) if cls.functions else "(none)"
        base: str = f"tool: {cls.name}\nfile: {cls.source_file}\ndesc: {cls.description}\nfuncs: {funcs}"
        if cls.notes:
            base += f"\nnotes: {cls.notes}"
        base += "\nrun: python main.py " + cls.name + " [args ...]"
        return base


class Audio2textTool(BaseTool):
    """Wrapper for original audio2text.py: signal_handler() + 1 more."""
    name: str = 'audio2text'
    source_file: str = 'audio2text.py'
    description: str = 'signal_handler() + 1 more'
    functions: list[str] = ['signal_handler', 'wav_to_text_chunked']
    notes: str = ''
    source: str = _AUDIO2TEXT_SOURCE

class Audio2txtTool(BaseTool):
    """Wrapper for original audio2txt.py: m4a_to_text() + 0 more."""
    name: str = 'audio2txt'
    source_file: str = 'audio2txt.py'
    description: str = 'm4a_to_text() + 0 more'
    functions: list[str] = ['m4a_to_text']
    notes: str = ''
    source: str = _AUDIO2TXT_SOURCE

class Mp3playTool(BaseTool):
    """Wrapper for original mp3play.py: playsound() + 0 more."""
    name: str = 'mp3play'
    source_file: str = 'mp3play.py'
    description: str = 'playsound() + 0 more'
    functions: list[str] = ['playsound']
    notes: str = ''
    source: str = _MP3PLAY_SOURCE

class TtsFromFileTool(BaseTool):
    """Wrapper for original tts_from_file.py: speak_text() + 2 more."""
    name: str = 'tts_from_file'
    source_file: str = 'tts_from_file.py'
    description: str = 'speak_text() + 2 more'
    functions: list[str] = ['speak_text', 'chunk_text', 'main']
    notes: str = ''
    source: str = _TTS_FROM_FILE_SOURCE

class Txt2wavTool(BaseTool):
    """Wrapper for original txt2wav.py: speak_text() + 3 more."""
    name: str = 'txt2wav'
    source_file: str = 'txt2wav.py'
    description: str = 'speak_text() + 3 more'
    functions: list[str] = ['speak_text', 'read_text_file', 'chunk_text', 'text_file_to_speech']
    notes: str = ''
    source: str = _TXT2WAV_SOURCE

class Whisper2txtTool(BaseTool):
    """Wrapper for original whisper2txt.py: m4a_to_text_whisper() + 0 more."""
    name: str = 'whisper2txt'
    source_file: str = 'whisper2txt.py'
    description: str = 'm4a_to_text_whisper() + 0 more'
    functions: list[str] = ['m4a_to_text_whisper']
    notes: str = ''
    source: str = _WHISPER2TXT_SOURCE

class AudioSpeechTextUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'audio2text': Audio2textTool,
        'audio2txt': Audio2txtTool,
        'mp3play': Mp3playTool,
        'tts_from_file': TtsFromFileTool,
        'txt2wav': Txt2wavTool,
        'whisper2txt': Whisper2txtTool,
    }

    @classmethod
    def list_tools(cls: type[AudioSpeechTextUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[AudioSpeechTextUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[AudioSpeechTextUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for audio_speech_text (6 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[AudioSpeechTextUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[AudioSpeechTextUnified], argv: Sequence[str] | None = None) -> int:
        """Entry point: dispatch to subcommand or handle --list/--info."""
        args: list[str] = list(sys.argv[1:] if argv is None else argv)
        # Fast path: first arg is a known tool -> direct dispatch (preserves --help passthrough).
        if args and args[0] in cls.TOOLS:
            tname: str = args[0]
            targs: list[str] = args[1:]
            tool: type[BaseTool] = cls.TOOLS[tname]
            return tool.run(targs)
        # Single-tool convenience: `main.py [args...]` runs the only tool.
        if len(cls.TOOLS) == 1 and args and args[0] not in ("--list", "--info", "--help", "-h"):
            only: type[BaseTool] = next(iter(cls.TOOLS.values()))
            # Allow both `main.py <tool> ...` and `main.py ...` (already handled <tool> above).
            if args[0] == only.name:
                return only.run(args[1:])
            # If it looks like a unified flag combo we already excluded, else treat all as tool args.
            # Guard: if user passed an unknown tool-like bare word, still pass to tool (faithful passthrough).
            return only.run(args)
        parser: argparse.ArgumentParser = cls.build_parser()
        ns: argparse.Namespace = parser.parse_args(args)
        flag_list: bool = bool(getattr(ns, "list", False))
        flag_info: str | None = getattr(ns, "info", None)
        tool_arg: str | None = getattr(ns, "tool", None)
        if flag_list:
            cls.print_list()
            return 0
        if flag_info is not None:
            tgt: type[BaseTool] | None = cls.get_tool(flag_info)
            if tgt is None:
                print(f"unknown tool: {flag_info}", file=sys.stderr)
                print("available:", ", ".join(cls.list_tools()), file=sys.stderr)
                return 2
            print(tgt.info_text())
            return 0
        if tool_arg is not None:
            tgt2: type[BaseTool] | None = cls.get_tool(tool_arg)
            if tgt2 is None:
                print(f"unknown tool: {tool_arg}", file=sys.stderr)
                print("available:", ", ".join(cls.list_tools()), file=sys.stderr)
                return 2
            rest: list[str] = list(getattr(ns, "passthrough", []) or [])
            return tgt2.run(rest)
        parser.print_help()
        print("\navailable tools:")
        cls.print_list()
        return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Module entry point."""
    return AudioSpeechTextUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
