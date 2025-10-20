# app/tasks.py
import math
from .database import SessionLocal
from . import models
import logging

logger = logging.getLogger("liga")

def safe_rate(ok: int, total: int) -> float:
    return (ok / total) if total and total > 0 else 0.0

import math
from .database import SessionLocal
from . import models
import logging

logger = logging.getLogger("liga")


def safe_rate(ok: int, total: int) -> float:
    return (ok / total) if total and total > 0 else 0.0

#Calculamos el valor de los jugadores (en esto me a ayudado la IA, de hecho, aun no entiendo del todo bien como hace el calculo)
def valor_en_euros(valor_interno: float, posicion: str) -> float:

    valor_interno = max(0.0, min(valor_interno, 100.0))
    euros = 0.2 * (1.08 ** valor_interno) 

    multiplicadores = {
        "portero": 0.7,
        "defensa": 0.8,
        "mediocampo": 1.0,
        "delantero": 1.3,
    }
    factor = multiplicadores.get(posicion, 1.0)
    return round(euros * factor, 2)



def compute_player_value(player: models.Player, st: models.Stats | None, partidos_equipo: int) -> float:
    goles = player.goles or 0
    partidos = max(partidos_equipo or 0, 0)

    tiros_on_target = safe_rate(st.tiros_a_puerta, st.tiros) if st else 0.0
    regate_rate = safe_rate(st.regates_exitosos, st.regates_intentados) if st else 0.0
    pase_rate = safe_rate(st.pases_completados, st.pases_intentados) if st else 0.0
    entrada_rate = safe_rate(st.entradas_exitosas, st.entradas_intentadas) if st else 0.0
    asistencias = st.asistencias if st else 0
    paradas = st.paradas if st else 0

    weights = {
        "delantero":   dict(g=6.0, a=3.0, shot=3.0, dribble=2.0, pass_=1.5, tackle=0.5, save=0.0),
        "mediocampo":  dict(g=3.5, a=4.0, shot=1.5, dribble=2.5, pass_=3.5, tackle=1.5, save=0.0),
        "defensa":     dict(g=1.0, a=1.0, shot=0.5, dribble=0.5, pass_=2.0, tackle=5.0, save=0.0),
        "portero":     dict(g=0.5, a=0.5, shot=0.0, dribble=0.0, pass_=1.0, tackle=1.0, save=7.0),
    }
    w = weights.get(player.posicion, weights["mediocampo"])

    comp_goles = w["g"] * goles
    comp_asist = w["a"] * asistencias
    comp_shots = w["shot"] * (tiros_on_target * 10)
    comp_dribb = w["dribble"] * (regate_rate * 10)
    comp_pass  = w["pass_"] * (pase_rate * 10)
    comp_tackl = w["tackle"] * (entrada_rate * 10)
    comp_save  = w["save"] * math.log1p(paradas) * 2

    base = comp_goles + comp_asist + comp_shots + comp_dribb + comp_pass + comp_tackl + comp_save

    bonus = 1.0 + min(partidos / 100.0, 0.15)

    cards_penalty = 1.0 - min((player.tarjetas_a * 0.01 + player.tarjetas_r * 0.05), 0.2)

    valor = max(base * bonus * cards_penalty, 0.0)
    return round(valor, 2)


def recompute_player_value(player_id: int) -> None:
    db = SessionLocal()
    try:
        player = db.get(models.Player, player_id)
        if not player:
            logger.warning(f"[tasks] Player {player_id} no existe al recomputar valor")
            return

        st = db.query(models.Stats).filter(models.Stats.player_id == player_id).one_or_none()
        partidos_equipo = _count_team_games(db, player.equipo_id)
        new_val = compute_player_value(player, st, partidos_equipo)
        new_market_val = valor_en_euros(new_val, player.posicion)

        if player.valor != new_val or getattr(player, "valor_mercado", 0.0) != new_market_val:
            player.valor = new_val
            player.valor_mercado = new_market_val
            db.commit()
            logger.info(
                f"[tasks] Valor jugador {player.id} actualizado -> "
                f"interno={new_val:.2f}, mercado={new_market_val:.2f}M€"
            )
    except Exception as e:
        db.rollback()
        logger.exception(f"[tasks] Error recomputando valor de player {player_id}: {e}")
    finally:
        db.close()

def recompute_team_record(team_id: int) -> None:

    db = SessionLocal()
    try:
        Team, Game = models.Team, models.Game
        team = db.get(Team, team_id)
        if not team:
            return
        pj = db.query(Game).filter(
            Game.estado == "jugado",
            ((Game.local_id == team_id) | (Game.visitante_id == team_id))
        ).count()

        wins = db.query(Game).filter(
            Game.estado == "jugado",
            (
                ((Game.local_id == team_id) & (Game.goles_local > Game.goles_visitante)) |
                ((Game.visitante_id == team_id) & (Game.goles_visitante > Game.goles_local))
            )
        ).count()

        team.partidos = pj
        team.victorias = wins
        db.commit()
        logger.info(f"[tasks] Recuento equipo {team_id}: PJ={pj}, W={wins}")
    finally:
        db.close()
