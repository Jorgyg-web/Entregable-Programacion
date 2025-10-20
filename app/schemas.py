from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PlayerCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    dorsal: int = Field(..., ge=1, le=99)
    posicion: str = Field(..., pattern="^(portero|defensa|mediocampo|delantero)$")
    goles: int | None = 0
    tarjetas_a: int | None = 0
    tarjetas_r: int | None = 0
    valor: int | None = 0
    equipo_id: Optional[int] = None
    
class PlayerUpdate(BaseModel):
    nombre: str = Field(None, min_length=2, max_length=50)
    dorsal: int = Field(None, ge=1, le=99)    
    posicion: str = Field(None, pattern="^(portero|defensa|mediocampo|delantero)$")
    goles: int | None = 0
    tarjetas_a: int | None = 0
    tarjetas_r: int | None = 0
    valor: int | None = 0
    equipo_id: Optional[int] = None
    
class TeamCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    jugadores: int | None = 0
    partidos: int | None = 0
    victorias: int | None = 0
    
class TeamUpdate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    jugadores: int | None = 0
    partidos: int | None = 0
    victorias: int | None = 0
    
class StatsIn(BaseModel):
    tiros: int = 0
    tiros_a_puerta: int = 0
    asistencias: int = 0
    regates_intentados: int = 0
    regates_exitosos: int = 0
    pases_intentados: int = 0
    pases_completados: int = 0
    entradas_intentadas: int = 0
    entradas_exitosas: int = 0
    paradas: int = 0   

class GameCreate(BaseModel):
    local_id: int
    visitante_id: int
    fecha: Optional[datetime | str] = None
    jornada: Optional[int] = None

class GameResultUpdate(BaseModel):
    goles_local: int = Field(..., ge=0)
    goles_visitante: int = Field(..., ge=0)    