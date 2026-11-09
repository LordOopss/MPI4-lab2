# LAB 2 – Parallel Word Counting in a Text Corpus with MPI

## 1. Título e información del equipo

**Laboratorio:** Parallel Word Counting in a Text Corpus with MPI

**Equipo:** Juan Manuel Vallejo

## 2. Descripción del problema

El corpus es una carpeta `dataset/` con 3.000 archivos de texto (`file_0001.txt` … `file_3000.txt`) y un archivo de consulta, `consulta.txt`, con 200 palabras distintas, una por línea.

El objetivo es contar cuántas veces aparece cada palabra de la consulta en todo el corpus y reportar las 10 más frecuentes. El programa debe coincidir exactamente con la línea base secuencial.

El conjunto de datos se genera con `generator.py` (semilla fija `42`, así que todos los equipos obtienen los mismos datos). El corpus generado tiene 44.951.458 palabras en total, y los tamaños de los archivos varían mucho, así que el costo de procesar cada archivo es muy diferente.

El laboratorio compara tres programas: una línea base secuencial, una primera versión MPI con distribución estática de archivos y una segunda versión MPI con distribución dinámica.

## 3. Entorno e instrucciones de ejecución

### a. Plan experimental

- Conjunto de datos: se genera una vez con `generator.py` (semilla 42). Es el mismo en todas las ejecuciones.
- Cada implementación se ejecuta tres veces. La mediana se usa para todas las comparaciones.
- Las versiones MPI se ejecutan con `p` procesos, donde `p` es el valor recomendado por `detectar_procesos_mpi.py` en la máquina del equipo (PC con Windows y Docker Desktop).
- Valores medidos: tiempo total de ejecución, tiempo de procesamiento local de cada proceso y desbalance de carga `LI = max(t_i) / mean(t_i)`.
- Valores derivados: aceleración `S_p = T_seq / T_p` y eficiencia `E_p = S_p / p`.

### b. Línea base secuencial

`baseline_secuencial.py` es la implementación de referencia (provista, no modificada). Hace lo siguiente:

1. lee `consulta.txt` y pasa las palabras a minúsculas,
2. recorre cada `file_*.txt` del conjunto de datos, línea por línea, y cuenta los tokens que están en la consulta,
3. mide el tiempo solo del paso de conteo y lo imprime como `Tiempo de ejecución: … segundos`,
4. escribe `dataset/baseline_results.csv` e imprime las 10 palabras principales.

### c. Versión MPI 1 (distribución estática)

`mpi1.py`:

1. El rango 0 lee `consulta.txt` y lista los archivos `file_*.txt` (ordenados por nombre).
2. El rango 0 envía las palabras de la consulta a todos los procesos con `comm.bcast`.
3. El rango 0 reparte la lista de archivos por turnos (el archivo `i` va al rango `i % p`) y envía a cada proceso su lista con `comm.scatter`.
4. Cada proceso cuenta las palabras de la consulta en sus propios archivos y mide cuánto tarda (su tiempo local).
5. Cada proceso devuelve sus conteos parciales y su tiempo local con `comm.gather`.
6. El rango 0 combina los conteos parciales e imprime el tiempo total, el número de archivos y el tiempo local por proceso, el desbalance de carga y las 10 palabras principales.

### d. Versión MPI 2 (distribución dinámica)

`mpi2.py` es el mismo programa, pero con una cola de trabajo en lugar de un reparto fijo:

1. El rango 0 ordena los archivos de mayor a menor, para que los archivos grandes empiecen primero y los pequeños llenen los huecos al final.
2. Cada trabajador tiene dos archivos en cola. Cuando envía sus conteos parciales, recibe de inmediato el nombre del siguiente archivo.
3. El rango 0 también cuenta archivos por su cuenta, entre revisiones de resultados terminados (`iprobe`), para no bloquear a los trabajadores.

### e. Procedimiento de prueba

1. Instala Docker Desktop y asegúrate de que esté corriendo.
2. Pon `generator.py`, `baseline_secuencial.py`, `run_all.sh`, `mpi1.py` y `mpi2.py` en la misma carpeta.
3. Encuentra `p` en tu máquina: ejecuta el calibrador del repositorio del taller (`detectar_procesos_mpi.py`) y usa su `N RECOMENDADO`.
4. Genera el conjunto de datos y ejecuta todos los experimentos con `run_all.sh`. Pon `NP_LIST` con tu `p` y `RUNS` en 3.

Windows (PowerShell, desde la carpeta del proyecto):

```powershell
docker run --rm -v "${PWD}:/app" -e NP_LIST=11 -e RUNS=3 augustosalazar/slim-mpi:2 sh /app/run_all.sh
```

macOS / Linux:

```bash
docker run --rm -v "$(pwd):/app" -e NP_LIST=11 -e RUNS=3 augustosalazar/slim-mpi:2 sh /app/run_all.sh
```

El script escribe los logs en `results/logs/` y un resumen en `results/times_summary.csv`.

> **Nota:** `run_all.sh` busca la línea `EXECUTION_TIME=` en cada log. La línea base imprime `Tiempo de ejecución:` en su lugar, así que su tiempo no se escribe en `times_summary.csv`. Toma el tiempo de la línea base de `results/logs/baseline_secuencial.log` (y las dos corridas extra de `baseline_2.log` y `baseline_3.log`).

Para ejecutar solo la línea base:

```bash
docker run --rm -v "$(pwd):/app" augustosalazar/slim-mpi:2 python /app/baseline_secuencial.py
```

## 4. Resultados (p = 11)

Cada tabla muestra las tres corridas y su mediana. La mediana de cada columna se calcula por separado.

### a. Línea base secuencial

| Corrida | Tiempo (s) |
| --- | ---: |
| 1 | 74,444 |
| 2 | 74,396 |
| 3 | 73,437 |
| **Mediana** | **74,396** |

La salida de la línea base (las 10 palabras principales y sus conteos) es la referencia para verificar la corrección.

### b. Versión MPI 1 (estática)

| Corrida | Tiempo total (s) | Desbalance de carga LI |
| --- | ---: | ---: |
| 1 | 9,587 | 1,057 |
| 2 | 9,627 | 1,053 |
| 3 | 9,533 | 1,049 |
| **Mediana** | **9,587** | **1,053** |

Aceleración `S_11 = 74,396 / 9,587 = 7,76`, eficiencia `E_11 = 7,76 / 11 = 0,71`.

Las 10 palabras principales son idénticas a la línea base en las tres corridas.

Tiempo de procesamiento local por proceso en la corrida mediana (corrida 2):

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

### c. Versión MPI 2 (dinámica)

| Corrida | Tiempo total (s) | Desbalance de carga LI |
| --- | ---: | ---: |
| 1 | 12,506 | 1,235 |
| 2 | 12,255 | 1,208 |
| 3 | 14,756 | 1,251 |
| **Mediana** | **12,506** | **1,235** |

Aceleración `S_11 = 74,396 / 12,506 = 5,95`, eficiencia `E_11 = 0,54`.

Las 10 palabras principales son idénticas a la línea base en las tres corridas.

Tiempos por proceso en la corrida mediana (corrida 1):

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

El rango 0 procesa 332 archivos y tarda 11,90 s. Los trabajadores procesan entre 259 y 274 archivos cada uno y terminan su trabajo entre 9,15 y 9,92 s, así que quedan inactivos entre 2,6 y 3,4 s antes del final, en 12,51 s.

### d. Resumen

| Versión | Tiempo mediano (s) | Aceleración | Eficiencia | LI (mediana) |
| --- | ---: | ---: | ---: | ---: |
| Secuencial | 74,396 | 1,00 | – | – |
| MPI v1, estática | 9,587 | 7,76 | 0,71 | 1,053 |
| MPI v2, dinámica | 12,506 | 5,95 | 0,54 | 1,235 |

## 5. Análisis

### Desempeño en paralelo

La versión 1 reduce el tiempo de 74,4 s a 9,6 s, una aceleración de 7,76 con 11 procesos. La eficiencia es 0,71, así que se pierde cerca del 29 % de la aceleración ideal. El PC tiene 12 procesadores lógicos, y cada uno se comparte con el sistema operativo y con Docker, por eso no se puede alcanzar la aceleración ideal de 11. El costo de comunicación es pequeño: un broadcast de 200 palabras, un scatter de 3.000 nombres de archivo y un gather de 11 diccionarios, todo en un solo paso, frente a 9,6 s de trabajo.

### Balance de carga

La versión 1 ya está bien balanceada: LI está entre 1,05 y 1,06 en todas las corridas. El reparto por turnos le da a cada proceso entre 272 y 273 archivos, y los tiempos locales en la corrida mediana van de 8,3 s a 9,6 s. La diferencia restante viene del tamaño de los archivos, que no se compensa del todo con 272 archivos por proceso.

La versión 2 no redujo el desbalance; su LI es más alto (cerca de 1,24). El problema es el rango 0. Cuenta archivos y además reparte el trabajo. Mientras cuenta un archivo, no responde a los trabajadores, así que ellos terminan sus archivos en cola y esperan. El rango 0 termina último (11,9 s en la corrida mediana), y los trabajadores esperan entre 2,6 y 3,4 s cada uno al final. El rango 0 también termina con más archivos (cerca de 330 contra unos 266 por trabajador en la corrida mediana), porque toma trabajo entre sus propios conteos. El costo promedio por archivo es de unos 35 ms, así que los mensajes no son caros; lo que cuesta tiempo es la espera causada por el rango 0.

No probamos una variante en la que el rango 0 solo coordine y no cuente archivos. Esa variante eliminaría la espera descrita arriba, pero no forma parte de estos resultados.

### Limitaciones

- **Máquina:** todas las corridas son en un solo PC, así que los resultados podrían no aplicar a otra máquina.
- **Repeticiones:** tres corridas por configuración es una muestra pequeña. La corrida 3 de la versión 2 (14,8 s) es claramente más lenta que las otras dos.
- **Cronómetro:** los tiempos son de reloj de pared, medidos dentro de cada proceso. Otros programas corriendo en el PC pueden afectarlos.
- **Conjunto de datos único:** todas las corridas usan un solo conjunto de datos (semilla 42).
- **Partes medidas:** la línea base mide solo el paso de conteo, mientras que el total de MPI también incluye el broadcast, el scatter y el gather.
- **Salida de la línea base:** la línea base imprime su tiempo como `Tiempo de ejecución:` y `run_all.sh` no lo registra, así que sus tres tiempos se copiaron a mano de los logs en `results/logs/`. Los dos logs extra de la línea base fueron escritos en UTF-16 por PowerShell y se convirtieron a UTF-8 para este repositorio; su contenido no cambió.

## 6. Conclusiones

Para este conjunto de datos y esta máquina recomiendo la distribución estática por turnos de la versión 1. Es más simple, alcanza una aceleración de 7,76 con 11 procesos, y su desbalance de carga ya está cerca de 1 (LI 1,05), así que la planificación dinámica tiene poco que ganar. La versión 2 fue cerca de 30 % más lenta (12,5 s contra 9,6 s) y su desbalance fue mayor, porque el rango 0 tiene que coordinar el trabajo y además contar archivos. La distribución dinámica valdría la pena probarla con costos de archivo más variables, o con un coordinador que no cuente archivos.
