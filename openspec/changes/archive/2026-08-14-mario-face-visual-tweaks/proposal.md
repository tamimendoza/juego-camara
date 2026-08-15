## Why

En el Mario Face Jump la apariencia tiene tres problemas visuales: el graffiti
"Familia Mendoza Silva" se dibuja por encima del suelo (en el cielo), las nubes con
sprite se ven como llamas (el recorte del sprite es mucho más ancho que alto, pero se
redimensiona a una proporción casi cuadrada `width x width*2/3`) y no hay forma de saber
si el rostro del jugador entra bien en el círculo de la cabeza cuando se aleja de la
cámara (necesario para detectar el cuerpo completo).

## What Changes

- El texto "Familia Mendoza Silva" pasa a dibujarse sobre el área de ladrillos (por
  debajo de `ground_y`), en lugar de encima del suelo.
- Las nubes del Mario Face Jump se recortan en altura al redimensionar el sprite para
  que conserven la proporción ancha del sprite y no parezcan fuego.
- Se agrega un círculo de vista previa del rostro en la parte inferior derecha, sobre
  los ladrillos y fuera de la zona de juego, que muestra el recorte de rostro en vivo
  (misma `face_image` / `face_mask` usada en la cabeza) para verificar que el rostro
  entra y queda centrado cuando el jugador se aleja.
- Alcance: solo la variante Mario Face Jump (`mario_face_game.py`); el Mario Bros
  estándar no cambia.

## Capabilities

### New Capabilities

- (ninguna)

### Modified Capabilities

- `game-brick-ground`: cambia la posición del graffiti — el texto "Familia Mendoza
  Silva" debe dibujarse sobre los ladrillos del suelo (debajo de la línea del suelo),
  no encima de ella.
- `game-moving-clouds`: cambia el renderizado de las nubes con sprite — la altura
  debe recortarse para conservar una proporción ancha de nube y no parecer fuego.
- `mario-face-capture`: agrega un nuevo requisito — una vista previa circular del
  rostro en vivo en la esquina inferior derecha para verificar que el rostro entra
  bien en el círculo de la cabeza cuando el jugador está lejos de la cámara.

## Impact

- `src/mario_face_game.py`: posición del graffiti (override de `_render_static_environment`
  o parámetro), altura de nubes en `_spawn_cloud` / `_seed_clouds`, y dibujado del
  círculo de vista previa del rostro en `_render_game`.
- `src/mario_game.py`: solo si se agrega un parámetro opcional al graffiti (cambio no
  destructivo); de lo contrario sin cambios.
- `src/game.py`: sin cambios (la lógica de sprite de `Cloud` ya existe).
- Tests: `tests/test_mario_face_game.py`.
- `run_mario_face.sh` no cambia.
