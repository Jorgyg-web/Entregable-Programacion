from typing import Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
import logging

from . import models, schemas

logger = logging.getLogger("liga")

#Teams
def create_team(db: Session, data: schemas.TeamCreate) -> models.Team:
    logger.debug(f"[crud] Creando equipo: {data}")
    team = models.Team(**data.model_dump())
    db.add(team)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"[crud] Nombre de equipo duplicado: {team.nombre} -> {e}")
        raise ValueError("El nombre del equipo ya existe")
    db.refresh(team)
    logger.info(f"[crud] Equipo creado: {team.id} - {team.nombre}")
    return team

def list_teams(db: Session) -> list[models.Team]:
    logger.debug("[crud] Listando equipos")
    teams = db.execute(
        select(models.Team).order_by(models.Team.id.desc())
    ).scalars().all()
    logger.info(f"[crud] Se encontraron {len(teams)} equipos")
    return teams

def get_team(db: Session, team_id: int) -> models.Team | None:
    logger.debug(f"[crud] Buscando equipo id={team_id}")
    team = db.get(models.Team, team_id)
    if team:
        logger.info(f"[crud] Equipo encontrado: {team.id} - {team.nombre}")
    else:
        logger.warning(f"[crud] Equipo no encontrado: {team_id}")
    return team

def update_team(db: Session, team_id: int, patch: schemas.TeamUpdate) -> models.Team | None:
    logger.debug(f"[crud] Actualizando equipo id={team_id} con {patch}")
    team = db.get(models.Team, team_id)
    if not team:
        logger.warning(f"[crud] Equipo a actualizar no encontrado: {team_id}")
        return None
    for field, value in patch.model_dump(exclude_unset=True).items():
        setattr(team, field, value)
    db.commit()
    db.refresh(team)
    logger.info(f"[crud] Equipo actualizado: {team.id} - {team.nombre}")
    return team

def delete_team(db: Session, team_id: int) -> bool:
    logger.debug(f"[crud] Eliminando equipo id={team_id}")
    team = db.get(models.Team, team_id)
    if not team:
        logger.warning(f"[crud] Equipo a eliminar no encontrado: {team_id}")
        return False
    db.delete(team)
    db.commit()
    logger.info(f"[crud] Equipo eliminado: {team_id}")
    return True

#Players
def create_player(db: Session, data: schemas.PlayerCreate, equipo_id: Optional[int] = None) -> models.Player:
    logger.debug(f"[crud] Creando jugador: {data} (equipo_id={equipo_id})")
    payload = data.model_dump()
    if equipo_id is not None:
        payload["equipo_id"] = equipo_id
    player = models.Player(**payload)
    db.add(player)
    db.commit()
    db.refresh(player)

    if player.equipo_id:
        total = db.scalar(
            select(func.count()).select_from(models.Player).where(models.Player.equipo_id == player.equipo_id)
        )
        team = db.get(models.Team, player.equipo_id)
        if team is not None:
            team.jugadores = int(total or 0)
            db.commit()

    logger.info(f"[crud] Jugador creado: {player.id} - {player.nombre}")
    return player

def list_players(db: Session) -> list[models.Player]:
    logger.debug("[crud] Listando jugadores")
    players = db.execute(
        select(models.Player).order_by(models.Player.id.desc())
    ).scalars().all()
    logger.info(f"[crud] Se encontraron {len(players)} jugadores")
    return players

def get_player(db: Session, player_id: int) -> models.Player | None:
    logger.debug(f"[crud] Buscando jugador id={player_id}")
    player = db.get(models.Player, player_id)
    if player:
        logger.info(f"[crud] Jugador encontrado: {player.id} - {player.nombre}")
    else:
        logger.warning(f"[crud] Jugador no encontrado: {player_id}")
    return player


def update_player(db: Session, player_id: int, patch: Optional[Union[dict, "schemas.PlayerUpdate"]] = None) -> Optional["models.Player"]:
    logger.debug(f"[crud] Actualizando jugador id={player_id} con {patch}")

    player = db.get(models.Player, player_id)
    if not player:
        logger.warning(f"[crud] Jugador a actualizar no encontrado: {player_id}")
        return None

    if patch is None:
        payload = {}
    elif hasattr(patch, "model_dump"):  
        payload = patch.model_dump(exclude_unset=True)
    elif isinstance(patch, dict):
        payload = dict(patch)
    else:
        logger.warning(f"[crud] Tipo de patch no soportado: {type(patch)}")
        return None

    if not payload:
        logger.info(f"[crud] Sin cambios para jugador id={player_id}")
        return player 
    if "equipo_id" in payload and payload["equipo_id"] is not None:
        team = db.get(models.Team, payload["equipo_id"])
        if team is None:
            logger.warning(f"[crud] Equipo no existe: {payload['equipo_id']}")
            return None

    equipo_antes = player.equipo_id

    # Aplica cambios
    for field, value in payload.items():
        setattr(player, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.exception("[crud] IntegrityError al actualizar jugador")
        return None

    db.refresh(player)
    logger.info(f"[crud] Jugador actualizado: {player.id} - {player.nombre}")

    # (Opcional) si quieres mantener contadores por equipo cuando cambie equipo_id:
    if equipo_antes != player.equipo_id:
        try:
            # actualizar contador equipo anterior
            if equipo_antes:
                total_antes = db.scalar(
                    select(func.count()).select_from(models.Player)
                    .where(models.Player.equipo_id == equipo_antes)
                )
                team_antes = db.get(models.Team, equipo_antes)
                if team_antes is not None:
                    team_antes.jugadores = int(total_antes or 0)

            # actualizar contador equipo nuevo
            if player.equipo_id:
                total_despues = db.scalar(
                    select(func.count()).select_from(models.Player)
                    .where(models.Player.equipo_id == player.equipo_id)
                )
                team_despues = db.get(models.Team, player.equipo_id)
                if team_despues is not None:
                    team_despues.jugadores = int(total_despues or 0)

            db.commit()
        except IntegrityError:
            db.rollback()
            logger.exception("[crud] IntegrityError al recalcular contadores de equipos")

    return player


def delete_player(db: Session, player_id: int) -> bool:
    logger.debug(f"[crud] Eliminando jugador id={player_id}")
    player = db.get(models.Player, player_id)
    if not player:
        logger.warning(f"[crud] Jugador a eliminar no encontrado: {player_id}")
        return False

    equipo_id = player.equipo_id
    db.delete(player)
    db.commit()

    if equipo_id:
        total = db.scalar(
            select(func.count()).select_from(models.Player).where(models.Player.equipo_id == equipo_id)
        )
        team = db.get(models.Team, equipo_id)
        if team is not None:
            team.jugadores = int(total or 0)
            db.commit()

    logger.info(f"[crud] Jugador eliminado: {player_id}")
    return True

def get_players_without_team(db: Session) -> list[models.Player]:
    logger.debug("[crud] Devolviendo jugadores que no tienen equipo")
    players = db.execute(
        select(models.Player).order_by(models.Player.id.desc()).where(models.Player.equipo_id == None)).scalars().all()
    logger.info(f"[crud] Se encontraron {len(players)} jugadores")
    return players

#Estadisticas
def upsert_stats_for_player(db: Session, player_id: int, data: dict) -> models.Stats:
    logger.debug(f"[crud] Upsert estadisticas player_id={player_id}: {data}")
    st = db.query(models.Stats).filter(models.Stats.player_id == player_id).one_or_none()
    if st is None:
        st = models.Stats(player_id=player_id, **data)
        db.add(st)
    else:
        for k, v in data.items():
            setattr(st, k, v)
    db.commit()
    db.refresh(st)
    logger.info(f"[crud] Estadisticas actualizadas player_id={player_id}")
    return st

def get_stats(db: Session, player_id: int) -> models.Stats | None:
    logger.debug(f"[crud] Obteniendo estadisticas player_id={player_id}")
    st = db.query(models.Stats).filter(models.Stats.player_id == player_id).one_or_none()
    if st:
        logger.info(f"[crud] Estadisticas encontradas player_id={player_id}")
    else:
        logger.warning(f"[crud] Estadisticas no encontradas player_id={player_id}")
    return st

def get_player_and_stats(db: Session, player_id: int) -> models.Player | None:
    logger.debug(f"[crud] Buscando jugador id={player_id}")
    player = db.execute(select(models.Player, models.Stats)
        .join(models.Stats, models.Player.id == models.Stats.player_id) 
        .where(models.Player.id == player_id)).scalars().first()
    if player:
        logger.info(f"[crud] Jugador encontrado: {player.id} - {player.nombre}")
    else:
        logger.warning(f"[crud] Jugador no encontrado: {player_id}")
    return player

#Partidos
def create_game(db: Session, local_id: int, visitante_id: int, fecha=None, jornada: int | None = None) -> models.Game:
    logger.debug(f"[crud] Creando partido L:{local_id} vs V:{visitante_id} fecha={fecha} jornada={jornada}")
    if local_id == visitante_id:
        raise ValueError("Un equipo no puede jugar contra sí mismo")

    game = models.Game(local_id=local_id, visitante_id=visitante_id, fecha=fecha, jornada=jornada)
    db.add(game)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"[crud] Duplicado de partido o restricción violada: {e}")
        raise ValueError("Partido duplicado para esa fecha/jornada")
    db.refresh(game)
    logger.info(f"[crud] Partido creado id={game.id} L:{local_id} vs V:{visitante_id}")
    return game


def set_game_result(db: Session, game_id: int, goles_local: int, goles_visitante: int) -> models.Game | None:
    logger.debug(f"[crud] Asignando resultado partido id={game_id}: {goles_local}-{goles_visitante}")
    game = db.get(models.Game, game_id)
    if not game:
        logger.warning(f"[crud] Partido no encontrado: {game_id}")
        return None

    game.goles_local = int(goles_local)
    game.goles_visitante = int(goles_visitante)
    game.estado = "jugado"
    db.commit()
    db.refresh(game)
    logger.info(f"[crud] Partido actualizado id={game.id} -> {goles_local}-{goles_visitante}")
    return game


def list_games(db: Session, team_id: int | None = None) -> list[models.Game]:
    logger.debug(f"[crud] Listando partidos team_id={team_id}")
    stmt = select(models.Game).order_by(models.Game.fecha.desc(), models.Game.id.desc())
    if team_id:
        stmt = stmt.where((models.Game.local_id == team_id) | (models.Game.visitante_id == team_id))
    games = db.execute(stmt).scalars().all()
    logger.info(f"[crud] Se encontraron {len(games)} partidos")
    return games