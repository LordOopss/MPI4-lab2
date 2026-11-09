# LAB 2 – Parallel Word Counting in a Text Corpus with MPI

## 1. Title and Team Information

**Lab:** Parallel Word Counting in a Text Corpus with MPI
**Team:** Lordo (add the names of the other team members here)

## 2. Problem Description

The corpus is a folder `dataset/` with 3,000 text files (`file_0001.txt` … `file_3000.txt`) and one query file, `consulta.txt`, with 200 distinct words, one per line.

The goal is to count how many times each query word appears in the whole corpus and report the 10 most frequent ones. The program must match the sequential baseline exactly.

The dataset is generated with `generator.py` (fixed seed `42`, so every team gets the same data). The generated corpus has 44,951,458 words in total, and the file sizes vary a lot, so the cost of processing each file is very different.

The lab compares three programs: a sequential baseline, a first MPI version with a static distribution of files, and a second MPI version with a dynamic distribution.

## 3. Environment and Execution Instructions

### a. Experimental Plan

- Dataset: generated once with `generator.py` (seed 42). It is the same for every run.
- Each implementation is run three times. The median is used for all comparisons.
- The MPI versions run with `p = 11` processes, the value recommended by `detectar_procesos_mpi.py` on the team's machine (Windows PC with Docker Desktop).
- Measured values: total execution time, the local processing time of each process, and the load imbalance `LI = max(t_i) / mean(t_i)`.
- Derived values: speedup `S_p = T_seq / T_p` and efficiency `E_p = S_p / p`.

### b. Sequential baseline

`baseline_secuencial.py` is the reference implementation (provided, not modified). It:

1. reads `consulta.txt` and lowercases the words,
2. goes through each `file_*.txt` in the dataset, line by line, and counts the tokens that are in the query,
3. measures the time of the counting step only, and prints it as `Tiempo de ejecución: … segundos`,
4. writes `dataset/baseline_results.csv` and prints the top 10 words.

### c. MPI version 1 (static distribution)

`mpi1.py`:

1. Rank 0 reads `consulta.txt` and lists the `file_*.txt` files (sorted by name).
2. Rank 0 sends the query words to all processes with `comm.bcast`.
3. Rank 0 splits the file list round-robin (file `i` goes to rank `i % p`) and sends each process its list with `comm.scatter`.
4. Each process counts the query words in its own files and measures how long that takes (its local time).
5. Each process returns its partial counts and its local time with `comm.gather`.
6. Rank 0 merges the partial counts and prints the total time, the number of files and the local time per process, the load imbalance, and the top 10 words.

### d. MPI version 2 (dynamic distribution)

`mpi2.py` is the same program with a work queue instead of a fixed split:

1. Rank 0 sorts the files from largest to smallest, so the big files start first and the small files fill the gaps at the end.
2. Each worker keeps two files queued. When it sends back its partial counts, it immediately receives the next file name.
3. Rank 0 also counts files itself, between checks for finished results (`iprobe`), so it does not block the workers.

### e. Test procedure

1. Install Docker Desktop and make sure it is running.
2. Put `generator.py`, `baseline_secuencial.py`, `run_all.sh`, `mpi1.py` and `mpi2.py` in the same folder.
3. Find `p` on your machine: run the calibrator from the workshop repository (`detectar_procesos_mpi.py`) and use its `N RECOMENDADO`.
4. Generate the dataset and run all the experiments with `run_all.sh`. Set `NP_LIST` to your `p` and `RUNS` to 3.

Windows (PowerShell, from the project folder):

```powershell
docker run --rm -v "${PWD}:/app" -e NP_LIST=11 -e RUNS=3 augustosalazar/slim-mpi:2 sh /app/run_all.sh
```

macOS / Linux:

```bash
docker run --rm -v "$(pwd):/app" -e NP_LIST=11 -e RUNS=3 augustosalazar/slim-mpi:2 sh /app/run_all.sh
```

The script writes the logs to `results/logs/` and a summary to `results/times_summary.csv`.

> **Note:** `run_all.sh` looks for the line `EXECUTION_TIME=` in each log. The baseline prints `Tiempo de ejecución:` instead, so its time is not written to `times_summary.csv`. Take the baseline time from `results/logs/baseline_secuencial.log` (and the two extra baseline runs from `baseline_2.log` and `baseline_3.log`).

To run the baseline alone:

```bash
docker run --rm -v "$(pwd):/app" augustosalazar/slim-mpi:2 python /app/baseline_secuencial.py
```

## 4. Results (p = 11)

Each table gives the three runs and their median. The median of each column is computed separately.

### a. Sequential baseline

| Run | Time (s) |
| --- | ---: |
| 1 | 74.444 |
| 2 | 74.396 |
| 3 | 73.437 |
| **Median** | **74.396** |

The baseline output (top 10 words and counts) is the reference for correctness.

### b. MPI version 1 (static)

| Run | Total time (s) | Load imbalance LI |
| --- | ---: | ---: |
| 1 | 9.587 | 1.057 |
| 2 | 9.627 | 1.053 |
| 3 | 9.533 | 1.049 |
| **Median** | **9.587** | **1.053** |

Speedup `S_11 = 74.396 / 9.587 = 7.76`, efficiency `E_11 = 7.76 / 11 = 0.71`.

The top 10 words are identical to the baseline in all three runs.

Local processing time per process in the median run (run 2):

| Rank | Files | Local time (s) |
| ---: | ---: | ---: |
| 0 | 273 | 9.617 |
| 1 | 273 | 9.509 |
| 2 | 273 | 8.783 |
| 3 | 273 | 8.992 |
| 4 | 273 | 9.312 |
| 5 | 273 | 8.719 |
| 6 | 273 | 9.283 |
| 7 | 273 | 9.012 |
| 8 | 272 | 8.290 |
| 9 | 272 | 9.432 |
| 10 | 272 | 9.472 |

### c. MPI version 2 (dynamic)

| Run | Total time (s) | Load imbalance LI |
| --- | ---: | ---: |
| 1 | 12.506 | 1.235 |
| 2 | 12.255 | 1.208 |
| 3 | 14.756 | 1.251 |
| **Median** | **12.506** | **1.235** |

Speedup `S_11 = 74.396 / 12.506 = 5.95`, efficiency `E_11 = 0.54`.

The top 10 words are identical to the baseline in all three runs.

Per-process times in the median run (run 1):

| Rank | Files | Local time (s) |
| ---: | ---: | ---: |
| 0 | 332 | 11.898 |
| 1 | 270 | 9.302 |
| 2 | 265 | 9.327 |
| 3 | 268 | 9.536 |
| 4 | 272 | 9.603 |
| 5 | 267 | 9.399 |
| 6 | 269 | 9.262 |
| 7 | 263 | 9.190 |
| 8 | 259 | 9.147 |
| 9 | 261 | 9.367 |
| 10 | 274 | 9.920 |

Rank 0 does 332 files and takes 11.90 s. The workers do 259–274 files each and finish their own work after 9.15–9.92 s, so they are idle for 2.6–3.4 s before the end at 12.51 s.

### d. Summary

| Version | Median time (s) | Speedup | Efficiency | LI (median) |
| --- | ---: | ---: | ---: | ---: |
| Sequential | 74.396 | 1.00 | – | – |
| MPI v1, static | 9.587 | 7.76 | 0.71 | 1.053 |
| MPI v2, dynamic | 12.506 | 5.95 | 0.54 | 1.235 |

## 5. Analysis

### Parallel performance

Version 1 reduces the time from 74.4 s to 9.6 s, a speedup of 7.76 with 11 processes. The efficiency is 0.71, so about 29 % of the ideal speedup is lost. The PC has 12 logical processors, and each one is shared with the operating system and Docker, so the ideal speedup of 11 cannot be reached. The communication cost is small: one broadcast of 200 words, one scatter of 3,000 file names and one gather of 11 dictionaries, all in a single step, compared with 9.6 s of work.

### Load balance

Version 1 is already well balanced: LI is between 1.05 and 1.06 in all runs. Round-robin gives each process 272 or 273 files, and the local times in the median run go from 8.3 s to 9.6 s. The remaining difference comes from the file sizes, which do not average out perfectly over 272 files per process.

Version 2 did not reduce the imbalance; its LI is higher (about 1.24). The problem is rank 0. It counts files and also dispatches work. While it is counting a file, it does not answer the workers, so they finish their queued files and wait. Rank 0 ends last (11.9 s in the median run), and the workers wait 2.6–3.4 s each at the end. Rank 0 also ends up with more files (about 330 against about 266 per worker in the median run), because it takes work between its own counts. The average cost per file is about 35 ms, so the messages are not expensive; the waiting caused by rank 0 is what costs time.

We did not test a variant where rank 0 only coordinates and does not count files. That variant would remove the waiting described above, but it is not part of these results.

### Limitations

- **Machine:** all runs are on one PC, so the results may not apply to another machine.
- **Repetitions:** three runs per configuration is a small sample. Version 2 run 3 (14.8 s) is clearly slower than the other two runs.
- **Timer:** times are wall-clock times, measured inside each process. Other programs running on the PC can affect them.
- **Single dataset:** all runs use one dataset (seed 42).
- **Measured parts:** the baseline times only the counting step, while the MPI total also includes the broadcast, the scatter and the gather.
- **Baseline output:** the baseline prints its time as `Tiempo de ejecución:` and `run_all.sh` does not record it, so its three times were copied by hand from the logs in `results/logs/`. The two extra baseline logs were written in UTF-16 by PowerShell and were converted to UTF-8 for this repository; their content is unchanged.

## 6. Conclusions

For this dataset and this machine I recommend the static round-robin distribution of version 1. It is simpler, it reaches a speedup of 7.76 with 11 processes, and its load imbalance is already close to 1 (LI 1.05), so dynamic scheduling has little to gain. Version 2 was about 30 % slower (12.5 s against 9.6 s) and its imbalance was higher, because rank 0 has to both coordinate the work and count files. Dynamic distribution would be worth trying with more variable file costs, or with a coordinator that does not count files.

## Files

- `generator.py`, `baseline_secuencial.py`, `run_all.sh`: as provided by the lab (not modified).
- `mpi1.py`: MPI version 1, static distribution.
- `mpi2.py`: MPI version 2, dynamic distribution.
- `README.md`: this report.
