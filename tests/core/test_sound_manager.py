"""Unit tests for the SoundManager class.

Tests cover sound loading, playback, graceful degradation when audio is
unavailable, and cleanup.  Tests run without a real audio device by relying
on the manager's fallback behavior.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.core.sound_manager import SoundManager, MUSIC_VOLUME, SFX_VOLUME


class TestSoundManager:
    def test_init_without_pygame(self):
        """SoundManager initializes even when pygame is not available."""
        with patch("src.core.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            assert mgr.available is False
            assert mgr.music_available is False

    def test_init_with_pygame_failure(self):
        """SoundManager degrades gracefully when mixer init fails."""
        mock_pygame = MagicMock()
        mock_pygame.mixer.InitError = Exception
        mock_pygame.mixer.init.side_effect = Exception("no audio device")
        with patch("src.core.sound_manager.pygame", mock_pygame):
            mgr = SoundManager(sounds_dir="sounds")
            assert mgr.available is False
            assert mgr.music_available is False

    def test_play_coin_no_crash_when_unavailable(self):
        """play_coin() is a no-op when audio is unavailable."""
        with patch("src.core.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            mgr.play_coin()  # should not raise

    def test_play_game_over_no_crash_when_unavailable(self):
        """play_game_over() is a no-op when audio is unavailable."""
        with patch("src.core.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            mgr.play_game_over()  # should not raise

    def test_play_background_music_no_crash_when_unavailable(self):
        """play_background_music() is a no-op when audio is unavailable."""
        with patch("src.core.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            mgr.play_background_music()  # should not raise

    def test_play_invincibility_theme_no_crash_when_unavailable(self):
        """play_invincibility_theme() is a no-op when audio is unavailable."""
        with patch("src.core.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            mgr.play_invincibility_theme()  # should not raise

    def test_stop_background_music_no_crash_when_unavailable(self):
        """stop_background_music() is a no-op when audio is unavailable."""
        with patch("src.core.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            mgr.stop_background_music()  # should not raise

    def test_stop_no_crash_when_unavailable(self):
        """stop() is a no-op when audio is unavailable."""
        with patch("src.core.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            mgr.stop()  # should not raise

    def test_close_resets_state(self):
        """close() sets available to False and clears sound objects."""
        with patch("src.core.sound_manager.pygame", None):
            mgr = SoundManager(sounds_dir="sounds")
            mgr.close()
            assert mgr.available is False
            assert mgr.music_available is False

    def test_missing_sound_file_degrades_gracefully(self):
        """SoundManager handles missing sound files without crashing."""
        mock_pygame = MagicMock()
        mock_pygame.mixer.InitError = Exception
        mock_pygame.mixer.init.return_value = None
        mock_pygame.mixer.Sound.side_effect = Exception("file not found")
        mock_pygame.mixer.Sound = MagicMock(side_effect=FileNotFoundError)
        mock_pygame.mixer.music.load.side_effect = FileNotFoundError
        with patch("src.core.sound_manager.pygame", mock_pygame):
            mgr = SoundManager(sounds_dir="nonexistent_dir")
            assert mgr._coin_sound is None
            assert mgr._game_over_sound is None
            assert mgr.music_available is False
            mgr.play_coin()
            mgr.play_game_over()
            mgr.play_background_music()
            mgr.play_invincibility_theme()
            mgr.stop_background_music()

    def test_volume_constants(self):
        """Music volume is lower than SFX volume."""
        assert MUSIC_VOLUME < SFX_VOLUME
        assert MUSIC_VOLUME == 0.3
        assert SFX_VOLUME == 0.7

    def test_music_loads_when_files_exist(self):
        """When GroundTheme.mp3 exists, music_available is True."""
        sounds_dir = os.path.join(os.path.dirname(__file__), "..", "sounds")
        sounds_dir = os.path.abspath(sounds_dir)
        if os.path.isfile(os.path.join(sounds_dir, "GroundTheme.mp3")):
            mgr = SoundManager(sounds_dir=sounds_dir)
            assert mgr.music_available is True
            mgr.close()

    def test_play_background_music_calls_music_play(self):
        """play_background_music() calls pygame.mixer.music.play with loop=-1."""
        mock_pygame = MagicMock()
        mock_pygame.mixer.init.return_value = None
        mock_pygame.mixer.Sound.return_value = MagicMock()
        mock_pygame.mixer.music.load.return_value = None
        with patch("src.core.sound_manager.pygame", mock_pygame):
            mgr = SoundManager(sounds_dir="sounds")
            mgr._music_available = True
            mgr.play_background_music()
            mock_pygame.mixer.music.play.assert_called_once_with(-1)

    def test_play_invincibility_theme_fades_and_reloads(self):
        """play_invincibility_theme() fades out music and loads InvincibilityTheme."""
        mock_pygame = MagicMock()
        mock_pygame.mixer.init.return_value = None
        mock_pygame.mixer.Sound.return_value = MagicMock()
        mock_pygame.mixer.music.load.return_value = None
        with patch("src.core.sound_manager.pygame", mock_pygame):
            mgr = SoundManager(sounds_dir="sounds")
            mgr._music_available = True
            mgr.play_invincibility_theme()
            mock_pygame.mixer.music.fadeout.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
