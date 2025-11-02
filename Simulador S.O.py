from dataclasses import dataclass, field
from typing import List

@dataclass
class Particion:
    id: str
    dir: int
    espacio: int
    id_proceso: str
    fragmentacion: int
    ocupado: bool

@dataclass
class Proceso:
    nombre: str
    tamano: int
    arribo: int
    irrupcion: int
    t_memoria: int

arreglo_particiones: List[Particion] = [
    Particion(id="Sistema Operativo", dir=0, espacio=100, id_proceso="", fragmentacion=0, ocupado=False), #cuando llegue un proceso en fragmentacion=espacio-tamaño del proceso
    Particion(id="Trabajos Grandes", dir=100, espacio=250, id_proceso="", fragmentacion=0, ocupado=False),
    Particion(id="Trabajos Medianos", dir=351, espacio=150, id_proceso="", fragmentacion=0, ocupado=False),
    Particion(id="Trabajos Pequeños", dir=501, espacio=50, id_proceso="", fragmentacion=0, ocupado=False)
]
#La idea es que los procesos ingresen por default a la cola de procesos, cuando se cumpla su arribo pasen a la cola de listo y se evaluen en base al metodo BestFit o el Algoritmo SRTF, se considera finalizado si t_memoria == irrupcion.

ColaProcesos=[]
ColaListo=[]
ColaSuspendido=[]
ColaFinalizado=[]

Procesos=0

def cargar_procesos(proceso,c_procesos):
    while c_procesos < 11:
        ColaProcesos.append(proceso)