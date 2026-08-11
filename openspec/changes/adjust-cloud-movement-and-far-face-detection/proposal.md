## Why

En el juego Mario Face Jump las nubes se ven mayormente "congeladas": el fondo mezcla
nubes estáticas dibujadas en posiciones fijas (`_render_static_environment`) con una
capa escasa de nubes en movimiento, así que solo algunas nubes se desplazan. Además, el
FaceLandmarker solo reconoce el rostro cuando el jugador está cerca de la cámara;
desde lejos (rostro pequeño) no detecta.

## What Changes

- Las nubes del cielo durante el juego pasan a moverse todas: se elimina el dibujado de
  nubes estáticas en posiciones fijas de la escena de juego y la capa de nubes en
  movimiento se inicializa poblada al iniciar/ reiniciar la partida, de modo que todas
  las nubes visibles se desplazan de derecha a izquierda.
- Se mantienen nubes estáticas solo en las pantallas de MENÚ y GAME OVER (fondo).
- Se baja el umbral de confianza de detección del rostro para aceptar rostros más
  pequeños/lejanos: `min_face_detection_confidence` y `min_tracking_confidence` pasan
  de `0.5` a `0.3` (valor a confirmar durante el diseño), y se evalúa reducir también
  `min_face_presence_confidence`.
- No hay cambios de API ni de dependencias; solo ajustes de parámetros y de renderizado.

## Capabilities

### New Capabilities

- (ninguna)

### Modified Capabilities

- `game-moving-clouds`: cambia el requisito de movimiento de nubes — durante el juego
  todas las nubes visibles deben desplazarse (se eliminan las nubes estáticas de la
  escena de juego y la capa en movimiento arranca poblada), no solo las pocas que
  aparecen esporádicamente.
- `mario-face-capture`: cambia el requisito de detección de rostro desde el webcam —
  el sistema debe detectar el rostro también a distancia (rostros pequeños/lejanos)
  bajando los umbrales de confianza del FaceLandmarker.

## Impact

- `src/mario_game.py`: `_render_static_environment` (quitar nubes estáticas), `_render_game`,
  `_update_clouds` / `_spawn_cloud` y el reset de `self._clouds` para poblar la capa al inicio.
- `src/mario_face_main.py`: umbrales del `FaceLandmarkerDetector`
  (`min_face_detection_confidence`, `min_tracking_confidence`, `min_face_presence_confidence`).
- `src/game.py`: constantes de nubes (`CLOUD_SPAWN_INTERVAL`, cantidad inicial) si el diseño
  lo requiere.
- `src/mario_face_game.py`: sin cambios funcionales; hereda el comportamiento del engine base.
- La variable `run_mario_face.sh` no cambia (solo lanza `python3 -m src.mario_face_main`).
