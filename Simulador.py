from dataclasses import dataclass
from typing import List
import os
import logging
import sys
import tkinter as tk
from tkinter import filedialog

# ---------------- CONFIGURACIÓN DE LOGGING ----------------
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

if logger.hasHandlers():
    logger.handlers.clear()
# Handler para archivo
file_handler = logging.FileHandler("simulacion.log", mode="w")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

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

    # ----- Métricas temporales añadidas -----
    tiempo_inicio: int = None
    tiempo_fin: int = None

# ------------------- PARTICIONES -------------------
arreglo_particiones: List[Particion] = [
    Particion(id="Sistema Operativo", dir=0, espacio=100, id_proceso="SO", fragmentacion=0, ocupado=True),
    Particion(id="Trabajos Grandes", dir=100, espacio=250, id_proceso="", fragmentacion=0, ocupado=False),
    Particion(id="Trabajos Medianos", dir=351, espacio=150, id_proceso="", fragmentacion=0, ocupado=False),
    Particion(id="Trabajos Pequeños", dir=501, espacio=50, id_proceso="", fragmentacion=0, ocupado=False)
]

# ------------------- COLAS -------------------
ColaProcesos=[]
ColaListo=[]
ColaSuspendido=[]
ColaFinalizado=[]

# ------------------- RESET SIMULACION -------------------
def reset_sim():
    global gradoMultiProgr, ColaListo, ColaSuspendido, ColaFinalizado, ColaProcesos
    gradoMultiProgr = 0
    ColaListo.clear()
    ColaSuspendido.clear()
    ColaFinalizado.clear()
    ColaProcesos.clear()
    
    for part in arreglo_particiones:
        if part.id != "Sistema Operativo":
            part.id_proceso = ""
            part.fragmentacion = 0
            part.ocupado = False
        else:
            part.ocupado = True
            part.id_proceso = "SO"

    logging.info("--- SIMULACIÓN REINICIADA ---")

# ------------------- CARGA DE PROCESOS -------------------
def cargar_lista_procesos():
    reset_sim()
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    ruta = filedialog.askopenfilename(
        title="Seleccionar archivo de procesos",
        filetypes=(("Archivos de Texto/CSV", "*.txt *.csv"), ("Todos", "*.*"))
    )
    root.destroy()

    if not ruta:
        print("No se seleccionó ningún archivo.")
        input("Presione ENTER para volver al menú...")
        return

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read()
        
        if "*" not in contenido and "\n" in contenido:
            items = contenido.strip().split("\n")
        else:
            items = contenido.strip().split("*")

        for item in items:
            if not item.strip():
                continue
            elemento = item.split("-")
            if len(elemento) < 6:
                continue

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
        logging.info("Lista de procesos cargada: %s", [p.nombre for p in ColaProcesos])
        print(f"\n¡Archivo cargado exitosamente! Se encontraron {len(ColaProcesos)} procesos: {[p.nombre for p in ColaProcesos]}")
    except Exception as e:
        logging.error(f"Error cargando archivo: {e}")
        print(f"\nError al cargar el archivo: {e}")

    input("Presione ENTER para volver al menú...")

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
    # mover victima a suspendidos
    if victima in ColaListo:
        try:
            ColaListo.remove(victima)
        except ValueError:
            pass
    if victima not in ColaSuspendido:
        ColaSuspendido.append(victima)
    return True

# ------------------- LOCALIZACION -------------------
def estado_localizacion(proceso):

    if best_fit(proceso):
        return True

    if hay_reemplazo():
        reemplazado = ejecutar_reemplazo(proceso)
        if reemplazado and best_fit(proceso):
            return True

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

# ------------------- FUNCIÓN: calcular grado (sin dobles) -------------------
def calcular_grado_mp(proceso_actual=None):
    ids = set()
    for p in ColaListo:
        ids.add(id(p))
    for p in ColaSuspendido:
        ids.add(id(p))
    if proceso_actual is not None:
        ids.add(id(proceso_actual))
    return len(ids)

# ------------------- TABLA ACTUALIZADA -------------------
def mostrar_tabla(tiempo, mensaje_evento, proceso_actual=None):
    global gradoMultiProgr
    gradoMultiProgr = calcular_grado_mp(proceso_actual)

    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"TIEMPO: {tiempo} | MULTIPROGRAMACIÓN: {gradoMultiProgr}/{LIMITE_MULTIPROG}")
    print("=" * 80)
    print(f"{'PARTICIÓN':<20} | {'ESTADO':<10} | {'PROCESO':<10} | {'FRAG':<8} | {'ESPACIO':<8}")
    print("-" * 80)
    
    for part in arreglo_particiones:
        estado_str = "OCUPADO" if part.ocupado else "LIBRE"
        proc_str = part.id_proceso if part.id_proceso else "---"
        
        color = "\033[91m" if part.ocupado else "\033[92m"
        reset = "\033[0m"
        
        print(f"{part.id:<20} | {color}{estado_str:<10}{reset} | {proc_str:<10} | {part.fragmentacion:<8} | {part.espacio:<8}")

    print("\n" + "=" * 80)
    print(" COLA DE LISTOS / EJECUCIÓN / SUSPENDIDOS")
    print("-" * 80)
    print(f"{'PROCESO':<10} | {'ESTADO':<12} | {'PROGRESO':<15} | {'PARTICIÓN':<20}")
    print("-" * 80)

    todos = ColaListo + ColaSuspendido
    todos_ordenados = sorted(todos, key=lambda p: p.irrupcion - p.t_memoria)

    if not todos_ordenados:
        print(" (Sin procesos en memoria ni suspendidos)")

    for p in todos_ordenados:
        MAX_BARRA = 20
        progreso_real = p.t_memoria / p.irrupcion if p.irrupcion > 0 else 0
        len_progreso = int(progreso_real * MAX_BARRA)
        barra = "#" * len_progreso + "-" * (MAX_BARRA - len_progreso)

        if p.estado == ESTADO_EJECUCION:
            color = "\033[93m"
            estado_txt = "EJECUTANDO"
        elif p.estado == ESTADO_SUSPENDIDO:
            color = "\033[91m"
            estado_txt = "SUSPENDIDO"
        else:
            color = "\033[96m"
            estado_txt = "LISTO"

        reset = "\033[0m"

        particion = p.particion_asignada if p.particion_asignada is not None else "---"

        print(
            f"{p.nombre:<10} | {color}{estado_txt:<12}{reset} | "
            f"{p.t_memoria}/{p.irrupcion} [{barra:<20}] | {particion:<20}"
        )

    print("\n" + "=" * 80)
    print(f" EVENTO: {mensaje_evento}")
    print("=" * 80)

# ------------------- BUCLE PRINCIPAL -------------------
def main_loop():
    global gradoMultiProgr
    tiempo_actual = 0
    mensaje= "Inicio de Simulación"

    if not ColaProcesos and not ColaSuspendido and not ColaListo:
        print("Cargue un archivo primero.")
        return

    while ColaProcesos or ColaSuspendido or ColaListo:

        eventos=[]

        # ------------------------------------------------------
        # 🔥 TIEMPO 0 → NO hacer nada (solo mostrar particiones)
        # ------------------------------------------------------
        if tiempo_actual == 0:
            mostrar_tabla(0, "Tiempo 0: Sin procesos aún")
            input("Presione ENTER para comenzar en tiempo 1...")
            tiempo_actual += 1
            continue

        # ------------------ LLEGADA NORMAL ---------------------
        for p in list(ColaProcesos):
            if p.arribo <= tiempo_actual:
                grado_prev = calcular_grado_mp()
                if grado_prev < LIMITE_MULTIPROG:
                    try:
                        ColaProcesos.remove(p)
                    except:
                        pass
                    ubicado = estado_localizacion(p)
                    if ubicado:
                        if p not in ColaListo:
                            ColaListo.append(p)
                        eventos.append(f"Llega {p.nombre} -> Asignado")
                    else:
                        eventos.append(f"Llega {p.nombre} -> Suspendido")
                else:
                    eventos.append(f"Llega {p.nombre} -> Espera (MP llena)")

        # ---------------- RECUPERAR SUSPENDIDOS ----------------
        for p in list(ColaSuspendido):
            if calcular_grado_mp() >= LIMITE_MULTIPROG:
                break
            ubicado = estado_localizacion(p)
            if ubicado:
                try:
                    ColaSuspendido.remove(p)
                except:
                    pass
                if p not in ColaListo:
                    ColaListo.append(p)
                eventos.append(f"Recuperado {p.nombre}")

        gradoMultiProgr = calcular_grado_mp()

        # ------------------------- EJECUCIÓN --------------------
        anterior = None
        for q in ColaListo:
            if q.estado == ESTADO_EJECUCION:
                anterior = q
            q.estado = ESTADO_LISTO

        proceso_actual = obtener_proceso_srtf()

        if anterior and anterior != proceso_actual:
            anterior.estado = ESTADO_LISTO

        if proceso_actual:
            if proceso_actual.tiempo_inicio is None:
                proceso_actual.tiempo_inicio = tiempo_actual
            proceso_actual.estado = ESTADO_EJECUCION
            proceso_actual.t_memoria += 1
            logging.info("Ejecutando %s (%d/%d)", proceso_actual.nombre, proceso_actual.t_memoria, proceso_actual.irrupcion)

        if eventos:
            mensaje = " | ".join(eventos)
        elif proceso_actual:
            mensaje = f"Ejecutando {proceso_actual.nombre}"
        else:
            mensaje = "Esperando procesos..."

        mostrar_tabla(tiempo_actual, mensaje, proceso_actual)

        # --------------------- FINALIZACIÓN ---------------------
        if proceso_actual:
            if proceso_actual.t_memoria >= proceso_actual.irrupcion:
                try:
                    ColaListo.remove(proceso_actual)
                except:
                    pass
                ColaFinalizado.append(proceso_actual)
                liberar_particion(proceso_actual)
                proceso_actual.tiempo_fin = tiempo_actual
                proceso_actual.estado = ESTADO_FINALIZADO

                logging.info("Finalizado %s", proceso_actual.nombre)

                for p in list(ColaSuspendido):
                    if calcular_grado_mp() >= LIMITE_MULTIPROG:
                        break
                    ubicado = estado_localizacion(p)
                    if ubicado:
                        try:
                            ColaSuspendido.remove(p)
                        except:
                            pass
                        ColaListo.append(p)
                        eventos.append(f"Recuperado {p.nombre}")

                gradoMultiProgr = calcular_grado_mp()

                input(f"FIN DE PROCESO {proceso_actual.nombre} (ENTER)")
            else:
                input("ENTER para siguiente ciclo...")
        else:
            input("ENTER para siguiente ciclo...")

        tiempo_actual += 1

    # ---------------- FIN SIMULACIÓN ------------------------
    mostrar_tabla(tiempo_actual, "SIMULACIÓN COMPLETADA")
    print(f"\nFinalizados: {[p.nombre for p in ColaFinalizado]}")

    if ColaFinalizado:
        n = len(ColaFinalizado)
        total_ret = 0
        total_esp = 0

        print("\n--- Métricas por proceso ---")
        for p in ColaFinalizado:
            if p.tiempo_fin is None:
                p.tiempo_fin = tiempo_actual
            ret = p.tiempo_fin - p.arribo
            esp = ret - p.irrupcion
            total_ret += ret
            total_esp += esp
            print(f"{p.nombre}: arribo={p.arribo}, inicio={p.tiempo_inicio}, fin={p.tiempo_fin}, retorno={ret}, espera={esp}")

        print("\n--- Métricas globales ---")
        print(f"Promedio retorno: {total_ret/n:.2f}")
        print(f"Promedio espera:  {total_esp/n:.2f}")
        print(f"Procesos terminados: {n}")
        print(f"Procesos/tiempo: {n/tiempo_actual:.4f}")

    input("ENTER para volver al menú...")

# ------------------- MENÚ -------------------
def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n--- MENÚ SIMULADOR S.O. ---")
        print("1. Cargar Archivo")
        print("2. Iniciar Simulación")
        print("3. Salir")
        
        opcion = input(">> ")
        
        if opcion == "1":
            cargar_lista_procesos()
        elif opcion == "2":
            main_loop()
        elif opcion == "3":
            break

if __name__ == "__main__":
    main()
