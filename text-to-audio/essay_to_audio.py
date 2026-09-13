#!/usr/bin/env python3
"""
Convert Grain of Salt essays to MP3 with Eleven Labs.

Does not use the lecture slide/video pipeline. Reads essay Markdown,
strips MyST markup, and writes MP3s to audio/.

Usage:
    python text-to-audio/essay_to_audio.py
    python text-to-audio/essay_to_audio.py --dry-run
    python text-to-audio/essay_to_audio.py book/grain-of-salt/2026-09-12-stop-policing-ai-use.md
    python text-to-audio/essay_to_audio.py --all
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ESSAYS_DIR = REPO_ROOT / "book" / "grain-of-salt"
AUDIO_DIR = REPO_ROOT / "audio"
CONFIG_PATH = Path(__file__).resolve().parent / "elevenlabs.yaml"
ENV_PATH = Path(__file__).resolve().parent / ".env"
LECTURE_ENV_PATH = Path(r"D:\Transcript2Slide2Audio\.env")

DIRECTIVE_BLOCK = re.compile(r"^:::+.*?^:::+[ \t]*\n?", re.MULTILINE | re.DOTALL)
FOOTNOTE_DEF = re.compile(r"^\[\^[^\]]+\]:.*$", re.MULTILINE)
FOOTNOTE_REF = re.compile(r"\[\^[^\]]+\]")
MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
HEADING = re.compile(r"^#{1,6}\s+", re.MULTILINE)
EXTRA_BLANK = re.compile(r"\n{3,}")


def load_config() -> dict:
    import yaml

    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_env() -> None:
    import os

    if os.environ.get("ELEVENLABS_API_KEY"):
        return
    for env_path in (ENV_PATH, LECTURE_ENV_PATH):
        if _set_elevenlabs_key_from_env_file(env_path):
            return


def _set_elevenlabs_key_from_env_file(env_path: Path) -> bool:
    import os

    if not env_path.exists():
        return False
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("ELEVENLABS_API_KEY="):
            continue
        value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
        if value:
            os.environ["ELEVENLABS_API_KEY"] = value
            return True
    return False


def essay_paths() -> list[Path]:
    return sorted(
        path
        for path in ESSAYS_DIR.glob("20*.md")
        if path.is_file()
    )


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    return parts[2].lstrip("\n")


def markdown_to_speech(text: str) -> str:
    text = strip_frontmatter(text)
    text = DIRECTIVE_BLOCK.sub("\n", text)
    text = FOOTNOTE_DEF.sub("", text)
    text = FOOTNOTE_REF.sub("", text)
    text = MD_LINK.sub(r"\1", text)
    text = BOLD.sub(r"\1", text)
    text = ITALIC.sub(r"\1", text)
    text = HEADING.sub("", text)
    text = EXTRA_BLANK.sub("\n\n", text)
    return text.strip()


def chunk_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    size = 0

    for paragraph in paragraphs:
        pieces = (
            _split_long_paragraph(paragraph, max_chars)
            if len(paragraph) > max_chars
            else [paragraph]
        )
        for piece in pieces:
            extra = len(piece) + (2 if current else 0)
            if current and size + extra > max_chars:
                chunks.append("\n\n".join(current))
                current = [piece]
                size = len(piece)
            else:
                current.append(piece)
                size += extra

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    pieces: list[str] = []
    current: list[str] = []
    size = 0
    for sentence in sentences:
        extra = len(sentence) + (1 if current else 0)
        if current and size + extra > max_chars:
            pieces.append(" ".join(current))
            current = [sentence]
            size = len(sentence)
        else:
            current.append(sentence)
            size += extra
    if current:
        pieces.append(" ".join(current))
    return pieces


def resolve_targets(paths: list[Path], convert_all: bool) -> list[Path]:
    if convert_all:
        return essay_paths()
    if paths:
        return [path.resolve() for path in paths]
    return essay_paths()


def output_path(essay: Path, chunk_index: int, chunk_count: int) -> Path:
    if chunk_count == 1:
        return AUDIO_DIR / f"{essay.stem}.mp3"
    return AUDIO_DIR / f"{essay.stem}-{chunk_index:02d}.mp3"


def synthesize(text: str, config: dict) -> bytes:
    import os

    from elevenlabs.client import ElevenLabs

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise SystemExit(
            "Missing ELEVENLABS_API_KEY. Copy text-to-audio/.env.example "
            "to text-to-audio/.env, or keep the key in "
            r"D:\Transcript2Slide2Audio\.env."
        )

    client = ElevenLabs(api_key=api_key)
    audio = client.text_to_speech.convert(
        voice_id=config.get("voice", "S752Nf8IeRCwuwzT3tiw"),
        model_id=config.get("model", "eleven_multilingual_v2"),
        output_format=config.get("output_format", "mp3_44100_128"),
        text=text,
    )
    return b"".join(audio)


def convert_essay(essay: Path, config: dict, dry_run: bool) -> int:
    if not essay.exists():
        print(f"Error: essay not found: {essay}", file=sys.stderr)
        return 1

    speech = markdown_to_speech(essay.read_text(encoding="utf-8"))
    if not speech:
        print(f"Error: no speakable text in {essay}", file=sys.stderr)
        return 1

    max_chars = int(config.get("max_chars", 4000))
    chunks = chunk_text(speech, max_chars)
    print(f"{essay.relative_to(REPO_ROOT)}: {len(speech)} chars, {len(chunks)} chunk(s)")

    if dry_run:
        for index, chunk in enumerate(chunks, start=1):
            dest = output_path(essay, index, len(chunks))
            print(f"  would write {dest.relative_to(REPO_ROOT)} ({len(chunk)} chars)")
        return 0

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    for index, chunk in enumerate(chunks, start=1):
        dest = output_path(essay, index, len(chunks))
        dest.write_bytes(synthesize(chunk, config))
        print(f"  wrote {dest.relative_to(REPO_ROOT)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert Grain of Salt essays to MP3 with Eleven Labs.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Essay Markdown files (default: list all essays)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Convert every dated Grain of Salt essay",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print paths and character counts; do not call Eleven Labs",
    )
    args = parser.parse_args(argv)

    config = load_config()
    load_env()

    dry_run = args.dry_run or (not args.paths and not args.all)
    targets = resolve_targets(args.paths, args.all)
    if not targets:
        print("No Grain of Salt essays found.", file=sys.stderr)
        return 1

    if dry_run and not args.dry_run and not args.paths and not args.all:
        print("Dry run (pass a path or --all to spend Eleven Labs credits):")

    status = 0
    for essay in targets:
        status = convert_essay(essay, config, dry_run) or status
    return status


if __name__ == "__main__":
    raise SystemExit(main())
