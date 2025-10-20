from sqlalchemy.orm import DeclarativeBase, relationship, column_property
from sqlalchemy import Integer, String, Column, ForeignKey, Enum, select, func, Float, DateTime, CheckConstraint, UniqueConstraint
from datetime import datetime

class DecBase(DeclarativeBase):
    pass

class Player(DecBase):
    __tablename__ = "jugadores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    dorsal = Column(Integer, nullable=False)
    posicion = Column(Enum("portero", "defensa", "mediocampo", "delantero", name="posicion_enum"), nullable=False)
    goles = Column(Integer, default=0)
    tarjetas_a = Column(Integer, default=0)
    tarjetas_r = Column(Integer, default=0)
    valor = Column(Float, default=0.0)
    equipo_id = Column(Integer, ForeignKey("equipos.id", ondelete="CASCADE"))
    equipo = relationship("Team", back_populates="players")

    estadisticas = relationship("Stats", back_populates="player", uselist=False, cascade="all, delete-orphan")

class Team(DecBase):
    __tablename__ = "equipos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), unique=True, nullable=False)
    jugadores = Column(Integer, default=0)
    partidos = Column(Integer, default=0)
    victorias = Column(Integer, default=0)
    players = relationship("Player", back_populates="equipo", cascade="all, delete-orphan")
    goles = column_property(
        select(func.coalesce(func.sum(Player.goles), 0))
        .where(Player.equipo_id == id)
        .correlate_except(Player)
        .scalar_subquery()
    )
    home_games = relationship(
        "Game",
        foreign_keys="[Game.local_id]",
        back_populates="local",
        cascade="all, delete-orphan",
    )
    away_games = relationship(
        "Game",
        foreign_keys="[Game.visitante_id]",
        back_populates="visitante",
        cascade="all, delete-orphan",
    )
class Stats(DecBase):
    __tablename__ = "estadisticas"

    player_id = Column(Integer, ForeignKey("jugadores.id", ondelete="CASCADE"), primary_key=True)

    tiros = Column(Integer, default=0)
    tiros_a_puerta = Column(Integer, default=0)
    asistencias = Column(Integer, default=0)

    regates_intentados = Column(Integer, default=0)
    regates_exitosos = Column(Integer, default=0)

    pases_intentados = Column(Integer, default=0)
    pases_completados = Column(Integer, default=0)

    entradas_intentadas = Column(Integer, default=0)
    entradas_exitosas = Column(Integer, default=0)

    paradas = Column(Integer, default=0)

    player = relationship("Player", back_populates="estadisticas")

class Game(DecBase):
    __tablename__ = "partidos"
    id = Column(Integer, primary_key=True, index=True)

    local_id = Column(Integer, ForeignKey("equipos.id", ondelete="CASCADE"), nullable=False)
    visitante_id = Column(Integer, ForeignKey("equipos.id", ondelete="CASCADE"), nullable=False)

    fecha = Column(DateTime, nullable=True)
    jornada = Column(Integer, nullable=True)
    estado = Column(Enum("pendiente", "jugado", name="estado_partido"), nullable=False, default="pendiente")
    goles_local = Column(Integer, default=0)
    goles_visitante = Column(Integer, default=0)

    local = relationship("Team", foreign_keys=[local_id], back_populates="home_games")
    visitante = relationship("Team", foreign_keys=[visitante_id], back_populates="away_games")