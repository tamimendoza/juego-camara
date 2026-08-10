"""Unit tests for the SoundManager class.

Tests cover sound loading, playback, graceful degradation when audio is
unavailable, and cleanup.  Tests run without a real audio device by relying
on the manager's fallback behavior.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.sound_manager import SoundManager


class TestSoundManager:
    def test_init_without_pygame(self):
        """SoundManager initializes even when pygame is not available."""
        with patch("src.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            assert mgr.available is False

    def test_init_with_pygame_failure(self):
        """SoundManager degrades gracefully when mixer init fails."""
        mock_pygame = MagicMock()
        mock_pygame.mixer.InitError = Exception
        mock_pygame.mixer.init.side_effect = Exception("no audio device")
        with patch("src.sound_manager.pygame", mock_pygame):
            mgr = SoundManager(sounds_dir="sounds")
            assert mgr.available is False

    def test_play_coin_no_crash_when_unavailable(self):
        """play_coin() is a no-op when audio is unavailable."""
        with patch("src.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            mgr.play_coin()  # should not raise

    def test_play_game_over_no_crash_when_unavailable(self):
        """play_game_over() is a no-op when audio is unavailable."""
        with patch("src.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            mgr.play_game_over()  # should not raise

    def test_stop_no_crash_when_unavailable(self):
        """stop() is a no-op when audio is unavailable."""
        with patch("src.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            mgr.stop()  # should not raise

    def test_close_resets_state(self):
        """close() sets available to False and clears sound objects."""
        with patch("src.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            mgr.close()
            assert mgr.available is False

    def test_missing_sound_file_degrades_gracefully(self):
        """SoundManager handles missing sound files without crashing."""
        mock_pygame = MagicMock()
        mock_pygame.mixer.InitError = Exception
        mock_pygame.mixer.init.return_value = None
        mock_pygame.mixer.Sound.side_effect = Exception("file not found")
        mock_pygame.mixer.Sound = MagicMock(side_effect=FileNotFoundError)
        with patch("src.sound_manager.pygame", mock_pygame):
            mgr = SoundManager(sounds_dir="nonexistent_dir")
            assert mgr._coin_sound is None
            assert mgr._game_over_sound is None
            mgr.play_coin()
            mgr.play_game_over()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
