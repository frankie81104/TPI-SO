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
    fragmentacion: int
    ocupado: bool

#Definciion de una clase proceso

@dataclass
class Proceso:
    id_proceso: int
    nombre: str
    tamano: int
    arribo: int
    irrupcion: int
    t_memoria: int
    estado: str = "nuevo"
    particion_asignada: str = None

#Definición del arreglo de particiones
#Cuando llegue un proceso en fragmentacion=espacio-tamaño del proceso

arreglo_particiones: List[Particion] = [
    Particion(id="Sistema Operativo", dir=0, espacio=100, id_proceso="", fragmentacion=0, ocupado=True), 
    Particion(id="Trabajos Grandes", dir=100, espacio=250, id_proceso="", fragmentacion=0, ocupado=False),
    Particion(id="Trabajos Medianos", dir=351, espacio=150, id_proceso="", fragmentacion=0, ocupado=False),
    Particion(id="Trabajos Pequeños", dir=501, espacio=50, id_proceso="", fragmentacion=0, ocupado=False)
]
#La idea es que los procesos ingresen por default a la cola de procesos,
#cuando se cumpla su arribo pasen a la cola de listo y se evaluen en base al metodo BestFit o el Algoritmo SRTF, se considera finalizado si t_memoria == irrupcion.

ColaProcesos=[]
ColaListo=[]
ColaSuspendido=[]
ColaFinalizado=[]

Procesos = 0


#Funcion encargada de cargar el contenido del archivo en la variable procesos
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
                t_memoria=int(elemento[5])
            )
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


#Bucle principal de carga en memoria
while gradoMultiProgr < LIMITE_MULTIPROG and ColaProcesos:
    elemento = ColaProcesos.pop(0)
    if DEBUG:
        print(f"Intentando asignar proceso: {elemento.nombre}")
    asignado = best_fit(elemento)
    if asignado:
        ColaListo.append(elemento)
        gradoMultiProgr += 1
        if DEBUG:
            print(f"→ Proceso {elemento.nombre} asignado a partición {elemento.particion_asignada}")
    else:
        ColaSuspendido.append(elemento)
        if DEBUG:
            print(f"→ Proceso {elemento.nombre} suspendido (sin espacio disponible)")

print("\n=== Estado final de la simulación ===")
print("Grado de multiprogramación actual:", gradoMultiProgr)
print("Cola de listos:", [p.nombre for p in ColaListo])
print("Cola suspendidos:", [p.nombre for p in ColaSuspendido])
print("Particiones ocupadas:")
for p in arreglo_particiones:
    print(f"- {p.id}: {'Ocupada' if p.ocupado else 'Libre'} (Proc: {p.id_proceso}, Frag: {p.fragmentacion})")
