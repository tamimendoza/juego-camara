## 1. Game Engine Module (src/game.py)

- [x] 1.1 Define game constants (resolution, ground level, jump params, speed params)
- [x] 1.2 Implement `JumpDetector` — shoulder midpoint y, EMA baseline, threshold trigger, cooldown
- [x] 1.3 Implement `PlayerCharacter` — jump physics, gravity, pose transform, render via SilhouetteDrawer
- [x] 1.4 Implement `Obstacle` — leftward movement, AABB collision, off-screen check, pass tracking
- [x] 1.5 Implement `ObstacleManager` — spawn timing, speed propagation, passed_count, collision check
- [x] 1.6 Implement `GameEngine` — MENU/PLAYING/GAME_OVER state machine, speed progression, collision dispatch

## 2. Game Entry Point (src/game_main.py)

- [x] 2.1 Mirror main.py structure: Camera → PoseDetector → GameEngine → render loop
- [x] 2.2 Wire pose landmark points into GameEngine.update
- [x] 2.3 Key handling: SPACE starts/restarts, q/ESC quits

## 3. Launch Script

- [x] 3.1 Create `run_game.sh` (bash, executable, mirrors run.sh with model download guard)

## 4. Tests (tests/test_game.py)

- [x] 4.1 Write JumpDetector tests (baseline, trigger, cooldown, missing landmarks)
- [x] 4.2 Write PlayerCharacter tests (jump, gravity, landing, bbox, pose transform)
- [x] 4.3 Write Obstacle / ObstacleManager tests (movement, spawn, pass counting, speed)
- [x] 4.4 Write GameEngine tests (state transitions, speed progression, collision)
- [x] 4.5 Run `pytest tests/` — all tests pass

## 5. Documentation

- [x] 5.1 Create `openspec/specs/pose-jump-game/spec.md` with GIVEN/WHEN/THEN scenarios
- [x] 5.2 Update `README.md` with game mode section
- [x] 5.3 Run `./run_game.sh` — manual playtest verifies end-to-end behavior
- [x] 5.4 Archive the change into `openspec/changes/archive/`
