#!/usr/bin/env python3
"""Seams: markdown_to_speech, speech_clips, clips_for_reading, convert_essay."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import essay_to_audio as tts


ESSAY = """---
title: Observe learning
---

# Stop Policing AI Use. Observe Learning.

First paragraph stays.

## Make learning observable

Second paragraph stays.
"""


class MarkdownToSpeechTests(unittest.TestCase):
    def test_strips_frontmatter_and_speaks_heading_lines(self) -> None:
        speech = tts.markdown_to_speech(ESSAY)
        self.assertEqual(
            speech,
            "Stop Policing AI Use. Observe Learning.\n\n"
            "First paragraph stays.\n\n"
            "Make learning observable\n\n"
            "Second paragraph stays.",
        )


class SpeechClipTests(unittest.TestCase):
    def test_one_clip_per_blank_line_paragraph(self) -> None:
        speech = (
            "Stop Policing AI Use. Observe Learning.\n\n"
            "First paragraph stays.\n\n"
            "Make learning observable\n\n"
            "Second paragraph stays."
        )
        self.assertEqual(
            tts.speech_clips(speech, max_chars=9000),
            [
                "Stop Policing AI Use. Observe Learning.",
                "First paragraph stays.",
                "Make learning observable",
                "Second paragraph stays.",
            ],
        )

    def test_oversized_paragraph_splits_on_sentences(self) -> None:
        speech = "AAAA. BBBB. CCCC."
        self.assertEqual(
            tts.speech_clips(speech, max_chars=8),
            ["AAAA.", "BBBB.", "CCCC."],
        )


class ClipHashTests(unittest.TestCase):
    def test_neighbor_change_is_a_new_clip(self) -> None:
        voice = "voice-a"
        model = "model-a"
        paragraphs = ["One.", "Two.", "Three."]
        original = tts.clips_for_reading(paragraphs, voice=voice, model=model)
        edited = tts.clips_for_reading(
            ["One.", "Two changed.", "Three."],
            voice=voice,
            model=model,
        )
        self.assertEqual(original[0].text, "One.")
        self.assertNotEqual(original[0].digest, edited[0].digest)
        self.assertNotEqual(original[1].digest, edited[1].digest)
        self.assertNotEqual(original[2].digest, edited[2].digest)

    def test_unchanged_far_paragraph_keeps_hash_when_only_end_changes(self) -> None:
        voice = "voice-a"
        model = "model-a"
        original = tts.clips_for_reading(
            ["One.", "Two.", "Three.", "Four."],
            voice=voice,
            model=model,
        )
        edited = tts.clips_for_reading(
            ["One.", "Two.", "Three.", "Four changed."],
            voice=voice,
            model=model,
        )
        self.assertEqual(original[0].digest, edited[0].digest)
        self.assertNotEqual(original[2].digest, edited[2].digest)
        self.assertNotEqual(original[3].digest, edited[3].digest)


class ReadingCacheTests(unittest.TestCase):
    def test_second_run_reuses_clips_and_rewrites_the_reading(self) -> None:
        calls: list[str] = []

        def fake_synthesize(clip: tts.Clip) -> bytes:
            calls.append(clip.digest)
            return f"AUDIO:{clip.digest}".encode("ascii")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "audio"
            essay = root / "essay.md"
            essay.write_text(
                "---\ntitle: X\n---\n\nOnly one paragraph.\n",
                encoding="utf-8",
            )
            config = {
                "voice": "voice-a",
                "model": "model-a",
                "output_format": "mp3_44100_128",
                "max_chars": 9000,
            }
            with patch.object(tts, "AUDIO_DIR", audio), patch.object(
                tts, "CLIPS_DIR", audio / "clips"
            ):
                first = tts.convert_essay(
                    essay, config, dry_run=False, synthesize_clip=fake_synthesize
                )
                self.assertEqual(first, 0)
                reading = audio / "essay.mp3"
                manifest = audio / "essay.json"
                self.assertTrue(reading.exists())
                self.assertTrue(manifest.exists())
                first_bytes = reading.read_bytes()
                first_call_count = len(calls)

                second = tts.convert_essay(
                    essay, config, dry_run=False, synthesize_clip=fake_synthesize
                )
                self.assertEqual(second, 0)
                self.assertEqual(len(calls), first_call_count)
                self.assertEqual(reading.read_bytes(), first_bytes)


if __name__ == "__main__":
    unittest.main()
