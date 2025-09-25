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

<!-- ## Requirements

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

--- -->

## Usage

Run the script from your terminal. The basic command structure is:

```bash
python verilog_to_graph.py <VERILOG_FILE> [OPTIONS]