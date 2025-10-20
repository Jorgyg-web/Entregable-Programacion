# Caso de uso: Gestión de Liga de Fútbol - API REST con FastAPI

## Objetivo del proyecto

El objetivo es implementar una **API REST completa** para gestionar una **liga de fútbol profesional**, incluyendo equipos, jugadores, partidos y estadísticas.  

---

## Caso de uso implementado: Liga de Fútbol

La API representa el sistema básico de una **liga de fútbol**, en la que cada **equipo** puede tener varios **jugadores** asociados y disputar **partidos** oficiales.

---

## Entidades principales

### Equipo (`Team`)
- Campos: `id`, `nombre`, `jugadores`, `partidos`, `victorias`, `goles`
- Un equipo puede contener varios jugadores.
- Los campos `partidos` y `victorias` se actualizan automáticamente al registrarse resultados.
- No pueden modificarse manualmente desde la API.

### Jugador (`Player`)
- Campos: `id`, `nombre`, `dorsal`, `posicion`, `goles`, `tarjetas_a`, `tarjetas_r`, `valor`, `equipo_id`
- Cada jugador pertenece a un equipo.
- El valor del jugador se actualiza automáticamente en función de sus estadísticas y rendimiento.

### Estadísticas (`Stats`)
- Campos:  
  `player_id`, `tiros`, `tiros_a_puerta`, `asistencias`, `regates_intentados`, `regates_exitosos`,  
  `pases_intentados`, `pases_completados`, `entradas_intentadas`, `entradas_exitosas`, `paradas`
- Cada jugador tiene un conjunto de estadísticas asociadas 1:1.
- Se pueden crear o modificar mediante `PUT /players/{id}/stats`.

### Partido (`Game`)
- Campos:  
  `id`, `local_id`, `visitante_id`, `goles_local`, `goles_visitante`, `estado`, `fecha`, `jornada`
- Representa un enfrentamiento entre dos equipos.
- Al registrar un resultado, se actualizan automáticamente los partidos y victorias de los equipos.
- No puede modificarse manualmente.

---

## Funcionalidad conseguida

### Endpoints RESTful
Se implementaron múltiples rutas que permiten la gestión completa de equipos, jugadores, estadísticas y partidos:

| Método | Endpoint | Descripción |
|--------|-----------|-------------|
| `GET` | `/teams` | Listar todos los equipos |
| `POST` | `/teams` | Crear un nuevo equipo |
| `GET` | `/teams/{id}` | Consultar los datos de un equipo concreto |
| `PATCH` | `/teams/{id}` | Actualizar parcialmente los datos de un equipo |
| `DELETE` | `/teams/{id}` | Eliminar un equipo |
| `GET` | `/teams/{id}/players` | Listar jugadores de un equipo |
| `GET` | `/players` | Listar todos los jugadores |
| `POST` | `/players` | Crear un jugador |
| `GET` | `/players/{id}` | Ver los datos de un jugador |
| `PATCH` | `/players/{id}` | Actualizar un jugador |
| `PUT` | `/players/{id}/stats` | Crear o modificar estadísticas de un jugador |
| `GET` | `/players/{id}/team` | Consultar el equipo de un jugador |
| `DELETE` | `/players/{id}` | Eliminar un jugador |
| `GET` | `/games` | Listar todos los partidos |
| `POST` | `/games` | Crear un partido |
| `PATCH` | `/games/{id}/result` | Registrar el resultado de un partido |

---

### Funcionalidades del script

- Creación automática de equipos de **Primera División**.
- Generación aleatoria de jugadores (nombres, dorsales, posiciones, estadísticas).
- Asignación aleatoria de jugadores a equipos.
- Creación de partidos aleatorios entre equipos.
- Al crear un jugador:
  - Se solicita en qué equipo estará.
  - Si el equipo ya tiene partidos jugados, se pregunta si se quieren añadir estadísticas.
- Menú interactivo para operaciones CRUD:
  - Crear, ver, actualizar y eliminar equipos y jugadores.
  - Ver jugadores sin equipo.
  - Asignar jugadores a equipos.
  - Consultar el equipo de un jugador.

---

## Lógica automática implementada

- Recalculo automático del valor del jugador al modificar sus estadísticas o resultados de su equipo.  
- Actualización automática de `partidos` y `victorias` en equipos al registrar resultados.  
- Prevención de duplicados y validaciones lógicas (un equipo no puede jugar contra sí mismo).   
- Los campos `partidos` y `victorias` en equipos no son editables manualmente.

---

