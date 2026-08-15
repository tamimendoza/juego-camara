"""Unit tests for the NotificationManager class.

Tests cover GNOME ``gsettings`` suppression, the best-effort D-Bus inhibit
path, graceful degradation in unsupported environments, and restoration of
the desktop's original state.  All external commands are faked so the tests
run without a desktop session.
"""

import pytest

from src.core.notification_manager import (
    NotificationManager,
    GSETTINGS_SCHEMA,
    GSETTINGS_KEY,
    NOTIFICATIONS_IFACE,
)


class FakeProc:
    """Minimal stand-in for ``subprocess.CompletedProcess``."""

    def __init__(self, returncode=0, stdout=""):
        self.returncode = returncode
        self.stdout = stdout


class TestNotificationManagerGsettings:
    def test_activate_sets_banners_false_and_records_original(self):
        """activate() disables banners via gsettings and stores the original value."""
        mgr = NotificationManager()
        calls = []

        def fake_gsettings(*args):
            calls.append(args)
            if args[0] == "get":
                return FakeProc(stdout="true")
            return FakeProc()

        mgr._run_gsettings = fake_gsettings
        mgr._run_dbus = lambda *a, **k: None

        mgr.activate()

        assert mgr._original_banners == "true"
        assert mgr._inhibit_id is None
        assert ("set", GSETTINGS_SCHEMA, GSETTINGS_KEY, "false") in calls

    def test_deactivate_restores_original_value(self):
        """deactivate() restores the original show-banners value after play."""
        mgr = NotificationManager()
        set_calls = []

        def fake_gsettings(*args):
            if args[0] == "get":
                return FakeProc(stdout="true")
            set_calls.append(args)
            return FakeProc()

        mgr._run_gsettings = fake_gsettings
        mgr._run_dbus = lambda *a, **k: None

        mgr.activate()
        mgr.deactivate()

        assert ("set", GSETTINGS_SCHEMA, GSETTINGS_KEY, "true") in set_calls
        assert mgr._original_banners is None


class TestNotificationManagerDBus:
    def test_activate_inhibits_when_capability_advertised(self):
        """activate() inhibits via D-Bus when 'inhibitions' is advertised."""
        mgr = NotificationManager()
        calls = []

        def fake_dbus(*args):
            calls.append(args)
            method = args[2]
            if method == NOTIFICATIONS_IFACE + ".GetCapabilities":
                return FakeProc(stdout='string "inhibitions"')
            if method == NOTIFICATIONS_IFACE + ".Inhibit":
                return FakeProc(stdout="uint32 7")
            return FakeProc()

        mgr._run_gsettings = lambda *a, **k: None
        mgr._run_dbus = fake_dbus

        mgr.activate()

        assert mgr._inhibit_id == "7"
        assert any(a[2] == NOTIFICATIONS_IFACE + ".Inhibit" for a in calls)

    def test_deactivate_uninhibits_with_stored_id(self):
        """deactivate() releases the inhibition using the stored ID."""
        mgr = NotificationManager()
        calls = []

        def fake_dbus(*args):
            calls.append(args)
            method = args[2]
            if method == NOTIFICATIONS_IFACE + ".GetCapabilities":
                return FakeProc(stdout='string "inhibitions"')
            if method == NOTIFICATIONS_IFACE + ".Inhibit":
                return FakeProc(stdout="uint32 7")
            return FakeProc()

        mgr._run_gsettings = lambda *a, **k: None
        mgr._run_dbus = fake_dbus

        mgr.activate()
        mgr.deactivate()

        uninhibit_calls = [a for a in calls if a[2] == NOTIFICATIONS_IFACE + ".Uninhibit"]
        assert len(uninhibit_calls) == 1
        assert uninhibit_calls[0][-1] == "uint32:7"
        assert mgr._inhibit_id is None

    def test_activate_does_not_inhibit_without_capability(self):
        """activate() never calls Inhibit when the capability is absent."""
        mgr = NotificationManager()
        calls = []

        def fake_dbus(*args):
            calls.append(args)
            return FakeProc(stdout='string "body"')

        mgr._run_gsettings = lambda *a, **k: None
        mgr._run_dbus = fake_dbus

        mgr.activate()

        assert mgr._inhibit_id is None
        assert all(a[2] != NOTIFICATIONS_IFACE + ".Inhibit" for a in calls)

    def test_dbus_inhibit_failure_degrades_gracefully(self):
        """A failing Inhibit call leaves the manager unactivated without raising."""
        mgr = NotificationManager()

        def fake_dbus(*args):
            method = args[2]
            if method == NOTIFICATIONS_IFACE + ".GetCapabilities":
                return FakeProc(stdout='string "inhibitions"')
            return FakeProc(returncode=1)

        mgr._run_gsettings = lambda *a, **k: None
        mgr._run_dbus = fake_dbus

        mgr.activate()

        assert mgr._inhibit_id is None


class TestNotificationManagerGracefulDegradation:
    def test_activate_never_raises_when_unsupported(self):
        """A desktop with no supported mechanism leaves the game runnable."""
        mgr = NotificationManager()
        mgr._run_gsettings = lambda *a, **k: None
        mgr._run_dbus = lambda *a, **k: None

        mgr.activate()

        assert mgr._original_banners is None
        assert mgr._inhibit_id is None

    def test_activate_swallows_helper_exceptions(self):
        """Exceptions raised by the command helpers are swallowed."""

        def boom(*a, **k):
            raise RuntimeError("boom")

        mgr = NotificationManager()
        mgr._run_gsettings = boom
        mgr._run_dbus = boom

        mgr.activate()

        assert mgr._original_banners is None
        assert mgr._inhibit_id is None

    def test_gsettings_get_failure_degrades(self):
        """A failing gsettings get leaves the manager unactivated."""
        mgr = NotificationManager()

        def fake_gsettings(*args):
            if args[0] == "get":
                return FakeProc(returncode=1)
            return FakeProc()

        mgr._run_gsettings = fake_gsettings
        mgr._run_dbus = lambda *a, **k: None

        mgr.activate()

        assert mgr._original_banners is None

    def test_gsettings_set_failure_does_not_record_original(self):
        """If setting banners to false fails, nothing is recorded for restore."""
        mgr = NotificationManager()

        def fake_gsettings(*args):
            if args[0] == "get":
                return FakeProc(stdout="true")
            return FakeProc(returncode=1)

        mgr._run_gsettings = fake_gsettings
        mgr._run_dbus = lambda *a, **k: None

        mgr.activate()

        assert mgr._original_banners is None


class TestNotificationManagerRestore:
    def test_deactivate_noop_when_never_activated(self):
        """deactivate() is a no-op when activate() never succeeded."""
        mgr = NotificationManager()
        mgr._run_gsettings = lambda *a, **k: None
        mgr._run_dbus = lambda *a, **k: None

        mgr.deactivate()

        assert mgr._original_banners is None
        assert mgr._inhibit_id is None

    def test_deactivate_restores_gsettings_after_partial_activation(self):
        """Restore still happens when only the gsettings path succeeded."""
        mgr = NotificationManager()
        set_calls = []

        def fake_gsettings(*args):
            if args[0] == "get":
                return FakeProc(stdout="true")
            set_calls.append(args)
            return FakeProc()

        mgr._run_gsettings = fake_gsettings
        mgr._run_dbus = lambda *a, **k: None

        mgr.activate()
        assert mgr._original_banners is not None
        assert mgr._inhibit_id is None

        mgr.deactivate()

        assert ("set", GSETTINGS_SCHEMA, GSETTINGS_KEY, "true") in set_calls
        assert mgr._original_banners is None

    def test_deactivate_restores_dbus_after_partial_activation(self):
        """Restore still happens when only the D-Bus path succeeded."""
        mgr = NotificationManager()
        calls = []

        def fake_dbus(*args):
            calls.append(args)
            method = args[2]
            if method == NOTIFICATIONS_IFACE + ".GetCapabilities":
                return FakeProc(stdout='string "inhibitions"')
            if method == NOTIFICATIONS_IFACE + ".Inhibit":
                return FakeProc(stdout="uint32 7")
            return FakeProc()

        mgr._run_gsettings = lambda *a, **k: None
        mgr._run_dbus = fake_dbus

        mgr.activate()
        assert mgr._inhibit_id == "7"
        assert mgr._original_banners is None

        mgr.deactivate()

        assert any(a[2] == NOTIFICATIONS_IFACE + ".Uninhibit" for a in calls)
        assert mgr._inhibit_id is None

    def test_activate_is_idempotent(self):
        """A second activate() does not overwrite the recorded original value."""
        mgr = NotificationManager()
        get_calls = []

        def fake_gsettings(*args):
            if args[0] == "get":
                get_calls.append(args)
                return FakeProc(stdout="true")
            return FakeProc()

        mgr._run_gsettings = fake_gsettings
        mgr._run_dbus = lambda *a, **k: None

        mgr.activate()
        mgr.activate()

        assert len(get_calls) == 1
        assert mgr._original_banners == "true"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])