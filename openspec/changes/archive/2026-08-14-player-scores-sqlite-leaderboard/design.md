## Context

El juego activo es la variante Mario Face (`MarioFaceGameEngine` en
`src/games/mario/mario_face_game.py`, heredado de `MarioGameEngine` en
`src/games/mario/mario_game.py`), lanzado por `src/games/mario/main.py` a
través de `run_mario_face.sh`. Hoy el flujo es MENU (SPACE) → PLAYING →
GAME_OVER (SPACE) y no se persiste nada. Las monedas de la partida ya se
contabilizan (`self._coins`), igual que el nivel (`self._obstacle_manager.level`),
y el HUD y el GAME OVER ya las muestran. `sqlite3` pertenece a la stdlib de
Python (versión 3.10 en `requirements.txt`), así que no se agrega dependencia.
La entrada de teclado llega vía `cv2.waitKey` en el bucle principal
(`main.py:123-127`), sin OpenCV HighGUI avanzado.

## Goals / Non-Goals

**Goals:**
- Agregar una pantalla de ingreso de nombre en la ventana del juego con
  escritura por teclado (caracteres alfanuméricos, borrado, ENTER para
  confirmar).
- Persistir la mejor puntuación por usuario (nombre, monedas, nivel) en una
  base SQLite local.
- Mostrar el ranking Top 5 ordenado por monedas en GAME OVER y volver al
  ingreso de nombre con ENTER.
- Mostrar el nombre del jugador en el HUD durante la partida.

**Non-Goals:**
- No cambiar la física, obstáculos, niveles, vidas, sonido ni detección de pose/rostro.
- No sincronizar puntuaciones entre dispositivos ni agregar servidor/API.
- No modificar el juego base `src/framework/jump_game.py` ni el juego genérico
  (`src/core/game.py` si existiera): el cambio se concentra en la familia Mario.
- No implementar múltiples tipos de base de datos: solo SQLite local.

## Decisions

**D1. Nuevo estado NAME_ENTRY separado de MENU.**
`MarioGameEngine` gana un estado `NAME_ENTRY` (p.ej. `NAME_ENTRY = 3`).
`reset()` deja el engine en `NAME_ENTRY` en lugar de `MENU` para la variante
Mario Face. El render del estado muestra el prompt y el nombre en edición; el
estado `MENU` queda sin uso (o se mantiene para el engine base). Alternativa
descartada: reutilizar `MENU` con una bandera — acopla lógica de texto a un
estado que también podría querer otro contenido.

**D2. Nombre del jugador administrado por el engine con un `name_buffer`.**
El engine mantiene un buffer de texto (`self._player_name`) y un cursor
lógico. `handle_key` pasa a distinguir: caracteres imprimibles (32–126, se
agregan hasta un tope p.ej. 15 caracteres), `BACKSPACE` (borra último
carácter), `ENTER` (confirma y transiciona a PLAYING si no está vacío) y `q`/ESC
(salida). La confirmación con nombre vacío no cambia de estado (se mantiene el
prompt). Alternativa descartada: pedir el nombre por consola con `input()` —
bloquea el bucle de video y rompe la experiencia de ventana del juego.

**D3. Módulo de persistencia SQLite dedicado.**
Nuevo módulo `src/core/score_store.py` con una clase `ScoreStore` que:
- Abre/conecta `scores.db` en la raíz del proyecto (ruta resuelta por
  `_resource_path`-style, tres niveles arriba de `src/games/mario/`).
- Crea la tabla `players (name TEXT PRIMARY KEY, coins INTEGER NOT NULL,
  level INTEGER NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)` en el
  primer uso (`CREATE TABLE IF NOT EXISTS`).
- Expone `upsert_best(name, coins, level)`: inserta si el nombre no existe;
  si existe y `coins` es mayor, actualiza monedas/nivel/timestamp; si `coins`
  es menor o igual, no modifica.
- Expone `top_scores(limit=5)`: retorna hasta `limit` filas
  `ORDER BY coins DESC, updated_at ASC`.
- Cierra la conexión con `close()`.
Alternativas descartadas: guardar en un archivo JSON (no soporta consultas
ordenadas robustas ni upsert transaccional); tabla con una fila por partida
(contrario a la decisión "mejor puntuación por usuario").

**D4. Guardado y ranking integrados en la transición a GAME_OVER.**
Cuando el engine pasa a `GAME_OVER` (última vida perdida en
`_update_playing`), se invoca `upsert_best(player_name, coins, level)` y se
cachea el Top 5 en el engine (`self._leaderboard`). La pantalla GAME OVER
renderiza el resumen actual y debajo el Top 5. Alternativa descartada:
consultar el ranking en cada frame de GAME OVER — innecesario e ineficiente.

**D5. ENTER como tecla de confirmación en NAME_ENTRY y de reinicio en GAME_OVER.**
En `NAME_ENTRY`, ENTER confirma el nombre y arranca. En `GAME_OVER`, ENTER
vuelve a `NAME_ENTRY` con el campo de nombre vacío. `handle_key` en
`MarioGameEngine` se actualiza para esto; `SPACE` deja de iniciar/reiniciar en
la variante Mario Face (se conserva el comportamiento del engine base).

**D6. HUD con nombre del jugador.**
`_draw_hud` (en `mario_face_game.py`) agrega una línea con el nombre del
jugador actual (p.ej. encima del contador de monedas). El nombre se conserva
durante la partida aunque el mejor registro no se actualice.

## Risks / Trade-offs

- **Corrupción o bloqueo de la base por uso concurrente** → el `ScoreStore` es
  de una sola instancia usada por un único proceso; `PRIMARY KEY` + upsert
  transaccional evita filas duplicadas. La conexión se abre una vez y se cierra
  en `engine.close()`.
- **El ranking de "mejor puntuación por usuario" oculta partidas previas** →
  es la decisión del producto (confirmada): el Top 5 muestra el mejor registro
  de cada jugador, no todas las partidas.
- **Nombres duplicados/ambiguos (misma persona con variantes de nombre)** →
  se trata como jugadores distintos; es aceptable y no requiere deduplicación.
- **`cv2.waitKey` con teclas no-ASCII o IME** → solo se aceptan caracteres
  imprimibles ASCII (32–126); nombres con acentos/ñ no se capturan. Mitigación
  documentada; se puede ampliar con mapeo de teclas si se requiere.
- **DB creada en la raíz del repo** → se agrega `scores.db` (o el patrón
  `scores*.db`) a `.gitignore` para no versionar datos locales.

## Migration Plan

- No hay migración de datos previos (no existía persistencia).
- Deploy: agregar `src/core/score_store.py`, modificar `MarioGameEngine`,
  `MarioFaceGameEngine`, `mario_game.py`/`mario_face_game.py` y `main.py`.
  La base se crea automáticamente en el primer arranque.
- Rollback: quitar el `ScoreStore`, el estado `NAME_ENTRY` y volver al flujo
  SPACE; sin datos que preservar (la DB es local y se puede borrar).

## Open Questions

- Ninguna que cambie specs, enfoque o tareas: la confirmación del ranking
  "mejor puntuación por usuario", el ingreso del nombre en la ventana y el Top 5
  fueron decididos con el usuario.
