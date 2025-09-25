
# Verilog to NetworkX Graph Converter 📜➡️📊

This Python script parses a simple gate-level Verilog netlist and converts it into a directed graph using the NetworkX library. It can generate a visual representation of the circuit or save the graph object for further programmatic analysis.



---

## Features

* **Parses Basic Verilog**: Understands `input`, `output`, `wire` declarations and standard gate instantiations (`and`, `or`, `not`, `nand`, `nor`, `xor`, `xnor`).
* **Graph Generation**: Creates a `networkx.DiGraph` object where both gates and signals (wires) are nodes.
* **Rich Visualization**: Generates a color-coded plot of the circuit using Matplotlib for easy understanding.
    * 🟩 **Green**: Primary Inputs (PI)
    * 🟥 **Red**: Primary Outputs (PO)
    * 🟦 **Blue**: Logic Gates
    * 🐘 **Gray**: Wires
* **Flexible Output**:
    * Display the graph interactively.
    * Save the visualization to an image file (e.g., `.png`, `.jpg`, `.svg`).
    * Save the graph object to a file (`.gpickle`) to be loaded back into Python.

---

## Requirements

To use this script, you need Python 3.6+ and a few packages. You also need to install the Graphviz layout engine, which is used to create a clean, hierarchical graph layout.

1.  **Install Python Packages**:
    ```bash
    pip install networkx matplotlib pydot
    ```

2.  **Install Graphviz**: This is a system dependency, not a Python package.
    * **Website**: [https://graphviz.org/download/](https://graphviz.org/download/)
    * **Windows**: You can use `winget install graphviz` or download from the site and add it to your system's PATH.
    * **macOS**: Use Homebrew: `brew install graphviz`
    * **Linux (Ubuntu/Debian)**: Use apt: `sudo apt-get install graphviz`

---

## Usage

Run the script from your terminal. The basic command structure is:


Run the script from your terminal. The basic command structure is:

```bash
python verilog_to_graph.py <VERILOG_FILE> [OPTIONS]
````

### Arguments

  * `verilog_file`: **(Required)** The path to the input Verilog file.
  * `-o, --output_image <FILENAME>`: **(Optional)** Saves the graph visualization to the specified image file.
  * `-s, --save_graph <FILENAME>`: **(Optional)** Saves the NetworkX graph object to the specified file (e.g., `circuit.gpickle`).

<!-- end list -->



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
````

1.  **Display the graph interactively** (no output files are saved):

    ```bash
    python verilog_to_graph.py example.v
    ```

2.  **Save the graph as a PNG image**:

    ```bash
    python verilog_to_graph.py example.v -o circuit_diagram.png
    ```

3.  **Save the NetworkX graph object for later use**:

    ```bash
    python verilog_to_graph.py example.v -s my_graph.pkl
    ```

4.  **Save both the image and the graph object**:

    ```bash
    python verilog_to_graph.py example.v -o circuit_diagram.png -s my_graph.pkl
    ```

<!-- end list -->



## Working with Saved Graph Objects

You can easily load "pickle" it into another script or an interactive session for analysis.

```python
import pickle
import networkx as nx # You still need to import networkx

# Define the path to your saved graph file
path = "my_graph.pkl"

# Open the file in binary read mode
with open(path, "rb") as f:
    # Load the object from the file
    G = pickle.load(f)

# You can now analyze it
print(f"Loaded graph with {G.number_of_nodes()} nodes.")

# Find all 'and' gates
and_gates = [n for n, d in G.nodes(data=True) if d.get('func') == 'and']
print(f"Found 'and' gates: {and_gates}")

# Find the path from an input to an output
paths = nx.all_simple_paths(G, source='a', target='y')
print(f"Paths from 'a' to 'y': {list(paths)}")
```

-----

## Node Attributes in the Graph 🏷️

Every node has a **name** (its unique identifier) and a dictionary of attributes. The primary attributes assigned by the script are `type` and `func`.

### 1\. Gate Nodes

These represent the logic gates from the Verilog netlist.

  * **Node Name**: The instance name of the gate (e.g., `U1`, `U3`).
  * **`type` Attribute**: The value is always `'gate'`.
  * **`func` Attribute**: The value is a string specifying the gate's logic function (e.g., `'and'`, `'or'`, `'not'`).

### 2\. Signal Nodes

These represent the inputs, outputs, and internal connections.

  * **Primary Input (PI) Nodes**

      * **Node Name**: The name of an input port (e.g., `a`, `b`, `c`).
      * **`type` Attribute**: The value is always `'PI'`.

  * **Primary Output (PO) Nodes**

      * **Node Name**: The name of an output port (e.g., `y`).
      * **`type` Attribute**: The value is always `'PO'`.

  * **Wire Nodes**

      * **Node Name**: The name of an internal wire (e.g., `n1`, `n2`).
      * **`type` Attribute**: The value is always `'wire'`.

-----

## How to Access Node Attributes

You can easily access and inspect these attributes programmatically. The `G.nodes(data=True)` method is perfect for this, as it lets you loop through all nodes and their associated attribute dictionaries.

Here's a code snippet showing how to inspect the nodes of a loaded graph:

```python
import pickle
import networkx as nx # You still need to import networkx

# Define the path to your saved graph file
path = "my_graph.pkl"

# Open the file in binary read mode
with open(path, "rb") as f:
    # Load the object from the file
    G = pickle.load(f)

print("--- Inspecting Graph Nodes ---")

# Loop through each node and its attributes
for node_name, attributes in G.nodes(data=True):
    # The 'attributes' variable is a dictionary
    node_type = attributes.get('type')

    if node_type == 'gate':
        gate_function = attributes.get('func')
        print(f"Node '{node_name}' is a GATE with function: {gate_function}")
    elif node_type in ['PI', 'PO', 'wire']:
        print(f"Node '{node_name}' is a SIGNAL of type: {node_type}")

```