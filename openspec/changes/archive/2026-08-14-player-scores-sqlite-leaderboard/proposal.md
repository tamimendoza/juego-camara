## Why

El juego Mario Face Jump no guarda resultados: al terminar una partida no queda
ningún registro del jugador, sus monedas ni su nivel, y cada partida arranca
igual. Queremos personalizar cada partida pidiendo el nombre del jugador,
guardar su mejor puntuación (monedas + nivel) en una base SQLite y mostrar un
ranking en pantalla al perder, para que el juego tenga progreso y competencia
entre jugadores.

## What Changes

- Antes de iniciar cada partida (al abrir el juego y tras cada GAME OVER) se
  muestra una pantalla de ingreso de nombre: el jugador escribe su nombre con el
  teclado dentro de la ventana del juego y lo confirma con ENTER.
- Se agrega un almacenamiento SQLite local que guarda la **mejor** puntuación por
  usuario (nombre, monedas y nivel alcanzado). Si el jugador ya tiene un registro
  y la partida nueva tiene más monedas, se actualiza; si no, se conserva la
  existente.
- Al perder (GAME OVER), además del resumen de la partida, se muestra el ranking
  **Top 5** de jugadores ordenado por monedas (descendente).
- Con ENTER en GAME OVER se vuelve a la pantalla de ingreso de nombre para iniciar
  una nueva partida.
- El nombre ingresado se muestra en el HUD durante la partida.
- No hay cambios de API ni de dependencias nuevas: `sqlite3` es parte de la
  librería estándar de Python.

## Capabilities

### New Capabilities

- `player-scores-leaderboard`: cubre el flujo de identificación del jugador
  (ingreso de nombre en la ventana), la persistencia SQLite de la mejor
  puntuación por usuario (monedas y nivel) y la pantalla de ranking Top 5
  ordenado por monedas que se muestra al perder la partida.

### Modified Capabilities

- `mario-face-capture`: cambia los requisitos de arranque, estados y reinicio —
  el menú de inicio pasa a ser una pantalla de ingreso de nombre (ENTER confirma
  y arranca), el reinicio desde GAME OVER se hace con ENTER (volviendo al
  ingreso de nombre) en lugar de SPACE, y el HUD pasa a incluir el nombre del
  jugador.

## Impact

- `src/games/mario/mario_face_game.py`: nueva pantalla de ingreso de nombre,
  transición MENU → PLAYING por ENTER, GAME OVER con ranking, reinicio por
  ENTER, HUD con nombre del jugador.
- `src/games/mario/mario_game.py`: manejo de teclado y estados base si el diseño
  decide integrar el nombre/pantallas a nivel del engine base.
- `src/games/mario/main.py`: inicialización del almacenamiento SQLite y del
  engine con el repositorio de puntuaciones.
- Nuevo módulo de persistencia (p.ej. `src/core/score_store.py` o
  `src/games/mario/score_store.py`): conexión SQLite, tabla `players`
  (nombre, monedas, nivel), upsert de la mejor puntuación y consulta del Top 5.
- Archivo de base de datos local (p.ej. `scores.db`) creado en la raíz del
  proyecto en el primer uso; se agrega a `.gitignore`.
- `requirements.txt`: sin cambios (se usa `sqlite3` de la stdlib).