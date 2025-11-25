from dataclasses import dataclass
from typing import List
import os
import logging
import sys

# ---------------- CONFIGURACIÓN DE LOGGING ----------------
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Handler para archivo
file_handler = logging.FileHandler("simulacion.log", mode="w")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Handler para consola
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(file_formatter)
logger.addHandler(console_handler)

DEBUG = True

# Estados
ESTADO_NUEVO = "nuevo"
ESTADO_LOCALIZACION = "localizacion"
ESTADO_LISTO = "listo"
ESTADO_EJECUCION = "ejecutando"
ESTADO_SUSPENDIDO = "suspendido"
ESTADO_FINALIZADO = "finalizado"

gradoMultiProgr = 0
LIMITE_MULTIPROG = 5

# ------------------- CLASE PARTICION -------------------
@dataclass
class Particion:
    id: str
    dir: int
    espacio: int
    id_proceso: str
    fragmentacion: int
    ocupado: bool

# ------------------- CLASE PROCESO -------------------
@dataclass
class Proceso:
    id_proceso: int
    nombre: str
    tamano: int
    arribo: int
    irrupcion: int
    t_memoria: int
    estado: str = ESTADO_NUEVO
    particion_asignada: str = None

# ------------------- PARTICIONES -------------------
arreglo_particiones: List[Particion] = [
    Particion(id="Sistema Operativo", dir=0, espacio=100, id_proceso="", fragmentacion=0, ocupado=True),
    Particion(id="Trabajos Grandes", dir=100, espacio=250, id_proceso="", fragmentacion=0, ocupado=False),
    Particion(id="Trabajos Medianos", dir=351, espacio=150, id_proceso="", fragmentacion=0, ocupado=False),
    Particion(id="Trabajos Pequeños", dir=501, espacio=50, id_proceso="", fragmentacion=0, ocupado=False)
]

# ------------------- COLAS -------------------
ColaProcesos=[]
ColaListo=[]
ColaSuspendido=[]
ColaFinalizado=[]

# ------------------- CARGA DE PROCESOS -------------------
def cargar_lista_procesos():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "procesos.csv")
    with open(ruta, "r", encoding="utf-8") as f:
        procesos = f.read()

    procesos = procesos.strip().split("*")

    for p in procesos:
        if not p.strip():
            continue
        elemento = p.split("-")
        ColaProcesos.append(
            Proceso(
                id_proceso=int(elemento[0]),
                nombre=elemento[1],
                tamano=int(elemento[2]),
                arribo=int(elemento[3]),
                irrupcion=int(elemento[4]),
                t_memoria=int(elemento[5])
            )
        )

cargar_lista_procesos()
logging.info("Lista de procesos cargada: %s", [p.nombre for p in ColaProcesos])

# ------------------- BEST FIT -------------------
def best_fit(proceso):
    best_part = None
    min_frag = float('inf')
    for part in arreglo_particiones:
        if not part.ocupado and part.espacio >= proceso.tamano:
            fractual = part.espacio - proceso.tamano
            if fractual < min_frag:
                min_frag = fractual
                best_part = part

    if best_part:
        best_part.ocupado = True
        best_part.id_proceso = proceso.nombre
        best_part.fragmentacion = min_frag
        proceso.particion_asignada = best_part.id
        proceso.estado = ESTADO_LISTO
        logging.info("Proceso %s asignado a %s (fragmentación %d)", proceso.nombre, best_part.id, min_frag)
        return True
    logging.debug("No se encontró partición para %s", proceso.nombre)
    return False

# ------------------- LIBERAR PARTICION -------------------
def liberar_particion(proceso):
    for part in arreglo_particiones:
        if part.id == proceso.particion_asignada:
            part.ocupado = False
            part.id_proceso = ""
            part.fragmentacion = 0
            logging.info("Partición %s liberada por %s", part.id, proceso.nombre)

# ------------------- REEMPLAZO -------------------
def hay_reemplazo():
    return any(part.ocupado and part.id != "Sistema Operativo" for part in arreglo_particiones)

def ejecutar_reemplazo(nuevo_proceso):
    candidatos = [p for p in ColaListo if p.particion_asignada != "Sistema Operativo"]
    if not candidatos:
        return False

    victima = min(candidatos, key=lambda p: p.arribo)
    logging.info("Reemplazo: expulsando %s para alojar %s", victima.nombre, nuevo_proceso.nombre)

    liberar_particion(victima)
    victima.estado = ESTADO_SUSPENDIDO
    ColaListo.remove(victima)
    ColaSuspendido.append(victima)
    return True

# ------------------- LOCALIZACION CORREGIDA -------------------
def estado_localizacion(proceso):
    proceso.estado = ESTADO_LOCALIZACION

    # Intentar best fit primero
    if best_fit(proceso):
        return True

    # Si no hay partición libre suficientemente grande, intentar reemplazo
    if hay_reemplazo():
        reemplazado = ejecutar_reemplazo(proceso)
        if reemplazado:
            if best_fit(proceso):
                return True

    # Si sigue sin poder asignarse, suspender
    proceso.estado = ESTADO_SUSPENDIDO
    if proceso not in ColaSuspendido:
        ColaSuspendido.append(proceso)
    logging.info("Proceso %s suspendido", proceso.nombre)
    return False

# ------------------- SRTF -------------------
def obtener_proceso_srtf():
    if not ColaListo:
        return None
    return min(ColaListo, key=lambda p: p.irrupcion - p.t_memoria)

# ------------------- BUCLE PRINCIPAL -------------------
tiempo_actual = 0

while ColaProcesos or ColaSuspendido or ColaListo:
    logging.info("Tiempo actual: %d", tiempo_actual)

    # Llegada de procesos
    for p in list(ColaProcesos):
        if p.arribo <= tiempo_actual:
            ColaProcesos.remove(p)
            logging.info("Llegada de proceso %s", p.nombre)
            if gradoMultiProgr < LIMITE_MULTIPROG:
                asignado = estado_localizacion(p)
                if asignado:
                    ColaListo.append(p)
                    gradoMultiProgr += 1
            else:
                p.estado = ESTADO_SUSPENDIDO
                if p not in ColaSuspendido:
                    ColaSuspendido.append(p)
                logging.info("Suspendido %s por límite de multiprogramación", p.nombre)

    # Reintento de suspendidos
    for p in list(ColaSuspendido):
        if gradoMultiProgr < LIMITE_MULTIPROG and estado_localizacion(p):
            ColaSuspendido.remove(p)
            ColaListo.append(p)
            p.estado = ESTADO_LISTO
            gradoMultiProgr += 1
            logging.info("Reasignado desde suspendido: %s", p.nombre)

    # Ejecución - SRTF
    proceso_actual = obtener_proceso_srtf()

    if proceso_actual:
        proceso_actual.estado = ESTADO_EJECUCION
        proceso_actual.t_memoria += 1
        logging.info("Ejecutando %s (%d/%d) en %s", proceso_actual.nombre,
                     proceso_actual.t_memoria, proceso_actual.irrupcion,
                     proceso_actual.particion_asignada)
    else:
        logging.debug("No hay procesos listos")

    # Mostrar estado de particiones
    for part in arreglo_particiones:
        logging.debug("Partición %s: %s, Proc: %s, Frag: %d", part.id,
                      "Ocupada" if part.ocupado else "Libre",
                      part.id_proceso if part.id_proceso else "-",
                      part.fragmentacion)

    # Finalización de proceso actual
    if proceso_actual:
        if proceso_actual.t_memoria >= proceso_actual.irrupcion:
            ColaListo.remove(proceso_actual)
            ColaFinalizado.append(proceso_actual)
            liberar_particion(proceso_actual)
            gradoMultiProgr -= 1
            proceso_actual.estado = ESTADO_FINALIZADO
            logging.info("Proceso %s finalizado", proceso_actual.nombre)

    # Avanza el tiempo y espera interacción del usuario
    tiempo_actual += 1
    input("Presione ENTER para continuar...")

# Resultados finales
logging.info("=== Estado final de la simulación ===")
logging.info("Tiempo total: %d", tiempo_actual)
logging.info("Procesos finalizados: %s", [p.nombre for p in ColaFinalizado])
for p in arreglo_particiones:
    logging.info("Partición %s: %s, Proc: %s, Frag: %d",
                 p.id, "Ocupada" if p.ocupado else "Libre",
                 p.id_proceso if p.id_proceso else "-",
                 p.fragmentacion)
