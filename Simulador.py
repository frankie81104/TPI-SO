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
    t_memoria: int = 0
    estado: str = ESTADO_NUEVO
    particion_asignada: str = None

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


# ------------------- LOCALIZACION -------------------
def estado_localizacion(proceso):
    if best_fit(proceso):
        return True
    return False


# ------------------- SRTF -------------------
def obtener_proceso_srtf():
    if not ColaListo:
        return None
    return min(ColaListo, key=lambda p: p.irrupcion - p.t_memoria)


# ------------------- TABLA ACTUALIZADA -------------------
def mostrar_tabla(tiempo, mensaje_evento):
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
    
    # ---------------- COLAS ----------------
    print("COLAS ACTUALES:")
    print("-" * 80)
    print(f"Listo      : {[p.nombre for p in ColaListo]}")
    print(f"Suspendido : {[p.nombre for p in ColaSuspendido]}")
    print(f"Finalizado : {[p.nombre for p in ColaFinalizado]}")
    print("-" * 80)

    # ---------------- LISTA DE PROCESOS EN MEMORIA ----------------
    print("PROCESOS EN MEMORIA (Listos + Ejecutando + Suspendidos):")
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


# ------------------- BUCLE PRINCIPAL CORREGIDO CON ESTADÍSTICAS -------------------
def main_loop():
    global gradoMultiProgr
    tiempo_actual = 0
    mensaje = "Inicio de Simulación"

    if not ColaProcesos and not ColaSuspendido and not ColaListo:
        print("Cargue un archivo primero.")
        return

    for p in ColaProcesos:
        p.tiempo_inicio = None
        p.tiempo_fin = None

    while ColaProcesos or ColaSuspendido or ColaListo:
        eventos = []

        # ---------------- ACTUALIZAR GRADO DE MULTIPROGRAMACION ----------------
        gradoMultiProgr = len([p for p in ColaListo + ColaSuspendido if p.particion_asignada != "SO"])

        # ---------------- REINTENTO DE PROCESOS SUSPENDIDOS ----------------
        for p in list(ColaSuspendido):
            if gradoMultiProgr < LIMITE_MULTIPROG:
                if estado_localizacion(p):
                    ColaSuspendido.remove(p)
                    p.estado = ESTADO_LISTO
                    ColaListo.append(p)
                    eventos.append(f"Recuperado {p.nombre}")
                    gradoMultiProgr += 1
                    if p.tiempo_inicio is None:
                        p.tiempo_inicio = tiempo_actual
                    break

        # ---------------- LLEGADA DE NUEVOS PROCESOS ----------------
        for p in list(ColaProcesos):
            if p.arribo <= tiempo_actual:
                if gradoMultiProgr < LIMITE_MULTIPROG:
                    if estado_localizacion(p):
                        ColaListo.append(p)
                        p.estado = ESTADO_LISTO
                        eventos.append(f"Llega {p.nombre} -> Asignado a memoria")
                        if p.tiempo_inicio is None:
                            p.tiempo_inicio = tiempo_actual
                    else:
                        p.estado = ESTADO_SUSPENDIDO
                        ColaSuspendido.append(p)
                        eventos.append(f"Llega {p.nombre} -> Suspendido por memoria")
                    gradoMultiProgr += 1
                    ColaProcesos.remove(p)
                    break
                else:
                    eventos.append(f"Llega {p.nombre} -> Esperando (límite MP)")

        # ---------------- SELECCIÓN SRTF ----------------
        proceso_actual = obtener_proceso_srtf()
        
        for p in ColaListo:
            p.estado = ESTADO_LISTO

        if proceso_actual:
            proceso_actual.estado = ESTADO_EJECUCION

        # ---------------- MENSAJE DE EVENTO ----------------
        if eventos:
            mensaje = " | ".join(eventos)
        elif proceso_actual:
            mensaje = f"Ejecutando {proceso_actual.nombre}"
        else:
            mensaje = "Esperando procesos..."

        # ---------------- MOSTRAR TABLA (PRIMERO MOSTRAMOS) ----------------
        mostrar_tabla(tiempo_actual, mensaje)

        # ---------------- EJECUCIÓN REAL (DESPUÉS SUMAMOS) ----------------
        if proceso_actual:
            proceso_actual.t_memoria += 1 
            
            logging.info("Ejecutando %s (%d/%d) en %s",
                        proceso_actual.nombre, proceso_actual.t_memoria,
                        proceso_actual.irrupcion, proceso_actual.particion_asignada)

            if proceso_actual.t_memoria >= proceso_actual.irrupcion:
                ColaListo.remove(proceso_actual)
                ColaFinalizado.append(proceso_actual)
                liberar_particion(proceso_actual)
                proceso_actual.estado = ESTADO_FINALIZADO
                proceso_actual.tiempo_fin = tiempo_actual + 1
                logging.info("Finalizado %s", proceso_actual.nombre)
                gradoMultiProgr -= 1

                input(f"FIN DE PROCESO {proceso_actual.nombre} (Presione ENTER)")
            else:
                input("Presione ENTER para siguiente ciclo...")
        else:
            input("CPU Ociosa - Presione ENTER...")

        tiempo_actual += 1
    
    # ------------------- INFORME ESTADÍSTICO -------------------
    if ColaFinalizado:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("\n--- INFORME ESTADÍSTICO ---")
        total_retorno = 0
        total_espera = 0
        print(f"{'PROCESO':<10} | {'ARRIBO':<6} | {'IRRUPCION':<10} | {'RETORNO':<7} | {'ESPERA':<6}")
        print("-"*60)
        for p in ColaFinalizado:
            tiempo_retorno = p.tiempo_fin - p.arribo
            tiempo_espera = tiempo_retorno - p.irrupcion
            total_retorno += tiempo_retorno
            total_espera += tiempo_espera
            print(f"{p.nombre:<10} | {p.arribo:<6} | {p.irrupcion:<10} | {tiempo_retorno:<7} | {tiempo_espera:<6}")

        promedio_retorno = total_retorno / len(ColaFinalizado)
        promedio_espera = total_espera / len(ColaFinalizado)
        tiempo_total = tiempo_actual
        rendimiento = len(ColaFinalizado) / tiempo_total if tiempo_total > 0 else 0

        print("\nTiempos promedios:")
        print(f"Tiempo medio de retorno : {promedio_retorno:.2f}")
        print(f"Tiempo medio de espera  : {promedio_espera:.2f}")
        print(f"Rendimiento del sistema : {rendimiento:.2f} trabajos por unidad de tiempo")
    else:
        print("No se ejecutaron procesos.")
    
    input("\nPresione ENTER para volver al menú...")

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
        
        procesos_validos = []
        procesos_rechazados = []
        max_tam = 250

        for item in items:
            if not item.strip():
                continue
            elemento = item.split("-")
            if len(elemento) < 5:
                continue

            tamano = int(elemento[2])
            if tamano > max_tam:
                procesos_rechazados.append(elemento[1])
                print(f"Proceso {elemento[1]} rechazado: tamaño {tamano} excede el maximo({max_tam})")
                continue

            ColaProcesos.append(
                Proceso(
                    id_proceso=int(elemento[0]),
                    nombre=elemento[1],
                    tamano=int(elemento[2]),
                    arribo=int(elemento[3]),
                    irrupcion=int(elemento[4])
                )
            )
        logging.info("Lista de procesos cargada: %s", [p.nombre for p in ColaProcesos])
        print(f"\n¡Archivo cargado exitosamente! Se encontraron {len(ColaProcesos)} procesos: {[p.nombre for p in ColaProcesos]}")
    except Exception as e:
        logging.error(f"Error cargando archivo: {e}")
        print(f"\nError al cargar el archivo: {e}")

    input("Presione ENTER para volver al menú...")

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
