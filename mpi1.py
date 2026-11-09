"""MPI version 1: broadcast of the query and static file distribution.

Flow:
1. rank 0 reads consulta.txt and lists the file_*.txt corpus files.
2. rank 0 broadcasts the query words to all processes (comm.bcast).
3. rank 0 splits the file list statically (round robin) and scatters it.
4. Each process counts the query words in its own files and times that work.
5. Partial counts are gathered in rank 0, which builds the global top 10.

Run from the project folder (it reads ./dataset):
    mpiexec -n 8 python mpi1.py
"""

import os
import sys
import time
from collections import Counter

from mpi4py import MPI

from baseline_secuencial import cargar_consulta

TOP_N = 10


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


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    carpeta = os.path.dirname(os.path.abspath(__file__))
    dataset = os.path.join(carpeta, "dataset")

    # Rank 0 prepares the query and the static assignment of files.
    if rank == 0:
        if not os.path.isdir(dataset):
            print(f"Error: no existe la carpeta dataset en {dataset}")
            comm.Abort(1)
        try:
            palabras_objetivo = cargar_consulta(os.path.join(dataset, "consulta.txt"))
        except FileNotFoundError as error:
            print("Error:", error)
            comm.Abort(1)
        archivos = sorted(
            nombre for nombre in os.listdir(dataset)
            if nombre.startswith("file_") and nombre.endswith(".txt")
        )
        # Static distribution: file i goes to process i % size.
        asignaciones = [archivos[r::size] for r in range(size)]
    else:
        palabras_objetivo = None
        asignaciones = None

    comm.Barrier()
    inicio = time.perf_counter()

    palabras_objetivo = comm.bcast(palabras_objetivo, root=0)
    mis_archivos = comm.scatter(asignaciones, root=0)

    # Local work, timed per process.
    inicio_local = time.perf_counter()
    conteo_local = Counter()
    for nombre in mis_archivos:
        conteo_local.update(contar_en_archivo(os.path.join(dataset, nombre), palabras_objetivo))
    tiempo_local = time.perf_counter() - inicio_local

    # Partial results go back to rank 0.
    aportes = comm.gather((rank, len(mis_archivos), tiempo_local, dict(conteo_local)), root=0)

    if rank != 0:
        return

    global_conteo = Counter()
    for _, _, _, conteo in aportes:
        global_conteo.update(conteo)
    tiempo_total = time.perf_counter() - inicio

    reportar(size, aportes, global_conteo, tiempo_total, sum(len(a) for a in asignaciones))


def reportar(size, aportes, global_conteo, tiempo_total, total_archivos):
    """Prints the timing, the per-process report and the top 10 words."""
    aportes = sorted(aportes, key=lambda a: a[0])
    tiempos = [a[2] for a in aportes]
    media = sum(tiempos) / len(tiempos)
    li = max(tiempos) / media if media > 0 else 1.0

    print(f"EXECUTION_TIME={tiempo_total:.6f}")
    print(f"Procesos: {size}")
    print(f"Archivos procesados: {total_archivos}")
    print("Reporte por proceso:")
    for rank, n_archivos, tiempo_local, _ in aportes:
        print(f"  rank {rank}: archivos={n_archivos} tiempo_local={tiempo_local:.6f} s")
    print(f"LOAD_IMBALANCE={li:.4f}")
    print(f"Top {TOP_N} palabras de consulta en el corpus:")
    for palabra, cuenta in global_conteo.most_common(TOP_N):
        print(f"  {palabra}: {cuenta}")


if __name__ == "__main__":
    sys.exit(main())
