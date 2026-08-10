"""Sound effects manager for the Mario Bros pose jump game.

Uses ``pygame.mixer`` (already a project dependency) to load and play MP3
sound-effect files from the ``sounds/`` directory.  When audio hardware is
unavailable (headless / CI) or sound files are missing, the manager degrades
to a silent no-op so the game never crashes.
"""

import os
from typing import Optional

try:
    import pygame
except ImportError:  # pragma: no cover - pygame is a declared dependency
    pygame = None  # type: ignore[assignment]


class SoundManager:
    """Load and play sound-effect files via ``pygame.mixer``.

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

        if pygame is not None:
            try:
                pygame.mixer.init()
                self._available = True
            except Exception:
                self._available = False

        if self._available:
            self._coin_sound = self._load_sound("mario-moneda.mp3")
            self._game_over_sound = self._load_sound("mario-bros-game-over-1.mp3")

    def _load_sound(self, filename: str) -> Optional[object]:
        """Load a single sound file, returning ``None`` on failure."""
        if not self._available:
            return None
        path = os.path.join(self._sounds_dir, filename)
        if not os.path.isfile(path):
            return None
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            return None

    @property
    def available(self) -> bool:
        """``True`` when the mixer is initialized and at least one sound loaded."""
        return self._available

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

    def stop(self) -> None:
        """Stop all currently playing sounds."""
        if self._available:
            try:
                pygame.mixer.stop()
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
        self._available = False
        self._coin_sound = None
        self._game_over_sound = None
