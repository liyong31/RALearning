# Experiments

This directory contains scripts for running experiments on Active Learning Deterministic Register Automata (DRAs), including learning the $L_n$ languages, the $L_{mid}$ and $L_{rep}$ languages, and randomly generated DRAs.

## Prerequisites

### Setting up a Virtual Environment (Linux/macOS)

1. **Create a virtual environment:**
   ```bash
   cd /path/to/RALearning/experiments
   python3 -m venv venv
   ```

2. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```
   You should see `(venv)` in your terminal prompt after activation.

3. **Install required packages:**
   ```bash
   pip install numpy matplotlib
   ```

4. **Deactivate when done:**
   ```bash
   deactivate
   ```

## Directory Structure

The scripts use the following directory structure:
- `generated-DRA/` - Contains generated automata
- `target-DRA/` - Contains target automata (used in the experiments) to be learned
- `learned-DRA/` - Contains learned automata and log files

---

## Learning $L_n$ Languages

This section describes how to run experiments for learning the language $L_n$ for $n = 1, 2, \ldots, 25$, where $L_n$ contains words that are strictly increasing or decreasing and have length $n$.

### Prerequisites

See the "Prerequisites" section above for setting up a virtual environment and installing required packages.

### 1. Generate $L_n$ Automata

**Script:** `Ln/generate_ln_batch.py`

This script generates $L_n$ automata for $n = 1, 2, \ldots, 25$ and saves them to `generated-DRA/`.

**Usage:**
```bash
cd experiments/Ln
python generate_ln_batch.py
```

**What it does:**
1. Generates $L_n$ automata for $n = 1$ to $n = 25$
2. Saves generated automata to `generated-DRA/L{n}.txt`

**Output:**
- Generated automata saved to `generated-DRA/L{n}.txt` for each $n$

### 2. Learn $L_n$ Automata

**Script:** `Ln/learn_ln_batch.py`

This script learns automata from `target-DRA/` and saves results to `learned-DRA/`.

**Usage:**
```bash
cd experiments/Ln
python learn_ln_batch.py
```

**What it does:**
1. Reads automata from `target-DRA/L{n}.txt` files
2. Learns each automaton using `ralt_quiet.py`
3. Saves learned automata and log files to `learned-DRA/`
4. Records timing information for each learning process

**Output:**
- Learned automata: `learned-DRA/L{n}_learned.txt`
- Log files: `learned-DRA/L{n}.log`

### 3. Plot $L_n$ Statistics

**Script:** `Ln/plot_ln.py`

This script generates plots showing learning statistics (EQ, MQ, MM) vs $n$ for $L_n$ languages.

**Usage:**
```bash
cd experiments/Ln
# Make sure virtual environment is activated and matplotlib/numpy are installed
source ../random-DRA/venv/bin/activate  # if not already activated
python plot_ln.py
```

**What it does:**
1. Reads log files from `learned-DRA/` directory
2. Parses query counts (EQ, MQ, MM) for each $n$
3. Generates 2 separate plots:
   - `query_statistics_eq_mm.png` - Equivalence and Memorability Queries vs $n$
   - `query_statistics_mq.png` - Membership Queries vs $n$

**Output:**
- Two PNG files saved in `learned-DRA/` directory

### 4. Display Statistics Table

**Script:** `Ln/print_stats.py`

**Usage:**
```bash
cd experiments/Ln
python print_stats.py
```

**What it does:**
Displays a table with states, transitions, query counts (EQ, MQ, MM), and learning time for each $n$.

---

## Learning $L_{mid}$ and $L_{rep}$

This section describes how to learn the specific languages $L_{mid}$ and $L_{rep}$ recognized by the DRA in `Lmid.txt` and the DRA in `Lrep.txt`, respectively.

### Learning $L_{mid}$

**Location:** `experiments/Lmid/Lmid.txt`

To learn $L_{mid}$:

```bash
cd experiments/Lmid
python ../../ralt.py --inp Lmid.txt --out Lmid_learned.txt > Lmid.log 2>&1
```

**Output:**
- Learned automaton: `Lmid_learned.txt`
- Log file: `Lmid.log`

### Learning $L_{rep}$

**Location:** `experiments/Lrep/Lrep.txt`

To learn $L_{rep}$:

```bash
cd experiments/Lrep
python ../../ralt.py --inp Lrep.txt --out Lrep_learned.txt > Lrep.log 2>&1
```

**Output:**
- Learned automaton: `Lrep_learned.txt`
- Log file: `Lrep.log`

---

## Learning Randomly Generated DRAs

This section describes how to run experiments for learning randomly generated deterministic register automata.

### 1. Generate Random DRAs

**Script:** `random-DRA/generate_random_DRA.py`

This script generates random Register Automata, learns them, and saves the learned automata to `generated-DRA/`.

**Usage:**
```bash
cd experiments/random-DRA
python generate_random_DRA.py
```

**What it does:**
1. Generates target automata of various sizes
2. Learns each target automaton using `ralt.py`
3. Saves learned automata to `generated-DRA/size{N}/` if the hypothesis size is a multiple of 5 or in target_sizes
4. Tracks progress and stops when enough automata are collected for each target size

**Output:**
- Learned automata saved to `generated-DRA/size{N}/seed{SEED}_learned.txt`

### 2. Learn the Generated DRAs

**Script:** `random-DRA/learn_batch.py`

This script learns automata from `target-DRA/` and saves results to `learned-DRA/`.

**Usage:**
```bash
cd experiments/random-DRA
python learn_batch.py
```

**What it does:**
1. Reads automata from `target-DRA/size{N}/` directories
2. Learns each automaton using `ralt_quiet.py`
3. Saves learned automata and log files to `learned-DRA/size{N}/`
4. Records timing information in `learned-DRA/timing.log`
5. Limits to at most 50 automata per size

**Output:**
- Learned automata: `learned-DRA/size{N}/seed{SEED}_learned.txt`
- Log files: `learned-DRA/size{N}/seed{SEED}_learned.log`
- Timing log: `learned-DRA/timing.log`

### 3. Plot Figures

**Script:** `random-DRA/plot_learned.py`

This script generates plots showing learning statistics (EQ, MQ, MM, Time) vs automaton size.

**Usage:**
```bash
cd experiments/random-DRA
# Make sure virtual environment is activated and matplotlib/numpy are installed
source venv/bin/activate  # if not already activated
python plot_learned.py
```

**What it does:**
1. Reads log files from `learned-DRA/size{N}/` directories
2. Parses query counts (EQ, MQ, MM) and timing information
3. Calculates averages for each size
4. Generates 4 separate plots:
   - `avg_eq_vs_size.png` - Average Equivalence Queries vs Size
   - `avg_mq_vs_size.png` - Average Membership Queries vs Size
   - `avg_mm_vs_size.png` - Average Memorability Queries vs Size
   - `avg_time_vs_size.png` - Average Learning Time vs Size

**Output:**
- Four PNG files saved in `learned-DRA/` directory

### 4. Display Statistics Table

**Script:** `random-DRA/print_stats.py`

**Usage:**
```bash
cd experiments/random-DRA
python print_stats.py
```

**What it does:**
Displays a table with average states, transitions, query counts (EQ, MQ, MM), and total time per size.


## General Notes

- All scripts should be run from their respective experiment directories (`experiments/random-DRA/` or `experiments/Ln/`)
- The scripts automatically create necessary subdirectories
- Temporary files are created in the current directory and cleaned up automatically
- Log files contain information (automata size, number of queries for each query type) about the learning outcome
- For random-DRA experiments, the `learn_batch.py` script limits to 50 automata per size to avoid excessive computation

<!-- ## Troubleshooting

**Import errors (numpy/matplotlib not found):**
- Make sure the virtual environment is activated: `source venv/bin/activate`
- Install packages: `pip install numpy matplotlib`

**Script not found errors:**
- Make sure you're in the correct directory: `cd experiments/random-DRA`
- Check that the script file exists: `ls *.py`

**Permission errors:**
- Make scripts executable if needed: `chmod +x *.py` -->

