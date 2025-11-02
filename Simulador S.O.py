from dataclasses import dataclass, field
from typing import List
import os

DEBUG = True
#Definición de una clase partición

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
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),"procesos.csv")
    with open(ruta, "r", encoding="utf-8") as f:
        procesos = f.read()
    if DEBUG == True:
        print(str(procesos))
    procesos = procesos.split("*")
    if DEBUG == True:
        print(str(procesos))
    for i in range (len(procesos)):
        elemento = procesos[i].split("-")
        if DEBUG == True: print(elemento)
        ColaProcesos.append(elemento)
cargar_lista_procesos()