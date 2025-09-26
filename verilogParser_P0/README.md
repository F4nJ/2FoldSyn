Certainly. Here is the updated README file, revised to include the new `--collapse-wires` feature, an explanation of the two graph representations, and a corresponding example.

-----

# Verilog to NetworkX Graph Converter 📜➡️📊

This Python script parses a simple gate-level Verilog netlist and converts it into a directed graph using the NetworkX library. It can generate a visual representation of the circuit or save the graph object for further programmatic analysis.

-----

## Features

  * **Parses Basic Verilog**: Understands `input`, `output`, `wire` declarations and standard gate instantiations (`and`, `or`, `not`, etc.).
  * **Two Graph Representations**: Can generate a detailed graph with explicit wire nodes or a compact version where wires are collapsed into direct edges.
  * **Rich Visualization**: Generates a color-coded plot of the circuit using Matplotlib for easy understanding.
      * 🟩 **Green**: Primary Inputs (PI)
      * 🟥 **Red**: Primary Outputs (PO)
      * 🟦 **Blue**: Logic Gates
      * 🐘 **Gray**: Wires (in default mode)
  * **Flexible Output**:
      * Display the graph interactively.
      * Save the visualization to an image file (e.g., `.png`).
      * Save the graph object to a file to be loaded back into Python.

-----

## Requirements

To use this script, you need Python 3.6+ and a few packages. You also need to install the Graphviz layout engine for clean, hierarchical graph layouts.

1.  **Install Python Packages**:

    ```bash
    pip install networkx matplotlib pydot
    ```

2.  **Install Graphviz**: This is a system dependency, not a Python package.

      * **Website**: [https://graphviz.org/download/](https://graphviz.org/download/)
      * **macOS**: Use Homebrew: `brew install graphviz`
      * **Linux (Ubuntu/Debian)**: Use apt: `sudo apt-get install graphviz`

-----

## Usage

Run the script from your terminal. The basic command structure is:

```bash
python verilog_to_graph.py <VERILOG_FILE> [OPTIONS]
```

### Arguments

  * `verilog_file`: **(Required)** The path to the input Verilog file.
  * `-o, --output_image <FILENAME>`: **(Optional)** Saves the graph visualization to the specified image file.
  * `-s, --save_graph <FILENAME>`: **(Optional)** Saves the NetworkX graph object to the specified file (e.g., `circuit.pkl`).
  * `--collapse-wires`: **(Optional Flag)** Collapses wire nodes into direct edges from source to sink. This is the default situation.
  * `--expand-wires`: **(Optional Flag)** Expands wire nodes into a node between source and sink.


### Examples

Let's use a sample Verilog file named `example.v`:

```verilog
// example.v
module example(a, b, c, y);
  input a, b, c;
  output y;
  wire n1, n2;

  and U1 (n1, a, b);
  not U2 (n2, c);
  or  U3 (y, n1, n2);

endmodule
```

1.  **Display the default graph interactively**:

    ```bash
    python verilog_to_graph.py example.v
    ```

2.  **Save the default graph as a PNG image**:

    ```bash
    python verilog_to_graph.py example.v -o default_graph.png
    ```

3.  **Generate and save the compact graph by collapsing wires**:

    ```bash
    python verilog_to_graph.py example.v --collapse-wires -o collapsed_graph.png
    ```

3.  **Generate and save the compact graph by expanding wires**:

    ```bash
    python verilog_to_graph.py example.v --expand-wires -o expand_graph.png
    ```

4.  **Save the graph object**:

    ```bash
    python verilog_to_graph.py example.v -s my_graph.pkl
    ```

-----

## Graph Representations 🤔

The script can generate two types of graphs depending on your analysis needs.

### Method 1: Wires as Nodes (`--expand-wires`)

This method creates a graph that explicitly represents every element from the Verilog file. Wires are treated as their own nodes.

**Pros**: High fidelity to the original netlist; easy to analyze properties like fan-out.
**Cons**: Results in a larger, more complex graph; logical paths between gates are indirect.

### Method 2: Wires as Edges (`--collapse-wires` or default)

This method abstracts away the wires, creating direct edges from a source gate to all of its sink gates.

**Pros**: Creates a compact graph that shows direct logical flow; simpler for pathfinding algorithms and GNNs.
**Cons**: The explicit concept of a named "wire" is lost.

-----

## Working with Saved Graph Objects

You can load the saved graph object using Python's `pickle` module for further analysis.

```python
import pickle
import networkx as nx

path = "my_graph.pkl"

with open(path, "rb") as f:
    G = pickle.load(f)

print(f"Loaded graph with {G.number_of_nodes()} nodes.")
```

-----

## Node Attributes in the Graph 🏷️

Each node has attributes describing what it represents. **Note**: `wire` nodes onlt exist if you use the `--expand-wires` flag.

  * **Gate Nodes**: `type: 'gate'`, `func: 'and'` (or `'or'`, `'not'`, etc.)
  * **Signal Nodes**:
      * **PI Nodes**: `type: 'PI'`
      * **PO Nodes**: `type: 'PO'`
      * **Wire Nodes**: `type: 'wire'` (only in default mode)