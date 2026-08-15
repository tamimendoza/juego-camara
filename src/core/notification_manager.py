"""Desktop notification suppression manager for the pose jump game.

While the game runs fullscreen, desktop notification banners would pop over
the window and interrupt play.  This manager suppresses them for the duration
of the game session and restores the desktop's original state on exit.

Two mechanisms are supported, probed in order:

1. GNOME via ``gsettings`` (``org.gnome.desktop.notifications``
   ``show-banners``) — the Ubuntu default.
2. Best-effort D-Bus inhibit over ``org.freedesktop.Notifications`` when the
   daemon advertises an ``inhibitions`` capability.

When no supported mechanism is available (headless machine, CI, unsupported
desktop) or a mechanism fails at runtime, the manager degrades to a silent
no-op so the game never crashes.  All external commands are invoked
out-of-process through tiny overridable helpers (``_run_gsettings`` /
``_run_dbus``) that swallow failures; tests replace them with fakes.
"""

import re
import subprocess


GSETTINGS_SCHEMA = "org.gnome.desktop.notifications"
GSETTINGS_KEY = "show-banners"

NOTIFICATIONS_SERVICE = "org.freedesktop.Notifications"
NOTIFICATIONS_PATH = "/org/freedesktop/Notifications"
NOTIFICATIONS_IFACE = "org.freedesktop.Notifications"

_APP_ID = "juego-camara"
_REASON = "game session"

_COMMAND_TIMEOUT = 2.0


class NotificationManager:
    """Suppress desktop notifications while a game session is active.

    ``activate()`` enables suppression via whichever mechanisms are
    available and records what it changed; ``deactivate()`` restores exactly
    that state.  Calling ``deactivate()`` when never activated is a no-op.
    Neither method ever raises.
    """

    def __init__(self, timeout: float = _COMMAND_TIMEOUT):
        self._timeout = timeout
        self._original_banners = None
        self._inhibit_id = None

    def activate(self) -> None:
        """Enable notification suppression for the game session.

        Never raises: any mechanism failure degrades silently, leaving the
        manager in a safe "not activated" state for the failed path.
        """
        if self._original_banners is not None or self._inhibit_id is not None:
            return
        try:
            self._activate_gsettings()
        except Exception:
            self._original_banners = None
        try:
            self._activate_dbus()
        except Exception:
            self._inhibit_id = None

    def deactivate(self) -> None:
        """Restore the desktop's original notification state.

        Restores every setting the manager changed, even if only part of the
        activation succeeded.  Never raises.
        """
        try:
            self._deactivate_dbus()
        except Exception:
            self._inhibit_id = None
        try:
            self._deactivate_gsettings()
        except Exception:
            self._original_banners = None

    def _activate_gsettings(self) -> None:
        proc = self._run_gsettings("get", GSETTINGS_SCHEMA, GSETTINGS_KEY)
        if proc is None or proc.returncode != 0:
            return
        original = proc.stdout.strip()
        if not original:
            return
        set_proc = self._run_gsettings("set", GSETTINGS_SCHEMA, GSETTINGS_KEY, "false")
        if set_proc is None or set_proc.returncode != 0:
            return
        self._original_banners = original

    def _deactivate_gsettings(self) -> None:
        if self._original_banners is None:
            return
        try:
            self._run_gsettings("set", GSETTINGS_SCHEMA, GSETTINGS_KEY, self._original_banners)
        finally:
            self._original_banners = None

    def _activate_dbus(self) -> None:
        proc = self._run_dbus(
            NOTIFICATIONS_SERVICE, NOTIFICATIONS_PATH,
            NOTIFICATIONS_IFACE + ".GetCapabilities",
        )
        if proc is None or proc.returncode != 0:
            return
        if "inhibitions" not in proc.stdout:
            return
        inhibit_proc = self._run_dbus(
            NOTIFICATIONS_SERVICE, NOTIFICATIONS_PATH,
            NOTIFICATIONS_IFACE + ".Inhibit",
            f'string:"{_APP_ID}"', f'string:"{_REASON}"',
        )
        if inhibit_proc is None or inhibit_proc.returncode != 0:
            return
        match = re.search(r"uint32\s+(\d+)", inhibit_proc.stdout)
        if match:
            self._inhibit_id = match.group(1)

    def _deactivate_dbus(self) -> None:
        if self._inhibit_id is None:
            return
        try:
            self._run_dbus(
                NOTIFICATIONS_SERVICE, NOTIFICATIONS_PATH,
                NOTIFICATIONS_IFACE + ".Uninhibit",
                f"uint32:{self._inhibit_id}",
            )
        finally:
            self._inhibit_id = None

    def _run_gsettings(self, *args) -> object:
        """Run a ``gsettings`` command; return None on any failure."""
        try:
            return subprocess.run(
                ["gsettings", *args],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except Exception:
            return None

    def _run_dbus(self, dest: str, object_path: str, method: str, *args) -> object:
        """Run a ``dbus-send`` method call; return None on any failure."""
        try:
            return subprocess.run(
                [
                    "dbus-send", "--session", "--print-reply",
                    f"--dest={dest}", object_path, method, *args,
                ],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except Exception:
            return None