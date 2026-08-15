# player-scores-leaderboard Specification

## Purpose
Identifica al jugador por nombre antes de cada partida, guarda su mejor
puntuación (monedas y nivel) en una base SQLite local y muestra un ranking
Top 5 ordenado por monedas al perder la partida.

## Requirements

### Requirement: Ingreso de nombre del jugador

El sistema SHALL mostrar una pantalla de ingreso de nombre antes de iniciar
cada partida. El jugador escribe su nombre con el teclado dentro de la ventana
del juego y lo confirma con ENTER para arrancar la partida.

#### Scenario: Se muestra la pantalla de ingreso de nombre al abrir el juego

- **WHEN** el juego inicia y la cámara está abierta
- **THEN** el sistema muestra una pantalla de ingreso de nombre sobre el fondo
  Mario (cielo, nubes, arbustos y suelo de ladrillos)
- **AND** el campo de nombre está vacío y enfocado para escribir
- **AND** no se inicia la partida hasta confirmar el nombre

#### Scenario: El jugador escribe su nombre

- **WHEN** el jugador presiona teclas alfanuméricas y de borrado en la pantalla
  de ingreso de nombre
- **THEN** el sistema agrega o elimina caracteres del nombre mostrado en pantalla
- **AND** el nombre se muestra en el campo de texto conforme se escribe

#### Scenario: ENTER confirma el nombre e inicia la partida

- **WHEN** el jugador presiona ENTER con un nombre no vacío
- **THEN** el sistema almacena el nombre como jugador de la partida
- **AND** transiciona al estado PLAYING
- **AND** el personaje aparece en el suelo y los obstáculos empiezan a generarse
  desde la derecha con separación amplia (nivel 1)

#### Scenario: ENTER con nombre vacío no inicia la partida

- **WHEN** el jugador presiona ENTER sin haber escrito ningún carácter
- **THEN** el sistema no inicia la partida
- **AND** mantiene la pantalla de ingreso de nombre esperando un nombre

### Requirement: Persistencia SQLite de la mejor puntuación por jugador

El sistema SHALL almacenar en una base SQLite local la mejor puntuación de cada
jugador: nombre, monedas y nivel alcanzado. La base SHALL conservar un único
registro por jugador: si una partida nueva supera las monedas del registro
existente, el registro se actualiza; si no, se conserva el anterior.

#### Scenario: Primera partida de un jugador

- **WHEN** un jugador termina su primera partida (GAME OVER)
- **THEN** el sistema inserta un registro con su nombre, las monedas finales y
  el nivel alcanzado

#### Scenario: La partida supera el mejor registro previo

- **WHEN** un jugador con registro existente termina una partida con más monedas
  que su mejor registro
- **THEN** el sistema actualiza el registro con las nuevas monedas y el nivel
  alcanzado

#### Scenario: La partida no supera el mejor registro previo

- **WHEN** un jugador con registro existente termina una partida con monedas
  menores o iguales a su mejor registro
- **THEN** el sistema conserva el registro existente sin modificar

#### Scenario: Los datos persisten entre ejecuciones

- **WHEN** el juego se cierra y se vuelve a abrir
- **THEN** el sistema conserva los registros de jugadores guardados en la base
  SQLite local

### Requirement: Ranking Top 5 ordenado por monedas

El sistema SHALL mostrar al perder la partida (GAME OVER) el ranking de los 5
mejores jugadores, ordenado por monedas en orden descendente, junto con su
nivel.

#### Scenario: Se muestra el Top 5 al perder

- **WHEN** la partida termina en GAME OVER
- **THEN** el sistema muestra sobre la pantalla de GAME OVER el resumen de la
  partida (puntuación, monedas, nivel, velocidad)
- **AND** muestra hasta 5 puestos del ranking ordenados de mayor a menor monedas
- **AND** cada puesto muestra la posición, el nombre, las monedas y el nivel del
  jugador

#### Scenario: Menos de 5 jugadores registrados

- **WHEN** hay menos de 5 jugadores en la base
- **THEN** el sistema muestra únicamente los puestos existentes

#### Scenario: Los jugadores sin partidas no aparecen

- **WHEN** un jugador no ha terminado ninguna partida
- **THEN** el sistema no lo incluye en el ranking

### Requirement: Reinicio de partida desde GAME OVER

El sistema SHALL permitir iniciar una nueva partida desde la pantalla de GAME
OVER presionando ENTER, lo que devuelve al jugador a la pantalla de ingreso de
nombre.

#### Scenario: ENTER desde GAME OVER vuelve al ingreso de nombre

- **WHEN** el sistema está en GAME OVER y el jugador presiona ENTER
- **THEN** el sistema muestra la pantalla de ingreso de nombre con el campo
  vacío
- **AND** espera un nuevo nombre para iniciar la partida siguiente

#### Scenario: Reinicio sin perder el registro guardado

- **WHEN** el jugador inicia una nueva partida tras un GAME OVER
- **THEN** el mejor registro del jugador anterior permanece en la base SQLite