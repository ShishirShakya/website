#!/usr/bin/env python3
"""
Convert a Grain of Salt essay into a Reading of hashed Clips.

The essay Markdown is the source. Markup is stripped, then each blank-line
paragraph becomes a Clip. Clip identity is a hash of voice, model, the
paragraph, and the previous and next paragraph. Cached Clips are joined
into one Reading mp3.

Usage:
    python text-to-audio/essay_to_audio.py
    python text-to-audio/essay_to_audio.py --dry-run
    python text-to-audio/essay_to_audio.py book/grain-of-salt/2026-09-12-stop-policing-ai-use.md
    python text-to-audio/essay_to_audio.py --all
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
ESSAYS_DIR = REPO_ROOT / "book" / "grain-of-salt"
AUDIO_DIR = REPO_ROOT / "audio"
CLIPS_DIR = AUDIO_DIR / "clips"
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

SynthesizeClip = Callable[["Clip"], bytes]


@dataclass(frozen=True)
class Clip:
    text: str
    previous_text: str
    next_text: str
    digest: str


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


def speech_clips(speech: str, max_chars: int) -> list[str]:
    paragraphs = [p.strip() for p in speech.split("\n\n") if p.strip()]
    clips: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            clips.append(paragraph)
        else:
            clips.extend(_split_long_paragraph(paragraph, max_chars))
    return clips


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


def clip_hash(
    voice: str,
    model: str,
    text: str,
    previous_text: str,
    next_text: str,
) -> str:
    payload = json.dumps(
        {
            "model": model,
            "next_text": next_text,
            "previous_text": previous_text,
            "text": text,
            "voice": voice,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def clips_for_reading(
    paragraphs: list[str],
    *,
    voice: str,
    model: str,
) -> list[Clip]:
    clips: list[Clip] = []
    for index, text in enumerate(paragraphs):
        previous_text = paragraphs[index - 1] if index else ""
        next_text = paragraphs[index + 1] if index + 1 < len(paragraphs) else ""
        clips.append(
            Clip(
                text=text,
                previous_text=previous_text,
                next_text=next_text,
                digest=clip_hash(voice, model, text, previous_text, next_text),
            )
        )
    return clips


def resolve_targets(paths: list[Path], convert_all: bool) -> list[Path]:
    if convert_all:
        return essay_paths()
    if paths:
        return [path.resolve() for path in paths]
    return essay_paths()


def clip_path(digest: str) -> Path:
    return CLIPS_DIR / f"{digest}.mp3"


def manifest_path(essay: Path) -> Path:
    return AUDIO_DIR / f"{essay.stem}.json"


def reading_path(essay: Path) -> Path:
    return AUDIO_DIR / f"{essay.stem}.mp3"


def _label(path: Path) -> Path:
    try:
        return path.relative_to(REPO_ROOT)
    except ValueError:
        return path


def write_manifest(essay: Path, clips: list[Clip], config: dict) -> Path:
    dest = manifest_path(essay)
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "essay": essay.stem,
        "voice": config.get("voice", ""),
        "model": config.get("model", ""),
        "clips": [{"hash": clip.digest, "chars": len(clip.text)} for clip in clips],
    }
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return dest


def join_clips(clip_paths: list[Path], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if len(clip_paths) == 1:
        shutil.copyfile(clip_paths[0], dest)
        return

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required to join Clips into a Reading.")

    list_path = dest.with_suffix(".concat.txt")
    lines = []
    for path in clip_paths:
        posix = path.resolve().as_posix().replace("'", r"'\''")
        lines.append(f"file '{posix}'")
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        result = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c",
                "copy",
                str(dest),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            raise SystemExit("ffmpeg failed to join Clips into a Reading.")
    finally:
        if list_path.exists():
            list_path.unlink()


def synthesize(clip: Clip, config: dict) -> bytes:
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
    kwargs: dict = {}
    if clip.previous_text:
        kwargs["previous_text"] = clip.previous_text
    if clip.next_text:
        kwargs["next_text"] = clip.next_text
    audio = client.text_to_speech.convert(
        voice_id=config.get("voice", "nqXP0AHNhLuxYoxwhQxh"),
        model_id=config.get("model", "eleven_multilingual_v2"),
        output_format=config.get("output_format", "mp3_44100_128"),
        text=clip.text,
        **kwargs,
    )
    return b"".join(audio)


def convert_essay(
    essay: Path,
    config: dict,
    dry_run: bool,
    synthesize_clip: Optional[SynthesizeClip] = None,
) -> int:
    if not essay.exists():
        print(f"Error: essay not found: {essay}", file=sys.stderr)
        return 1

    speech = markdown_to_speech(essay.read_text(encoding="utf-8"))
    if not speech:
        print(f"Error: no speakable text in {essay}", file=sys.stderr)
        return 1

    max_chars = int(config.get("max_chars", 9000))
    paragraphs = speech_clips(speech, max_chars)
    voice = str(config.get("voice", "nqXP0AHNhLuxYoxwhQxh"))
    model = str(config.get("model", "eleven_multilingual_v2"))
    clips = clips_for_reading(paragraphs, voice=voice, model=model)
    clip_word = "Clip" if len(clips) == 1 else "Clips"
    print(f"{_label(essay)}: {len(speech)} chars, {len(clips)} {clip_word}")

    hits = 0
    misses = 0
    for clip in clips:
        cached = clip_path(clip.digest)
        exists = cached.exists()
        if exists:
            hits += 1
            status = "HIT"
        else:
            misses += 1
            status = "MISS"
        print(f"  {status} clips/{clip.digest}.mp3 ({len(clip.text)} chars)")

    if dry_run:
        print(f"  would write {_label(reading_path(essay))} ({hits} hit, {misses} miss)")
        return 0

    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    producer = synthesize_clip or (lambda clip: synthesize(clip, config))
    clip_files: list[Path] = []
    for clip in clips:
        dest = clip_path(clip.digest)
        if not dest.exists():
            dest.write_bytes(producer(clip))
            print(f"  wrote {_label(dest)}")
        clip_files.append(dest)

    joined = reading_path(essay)
    join_clips(clip_files, joined)
    written_manifest = write_manifest(essay, clips, config)
    print(f"  wrote {_label(joined)}")
    print(f"  wrote {_label(written_manifest)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert Grain of Salt essays to a Reading of hashed Clips.",
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
        help="Print Clip cache hits and misses; do not call Eleven Labs",
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
