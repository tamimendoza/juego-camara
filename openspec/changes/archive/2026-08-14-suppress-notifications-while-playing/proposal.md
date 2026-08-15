## Why

While playing the game, desktop system notifications (chat messages, email,
app banners) pop up over the fullscreen window and interrupt the session.
Players should play without being distracted by notification banners during
the whole time the game is running, and notifications should come back
immediately when the game exits.

## What Changes

- A new shared `src/core/notification_manager.py` that suppresses desktop
  notification banners while the game runs and restores them on exit.
- Automatic desktop detection with graceful degradation: GNOME is handled via
  `gsettings` (de)activating `org.gnome.desktop.notifications` `show-banners`;
  other desktops fall back to the D-Bus `org.freedesktop.Notifications`
  inhibit interface when the daemon exposes it. If no supported mechanism is
  available (headless / CI / unsupported desktop), the manager becomes a
  silent no-op so the game never fails to start.
- The manager is activated when the game starts (in `src/games/mario/main.py`)
  and always deactivated on exit, including unexpected termination paths via
  `finally`.
- Notification suppression applies for the whole application lifetime, from
  game launch until the window is closed, regardless of game state
  (menu, name entry, playing, game over).

## Capabilities

### New Capabilities

- `system-notification-suppression`: suppressing desktop notification banners
  for the duration of the game session and restoring them on exit, with
  automatic desktop detection and graceful degradation.

### Modified Capabilities

<!-- None: no existing capability's requirements change. -->

## Impact

- **New file**: `src/core/notification_manager.py` (tests in
  `tests/core/test_notification_manager.py`).
- **Modified**: `src/games/mario/main.py` to acquire the manager at startup
  and release it in the existing `finally` cleanup block.
- **External tools**: invokes `gsettings` (GLib, present on GNOME/Ubuntu) and
  D-Bus via `subprocess`/`dbus-send`; both are already standard on the target
  Linux desktops. No new Python dependencies.
- Existing tests run without a desktop session, so the manager must no-op
  safely in that environment.