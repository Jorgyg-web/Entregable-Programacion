# app/main.py
import logging
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from .database import SessionLocal, engine
from .models import DecBase
from . import schemas, crud, task

# Configuración de logging

logger = logging.getLogger("liga")
logger.setLevel(logging.DEBUG)

# Handler para consola (DEBUG+)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_format = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

# Handler para archivo debug.log (DEBUG+)
debug_file_handler = logging.FileHandler("debug.log", encoding="utf-8")
debug_file_handler.setLevel(logging.DEBUG)
debug_file_handler.setFormatter(console_format)
logger.addHandler(debug_file_handler)

# Handler para archivo warning.log (WARNING+)
warning_file_handler = logging.FileHandler("warning.log", encoding="utf-8")
warning_file_handler.setLevel(logging.WARNING)
warning_file_handler.setFormatter(console_format)
logger.addHandler(warning_file_handler)


app = FastAPI(title="Liga API")
logger.info("FastAPI app initialized")

DecBase.metadata.create_all(bind=engine)
logger.debug("Database tables created (if not exist)")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#Teams
@app.post("/teams")
def create_team(payload: schemas.TeamCreate, db=Depends(get_db)):
    logger.debug(f"POST /teams payload: {payload}")
    team = crud.create_team(db, payload)
    logger.info(f"Team created: {team.id} - {team.nombre}")
    return team

@app.get("/teams")
def list_teams(db=Depends(get_db)):
    logger.debug("GET /teams called")
    teams = crud.list_teams(db)
    logger.info(f"Returned {len(teams)} teams")
    return teams

@app.get("/teams/{team_id}")
def get_team(team_id: int, db=Depends(get_db)):
    logger.debug(f"GET /teams/{team_id} called")
    team = crud.get_team(db, team_id)
    if not team:
        logger.warning(f"Team not found: {team_id}")
        raise HTTPException(status_code=404, detail="Team not found")
    logger.info(f"Team returned: {team.id} - {team.nombre}")
    return team

@app.patch("/teams/{team_id}")
def patch_team(team_id: int, patch: schemas.TeamUpdate, db=Depends(get_db)):
    logger.debug(f"PATCH /teams/{team_id} payload: {patch}")
    team = crud.update_team(db, team_id, patch)
    if not team:
        logger.warning(f"Team to patch not found: {team_id}")
        raise HTTPException(status_code=404, detail="Team not found")
    logger.info(f"Team updated: {team.id} - {team.nombre}")
    return team

@app.delete("/teams/{team_id}")
def remove_team(team_id: int, db=Depends(get_db)):
    logger.debug(f"DELETE /teams/{team_id} called")
    ok = crud.delete_team(db, team_id)
    if not ok:
        logger.warning(f"Team to delete not found: {team_id}")
        raise HTTPException(status_code=404, detail="Team not found")
    logger.info(f"Team deleted: {team_id}")
    return None

@app.get("/teams/{team_id}/players")
def list_team_players(team_id: int, db=Depends(get_db)):
    logger.debug(f"GET /teams/{team_id}/players called")
    team = crud.get_team(db, team_id)
    if not team:
        logger.warning(f"Team not found: {team_id}")
        raise HTTPException(status_code=404, detail="Team not found")
    players = team.players or []
    logger.info(f"Returned {len(players)} players from team {team_id}")
    return players


#Players
@app.post("/players")
def create_player(payload: schemas.PlayerCreate,  background_tasks: BackgroundTasks, db=Depends(get_db)):
    logger.debug(f"POST /players payload: {payload}")
    player = crud.create_player(db, payload)
    logger.info(f"Player created: {player.id} - {player.nombre}")
    return player

@app.get("/players")
def list_players(db=Depends(get_db)):
    logger.debug("GET /players called")
    players = crud.list_players(db)
    logger.info(f"Returned {len(players)} players")
    return players

@app.get("/players/{player_id}")
def get_player(player_id: int, db=Depends(get_db)):
    logger.debug(f"GET /players/{player_id} called")
    player = crud.get_player_and_stats(db, player_id)
    if not player:
        logger.warning(f"Player not found: {player_id}")
        raise HTTPException(status_code=404, detail="Player not found")
    logger.info(f"Player returned: {player.id} - {player.nombre}")
    return player

@app.patch("/players/{player_id}")
def patch_player(player_id: int, patch: schemas.PlayerUpdate, background_tasks: BackgroundTasks, db=Depends(get_db)):
    logger.debug(f"PATCH /players/{player_id} payload: {patch}")
    player = crud.update_player(db, player_id, patch)
    if not player:
        logger.warning(f"Player to patch not found: {player_id}")
        raise HTTPException(status_code=404, detail="Player not found")
    background_tasks.add_task(task.recompute_player_value, player_id=player_id)
    logger.info(f"Player updated: {player.id} - {player.nombre}")
    return player

@app.delete("/players/{player_id}")
def remove_player(player_id: int, db=Depends(get_db)):
    logger.debug(f"DELETE /players/{player_id} called")
    ok = crud.delete_player(db, player_id)
    if not ok:
        logger.warning(f"Player to delete not found: {player_id}")
        raise HTTPException(status_code=404, detail="Player not found")
    logger.info(f"Player deleted: {player_id}")
    return None


#Extras
@app.patch("/players/{player_id}/team/{team_id}")
def assign_player_to_team(player_id: int, team_id: int, db=Depends(get_db)):
    logger.debug(f"PATCH /players/{player_id}/team/{team_id} called")
    player = crud.get_player(db, player_id)
    team = crud.get_team(db, team_id)
    if not player:
        logger.warning(f"Player not found: {player_id}")
        raise HTTPException(status_code=404, detail="Player not found")
    if not team:
        logger.warning(f"Team not found: {team_id}")
        raise HTTPException(status_code=404, detail="Team not found")
    
    patched = crud.update_player(db, player_id, {"equipo_id": team_id})
    logger.info(f"Player {player_id} assigned to team {team_id}")
    return patched

@app.get("/players/{player_id}/team")
def get_player_team(player_id: int, db=Depends(get_db)):
    logger.debug(f"GET /players/{player_id}/team called")
    player = crud.get_player(db, player_id)
    if not player:
        logger.warning(f"Player not found: {player_id}")
        raise HTTPException(status_code=404, detail="Player not found")
    if not player.equipo:
        logger.warning(f"Team not found for player {player_id}")
        raise HTTPException(status_code=404, detail="Team not found")
    logger.info(f"Player {player_id} belongs to team {player.equipo.id}")
    return player.equipo

@app.get("/playersNoTeam")
def list_players_without_teams(db=Depends(get_db)):
    logger.debug("GET /players called")
    players = crud.get_players_without_team(db)
    if len(players) == 0:
        return 'No hay jugadores sin equipo'
    logger.info(f"Returned {len(players)} players")
    return players

#Estadisticas
@app.put("/players/{player_id}/stats")
def upsert_player_stats(player_id: int, payload: schemas.StatsIn, background_tasks: BackgroundTasks, db=Depends(get_db)):
    player = crud.get_player(db, player_id)
    if not player:
        raise HTTPException(404, "Player not found")
    crud.upsert_stats_for_player(db, player_id, payload.model_dump())
    background_tasks.add_task(task.recompute_player_value, player_id=player_id)
    return {"detail": "Estadísticas actualizadas. Recomputando valor en background."}

@app.get("/playersDetail/{player_id}")
def get_player_detail(player_id: int, db=Depends(get_db)):
    player = crud.get_player(db, player_id)
    if not player:
        raise HTTPException(404, "Jugador no encontrado")

    stats = crud.get_stats(db, player_id)

    return {
        "jugador": {
            "id": player.id,
            "nombre": player.nombre,
            "dorsal": player.dorsal,
            "posicion": player.posicion,
            "goles": player.goles,
            "tarjetas_a": player.tarjetas_a,
            "tarjetas_r": player.tarjetas_r,
            "equipo_id": player.equipo_id,
            'valor': player.valor
        },
        "estadisticas": {
            "tiros": stats.tiros if stats else 0,
            "tiros_a_puerta": stats.tiros_a_puerta if stats else 0,
            "asistencias": stats.asistencias if stats else 0,
            "regates_intentados": stats.regates_intentados if stats else 0,
            "regates_exitosos": stats.regates_exitosos if stats else 0,
            "pases_intentados": stats.pases_intentados if stats else 0,
            "pases_completados": stats.pases_completados if stats else 0,
            "entradas_intentadas": stats.entradas_intentadas if stats else 0,
            "entradas_exitosas": stats.entradas_exitosas if stats else 0,
            "paradas": stats.paradas if stats else 0
        }
    }

#Partidos
@app.post("/games")
def create_game(payload: schemas.GameCreate, db = Depends(get_db), background_tasks: BackgroundTasks = None):
    fecha = payload.fecha
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha)
        except ValueError:
            raise HTTPException(422, "Formato de fecha inválido. Usa ISO 8601 (YYYY-MM-DDTHH:MM:SS)")

    try:
        game = crud.create_game(db, local_id=payload.local_id, visitante_id=payload.visitante_id, fecha=fecha, jornada=payload.jornada)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {
        "id": game.id,
        "local_id": game.local_id,
        "visitante_id": game.visitante_id,
        "fecha": game.fecha.isoformat() if game.fecha else None,
        "jornada": game.jornada,
        "estado": game.estado,
        "goles_local": game.goles_local,
        "goles_visitante": game.goles_visitante,
    }


@app.patch("/games/{game_id}/result")
def set_game_result(game_id: int, payload: schemas.GameResultUpdate, db = Depends(get_db), background_tasks: BackgroundTasks = None):
    game = crud.set_game_result(db, game_id=game_id, goles_local=payload.goles_local, goles_visitante=payload.goles_visitante)
    if not game:
        raise HTTPException(404, "Game not found")

    background_tasks.add_task(task.recompute_team_record, team_id=game.local_id)
    background_tasks.add_task(task.recompute_team_record, team_id=game.visitante_id)

    return {
        "id": game.id,
        "local_id": game.local_id,
        "visitante_id": game.visitante_id,
        "fecha": game.fecha.isoformat() if game.fecha else None,
        "jornada": game.jornada,
        "estado": game.estado,
        "goles_local": game.goles_local,
        "goles_visitante": game.goles_visitante,
    }


@app.get("/games")
def list_games(team_id: int | None = Query(default=None), db = Depends(get_db)):
    games = crud.list_games(db, team_id=team_id)
    return [
        {
            "id": g.id,
            "local_id": g.local_id,
            "visitante_id": g.visitante_id,
            "fecha": g.fecha.isoformat() if g.fecha else None,
            "jornada": g.jornada,
            "estado": g.estado,
            "goles_local": g.goles_local,
            "goles_visitante": g.goles_visitante,
        }
        for g in games
    ]


@app.get("/games/{game_id}")
def get_game(game_id: int, db = Depends(get_db)):
    g = db.get(Game, game_id)
    if not g:
        raise HTTPException(404, "Game not found")
    return {
        "id": g.id,
        "local_id": g.local_id,
        "visitante_id": g.visitante_id,
        "fecha": g.fecha.isoformat() if g.fecha else None,
        "jornada": g.jornada,
        "estado": g.estado,
        "goles_local": g.goles_local,
        "goles_visitante": g.goles_visitante,
    }