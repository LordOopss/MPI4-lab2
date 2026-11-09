"""MPI version 2: dynamic file distribution to reduce load imbalance.

Version 1 gives every process a fixed list of files. Files have very different
sizes (60% small, 30% medium, 10% large), so some processes finish much later.

Version 2 keeps a queue of files and hands out new work as processes become free:
1. rank 0 broadcasts the query words (comm.bcast), as in version 1.
2. Files are sorted from largest to smallest (largest-first scheduling), so the
   big files start early and small files fill the gaps at the end.
3. rank 0 keeps a queue and sends each worker a file name. When a worker sends back
   its partial counts, it immediately receives the next file.
4. Rank 0 also counts files itself. Between files it collects finished results, so
   it does not block the other processes.
5. Each worker keeps up to two files queued, so it does not wait for rank 0 to reply.

Run from the project folder (it reads ./dataset):
    mpiexec -n 8 python mpi2.py
"""

import os
import sys
import time
from collections import Counter, deque

from mpi4py import MPI

from baseline_secuencial import cargar_consulta

TOP_N = 10
PROFUNDIDAD = 2  # files queued in advance for each worker
ETIQUETA_TAREA = 1
ETIQUETA_RESULTADO = 2


def contar_en_archivo(ruta, palabras_objetivo):
    """Counts how many times each query word appears in one file."""
    conteo = Counter()
    with open(ruta, "r", encoding="utf-8") as f:
        for linea in f:
            for palabra in linea.split():
                palabra = palabra.lower()
                if palabra in palabras_objetivo:
                    conteo[palabra] += 1
    return conteo


def procesar(nombre, dataset, palabras_objetivo):
    """Counts one file and returns (partial counts, seconds spent)."""
    inicio = time.perf_counter()
    conteo = contar_en_archivo(os.path.join(dataset, nombre), palabras_objetivo)
    return dict(conteo), time.perf_counter() - inicio


def trabajar(comm, dataset, palabras_objetivo):
    """Workers: receive a file name, count it, send the result back, until None."""
    while True:
        nombre = comm.recv(source=0, tag=ETIQUETA_TAREA)
        if nombre is None:
            return
        resultado = procesar(nombre, dataset, palabras_objetivo)
        comm.send(resultado, dest=0, tag=ETIQUETA_RESULTADO)


def coordinar(comm, dataset, palabras_objetivo, archivos):
    """Rank 0: hands out files dynamically and also counts files itself.

    Returns (global counts, stats), where stats[rank] = [files, local seconds].
    """
    size = comm.Get_size()
    pendientes = deque(archivos)
    en_curso = {w: 0 for w in range(1, size)}
    cerrados = set()
    global_conteo = Counter()
    stats = {r: [0, 0.0] for r in range(size)}

    def enviar(trabajador):
        comm.send(pendientes.popleft(), dest=trabajador, tag=ETIQUETA_TAREA)
        en_curso[trabajador] += 1

    def cerrar(trabajador):
        comm.send(None, dest=trabajador, tag=ETIQUETA_TAREA)
        cerrados.add(trabajador)

    # Prime every worker with up to PROFUNDIDAD files.
    for trabajador in en_curso:
        for _ in range(PROFUNDIDAD):
            if pendientes:
                enviar(trabajador)
        if en_curso[trabajador] == 0:
            cerrar(trabajador)

    while pendientes or any(en_curso.values()):
        # Rank 0 counts one of its own files...
        if pendientes:
            conteo, segundos = procesar(pendientes.popleft(), dataset, palabras_objetivo)
            global_conteo.update(conteo)
            stats[0][0] += 1
            stats[0][1] += segundos

        # ...then takes any finished results. If no files are left, it waits for them.
        while any(en_curso.values()) and (
            not pendientes or comm.iprobe(source=MPI.ANY_SOURCE, tag=ETIQUETA_RESULTADO)
        ):
            estado = MPI.Status()
            conteo, segundos = comm.recv(source=MPI.ANY_SOURCE, tag=ETIQUETA_RESULTADO, status=estado)
            trabajador = estado.Get_source()
            en_curso[trabajador] -= 1
            global_conteo.update(conteo)
            stats[trabajador][0] += 1
            stats[trabajador][1] += segundos
            if pendientes:
                enviar(trabajador)
            elif en_curso[trabajador] == 0 and trabajador not in cerrados:
                cerrar(trabajador)

    return global_conteo, stats


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    carpeta = os.path.dirname(os.path.abspath(__file__))
    dataset = os.path.join(carpeta, "dataset")

    if rank == 0:
        if not os.path.isdir(dataset):
            print(f"Error: no existe la carpeta dataset en {dataset}")
            comm.Abort(1)
        try:
            palabras_objetivo = cargar_consulta(os.path.join(dataset, "consulta.txt"))
        except FileNotFoundError as error:
            print("Error:", error)
            comm.Abort(1)
        archivos = [
            nombre for nombre in os.listdir(dataset)
            if nombre.startswith("file_") and nombre.endswith(".txt")
        ]
        # Largest first: the big files start early, small ones fill the end.
        archivos.sort(key=lambda n: os.path.getsize(os.path.join(dataset, n)), reverse=True)
    else:
        palabras_objetivo = None
        archivos = None

    comm.Barrier()
    inicio = time.perf_counter()

    palabras_objetivo = comm.bcast(palabras_objetivo, root=0)

    if rank != 0:
        trabajar(comm, dataset, palabras_objetivo)
        return

    global_conteo, stats = coordinar(comm, dataset, palabras_objetivo, archivos)
    tiempo_total = time.perf_counter() - inicio
    reportar(size, stats, global_conteo, tiempo_total, len(archivos))


def reportar(size, stats, global_conteo, tiempo_total, total_archivos):
    """Prints the timing, the per-process report and the top 10 words."""
    tiempos = [stats[r][1] for r in range(size)]
    media = sum(tiempos) / len(tiempos)
    li = max(tiempos) / media if media > 0 else 1.0

    print(f"EXECUTION_TIME={tiempo_total:.6f}")
    print(f"Procesos: {size}")
    print(f"Archivos procesados: {total_archivos}")
    print("Reporte por proceso:")
    for rank in range(size):
        n_archivos, tiempo_local = stats[rank]
        print(f"  rank {rank}: archivos={n_archivos} tiempo_local={tiempo_local:.6f} s")
    print(f"LOAD_IMBALANCE={li:.4f}")
    print(f"Top {TOP_N} palabras de consulta en el corpus:")
    for palabra, cuenta in global_conteo.most_common(TOP_N):
        print(f"  {palabra}: {cuenta}")


if __name__ == "__main__":
    sys.exit(main())
