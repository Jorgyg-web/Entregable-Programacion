import requests
import random
from itertools import combinations

BASE_URL = "http://127.0.0.1:8000"

random.seed(42)

POSICIONES = ["portero", "defensa", "mediocampo", "delantero"]

N_PLAYERS = 40

#Creamos los equipos(He elegido equipos de Primera Division )
def create_teams():
    print("=== Creando equipos ===")
    nombres_laliga = [
        "Real Madrid CF",
        "FC Barcelona",
        "Atlético de Madrid",
        "Sevilla FC",
        "Valencia CF",
        "Villarreal CF",
        "Real Sociedad",
        "Athletic Club",
    ]

    equipos = [
        {"nombre": nombre, "jugadores": 0, "partidos": 0, "victorias": 0}
        for nombre in nombres_laliga
    ]

    team_ids = []
    for i, data in enumerate(equipos, start=1):
        r = requests.post(f"{BASE_URL}/teams", json=data)
        if r.status_code in (200, 201):
            team = r.json()
            team_ids.append(team["id"])
            print(f"[{i}] {team['nombre']} (id={team['id']})")
        else:
            print(f"[{i}] Error creando equipo: {r.status_code} - {r.text}")

    return team_ids

def gen_stats_for_position(pos: str) -> dict:
    if pos == "delantero":
        tiros = random.randint(10, 40)
        reg_int = random.randint(10, 35)
        pase_int = random.randint(100, 250)
        entr_int = random.randint(5, 25)
        paradas = 0
        asist = random.randint(0, 10)
    elif pos == "mediocampo":
        tiros = random.randint(5, 25)
        reg_int = random.randint(15, 40)
        pase_int = random.randint(200, 500)
        entr_int = random.randint(10, 40)
        paradas = 0
        asist = random.randint(2, 15)
    elif pos == "defensa":
        tiros = random.randint(0, 10)
        reg_int = random.randint(5, 20)
        pase_int = random.randint(150, 400)
        entr_int = random.randint(20, 60)
        paradas = 0
        asist = random.randint(0, 6)
    else:
        tiros = random.randint(0, 5)
        reg_int = random.randint(0, 5)
        pase_int = random.randint(100, 350)
        entr_int = random.randint(5, 20)
        paradas = random.randint(20, 120)
        asist = random.randint(0, 3)

    tiros_ap = random.randint(int(tiros * 0.3), tiros) if tiros > 0 else 0
    reg_ex = random.randint(int(reg_int * 0.3), reg_int) if reg_int > 0 else 0
    pase_comp = random.randint(int(pase_int * 0.7), pase_int) if pase_int > 0 else 0
    entr_ex = random.randint(int(entr_int * 0.4), entr_int) if entr_int > 0 else 0

    return {
        "tiros": tiros,
        "tiros_a_puerta": tiros_ap,
        "asistencias": asist,
        "regates_intentados": reg_int,
        "regates_exitosos": reg_ex,
        "pases_intentados": pase_int,
        "pases_completados": pase_comp,
        "entradas_intentadas": entr_int,
        "entradas_exitosas": entr_ex,
        "paradas": paradas,
    }

def create_players():
    print("\n=== Creando jugadores ===")
    nombres_base = [
        "Juan", "Pedro", "Luis", "Carlos", "Miguel", "Sergio", "Diego", "Álvaro",
        "Javier", "Iván", "Mario", "Héctor", "Rubén", "Andrés", "David", "Pablo",
        "Raúl", "Iker", "Gonzalo", "Hugo", "Leo", "Tomás", "Bruno", "Noah", "Joel"
    ]
    apellidos = ["García", "López", "Martínez", "Sánchez", "Pérez", "Gómez", "Díaz", "Navarro", "Romero", "Torres"]

    players_payload = []
    for i in range(N_PLAYERS):
        nombre = f"{random.choice(nombres_base)} {random.choice(apellidos)}"
        dorsal = random.randint(1, 99)
        posicion = random.choice(POSICIONES)
        goles = random.randint(0, 10)
        tarjetas_a = random.randint(0, 5)
        tarjetas_r = random.randint(0, 1)
        players_payload.append({
            "nombre": nombre,
            "dorsal": dorsal,
            "posicion": posicion,
            "goles": goles,
            "tarjetas_a": tarjetas_a,
            "tarjetas_r": tarjetas_r,
        })

    player_ids = []
    for i, data in enumerate(players_payload, start=1):
        r = requests.post(f"{BASE_URL}/players", json=data, timeout=10)
        if r.status_code not in (200, 201):
            print(f"[{i}] Error creando jugador: {r.status_code} - {r.text}")
            continue

        pj = r.json()
        player_ids.append(pj["id"])
        print(f"[{i}] {pj['nombre']} (id={pj['id']}, pos={pj['posicion']}, dorsal={pj['dorsal']})")

        stats_payload = gen_stats_for_position(pj["posicion"])
        rs = requests.put(f"{BASE_URL}/players/{pj['id']}/stats", json=stats_payload, timeout=10)
        if rs.status_code not in (200, 201):
            print(f"Error subiendo estadísticas: {rs.status_code} - {rs.text}")
        else:
            print(f"Estadísticas OK: {stats_payload}")

    return player_ids

#Asignamos jugadores a equipos, también aleatoriamente
def assign_players_to_teams(player_ids, team_ids):
    print("\n=== Asignando jugadores a equipos (aleatorio) ===")
    if not team_ids:
        print("No hay equipos para asignar.")
        return
    for i, pid in enumerate(player_ids, start=1):
        team_id = random.choice(team_ids)
        r = requests.patch(f"{BASE_URL}/players/{pid}/team/{team_id}")
        if r.status_code == 200:
            print(f"[{i}] Player {pid} -> Team {team_id}")
        else:
            print(f"[{i}] Error asignando jugador {pid} al equipo {team_id}: {r.status_code} - {r}")
            
def generate_random_games(team_ids, num_games=12, assign_results=True):
    print("\n=== Generando partidos aleatorios ===")
    if not team_ids or len(team_ids) < 2:
        print("No hay suficientes equipos para generar partidos.")
        return []

    all_pairs = list(combinations(team_ids, 2))
    random.shuffle(all_pairs)

    num_games = min(num_games, len(all_pairs))

    created_game_ids = []
    for i, (local_id, visitante_id) in enumerate(all_pairs[:num_games], start=1):
        payload = {"local_id": local_id, "visitante_id": visitante_id}
        r = requests.post(f"{BASE_URL}/games", json=payload, timeout=10)
        if r.status_code not in (200, 201):
            print(f"[{i}] Error creando partido {local_id}-{visitante_id}: {r.status_code} - {r.text}")
            continue

        game = r.json()
        created_game_ids.append(game["id"])
        print(f"[{i}] Partido creado id={game['id']} L:{game['local_id']} vs V:{game['visitante_id']}")

        if assign_results:
            gl = random.randint(0, 5)
            gv = random.randint(0, 5)
            rs = requests.patch(
                f"{BASE_URL}/games/{game['id']}/result",
                json={"goles_local": gl, "goles_visitante": gv},
                timeout=10
            )
            if rs.status_code in (200, 201):
                print(f" Resultado {gl}-{gv} aplicado")
            else:
                print(f" Error asignando resultado: {rs.status_code} - {rs.text}")

    return created_game_ids

#Funciones para facilitar tareas y reducir codigo
def _input_int(msg):
    raw = input(msg).strip()
    if not raw or not raw.isdigit():
        return None
    return int(raw)

def _print_resp(r):
    try:
        print(f"[{r.status_code}] {r.json()}")
    except Exception:
        print(f"[{r.status_code}] {r.text}")

#Funciones para probar todos los endpoints
def menu_crear_equipo():
    print("\n--- Crear equipo (POST /teams) ---")
    nombre = input("Nombre: ").strip()
    if not nombre:
        print("Nombre vacío. Cancelado.")
        return
    payload = {"nombre": nombre, "jugadores": 0, "partidos": 0, "victorias": 0}
    r = requests.post(f"{BASE_URL}/teams", json=payload)
    _print_resp(r)

def menu_ver_equipo():
    print("\n--- Ver equipo (GET /teams/{id}) ---")
    tid = _input_int("ID equipo: ")
    if tid is None:
        print("ID inválido.")
        return
    r = requests.get(f"{BASE_URL}/teams/{tid}")
    _print_resp(r)

def menu_ver_todos_equipos():
    print("\n--- Ver todos los equipos (GET /teams) ---")
    r = requests.get(f"{BASE_URL}/teams")
    _print_resp(r)

def menu_actualizar_equipo():
    print("\n--- Actualizar equipo (PATCH /teams/{id}) ---")
    tid = _input_int("ID equipo: ")
    if tid is None:
        print("ID inválido.")
        return

    r = requests.get(f"{BASE_URL}/teams/{tid}")
    if r.status_code != 200:
        print(f"Error al obtener equipo {tid}: {r.status_code} - {r.text}")
        return
    team = r.json()

    nombre_actual = team.get("nombre")
    partidos_actual = int(team.get("partidos", 0))
    victorias_actual = int(team.get("victorias", 0))

    print(f"\nEquipo actual:")
    print(f"Nombre: {nombre_actual}")
    print(f"Partidos: {partidos_actual}")
    print(f"Victorias: {victorias_actual}")

    print("\n¿Qué deseas actualizar?")
    print("1) Nombre")
    print("2) Partidos")
    print("3) Victorias")
    print("4) Cancelar")
    op = input("Selecciona opción: ").strip()

    payload = {
        "nombre": nombre_actual,
        "partidos": partidos_actual,
        "victorias": victorias_actual,
    }

    if op == "1":
        nuevo_nombre = input("Nuevo nombre: ").strip()
        if nuevo_nombre:
            payload["nombre"] = nuevo_nombre
        else:
            print("Nombre vacío, se mantiene el anterior.")

    elif op == "2":
        while True:
            nuevos_partidos = input("Nuevo número de partidos: ").strip()
            if not nuevos_partidos.isdigit():
                print("Valor inválido. Debe ser un número entero ≥ 0.")
                continue
            nuevos_partidos = int(nuevos_partidos)
            if nuevos_partidos < payload["victorias"]:
                print(f"No puede haber menos partidos ({nuevos_partidos}) que victorias ({payload['victorias']}).")
                continue
            payload["partidos"] = nuevos_partidos
            break

    elif op == "3":
        while True:
            nuevas_victorias = input("Nuevo número de victorias: ").strip()
            if not nuevas_victorias.isdigit():
                print("Valor inválido. Debe ser un número entero ≥ 0.")
                continue
            nuevas_victorias = int(nuevas_victorias)
            if nuevas_victorias < 0:
                print("Las victorias no pueden ser negativas.")
                continue
            if nuevas_victorias > payload["partidos"]:
                print(f"Has puesto {nuevas_victorias} victorias y actualmente hay {payload['partidos']} partidos.")
                while True:
                    nuevos_partidos = input("¿Cuántos partidos has jugado? ").strip()
                    if not nuevos_partidos.isdigit():
                        print("Valor inválido. Debe ser un número entero ≥ victorias.")
                        continue
                    nuevos_partidos = int(nuevos_partidos)
                    if nuevos_partidos < nuevas_victorias:
                        print(f"Los partidos ({nuevos_partidos}) no pueden ser menores que las victorias ({nuevas_victorias}).")
                        continue
                    payload["partidos"] = nuevos_partidos
                    break
            payload["victorias"] = nuevas_victorias
            break

    elif op == "4":
        print("Cancelado.")
        return

    else:
        print("Opción no válida.")
        return

    print(f"\nEnviando actualización: {payload}")
    r = requests.patch(f"{BASE_URL}/teams/{tid}", json=payload)
    _print_resp(r)

def menu_borrar_equipo():
    print("\n--- Borrar equipo (DELETE /teams/{id}) ---")
    tid = _input_int("ID equipo: ")
    if tid is None:
        print("ID inválido.")
        return
    r = requests.delete(f"{BASE_URL}/teams/{tid}")
    print('Equipo eliminado correctamente')

def menu_jugadores_de_equipo():
    print("\n--- Jugadores de un equipo (GET /teams/{id}/players) ---")
    tid = _input_int("ID equipo: ")
    if tid is None:
        print("ID inválido.")
        return
    r = requests.get(f"{BASE_URL}/teams/{tid}/players")
    _print_resp(r)

def menu_crear_jugador():
    print("\n--- Crear jugador (POST /players) ---")

    nombre = input("Nombre: ").strip()
    if not nombre:
        print("Nombre vacío. Cancelado.")
        return

    dorsal = _input_int("Dorsal (1-99): ")
    posicion = input("Posición (portero/defensa/mediocampo/delantero): ").strip() or "mediocampo"
    goles = _input_int("Goles (int, vacío=0): ") or 0
    tarjetas_a = _input_int("Tarjetas amarillas (int, vacío=0): ") or 0
    tarjetas_r = _input_int("Tarjetas rojas (int, vacío=0): ") or 0

    print("\n¿A qué equipo pertenece este jugador?")
    r_teams = requests.get(f"{BASE_URL}/teams", timeout=10)
    if r_teams.status_code == 200:
        teams = r_teams.json()
        for t in teams:
            print(f"  {t['id']}: {t['nombre']} ({t.get('partidos', 0)} partidos, {t.get('victorias', 0)} victorias)")
    else:
        print("No se pudieron obtener equipos desde la API.")
        teams = []

    equipo_id = _input_int("ID del equipo (vacío = sin equipo): ")

    payload = {
        "nombre": nombre,
        "dorsal": dorsal or 0,
        "posicion": posicion,
        "goles": goles,
        "tarjetas_a": tarjetas_a,
        "tarjetas_r": tarjetas_r,
    }
    if equipo_id:
        payload["equipo_id"] = equipo_id

    r = requests.post(f"{BASE_URL}/players", json=payload, timeout=10)
    _print_resp(r)

    if r.status_code not in (200, 201):
        return

    pj = r.json()
    team_id = equipo_id

    if team_id:
        try:
            rt = requests.get(f"{BASE_URL}/teams/{team_id}", timeout=10)
            if rt.status_code == 200:
                team = rt.json()
                partidos_equipo = team.get("partidos", 0)
                print(f"El equipo '{team['nombre']}' tiene actualmente {partidos_equipo} partidos.")

                if partidos_equipo > 0:
                    resp = input(f"¿Quieres añadir estadísticas para {pj['nombre']} (s/n)? ").strip().lower()
                    if resp == "s":
                        stats_payload = _generar_stats_para_posicion(pj["posicion"])
                        rs = requests.put(f"{BASE_URL}/players/{pj['id']}/stats", json=stats_payload, timeout=10)
                        if rs.status_code in (200, 201):
                            print("Estadísticas añadidas correctamente:")
                            print(stats_payload)
                        else:
                            print(f"Error al subir stats ({rs.status_code}): {rs.text}")
                    else:
                        print(f"No se añadieron estadísticas para {pj['nombre']}")
                else:
                    print(f"El equipo aún no tiene partidos jugados. No se piden estadísticas.")
            else:
                print(f"No se pudo obtener información del equipo (status {rt.status_code}).")
        except Exception as e:
            print(f"Error al consultar partidos del equipo: {e}")
    else:
        print(f"{pj['nombre']} no tiene equipo asignado, no se piden estadísticas.")


def _generar_stats_para_posicion(pos: str) -> dict:

    if pos == "delantero":
        tiros = random.randint(10, 40)
        reg_int = random.randint(10, 35)
        pase_int = random.randint(100, 250)
        entr_int = random.randint(5, 25)
        paradas = 0
        asist = random.randint(0, 10)
    elif pos == "mediocampo":
        tiros = random.randint(5, 25)
        reg_int = random.randint(15, 40)
        pase_int = random.randint(200, 500)
        entr_int = random.randint(10, 40)
        paradas = 0
        asist = random.randint(2, 15)
    elif pos == "defensa":
        tiros = random.randint(0, 10)
        reg_int = random.randint(5, 20)
        pase_int = random.randint(150, 400)
        entr_int = random.randint(20, 60)
        paradas = 0
        asist = random.randint(0, 6)
    else:  # portero
        tiros = random.randint(0, 5)
        reg_int = random.randint(0, 5)
        pase_int = random.randint(100, 350)
        entr_int = random.randint(5, 20)
        paradas = random.randint(20, 120)
        asist = random.randint(0, 3)

    return {
        "tiros": tiros,
        "tiros_a_puerta": random.randint(int(tiros * 0.3), tiros) if tiros > 0 else 0,
        "asistencias": asist,
        "regates_intentados": reg_int,
        "regates_exitosos": random.randint(int(reg_int * 0.3), reg_int) if reg_int > 0 else 0,
        "pases_intentados": pase_int,
        "pases_completados": random.randint(int(pase_int * 0.7), pase_int) if pase_int > 0 else 0,
        "entradas_intentadas": entr_int,
        "entradas_exitosas": random.randint(int(entr_int * 0.4), entr_int) if entr_int > 0 else 0,
        "paradas": paradas
    }


def menu_ver_jugador():
    print("\n--- Ver jugador (GET /players/{id}) ---")
    pid = _input_int("ID jugador: ")
    if pid is None:
        print("ID inválido.")
        return
    r = requests.get(f"{BASE_URL}/playersDetail/{pid}")
    _print_resp(r)

def menu_ver_todos_jugadores():
    print("\n--- Ver todos los jugadores (GET /players) ---")
    r = requests.get(f"{BASE_URL}/players")
    _print_resp(r)

def menu_actualizar_jugador():
    print("\n--- Actualizar jugador (PATCH /players/{id}) ---")
    pid = _input_int("ID jugador: ")
    if pid is None:
        print("ID inválido.")
        return

    print("Deja vacío para no cambiar ese campo.")
    nombre = input("Nombre: ").strip()
    dorsal = input("Dorsal: ").strip()
    posicion = input("Posición (portero/defensa/mediocampo/delantero): ").strip()
    goles = input("Goles: ").strip()
    tarjetas_a = input("Tarjetas amarillas: ").strip()
    tarjetas_r = input("Tarjetas rojas: ").strip()

    payload = {}
    if nombre: payload["nombre"] = nombre
    if dorsal.isdigit(): payload["dorsal"] = int(dorsal)
    if posicion: payload["posicion"] = posicion
    if goles.isdigit(): payload["goles"] = int(goles)
    if tarjetas_a.isdigit(): payload["tarjetas_a"] = int(tarjetas_a)
    if tarjetas_r.isdigit(): payload["tarjetas_r"] = int(tarjetas_r)

    if not payload:
        print("Sin cambios, cancelado.")
        return

    r = requests.patch(f"{BASE_URL}/players/{pid}", json=payload)
    _print_resp(r)

    if r.status_code not in (200, 201):
        return

    resp = input("¿Quieres actualizar también las estadísticas del jugador? (s/n): ").strip().lower()
    if resp != "s":
        print("No se modifican estadísticas.")
        return

    print("\n--- Actualizar estadísticas --- (vacío = sin cambios)")
    tiros = input("Tiros: ").strip()
    tiros_a_puerta = input("Tiros a puerta: ").strip()
    asistencias = input("Asistencias: ").strip()
    regates_intentados = input("Regates intentados: ").strip()
    regates_exitosos = input("Regates exitosos: ").strip()
    pases_intentados = input("Pases intentados: ").strip()
    pases_completados = input("Pases completados: ").strip()
    entradas_intentadas = input("Entradas intentadas: ").strip()
    entradas_exitosas = input("Entradas exitosas: ").strip()
    paradas = input("Paradas: ").strip()

    stats_payload = {}
    if tiros.isdigit(): stats_payload["tiros"] = int(tiros)
    if tiros_a_puerta.isdigit(): stats_payload["tiros_a_puerta"] = int(tiros_a_puerta)
    if asistencias.isdigit(): stats_payload["asistencias"] = int(asistencias)
    if regates_intentados.isdigit(): stats_payload["regates_intentados"] = int(regates_intentados)
    if regates_exitosos.isdigit(): stats_payload["regates_exitosos"] = int(regates_exitosos)
    if pases_intentados.isdigit(): stats_payload["pases_intentados"] = int(pases_intentados)
    if pases_completados.isdigit(): stats_payload["pases_completados"] = int(pases_completados)
    if entradas_intentadas.isdigit(): stats_payload["entradas_intentadas"] = int(entradas_intentadas)
    if entradas_exitosas.isdigit(): stats_payload["entradas_exitosas"] = int(entradas_exitosas)
    if paradas.isdigit(): stats_payload["paradas"] = int(paradas)

    if not stats_payload:
        print("Sin cambios en estadísticas, cancelado.")
        return

    rs = requests.put(f"{BASE_URL}/players/{pid}/stats", json=stats_payload)
    _print_resp(rs)


def menu_borrar_jugador():
    print("\n--- Borrar jugador (DELETE /players/{id}) ---")
    pid = _input_int("ID jugador: ")
    if pid is None:
        print("ID inválido.")
        return
    r = requests.delete(f"{BASE_URL}/players/{pid}")
    print('Jugador eliminado correctamente')

def menu_asignar_jugador_a_equipo():
    print("\n--- Asignar jugador a equipo (PATCH /players/{pid}/team/{tid}) ---")
    pid = _input_int("ID jugador: ")
    tid = _input_int("ID equipo: ")
    if pid is None or tid is None:
        print("IDs inválidos.")
        return
    r = requests.patch(f"{BASE_URL}/players/{pid}/team/{tid}")
    _print_resp(r)

def menu_ver_equipo_de_jugador():
    print("\n--- Ver equipo de un jugador (GET /players/{pid}/team) ---")
    pid = _input_int("ID jugador: ")
    if pid is None:
        print("ID inválido.")
        return
    r = requests.get(f"{BASE_URL}/players/{pid}/team")
    _print_resp(r)
    
def ver_jugadores_sin_equipo():
    print("\n--- Ver jugadores sin equipo (GET /playersNoTeam) ---")
    r = requests.get(f"{BASE_URL}/playersNoTeam")
    _print_resp(r)
    
def menu_crear_partido():
    print("\n--- Crear partido (POST /games) ---")
    local_id = _input_int("ID equipo LOCAL: ")
    visitante_id = _input_int("ID equipo VISITANTE: ")
    if local_id is None or visitante_id is None:
        print("IDs inválidos.")
        return
    fecha_raw = input("Fecha (ISO, vacío=ahora) [ej: 2025-10-19T20:00:00]: ").strip()
    jornada_raw = input("Jornada (vacío = ninguna): ").strip()

    payload = {
        "local_id": local_id,
        "visitante_id": visitante_id,
    }
    if fecha_raw:
        payload["fecha"] = fecha_raw  
    if jornada_raw.isdigit():
        payload["jornada"] = int(jornada_raw)

    r = requests.post(f"{BASE_URL}/games", json=payload, timeout=10)
    _print_resp(r)

def menu_resultado_partido():
    print("\n--- Asignar resultado (PATCH /games/{id}/result) ---")
    gid = _input_int("ID partido: ")
    if gid is None:
        print("ID inválido.")
        return
    gl = _input_int("Goles LOCAL: ")
    gv = _input_int("Goles VISITANTE: ")
    if gl is None or gv is None:
        print("Goles inválidos.")
        return
    payload = {"goles_local": gl, "goles_visitante": gv}
    r = requests.patch(f"{BASE_URL}/games/{gid}/result", json=payload, timeout=10)
    _print_resp(r)

def menu_listar_partidos():
    print("\n--- Listar partidos (GET /games) ---")
    tid = input("Filtrar por ID equipo (vacío = todos): ").strip()
    params = {}
    if tid.isdigit():
        params["team_id"] = int(tid)
    r = requests.get(f"{BASE_URL}/games", params=params, timeout=10)
    _print_resp(r)

def main():
    team_ids = create_teams()
    player_ids = create_players()
    assign_players_to_teams(player_ids, team_ids)
    generate_random_games(team_ids, num_games=12, assign_results=True)

    while True:
        print("\n=== Menú Liga API ===")
        print("1)  Crear equipo")
        print("2)  Ver equipo por ID")
        print("3)  Ver todos los equipos")
        print("4)  Actualizar equipo")
        print("5)  Eliminar equipo")
        print("6)  Ver jugadores de un equipo")
        print("7)  Crear jugador")
        print("8)  Ver jugador por ID")
        print("9)  Ver todos los jugadores")
        print("10) Actualizar jugador")
        print("11) Eliminar jugador")
        print("12) Asignar jugador a equipo")
        print("13) Ver equipo de un jugador")
        print("14) Ver jugadores sin equipo")
        print("15) Crear partido")
        print("16) Listar partidos")
        print("17) Asignar resultado a partido")
        print("0) Salir")
        op = input("Opción: ").strip()

        if op == "1": menu_crear_equipo()
        elif op == "2": menu_ver_equipo()
        elif op == "3": menu_ver_todos_equipos()
        elif op == "4": menu_actualizar_equipo()
        elif op == "5": menu_borrar_equipo()
        elif op == "6": menu_jugadores_de_equipo()
        elif op == "7": menu_crear_jugador()
        elif op == "8": menu_ver_jugador()
        elif op == "9": menu_ver_todos_jugadores()
        elif op == "10": menu_actualizar_jugador()
        elif op == "11": menu_borrar_jugador()
        elif op == "12": menu_asignar_jugador_a_equipo()
        elif op == "13": menu_ver_equipo_de_jugador()
        elif op == "14": ver_jugadores_sin_equipo()
        elif op == "15": menu_crear_partido()
        elif op == "16": menu_listar_partidos()
        elif op == "17": menu_resultado_partido()
        elif op == "0":
            print("Saliendo...")
            break
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()
