## 1. NotificationManager core module

- [x] 1.1 Create `src/core/notification_manager.py` with a `NotificationManager` class exposing `activate()` and `deactivate()` methods, following the graceful-degradation pattern of `sound_manager.py`
- [x] 1.2 Implement tiny overridable helpers `_run_gsettings(...)` and `_run_dbus(...)` that wrap `subprocess.run` with a timeout and swallow exceptions, so tests can fake them
- [x] 1.3 Implement GNOME path: on `activate()`, read current `org.gnome.desktop.notifications` `show-banners` via `gsettings get`, store the original value, and set it to `false`; on `deactivate()`, restore the original value only if the manager changed it
- [x] 1.4 Implement D-Bus best-effort path: on `activate()`, call `org.freedesktop.Notifications.GetCapabilities` over the session bus; if `inhibitions` is advertised, call `org.freedesktop.Notifications.Inhibit` and store the returned inhibition ID; on `deactivate()`, release it via `Uninhibit`
- [x] 1.5 Ensure `deactivate()` is a no-op when `activate()` never succeeded, and that partial activation (GNOME set but D-Bus failed, or vice versa) is restored fully
- [x] 1.6 Ensure `activate()` never raises: any exception or non-zero exit code is caught and leaves the manager in a safe "not activated" state

## 2. Wire into game entry point

- [x] 2.1 In `src/games/mario/main.py`, create a `NotificationManager`, call `activate()` before the game loop starts
- [x] 2.2 Call `deactivate()` in the existing `finally` block alongside `face_landmarker.close()`, `camera.release()`, `detector.close()`, and `engine.close()`
- [x] 2.3 Register `atexit` restore so an abnormal Python exit still deactivates suppression

## 3. Tests

- [x] 3.1 Create `tests/core/test_notification_manager.py` covering: activation on GNOME sets `show-banners` to `false` and records the original value; deactivation restores the original value
- [x] 3.2 Test D-Bus path: `activate()` probes capabilities and inhibits only when `inhibitions` is advertised; `deactivate()` uninhibits with the stored ID
- [x] 3.3 Test graceful degradation: missing `gsettings` binary, failing schema, failing D-Bus call, and unsupported desktop all leave the game runnable (`activate()` raises nothing)
- [x] 3.4 Test `deactivate()` no-op when never activated, and full restore after partial activation
- [x] 3.5 Run the full suite with `python3 -m pytest -q` and confirm existing tests still pass