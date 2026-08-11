"""Sound effects and background music manager for the pose jump game.

Uses ``pygame.mixer`` (already a project dependency) to load and play MP3
sound-effect files from the ``sounds/`` directory.  When audio hardware is
unavailable (headless / CI) or sound files are missing, the manager degrades
to a silent no-op so the game never crashes.

Background music is streamed via ``pygame.mixer.music`` (suitable for long
tracks), while short sound effects use ``pygame.mixer.Sound``.  Music volume
is kept below SFX volume so effects are always audible.
"""

import os
from typing import Optional

import numpy as np

try:
    import pygame
except ImportError:  # pragma: no cover - pygame is a declared dependency
    pygame = None  # type: ignore[assignment]


# Volume levels: music is intentionally quieter than SFX
MUSIC_VOLUME = 0.3
SFX_VOLUME = 0.7


class SoundManager:
    """Load and play sound-effect files and background music via ``pygame.mixer``.

    Parameters
    ----------
    sounds_dir:
        Directory containing the ``.mp3`` / ``.wav`` sound files.  Defaults to
        ``"sounds"`` relative to the current working directory.
    """

    def __init__(self, sounds_dir: str = "sounds"):
        self._sounds_dir = sounds_dir
        self._available = False
        self._coin_sound: Optional[object] = None
        self._game_over_sound: Optional[object] = None
        self._hit_sound: Optional[object] = None
        self._pose_warning_sound: Optional[object] = None
        self._music_available = False
        self._background_music_path: Optional[str] = None

        if pygame is not None:
            try:
                pygame.mixer.init()
                self._available = True
            except Exception:
                self._available = False

        if self._available:
            self._coin_sound = self._load_sound("mario-moneda.mp3")
            self._game_over_sound = self._load_sound("mario-bros-game-over-1.mp3")
            self._hit_sound = self._generate_beep(440, 0.2)
            self._pose_warning_sound = self._generate_beep(880, 0.3)

        # Initialize music subsystem separately
        if pygame is not None and self._available:
            try:
                pygame.mixer.music.load(
                    os.path.join(self._sounds_dir, "GroundTheme.mp3")
                )
                pygame.mixer.music.set_volume(MUSIC_VOLUME)
                self._music_available = True
            except Exception:
                self._music_available = False

    def _load_sound(self, filename: str) -> Optional[object]:
        """Load a single sound file, returning ``None`` on failure."""
        if not self._available:
            return None
        path = os.path.join(self._sounds_dir, filename)
        if not os.path.isfile(path):
            return None
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(SFX_VOLUME)
            return sound
        except Exception:
            return None

    def _generate_beep(self, frequency: float, duration: float) -> Optional[object]:
        """Generate a simple beep sound at the given frequency and duration."""
        if not self._available:
            return None
        try:
            sample_rate = 44100
            frames = int(duration * sample_rate)
            arr = np.sin(2 * np.pi * frequency * np.arange(frames) / sample_rate)
            arr = (arr * 32767 * SFX_VOLUME).astype(np.int16)
            return pygame.sndarray.make_sound(arr)
        except Exception:
            return None

    @property
    def available(self) -> bool:
        """``True`` when the mixer is initialized and at least one sound loaded."""
        return self._available

    @property
    def music_available(self) -> bool:
        """``True`` when background music is loaded and ready to play."""
        return self._music_available

    def play_coin(self) -> None:
        """Play the coin / obstacle-cleared sound."""
        if self._coin_sound is not None:
            try:
                self._coin_sound.play()
            except Exception:
                pass

    def play_game_over(self) -> None:
        """Play the game-over sound."""
        if self._game_over_sound is not None:
            try:
                self._game_over_sound.play()
            except Exception:
                pass

    def play_hit(self) -> None:
        """Play the hit sound (character loses a life)."""
        if self._hit_sound is not None:
            try:
                self._hit_sound.play()
            except Exception:
                pass

    def play_pose_warning(self) -> None:
        """Play the pose warning sound (person not fully detected)."""
        if self._pose_warning_sound is not None:
            try:
                self._pose_warning_sound.play()
            except Exception:
                pass

    def play_background_music(self) -> None:
        """Start playing the GroundTheme background music in a loop."""
        if self._music_available:
            try:
                pygame.mixer.music.play(-1)  # -1 = infinite loop
            except Exception:
                pass

    def play_invincibility_theme(self) -> None:
        """Play the InvincibilityTheme (layered on top of background music)."""
        if self._music_available:
            try:
                # Remember current music path so we can restore it
                self._background_music_path = os.path.join(
                    self._sounds_dir, "GroundTheme.mp3"
                )
                # Fade out current music, then play invincibility theme
                pygame.mixer.music.fadeout(500)
                inv_path = os.path.join(self._sounds_dir, "InvincibilityTheme.mp3")
                if os.path.isfile(inv_path):
                    pygame.mixer.music.load(inv_path)
                    pygame.mixer.music.set_volume(MUSIC_VOLUME)
                    pygame.mixer.music.play(-1)
            except Exception:
                pass

    def stop_invincibility_theme(self) -> None:
        """Stop the InvincibilityTheme and restore the GroundTheme background music."""
        if self._music_available:
            try:
                pygame.mixer.music.fadeout(500)
                if self._background_music_path and os.path.isfile(
                    self._background_music_path
                ):
                    pygame.mixer.music.load(self._background_music_path)
                    pygame.mixer.music.set_volume(MUSIC_VOLUME)
                    pygame.mixer.music.play(-1)
            except Exception:
                pass

    def stop_background_music(self) -> None:
        """Stop background music playback."""
        if self._music_available:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def stop(self) -> None:
        """Stop all currently playing sounds and music."""
        if self._available:
            try:
                pygame.mixer.stop()
            except Exception:
                pass
        if self._music_available:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def close(self) -> None:
        """Release mixer resources."""
        self.stop()
        if self._available:
            try:
                pygame.mixer.quit()
            except Exception:
                pass
        if self._music_available:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self._available = False
        self._music_available = False
        self._coin_sound = None
        self._game_over_sound = None
        self._hit_sound = None
        self._pose_warning_sound = None
        self._background_music_path = None
