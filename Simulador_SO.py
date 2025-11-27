from dataclasses import dataclass, field
from typing import List
import os

DEBUG = True
#Definición de una clase partición

gradoMultiProgr = 0
LIMITE_MULTIPROG = 5

@dataclass
class Particion:
    id: str
    dir: int
    espacio: int
    id_proceso: str
    fragmentacion: int = 0
    ocupado: bool = False

#Definición de una clase proceso

@dataclass
class Proceso:
    id_proceso: int
    nombre: str
    tamano: int
    arribo: int
    irrupcion: int
    t_memoria: int = 0  #el archivo csv no debe tener tiempo en memoria, eso va aumentando o disminuyendo segun como lo tratemos xd.
    estado: str = "nuevo"
    particion_asignada: str = None

#Definición del arreglo de particiones
#Cuando llegue un proceso en fragmentacion=espacio-tamaño del proceso

arreglo_particiones: List[Particion] = [
    Particion(id="Sistema Operativo", dir=0, espacio=100, id_proceso="Sistema Operativo", ocupado=True), 
    Particion(id="Trabajos Grandes", dir=100, espacio=250, id_proceso="", ocupado=False),
    Particion(id="Trabajos Medianos", dir=351, espacio=150, id_proceso="", ocupado=False),
    Particion(id="Trabajos Pequeños", dir=501, espacio=50, id_proceso="", ocupado=False)
]

#La idea es que los procesos ingresen por default a la cola de procesos,
#cuando se cumpla su arribo pasen a la cola de listo y se evaluen en base al metodo BestFit o el Algoritmo SRTF, 
#se considera finalizado si t_memoria == irrupcion.

ColaProcesos=[]
ColaListo=[]
ColaSuspendido=[]
ColaFinalizado=[]

Procesos = 0


#Función encargada de cargar el contenido del archivo en la variable procesos
def cargar_lista_procesos():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "procesos.csv")
    with open(ruta, "r", encoding="utf-8") as f:
        procesos = f.read()
    if DEBUG:
        print("Contenido del archivo:\n", procesos)

    procesos = procesos.strip().split("*")  # Separar por *
    if DEBUG:
        print("Lista separada por *:", procesos)

    for p in procesos:
        if not p.strip():
            continue
        elemento = p.split("-")
        if DEBUG:
            print("Elemento separado por '-':", elemento)
        # Crear instancia de Proceso con conversión de tipos
        ColaProcesos.append(
            Proceso(
                id_proceso=int(elemento[0]),
                nombre=elemento[1],
                tamano=int(elemento[2]),
                arribo=int(elemento[3]),
                irrupcion=int(elemento[4]),
            ) #elimine el elemento 5 por lo del tiempo en memoria no se le pasa
        )

cargar_lista_procesos()

if not ColaProcesos:
    print("No hay procesos en la cola de trabajos")


#Algoritmo Best Fit
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
        proceso.estado = 'listo'
        return True
    return False


#Liberar partición cuando un proceso termina
def liberar_particion(proceso):
    for part in arreglo_particiones:
        if part.id == proceso.particion_asignada:
            part.ocupado = False
            part.id_proceso = ""
            part.fragmentacion = 0
            if DEBUG:
                print(f"Partición {part.id} liberada por {proceso.nombre}")


#Método SRTF (Shortest Remaining Time First)
def obtener_proceso_srtf():
    if not ColaListo:
        return None
    # Calcula el tiempo restante de cada proceso y selecciona el menor
    return min(ColaListo, key=lambda p: p.irrupcion - p.t_memoria)

#Mostrar colas con ENTER
def Muestra_Colas(Listo, Suspendido, Finalizado, Part, Ejecucion=None):
    print("Presione Enter para continuar...")
    tecla = input()
    if not tecla:
        nombre_ejecucion = Ejecucion.nombre if Ejecucion else "Ninguno"    
        print(f"Proceso en ejecucion:{nombre_ejecucion}") 
        print("Cola de listos:", [p.nombre for p in Listo])
        print("Cola suspendidos:", [p.nombre for p in Suspendido])
        print("Cola finalizados:", [p.nombre for p in Finalizado])
        print("Particiones ocupadas:")
        for p in Part:
            print(f"- {p.id}: {'Ocupada' if p.ocupado else 'Libre'} (Proc: {p.id_proceso}, Frag: {p.fragmentacion})")


# --- SIMULACIÓN DEL ARRIBO DE PROCESOS Y CARGA A MEMORIA ---

tiempo_actual = 0

# El bucle controla el paso del tiempo del sistema
while ColaProcesos or ColaSuspendido or ColaListo:
    if DEBUG:
        print(f"\n⏱ Tiempo actual: {tiempo_actual}")

    #Llegada de procesos nuevos al sistema
    for p in list(ColaProcesos):
        if p.arribo <= tiempo_actual: #el arribo debe ser solo cuando el tiempo de arribo es igual al tiempo actual del SO
            ColaProcesos.remove(p)
            if DEBUG:
                print(f"→ Proceso {p.nombre} ha arribado al sistema (t={tiempo_actual})")

            # Intentar asignar directamente si hay espacio y multiprogramación lo permite
            if gradoMultiProgr < LIMITE_MULTIPROG:
                asignado = best_fit(p)
                if asignado:
                    ColaListo.append(p)
                    gradoMultiProgr += 1
                    Muestra_Colas(ColaListo, ColaSuspendido, ColaFinalizado, arreglo_particiones, Ejecucion = proceso_actual)
                    if DEBUG:
                        print(f"   Asignado a partición {p.particion_asignada}")

                else:
                    ColaSuspendido.append(p)
                    p.estado = "suspendido"
                    if DEBUG:
                        print(f"   Suspendido: sin espacio disponible")
            else:
                ColaSuspendido.append(p)
                p.estado = "suspendido"
                if DEBUG:
                    print(f"   Suspendido: límite multiprogramación alcanzado")



    
                    
    #Reintentar procesos suspendidos (por si se liberó espacio)
    for p in list(ColaSuspendido):
        if gradoMultiProgr < LIMITE_MULTIPROG:
            asignado = best_fit(p)
            if asignado:
                ColaSuspendido.remove(p)
                ColaListo.append(p)
                gradoMultiProgr += 1
                p.estado = "listo"
                if DEBUG:
                    print(f"   {p.nombre} reasignado desde suspendido a {p.particion_asignada}")

    #Ejecutar proceso según SRTF
    proceso_actual = obtener_proceso_srtf()

    if proceso_actual:
        proceso_actual.estado = "ejecutando"
        proceso_actual.t_memoria += 1  # simula un ciclo de CPU
        if DEBUG:
            print(f"Ejecutando {proceso_actual.nombre} ({proceso_actual.t_memoria}/{proceso_actual.irrupcion}) en {proceso_actual.particion_asignada}")

        # Si termina su ráfaga de CPU
        if proceso_actual.t_memoria >= proceso_actual.irrupcion: #esto hiciste por si en algun caso desborda de onda el tiempo en memoria?
            ColaListo.remove(proceso_actual)
            ColaFinalizado.append(proceso_actual)
            liberar_particion(proceso_actual)
            gradoMultiProgr -= 1
            proceso_actual.estado = "finalizado"
            Muestra_Colas(ColaListo, ColaSuspendido, ColaFinalizado, arreglo_particiones, Ejecucion = proceso_actual)
            if DEBUG:
                print(f"Proceso {proceso_actual.nombre} finalizado (t={tiempo_actual})")
    else:
        if DEBUG:
            print("No hay procesos listos para ejecutar")

    #Avanzar el tiempo del sistema
    tiempo_actual += 1


# --- Estado final de la simulación ---
if DEBUG:
    print("\n=== Estado final de la simulación ===")
    print("Tiempo total:", tiempo_actual)
    print("Grado de multiprogramación final:", gradoMultiProgr)
    print("Cola de listos:", [p.nombre for p in ColaListo])
    print("Cola suspendidos:", [p.nombre for p in ColaSuspendido])
    print("Cola finalizados:", [p.nombre for p in ColaFinalizado])
    print("Particiones ocupadas:")
    for p in arreglo_particiones:
        print(f"- {p.id}: {'Ocupada' if p.ocupado else 'Libre'} (Proc: {p.id_proceso}, Frag: {p.fragmentacion})")