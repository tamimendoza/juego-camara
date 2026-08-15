## Why

The current game speed increases by a 10% multiplier per level, which makes the game slowly more challenging but not aggressive enough for fast‑paced play.

Doubling the speed per level creates immediate, noticeable difficulty upgrades, adding excitement and a stronger skill curve while staying manageable for casual players.

## What Changes

* Change the speed multiplier used in the game engine from the existing `1.10` to a constant `2.0`.
* Update the spec documentation to reflect the new multiplier.

This is a pure behavioral change – no new capabilities are introduced.

## Capabilities

### New Capabilities

(Empty – no new capabilities.)

### Modified Capabilities

* **pose‑jump‑game** – Update the *Speed progression* requirement to use `2.0` instead of `1.10`.

## Impact

* Code change: `src/framework/jump_game.py` – `SPEED_MULTIPLIER` updated to `2.0`.
* Spec update: `openspec/specs/pose-jump-game/spec.md` – all references to the old multiplier replaced.
* Any downstream tests or numeric expectations that rely on the multiplier will need to update accordingly.
