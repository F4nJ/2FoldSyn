# Phase 1: Hybrid Circuit Partitioner

This module contains the Python script `partitioner.py`, which implements the hybrid circuit partitioning algorithm outlined in the research plan.

## Description

The script partitions a given circuit graph into smaller, functionally-related subgraphs. This is a critical preprocessing step for the DNAS synthesis phase. The algorithm uses a three-stage process to ensure high-quality partitions:

* **1. Coarse Partitioning:** Employs K-way Spectral Clustering to identify the main functional clusters in the circuit.
* **2. Boundary Refinement:** Uses the Kernighan-Lin (KL) algorithm to refine the boundaries between partitions, minimizing the number of interconnecting wires (cut size).
* **3. I/O Balancing:** Performs a final greedy pass to adjust boundary nodes, seeking a better balance between the number of inputs and outputs for each partition.

## Prerequisites

This script requires a collapsed circuit graph as input. This graph must be a **NetworkX DiGraph object** saved in a `.gpickle` file.

You can generate this file using the `verilogParser_P0` module:
```bash
python ../verilogParser_P0/verilog_to_graph.py <input_verilog>.v --collapse-wires -s <output_graph>.gpickle
```

## Usage

The script is run from the command line and accepts several arguments to control the partitioning process.

```bash
python partitioner.py <graph_file> --target-size <size> [options]
```

**Arguments:**

* `graph_file`: (Required) The path to the input `.gpickle` file.
* `--target-size`: (Required) The desired average number of nodes for each partition.
* `--kl-iter`: (Optional) The maximum number of iterations for each Kernighan-Lin run. Defaults to `10`.
* `--io-factor`: (Optional) A weighting factor for how strongly to prioritize I/O balance. Defaults to `0.1`.
* `-o, --output-file`: (Optional) The path to save the final partition data as a text file.

### Example

Here is an example of running the partitioner on the `c17` benchmark circuit, with all generated files placed in a `data/` subfolder.

```powershell
# From the partition_P1 directory:
python partitioner.py data/c17_graph.gpickle --target-size 4 -o data/c17_partitions.txt
```