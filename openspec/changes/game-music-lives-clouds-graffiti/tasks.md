## 1. SoundManager: Background music support

- [ ] 1.1 Add `play_background_music()` method to `SoundManager` using `pygame.mixer.music`
- [ ] 1.2 Add `play_invincibility_theme()` method to `SoundManager`
- [ ] 1.3 Add `stop_background_music()` method to `SoundManager`
- [ ] 1.4 Set music volume below SFX volume (music=0.3, SFX=0.7)
- [ ] 1.5 Add tests for background music and invincibility theme in `tests/test_sound_manager.py`

## 2. Level interval change (10 → 5)

- [ ] 2.1 Change `LEVEL_INTERVAL` from 10 to 5 in `src/game.py`
- [ ] 2.2 Change `LEVEL_INTERVAL` from 10 to 5 in `src/mario_game.py`
- [ ] 2.3 Change `LEVEL_INTERVAL` from 10 to 5 in `src/minecraft_game.py`
- [ ] 2.4 Update tests in `tests/test_game.py`, `tests/test_mario_game.py`, `tests/test_minecraft_game.py`

## 3. Lives system (3 hearts)

- [ ] 3.1 Add `lives` field and `MAX_LIVES = 3` constant to `GameEngine`
- [ ] 3.2 Add `lives` field and `MAX_LIVES = 3` constant to `MarioGameEngine`
- [ ] 3.3 Add `lives` field and `MAX_LIVES = 3` constant to `MinecraftGameEngine`
- [ ] 3.4 Add `render_hearts()` method to render 3 hearts in HUD
- [ ] 3.5 Decrement lives on collision; game over at 0 lives
- [ ] 3.6 Reset lives to 3 on restart
- [ ] 3.7 Add tests for lives system in all three test files

## 4. Sky blocks (life blocks in the sky)

- [ ] 4.1 Add `SkyBlock` class to `src/game.py`
- [ ] 4.2 Add `SkyBlockManager` class to `src/game.py`
- [ ] 4.3 Add sky blocks to `MarioGameEngine` (reuse from `game.py`)
- [ ] 4.4 Add sky blocks to `MinecraftGameEngine` (reuse from `game.py`)
- [ ] 4.5 Implement life gain on block collection (max 3 lives)
- [ ] 4.6 Play coin sound on block collection
- [ ] 4.7 Add tests for sky blocks in all three test files

## 5. Moving clouds

- [ ] 5.1 Add `_cloud_offset` field to `GameEngine`
- [ ] 5.2 Add `_cloud_offset` field to `MarioGameEngine`
- [ ] 5.3 Add `_cloud_offset` field to `MinecraftGameEngine`
- [ ] 5.4 Implement cloud drift in `_render_game()` / `_render_background()`
- [ ] 5.5 Implement cloud wrap-around at screen edges
- [ ] 5.6 Set cloud drift speed to ~50% of obstacle speed (parallax)
- [ ] 5.7 Add tests for moving clouds in all three test files

## 6. Brick ground with graffiti

- [ ] 6.1 Add brick ground rendering to `GameEngine._render_game()`
- [ ] 6.2 Add brick ground rendering to `MarioGameEngine` (already has brick pattern)
- [ ] 6.3 Add brick ground rendering to `MinecraftGameEngine`
- [ ] 6.4 Add graffiti text "Familia Mendoza Silva" to ground in all three engines
- [ ] 6.5 Add tests for brick ground and graffiti rendering

## 7. Pose stability (pause + warning)

- [ ] 7.1 Add `MIN_SHOULDER_WIDTH` and `MAX_SHOULDER_WIDTH` to `game.py`
- [ ] 7.2 Add `scale_warning` property to `PlayerCharacter`
- [ ] 7.3 Gate jump detection on `scale_warning` in `GameEngine._update_playing()`
- [ ] 7.4 Gate jump detection on `scale_warning` in `MarioGameEngine._update_playing()`
- [ ] 7.5 Minecraft variant already has this — verify and align
- [ ] 7.6 Render "Acerquese o alejese de la camara" warning at top of screen
- [ ] 7.7 Pause game (stop obstacle spawning) when warning is active
- [ ] 7.8 Add tests for pose stability in all three test files

## 8. Passed obstacle collision safety

- [ ] 8.1 Modify `Obstacle.check_collision()` to skip obstacles with `passed = True`
- [ ] 8.2 Modify `MarioObstacle.check_collision()` to skip passed obstacles
- [ ] 8.3 Modify `MinecraftObstacle.check_collision()` to skip passed obstacles
- [ ] 8.4 Add tests for collision safety with passed obstacles

## 9. Mid-air jump (double jump)

- [ ] 9.1 Verify `MAX_JUMPS = 2` and `DOUBLE_JUMP_VELOCITY` are set in all three
  game variants
- [ ] 9.2 Ensure `JumpDetector` cooldown allows a second jump gesture while
  airborne in all three variants
- [ ] 9.3 Ensure `PlayerCharacter.jump()` / `MarioCharacter.jump()` /
  `MinecraftMarioCharacter.jump()` support double jump in all three variants
- [ ] 9.4 Add tests for mid-air jump in all three test files

## 10. Integration into entry points

- [ ] 10.1 Update `src/game_main.py` to start background music on game start
- [ ] 10.2 Update `src/mario_main.py` to start background music on game start
- [ ] 10.3 Update `src/minecraft_main.py` to start background music on game start
- [ ] 10.4 Stop background music on game over / exit

## 11. Documentation

- [ ] 11.1 Update `README.md` with new features
- [ ] 11.2 Update module docstrings in `src/game.py`, `src/mario_game.py`, `src/minecraft_game.py`
