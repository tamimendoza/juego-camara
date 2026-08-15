## 1. Persistencia SQLite

- [x] 1.1 Crear `src/core/score_store.py` con la clase `ScoreStore` que abre la
      base `scores.db` en la raíz del proyecto y crea la tabla
      `players (name TEXT PRIMARY KEY, coins INTEGER NOT NULL, level INTEGER NOT
      NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)` con
      `CREATE TABLE IF NOT EXISTS`.
- [x] 1.2 Implementar `upsert_best(name, coins, level)`: inserta si el nombre no
      existe; si existe y `coins > registro`, actualiza monedas/nivel/timestamp;
      si `coins <= registro`, no modifica.
- [x] 1.3 Implementar `top_scores(limit=5)` que retorna hasta `limit` filas
      `ORDER BY coins DESC, updated_at ASC` (posición, nombre, monedas, nivel).
- [x] 1.4 Implementar `close()` para cerrar la conexión y probar que el módulo
      se puede instanciar sin cámara ni modelos.

## 2. Tests del ScoreStore

- [x] 2.1 Crear `tests/core/test_score_store.py` (usa una DB en `tmp_path`):
      inserción de primer registro, actualización solo cuando supera monedas,
      no-modificación cuando no supera, orden del Top 5, límite de 5 puestos y
      persistencia entre cierres/aperturas.
- [x] 2.2 Correr `python3 -m pytest -q tests/core/test_score_store.py` y dejar
      la suite en verde.

## 3. Estado NAME_ENTRY y buffer de nombre en el engine

- [x] 3.1 Agregar el estado `NAME_ENTRY` a `MarioGameEngine` y el atributo de
      buffer `self._player_name` (máx. 15 caracteres) y ranking cacheado
      `self._leaderboard`.
- [x] 3.2 Hacer que `reset()` de `MarioFaceGameEngine` deje el estado en
      `NAME_ENTRY` en lugar de `MENU`, con el buffer vacío.
- [x] 3.3 Actualizar `handle_key`: caracteres imprimibles ASCII (32–126)
      agregan al buffer, BACKSPACE borra el último carácter, ENTER confirma e
      inicia (si el nombre no está vacío), `q`/ESC salen. `SPACE` deja de
      iniciar/reiniciar en la variante Mario Face.
- [x] 3.4 Actualizar `update`/`render` para manejar `NAME_ENTRY` (render del
      prompt + nombre en edición; sin avance de partida).

## 4. Guardado y ranking al perder

- [x] 4.1 En la transición a `GAME_OVER` (última vida perdida en
      `_update_playing`), invocar `upsert_best(player_name, coins, level)` y
      cachear `top_scores(5)` en `self._leaderboard`.
- [x] 4.2 Extender `_render_game_over` de `MarioFaceGameEngine` para mostrar,
      además del resumen, el Top 5 ordenado por monedas (posición, nombre,
      monedas, nivel) y la leyenda "Press ENTER to continue".
- [x] 4.3 En `GAME_OVER`, hacer que ENTER devuelva a `NAME_ENTRY` con el buffer
      de nombre vacío.

## 5. HUD con nombre del jugador

- [x] 5.1 Extender `_draw_hud` de `MarioFaceGameEngine` para mostrar el nombre
      del jugador actual (p.ej. sobre el contador de monedas).

## 6. Integración en el arranque

- [x] 6.1 En `src/games/mario/main.py`, instanciar `ScoreStore()` y pasarlo al
      `MarioFaceGameEngine` (o crearlo dentro del engine), y cerrarlo en el
      bloque `finally` con el resto de recursos.
- [x] 6.2 Agregar `scores*.db` a `.gitignore`.
- [x] 6.3 Correr `python3 -m pytest -q` y verificar que toda la suite existente
      sigue en verde (sin romper `MarioGameEngine`/`MarioFaceGameEngine`).

## 8. Suite en verde

- [x] 8.1 Corregir los 8 tests de salto que fallaban (detector de dos fases
      crouch → salto): los tests simulaban salto directo sin agacharse. Se
      añadió el helper `make_crouching_landmarks` y se ajustó
      `make_jumping_landmarks` para subir hombros y tobillos en los tres
      archivos de test (`test_jump_game.py`, `test_mario_game.py`,
      `test_mario_face_game.py`). Suite completa: 336 passed, 0 failed.

## 7. Verificación manual

- [ ] 7.1 Lanzar `./run_mario_face.sh` y verificar: pantalla de nombre al
      abrir, escritura/borrado con teclado, ENTER con nombre inicia, GAME OVER
      muestra Top 5 ordenado por monedas, ENTER vuelve al ingreso de nombre, y
      que al reabrir el juego se conserva el mejor registro.