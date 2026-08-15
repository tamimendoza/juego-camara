## Context

The game runs fullscreen on Linux (Ubuntu, per README). Desktop notification
banners pop over the window and interrupt play. There is no project code
touching the desktop session today; the closest precedent is
`src/core/sound_manager.py`, which follows a degrade-gracefully pattern:
try the real backend, and if anything fails, become a silent no-op so the game
never crashes. `src/games/mario/main.py` already has a `try/finally` block
that releases camera, detector, and engine resources on exit — the natural
place to also release notification suppression. See proposal.md — Why.

## Goals / Non-Goals

**Goals:**
- Suppress notification banners for the whole game session on GNOME (the
  Ubuntu default) via `gsettings`.
- Best-effort suppression on other desktops whose notification daemon
  advertises an inhibit capability over D-Bus.
- Restore the desktop's exact original state on exit, even if only part of the
  activation succeeded.
- Fail-safe: never block game startup or the game loop because of a missing
  command, a failing D-Bus call, or a headless/CI environment.
- Unit-testable without a desktop session (mock the subprocess/D-Bus calls).

**Non-Goals:**
- Toggling the OS-level "Do Not Disturb" quick-setting beyond what the chosen
  mechanisms expose.
- Suppressing notifications only during specific game states (menu vs playing);
  suppression is session-wide.
- Support for Wayland/X11 window manager specifics beyond the D-Bus session
  bus and `gsettings`.
- Suppressing notifications emitted by the game itself (the game uses
  `print()` and in-window HUD, never OS notifications).

## Decisions

### D1: Mechanism detection order — GNOME via `gsettings`, then D-Bus best-effort

On activation, detect the available mechanism in this order:

1. **GNOME / gsettings**: if `gsettings` is on `$PATH` and the schema
   `org.gnome.desktop.notifications` exists, read the current value of
   `show-banners`, set it to `false`, and record the original value for
   restore. `gsettings` reads/writes the same dconf store the GNOME Shell
   notification daemon reads, so banners stop appearing immediately.
2. **D-Bus inhibit (best-effort)**: call
   `org.freedesktop.Notifications.GetCapabilities` over the session bus; if
   the reply advertises an `inhibitions` capability, acquire one via
   `org.freedesktop.Notifications.Inhibit` and hold its inhibition ID for
   release. This is not a guaranteed standard (see Risks), so it is best-effort
   and never blocks the game.
3. **No mechanism**: mark the manager unavailable. The game starts normally.

Restoration mirrors activation: release any acquired D-Bus inhibition, then
restore the original `show-banners` value (only if we changed it).

*Why `gsettings` first:* Ubuntu's default desktop is GNOME, and `gsettings
show-banners` is the single, well-documented, CLI-accessible toggle — no
Python dependency, no extra package. D-Bus inhibit is used only as an
opportunistic fallback for other desktops.

*Alternatives considered:* using `dconf` directly (same store, but more fragile
as it requires the exact binary path and schema introspection); shipping a
`libnotify`/Python-D-Bus binding (`dbus-python`, `jeepney`, `pydbus`). Rejected:
they add a Python dependency for a feature that is optional by design, and the
project already relies on shell tools elsewhere (`run_mario_face.sh`).

### D2: Stateless manager object with explicit `activate()` / `deactivate()`

`NotificationManager` exposes only `activate()` and `deactivate()`. Activation
stores what it changed; deactivation restores exactly that. Calling
`deactivate()` when never activated is a no-op. This maps cleanly onto
`main.py`'s existing `try/finally`.

*Why an object over module-level functions:* the "what did I change" state
(original `show-banners` value, active inhibition IDs) must live somewhere
resilient to multiple activation paths; an object makes it explicit and
unit-testable.

### D3: Out-of-process tool invocation via `subprocess.run`

`gsettings` and `dbus-send` are invoked with `subprocess.run(..., timeout=...)`
inside try/except. Exceptions and non-zero exit codes are swallowed (logged to
stderr at most). This keeps the game's hot loop unaffected: activation happens
once before the loop, deactivation once in `finally`.

*Why not a pure-Python D-Bus client:* `dbus-send` ships with every D-Bus
session (present on all target desktops) and needs no extra Python packages.
`gsettings` ships with GLib, present on Ubuntu.

### D4: Desktop detection is advisory, not gating

`XDG_CURRENT_DESKTOP` / `DESKTOP_SESSION` are read to decide probing order, but
the manager does not hard-fail based on them: it always probes for `gsettings`
and, if that's absent, for the D-Bus capability. A GNOME session always has
`gsettings`; a headless machine or a container usually does not, and the probe
then naturally degrades.

## Risks / Trade-offs

- **D-Bus `Inhibit` is not a ratified standard** (it exists as an
  xdg mailing-list proposal; only some daemons implement it). The
  `GetCapabilities` → `inhibitions` check prevents blind calls against daemons
  that would error. → If unsupported, the manager simply degrades to no-op.
- **`gsettings` writes a persistent user setting.** If the game is killed with
  `SIGKILL`, `finally` may not run and the setting could stay `false`. →
  Mitigation: restore in `finally`, and also register `atexit` for abnormal
  Python exits; a `SIGKILL` leaves DND on, which is the same state a user
  toggling it manually would be in — acceptable.
- **Another process changes `show-banners` mid-session.** → On deactivate we
  restore the value recorded at activation; a mid-session manual change is
  overwritten. Accepted trade-off for simplicity; rare in practice.
- **`dbus-send`/`gsettings` missing or slow on PATH.** → Both are wrapped in
  try/except with a short timeout; worst case is a silent no-op.
- **Tests can't run against a real desktop.** → Design the manager so all
  external calls go through tiny overridable helpers (`_run_gsettings`,
  `_run_dbus`), which tests replace with fakes.

## Migration Plan

Pure additive change. No schema/data migration. Rollback is simply reverting
the commit; the game behaves identically on desktops where the mechanisms are
absent. No changes to existing tests are required; new tests are added for the
manager (see tasks.md).

## Open Questions

None that affect specs, approach, or tasks.