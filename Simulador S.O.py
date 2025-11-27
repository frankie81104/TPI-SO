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

# Handler para consola--bloqueado por ahora xd
#console_handler = logging.StreamHandler(sys.stdout)
#console_handler.setLevel(logging.DEBUG)
#console_handler.setFormatter(file_formatter)
#logger.addHandler(console_handler)

#DEBUG = True

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

def reset_sim():
    """Reinicia variables manteniendo nombres originales."""
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

#------------------- TABLA VISTA -------------------
def mostrar_tabla(tiempo, mensaje_evento):
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"TIEMPO: {tiempo} | MULTIPROGRAMACIÓN: {gradoMultiProgr}/{LIMITE_MULTIPROG}")
    print("=" * 80)
    print(f"{'PARTICIÓN':<20} | {'ESTADO':<10} | {'PROCESO':<10} | {'FRAG':<8} | {'ESPACIO':<8}")
    print("-" * 80)
    
    for part in arreglo_particiones:
        estado_str = "OCUPADO" if part.ocupado else "LIBRE"
        proc_str = part.id_proceso if part.id_proceso else "---"
        
        color = "\033[91m" if part.ocupado else "\033[92m" # Rojo/Verde
        reset = "\033[0m"
        
        print(f"{part.id:<20} | {color}{estado_str:<10}{reset} | {proc_str:<10} | {part.fragmentacion:<8} | {part.espacio:<8}")

    print("\n" + "=" * 80)
    print(" COLA DE LISTOS / EJECUCIÓN (SRTF)")
    print("-" * 80)
    print(f"{'PROCESO':<10} | {'ESTADO':<12} | {'PROGRESO':<15} | {'PARTICIÓN':<20}")
    print("-" * 80)
    
    listos_ordenados = sorted(ColaListo, key=lambda p: p.irrupcion - p.t_memoria)
    
    if not listos_ordenados:
        print(" (Sin procesos en memoria)")
    
    for p in listos_ordenados:
        barra = "#" * p.t_memoria + "-" * (p.irrupcion - p.t_memoria)
        
        estado_txt = "EJECUTANDO" if p.estado == ESTADO_EJECUCION else "LISTO"
        color_proc = "\033[93m" if p.estado == ESTADO_EJECUCION else "\033[96m" # Amarillo/Cyan
        reset = "\033[0m"
        
        print(f"{p.nombre:<10} | {color_proc}{estado_txt:<12}{reset} | {p.t_memoria}/{p.irrupcion} [{barra:<10}] | {p.particion_asignada:<20}")

    print("\n" + "=" * 80)
    print(f" EVENTO: {mensaje_evento}")
    print("=" * 80)

# ------------------- BUCLE PRINCIPAL -------------------
def main_loop():
    global gradoMultiProgr
    tiempo_actual = 0
    mensaje= "Inicio de Simulacion"
    if not ColaProcesos and not ColaSuspendido and not ColaListo:
        print("Cargue un archivo primero.")
        return

    while ColaProcesos or ColaSuspendido or ColaListo:
        eventos=[]

        # Llegada de procesos
        for p in list(ColaProcesos):
            if p.arribo <= tiempo_actual:
                ColaProcesos.remove(p)
                #logging.info("Llegada de proceso %s", p.nombre)
                if gradoMultiProgr < LIMITE_MULTIPROG:
                    #asignado = estado_localizacion(p)
                    #if asignado:
                    if estado_localizacion(p):
                        ColaListo.append(p)
                        gradoMultiProgr += 1
                        eventos.append(f"Llega {p.nombre} -> Asignado")
                else:
                    p.estado = ESTADO_SUSPENDIDO
                    if p not in ColaSuspendido:
                        ColaSuspendido.append(p)
                    #logging.info("Suspendido %s por límite de multiprogramación", p.nombre)
                    eventos.append(f"Llega {p.nombre} -> Suspendido (Límite MP)")                    

        # Reintento de suspendidos
        for p in list(ColaSuspendido):
            if gradoMultiProgr < LIMITE_MULTIPROG and estado_localizacion(p):
                ColaSuspendido.remove(p)
                ColaListo.append(p)
                p.estado = ESTADO_LISTO
                gradoMultiProgr += 1
                #logging.info("Reasignado desde suspendido: %s", p.nombre)
                eventos.append(f"Recuperado {p.nombre}")

        # Ejecución - SRTF
        proceso_actual = obtener_proceso_srtf()
        for p in ColaListo:
            p.estado =  ESTADO_LISTO
            
        if proceso_actual:
            proceso_actual.estado = ESTADO_EJECUCION
            proceso_actual.t_memoria += 1
            logging.info("Ejecutando %s (%d/%d) en %s", proceso_actual.nombre, proceso_actual.t_memoria, proceso_actual.irrupcion, proceso_actual.particion_asignada)
        else:
            logging.debug("No hay procesos listos")
        # Actualizar UI
        if eventos:
            mensaje = " | ".join(eventos)
        elif proceso_actual:
            mensaje = f"Ejecutando {proceso_actual.nombre}"
        else:
            mensaje = "Esperando procesos..."
            
        mostrar_tabla(tiempo_actual, mensaje)

        # 4. Finalización
        if proceso_actual:
            if proceso_actual.t_memoria >= proceso_actual.irrupcion:
                ColaListo.remove(proceso_actual)
                ColaFinalizado.append(proceso_actual)
                liberar_particion(proceso_actual)
                gradoMultiProgr -= 1
                proceso_actual.estado = ESTADO_FINALIZADO
                logging.info("Finalizado %s", proceso_actual.nombre)
                input(f"FIN DE PROCESO {proceso_actual.nombre} (Presione ENTER)")
            else:
                input("Presione ENTER para siguiente ciclo...")
        else:
            input("Presione ENTER para siguiente ciclo...")

        tiempo_actual += 1

    mostrar_tabla(tiempo_actual, "SIMULACIÓN COMPLETADA")
    print(f"\nFinalizados: {[p.nombre for p in ColaFinalizado]}")
    input("Presione ENTER para volver al menú...")

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