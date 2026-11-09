# LAB 2 – Parallel Word Counting in a Text Corpus with MPI

## 1. Información del equipo

**Equipo:** Juan Manuel Vallejo

## 2. Descripción del problema

El corpus es la carpeta `dataset/` con 3.000 archivos de texto (`file_0001.txt` … `file_3000.txt`) y el archivo `consulta.txt`, con 200 palabras distintas, una por línea.

El objetivo es contar cuántas veces aparece cada palabra de la consulta en todo el corpus y reportar las 10 más frecuentes. El resultado debe coincidir exactamente con la línea base secuencial.

`generator.py` genera el dataset con semilla 42, así que todos los equipos usan los mismos datos. Tiene 44.951.458 palabras y los tamaños de los archivos varían mucho.

Se comparan tres programas:

- `baseline_secuencial.py`: referencia secuencial (provista, sin cambios).
- `mpi1.py`: MPI con distribución estática (reparto por turnos).
- `mpi2.py`: MPI con distribución dinámica (cola de trabajo).

## 3. Ejecución

### Método

- Cada programa se ejecuta 3 veces y se reporta la mediana.
- Procesos MPI: `p = 11`, el valor que recomendó `detectar_procesos_mpi.py` en el PC del equipo (Windows con Docker Desktop).
- Métricas: tiempo total, tiempo local por proceso, desbalance de carga `LI = max(tᵢ) / media(tᵢ)`, aceleración `S_p = T_seq / T_p` y eficiencia `E_p = S_p / p`.

### Pasos

1. Instala Docker Desktop y asegúrate de que esté corriendo.
2. Pon todos los archivos del proyecto en la misma carpeta.
3. Desde esa carpeta, ejecuta:

Windows (PowerShell):

```powershell
docker run --rm -v "${PWD}:/app" -e NP_LIST=11 -e RUNS=3 augustosalazar/slim-mpi:2 sh /app/run_all.sh
```

macOS / Linux:

```bash
docker run --rm -v "$(pwd):/app" -e NP_LIST=11 -e RUNS=3 augustosalazar/slim-mpi:2 sh /app/run_all.sh
```

`run_all.sh` genera el dataset, ejecuta la línea base y las dos versiones MPI, y guarda los logs en `results/logs/` y el resumen en `results/times_summary.csv`.

> **Nota:** `run_all.sh` busca la línea `EXECUTION_TIME=`, pero la línea base imprime `Tiempo de ejecución:`. Por eso sus tiempos se toman de `results/logs/baseline_*.log`.

### Versión 1 (estática)

El rango 0 ordena los archivos y asigna el archivo `i` al rango `i % p`. Cada proceso cuenta sus archivos, mide su tiempo local y devuelve sus conteos con `comm.gather`.

### Versión 2 (dinámica)

El rango 0 ordena los archivos de mayor a menor tamaño y los entrega como cola de trabajo. Cada trabajador mantiene dos archivos en cola y recibe uno nuevo cada vez que entrega un resultado. El rango 0 también cuenta archivos y revisa los resultados pendientes con `iprobe`.

## 4. Resultados (p = 11)

Tiempos en segundos. Cada tabla muestra tres corridas y su mediana.

### a. Línea base secuencial

| Corrida | Tiempo (s) |
| --- | ---: |
| 1 | 74,444 |
| 2 | 74,396 |
| 3 | 73,437 |
| **Mediana** | **74,396** |

### b. Versión 1 (estática)

| Corrida | Tiempo total (s) | LI |
| --- | ---: | ---: |
| 1 | 9,587 | 1,057 |
| 2 | 9,627 | 1,053 |
| 3 | 9,533 | 1,049 |
| **Mediana** | **9,587** | **1,053** |

Aceleración `S₁₁ = 74,396 / 9,587 = 7,76`. Eficiencia `E₁₁ = 7,76 / 11 = 0,71`.

Las 10 palabras principales coinciden con la línea base en las tres corridas.

Tiempo local por proceso en la corrida con LI mediano (corrida 2):

| Rango | Archivos | Tiempo local (s) |
| ---: | ---: | ---: |
| 0 | 273 | 9,617 |
| 1 | 273 | 9,509 |
| 2 | 273 | 8,783 |
| 3 | 273 | 8,992 |
| 4 | 273 | 9,312 |
| 5 | 273 | 8,719 |
| 6 | 273 | 9,283 |
| 7 | 273 | 9,012 |
| 8 | 272 | 8,290 |
| 9 | 272 | 9,432 |
| 10 | 272 | 9,472 |

### c. Versión 2 (dinámica)

| Corrida | Tiempo total (s) | LI |
| --- | ---: | ---: |
| 1 | 12,506 | 1,235 |
| 2 | 12,255 | 1,208 |
| 3 | 14,756 | 1,251 |
| **Mediana** | **12,506** | **1,235** |

Aceleración `S₁₁ = 74,396 / 12,506 = 5,95`. Eficiencia `E₁₁ = 0,54`.

Las 10 palabras principales coinciden con la línea base en las tres corridas.

Tiempo local por proceso en la corrida mediana (corrida 1):

| Rango | Archivos | Tiempo local (s) |
| ---: | ---: | ---: |
| 0 | 332 | 11,898 |
| 1 | 270 | 9,302 |
| 2 | 265 | 9,327 |
| 3 | 268 | 9,536 |
| 4 | 272 | 9,603 |
| 5 | 267 | 9,399 |
| 6 | 269 | 9,262 |
| 7 | 263 | 9,190 |
| 8 | 259 | 9,147 |
| 9 | 261 | 9,367 |
| 10 | 274 | 9,920 |

### d. Resumen

| Versión | Tiempo mediano (s) | Aceleración | Eficiencia | LI (mediana) |
| --- | ---: | ---: | ---: | ---: |
| Secuencial | 74,396 | 1,00 | – | – |
| MPI v1 (estática) | 9,587 | 7,76 | 0,71 | 1,053 |
| MPI v2 (dinámica) | 12,506 | 5,95 | 0,54 | 1,235 |

## 5. Análisis

**Rendimiento.** La versión 1 reduce el tiempo de 74,4 s a 9,6 s. Una causa probable de la eficiencia de 0,71 es que el PC tiene 12 procesadores lógicos compartidos con el sistema operativo y Docker, así que 11 procesos no alcanzan la aceleración ideal de 11. La comunicación es mínima: un broadcast, un scatter y un gather frente a 9,6 s de cómputo.

**Balance de carga.** La versión 1 está bien balanceada (LI entre 1,05 y 1,06). Cada proceso recibe 272 o 273 archivos, y sus tiempos locales van de 8,3 s a 9,6 s.

La versión 2 no mejoró el balance: su LI fue de 1,21–1,25. La causa más probable es el rango 0, que cuenta archivos y reparte trabajo al mismo tiempo. Mientras cuenta, no atiende a los trabajadores, que terminan su cola y esperan. El rango 0 termina último (11,9 s frente a 9,2–9,9 s de los trabajadores) y los trabajadores quedan inactivos entre 2,6 y 3,4 s. El costo promedio por archivo es de unos 34 ms, así que la comunicación no es lo que cuesta tiempo.

No se probó una variante en la que el rango 0 solo coordine y no cuente archivos. Esa variante podría eliminar la espera, pero no forma parte de estos resultados.

**Limitaciones.**

- Todas las corridas son en un solo PC; otra máquina podría dar resultados distintos.
- Tres corridas por configuración es una muestra pequeña. La corrida 3 de la versión 2 (14,8 s) es claramente más lenta.
- Los tiempos son de reloj de pared, así que otros programas del PC pueden afectarlos.
- Un solo dataset (semilla 42).
- La línea base mide solo el conteo; los tiempos MPI incluyen también el reparto y la recolección de resultados.

## 6. Conclusión

Para este dataset y esta máquina, recomiendo la versión 1 (estática). Es más simple, alcanza una aceleración de 7,76 con 11 procesos y su balance ya es casi perfecto. La versión 2 fue cerca de 30 % más lenta (12,5 s frente a 9,6 s) porque el rango 0 coordina y cuenta a la vez. La distribución dinámica valdría la pena con archivos de costo más variable o con un coordinador que no cuente archivos.
