## Context

El Mario Face Jump (`mario_face_game.py`) extiende `MarioGameEngine` (`mario_game.py`), que a su
vez usa clases compartidas de `game.py` (`Cloud`, `SkyBlock`, `BASE_SPEED`, `SPEED_MULTIPLIER`).
Estado actual relevante:

- `Cloud.render` (`game.py:541`) dibuja una elipse simple → por eso "no parecen nubes".
- El fondo de juego usa `frame[:] = (200, 230, 255)` (`mario_game.py:873` y `mario_face_game.py:164`),
  que en BGR es **naranja/durazno** (RGB 255,230,200), no celeste. `SKY_COLOR = (235,206,135)`
  (BGR) sí es celeste real (RGB 135,206,235).
- Velocidad: `BASE_SPEED * SPEED_MULTIPLIER^(level-1)` con `SPEED_MULTIPLIER=1.10` (multiplicativa).
- `_update_sky_blocks` (`mario_game.py:734`) otorga +1 vida; spawn por temporizador aleatorio.
- El HUD muestra `Monedas: {passed_count}` (obstáculos superados).

El alcance pedido es **solo Mario Face Jump**. Los cambios se aíslan en `MarioFaceGameEngine`
mediante overrides; el engine compartido solo recibe extensiones no destructivas (parámetro
opcional de sprite en `Cloud`, contador `_coins`).

## Goals / Non-Goals

**Goals:**
- Nubes con sprite de nube (recortado de `sprites/smb1_misc_sprites.gif`) en el Mario Face Jump.
- Cielo de juego celeste (BGR `SKY_COLOR`).
- Velocidad aditiva `BASE_SPEED * (1 + 0.1*(nivel-1))` (multiplicador 1.0→1.1→1.2x) solo en el
  variante Face.
- 1 moneda por obstáculo superado + 1 moneda por cuadrado del cielo; contador acumulado en el HUD.
- 1 cuadrado del cielo por cada 5 obstáculos (mismo hito que subir de nivel), que otorga moneda
  (no vida), reemplazando el comportamiento de bloques de vida del variante Face.

**Non-Goals:**
- No cambiar el Mario Bros base (`mario_game.py`) ni el Minecraft (`minecraft_game.py`) ni el
  juego base (`game.py`): conservan nubes elípticas, velocidad multiplicativa y bloques de vida.
- No tocar la detección de rostro, salto, vidas, música ni invencibilidad.

## Decisions

### 1. Nubes con sprite: extensión opt-in de `Cloud`

**Decisión:** Añadir a `Cloud` un atributo `sprite: Optional[np.ndarray] = None`. Si `sprite` es
`None` se mantiene la elipse actual; si viene una imagen BGRA, `render` la escala a
`(width, height)` y la pinta con alpha blending sobre el frame. El `MarioFaceGameEngine`
sobrescribe `_spawn_cloud`/`_seed_clouds` para pasar el sprite (heredado vía
`_update_clouds`/`_render_game`).

**Alternativas:** subclase `SpriteCloud(Cloud)` → descartada por duplicar lógica de movimiento
`update`/`off_screen` sin beneficio. Cambiar `Cloud.render` global → descartado porque rompería
Minecraft/base.

### 2. Cielo celeste en juego

**Decisión:** En `MarioFaceGameEngine._render_game`, reemplazar `frame[:] = (200, 230, 255)` por
`frame[:] = SKY_COLOR` (ya importado de `mario_game.py`). Es el celeste real del juego y queda
consistente con el menú.

### 3. Velocidad aditiva solo en el variante Face

**Decisión:** Definir `SPEED_INCREMENT = 0.1` en `mario_face_game.py` y sobrescribir la property
`speed` en `MarioFaceGameEngine`:

```python
@property
def speed(self):
    return BASE_SPEED * (1 + SPEED_INCREMENT * (self._obstacle_manager.level - 1))
```

`_update_playing` ya llama a `self.speed` y propaga a obstáculos; nubes y cuadrados ya escalan
con `current_speed` (`CLOUD_SPEED_FACTOR` / `SKY_BLOCK_SPEED_FACTOR`), cumpliendo "todo avanza
más rápido". Los HUD/game-over del engine base calculan `SPEED_MULTIPLIER^(level-1)` directamente,
así que `MarioFaceGameEngine` sobrescribe `_draw_hud` y `_render_game_over` para mostrar el
multiplicador aditivo `1 + 0.1*(level-1)`.

### 4. Monedas acumuladas y cuadrado del cielo

**Decisión:** Añadir `self._coins = 0` a `MarioGameEngine.__init__` y `reset()` (inofensivo para
Mario Bros base). En `_update_playing` (donde ya se reproduce `play_coin` al pasar un obstáculo)
se suma `self._coins += 1`. El `MarioFaceGameEngine`:
- Sobrescribe `_update_sky_blocks`/`_spawn_sky_block`: al recolectar un cuadrado suma
  `self._coins += 1`, reproduce `play_coin`, marca `collected`, y el spawn se ata al hito:
  cuando `level` sube (cada 5 obstáculos) se genera **un** cuadrado (se reemplaza el spawn por
  temporizador aleatorio).
- Sobrescribe `_draw_hud` para mostrar `Monedas: {self._coins}` (acumulado) y `_render_game_over`
  con el total de monedas.
- El cuadrado del cielo se dibuja con el sprite `sprites/SMW_v-ram-yane_QuestionMarkBlock.png`
  (bloque de interrogación) escalado a `SKY_BLOCK_SIZE`, para distinguirlo de un bloque normal.
  Si el sprite no se puede cargar en runtime, fallback al rectángulo amarillo actual.

La invencibilidad (`INVINCIBILITY_THRESHOLD`) sigue atada a `passed_count` (fuera de alcance).

### 5. Asset de sprite de nube

**Decisión:** Recortar el sprite de nube de `sprites/smb1_misc_sprites.gif` (región ~
x=[47,192], y=[199,234], transparencia preservada) y guardarlo como `sprites/cloud_sprite.png`
(RGBA) committeado. `cv2.imread` no lee GIF (verificado), por eso se exporta a PNG; `pygame`
(dependencia ya existente) puede leer GIF pero se evita parsearlo en runtime. Se carga el PNG
con `cv2.imread(..., IMREAD_UNCHANGED)`. Si el asset falta en runtime, se cae a la elipse (no crash).

## Risks / Trade-offs

- [El cambio aísla comportamiento en `MarioFaceGameEngine` mediante overrides] → la lógica vive
  en `mario_face_game.py` y el engine base queda intacto; riesgo de duplicar HUD → se reutilizan
  helpers del padre cuando es posible.
- [`cv2.imread` no soporta GIF] → se commitea `sprites/cloud_sprite.png` generado una vez; no se
  depende del GIF en runtime.
- [Sprite ausente o ilegible en runtime] → fallback a la elipse actual, sin crash.
- [Cambiar spawn de cuadrados de temporizador a hito de nivel] → puede reducir la cantidad de
  cuadrados por partida; es lo pedido ("1 cuadrado cada 5 obstáculos").
- [Overrides heredan comportamiento del padre para otros variantes] → los tests del base Mario
  siguen pasando porque `MarioGameEngine` no cambia su comportamiento observable.

## Migration Plan

1. Generar `sprites/cloud_sprite.png` y añadirlo al repo.
2. Implementar extensiones no destructivas en `game.py`/`mario_game.py` (`Cloud.sprite`,
   `self._coins`).
3. Implementar overrides en `mario_face_game.py` (velocidad, cielo, nubes, cuadrados, HUD).
4. Actualizar tests: `tests/test_mario_face_game.py` (velocidad aditiva, monedas, cuadrado por
   hito, sprite), y verificar que `tests/test_mario_game.py` y `tests/test_game.py` siguen verdes.
5. Rollback: revertir `mario_face_game.py`/`game.py`/`mario_game.py` no rompe otros variantes
   (los cambios compartidos son aditivos).

## Open Questions

- (ninguna)
