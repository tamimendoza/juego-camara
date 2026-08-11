## 1. SoundManager: Background music support

- [x] 1.1 Add `play_background_music()` method to `SoundManager` using `pygame.mixer.music`
- [x] 1.2 Add `play_invincibility_theme()` method to `SoundManager`
- [x] 1.3 Add `stop_background_music()` method to `SoundManager`
- [x] 1.4 Set music volume below SFX volume (music=0.3, SFX=0.7)
- [x] 1.5 Add tests for background music and invincibility theme in `tests/test_sound_manager.py`

## 2. Level interval change (10 → 5)

- [x] 2.1 Change `LEVEL_INTERVAL` from 10 to 5 in `src/game.py`
- [x] 2.2 Change `LEVEL_INTERVAL` from 10 to 5 in `src/mario_game.py`
- [x] 2.3 Change `LEVEL_INTERVAL` from 10 to 5 in `src/minecraft_game.py`
- [x] 2.4 Update tests in `tests/test_game.py`, `tests/test_mario_game.py`, `tests/test_minecraft_game.py`

## 3. Lives system (3 hearts)

- [x] 3.1 Add `lives` field and `MAX_LIVES = 3` constant to `GameEngine`
- [x] 3.2 Add `lives` field and `MAX_LIVES = 3` constant to `MarioGameEngine`
- [x] 3.3 Add `lives` field and `MAX_LIVES = 3` constant to `MinecraftGameEngine`
- [x] 3.4 Add `render_hearts()` method to render 3 hearts in HUD
- [x] 3.5 Decrement lives on collision; game over at 0 lives
- [x] 3.6 Reset lives to 3 on restart
- [x] 3.7 Add tests for lives system in all three test files

## 4. Sky blocks (life blocks in the sky)

- [x] 4.1 Add `SkyBlock` class to `src/game.py`
- [x] 4.2 Add `SkyBlockManager` class to `src/game.py`
- [x] 4.3 Add sky blocks to `MarioGameEngine` (reuse from `game.py`)
- [x] 4.4 Add sky blocks to `MinecraftGameEngine` (reuse from `game.py`)
- [x] 4.5 Implement life gain on block collection (max 3 lives)
- [x] 4.6 Play coin sound on block collection
- [x] 4.7 Add tests for sky blocks in all three test files

## 5. Moving clouds

- [x] 5.1 Add `_cloud_offset` field to `GameEngine`
- [x] 5.2 Add `_cloud_offset` field to `MarioGameEngine`
- [x] 5.3 Add `_cloud_offset` field to `MinecraftGameEngine`
- [x] 5.4 Implement cloud drift in `_render_game()` / `_render_background()`
- [x] 5.5 Implement cloud wrap-around at screen edges
- [x] 5.6 Set cloud drift speed to ~50% of obstacle speed (parallax)
- [x] 5.7 Add tests for moving clouds in all three test files

## 6. Brick ground with graffiti

- [x] 6.1 Add brick ground rendering to `GameEngine._render_game()`
- [x] 6.2 Add brick ground rendering to `MarioGameEngine` (already has brick pattern)
- [x] 6.3 Add brick ground rendering to `MinecraftGameEngine`
- [x] 6.4 Add graffiti text "Familia Mendoza Silva" to ground in all three engines
- [x] 6.5 Add tests for brick ground and graffiti rendering

## 7. Pose stability (pause + warning)

- [x] 7.1 Add `MIN_SHOULDER_WIDTH` and `MAX_SHOULDER_WIDTH` to `game.py`
- [x] 7.2 Add `scale_warning` property to `PlayerCharacter`
- [x] 7.3 Gate jump detection on `scale_warning` in `GameEngine._update_playing()`
- [x] 7.4 Gate jump detection on `scale_warning` in `MarioGameEngine._update_playing()`
- [x] 7.5 Minecraft variant already has this — verify and align
- [x] 7.6 Render "Acerquese o alejese de la camara" warning at top of screen
- [x] 7.7 Pause game (stop obstacle spawning) when warning is active
- [x] 7.8 Add tests for pose stability in all three test files

## 8. Passed obstacle collision safety

- [x] 8.1 Modify `Obstacle.check_collision()` to skip obstacles with `passed = True`
- [x] 8.2 Modify `MarioObstacle.check_collision()` to skip passed obstacles
- [x] 8.3 Modify `MinecraftObstacle.check_collision()` to skip passed obstacles
- [x] 8.4 Add tests for collision safety with passed obstacles

## 9. Mid-air jump (double jump)

- [x] 9.1 Verify `MAX_JUMPS = 2` and `DOUBLE_JUMP_VELOCITY` are set in all three
  game variants
- [x] 9.2 Ensure `JumpDetector` cooldown allows a second jump gesture while
  airborne in all three variants
- [x] 9.3 Ensure `PlayerCharacter.jump()` / `MarioCharacter.jump()` /
  `MinecraftMarioCharacter.jump()` support double jump in all three variants
- [x] 9.4 Add tests for mid-air jump in all three test files

## 10. Integration into entry points

- [x] 10.1 Update `src/game_main.py` to start background music on game start
- [x] 10.2 Update `src/mario_main.py` to start background music on game start
- [x] 10.3 Update `src/minecraft_main.py` to start background music on game start
- [x] 10.4 Stop background music on game over / exit

## 11. Documentation

- [x] 11.1 Update `README.md` with new features
- [x] 11.2 Update module docstrings in `src/game.py`, `src/mario_game.py`, `src/minecraft_game.py`
