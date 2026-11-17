#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import tempfile
import unittest
from pathlib import Path

from src.config_manager import ConfigManager
from src.music_player import MusicPlayer


class HolidayConfigTests(unittest.TestCase):
    def _config(self, mode="auto", periods=None):
        config = ConfigManager()
        config.preferences = {
            "holidays": {"mode": mode, "periods": periods or []},
        }
        return config

    def test_auto_period_includes_boundaries(self):
        config = self._config(periods=[
            {"start": "2026-01-01", "end": "2026-01-10"},
        ])
        self.assertTrue(config.is_holidays_active(datetime.date(2026, 1, 1)))
        self.assertTrue(config.is_holidays_active(datetime.date(2026, 1, 10)))
        self.assertFalse(config.is_holidays_active(datetime.date(2025, 12, 31)))
        self.assertFalse(config.is_holidays_active(datetime.date(2026, 1, 11)))

    def test_manual_modes_override_schedule(self):
        periods = [{"start": "2026-01-01", "end": "2026-01-10"}]
        on_date = datetime.date(2026, 5, 1)

        forced_on = self._config(mode="on", periods=periods)
        self.assertTrue(forced_on.is_holidays_active(on_date))

        forced_off = self._config(mode="off", periods=periods)
        self.assertFalse(forced_off.is_holidays_active(datetime.date(2026, 1, 5)))

    def test_invalid_periods_ignored_and_defaults(self):
        config = self._config(periods=[
            {"start": "2026-01-10", "end": "2026-01-01"},
            {"start": "bad", "end": "2026-01-01"},
        ])
        self.assertEqual(config.get_holidays()["periods"], [])
        self.assertFalse(config.is_holidays_active(datetime.date(2026, 1, 5)))

        empty = ConfigManager()
        empty.preferences = {}
        self.assertEqual(empty.get_holidays()["mode"], "auto")
        self.assertEqual(empty.get_holidays()["periods"], [])


class MusicSettingsTests(unittest.TestCase):
    def test_selected_tracks_absence_is_preserved(self):
        config = ConfigManager()
        config.preferences = {"music": {"folders": ["/music"]}}
        self.assertNotIn("selected_tracks", config.get_music_settings())

        config.preferences = {"music": {"folders": ["/music"], "selected_tracks": []}}
        self.assertEqual(config.get_music_settings()["selected_tracks"], [])


class MusicPlayerFilteringTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "a.mp3").write_bytes(b"")
        (self.root / "note.txt").write_text("not audio")
        nested = self.root / "nested"
        nested.mkdir()
        (nested / "b.ogg").write_bytes(b"")
        self.player = MusicPlayer()
        self.assertTrue(self.player.set_music_folders([self.root]))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_nested_folders_are_scanned(self):
        names = sorted(path.name for path in self.player.get_audio_files())
        self.assertEqual(names, ["a.mp3", "b.ogg"])

    def test_missing_setting_means_all_tracks(self):
        self.player.set_selected_tracks(None)
        self.assertEqual(len(self.player.get_audio_files()), 2)

    def test_whitelist_filters_tracks(self):
        nested_track = str(self.root / "nested" / "b.ogg")
        self.player.set_selected_tracks([nested_track])
        self.assertEqual(
            [path.name for path in self.player.get_audio_files()],
            ["b.ogg"],
        )

    def test_empty_whitelist_disables_music(self):
        self.player.set_selected_tracks([])
        self.assertEqual(self.player.get_audio_files(), [])
        self.assertIsNone(self.player.get_next_track())

    def test_empty_folder_list_clears_folders(self):
        self.assertFalse(self.player.set_music_folders([]))
        self.assertEqual(self.player.music_folders, [])
        self.assertEqual(self.player.get_audio_files(), [])


if __name__ == "__main__":
    unittest.main()
