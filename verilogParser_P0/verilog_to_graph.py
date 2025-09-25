import argparse
import re
import networkx as nx
import matplotlib.pyplot as plt

# You may need to install pydot and graphviz for the layout
# pip install pydot
# See: https://graphviz.org/download/
try:
    from networkx.drawing.nx_pydot import graphviz_layout
except ImportError:
    print("Warning: pydot and graphviz not found. Using a different layout.")
    def graphviz_layout(G, prog='dot'):
        return nx.spring_layout(G, seed=42)


# Regex patterns to parse Verilog netlists
INPUT_PATTERN = r"input\s+([^;]+);"
OUTPUT_PATTERN = r"output\s+([^;]+);"
WIRE_PATTERN = r"wire\s+([^;]+);"
GATE_INSTANCE_PATTERN = r"\s*\b(and|or|not|nand|nor|xor|xnor)\b\s+(\w+)\s*\(([^;]+)\);"

def create_graph_from_verilog(file_path):
    """
    Parses a simple Verilog netlist file and converts it into a NetworkX DiGraph.
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None

    content = content.replace('\\', '')
    G = nx.DiGraph()

    # Step 1: Parse and add all signal nodes (PIs, POs, Wires)
    for match in re.finditer(INPUT_PATTERN, content):
        signals = [s.strip() for s in match.group(1).split(',') if s.strip()]
        for signal in signals:
            G.add_node(signal, type='PI')

    for match in re.finditer(OUTPUT_PATTERN, content):
        signals = [s.strip() for s in match.group(1).split(',') if s.strip()]
        for signal in signals:
            if G.has_node(signal):
                G.nodes[signal]['type'] = 'PO'
            else:
                G.add_node(signal, type='PO')

    for match in re.finditer(WIRE_PATTERN, content):
        signals = [s.strip() for s in match.group(1).split(',') if s.strip()]
        for signal in signals:
            if not G.has_node(signal):
                G.add_node(signal, type='wire')

    # Step 2: Parse gates, add them as nodes, and create connections (edges)
    for match in re.finditer(GATE_INSTANCE_PATTERN, content):
        gate_type, instance_name, connections_str = match.groups()
        
        G.add_node(instance_name, type='gate', func=gate_type)

        connections = [c.strip() for c in connections_str.split(',')]
        output_signal = connections[0]
        input_signals = connections[1:]

        if not G.has_node(output_signal):
             G.add_node(output_signal, type='wire')
        G.add_edge(instance_name, output_signal)

        for input_signal in input_signals:
            if not G.has_node(input_signal):
                G.add_node(input_signal, type='wire')
            G.add_edge(input_signal, instance_name)

    return G

def visualize_graph(graph, file_name, output_image_path=None):
    """
    Creates a visualization of the circuit graph.
    Saves it to a file if a path is provided, otherwise displays it.
    """
    plt.figure(figsize=(15, 10))
    plt.title(f"Circuit Graph for {file_name}", size=15)

    pos = graphviz_layout(graph, prog='dot')

    node_colors = []
    for node in graph.nodes():
        node_type = graph.nodes[node].get('type', 'gate')
        color_map = {'PI': '#90ee90', 'PO': '#ffcccb', 'gate': '#add8e6', 'wire': '#d3d3d3'}
        node_colors.append(color_map.get(node_type, '#d3d3d3'))

    nx.draw(graph, pos, with_labels=True, node_color=node_colors, node_size=2500,
            font_size=8, font_weight='bold', arrows=True, arrowsize=20)

    gate_labels = {n: d['func'] for n, d in graph.nodes(data=True) if d.get('type') == 'gate'}
    nx.draw_networkx_labels(graph, pos, labels=gate_labels, font_color='black', font_size=7)

    # Save to file or show interactively
    if output_image_path:
        try:
            plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
            print(f"🖼️ Graph image saved to: {output_image_path}")
        except Exception as e:
            print(f"Could not save image file: {e}")
    else:
        plt.show()

def main():
    """
    Main function to handle command-line arguments and run the script.
    """
    parser = argparse.ArgumentParser(
        description="Convert a simple Verilog netlist into a NetworkX graph."
    )
    parser.add_argument("verilog_file", help="Path to the input Verilog file.")
    parser.add_argument(
        "-o", "--output_image",
        help="Path to save the output graph visualization (e.g., 'circuit.png')."
    )
    parser.add_argument(
        "-s", "--save_graph",
        help="Path to save the NetworkX graph object as a file (e.g., 'circuit.gpickle')."
    )
    args = parser.parse_args()

    circuit_graph = create_graph_from_verilog(args.verilog_file)

    if circuit_graph:
        print("✅ Verilog file parsed successfully!")
        print(f"📊 Graph contains {circuit_graph.number_of_nodes()} nodes and {circuit_graph.number_of_edges()} edges.")
        
        # Visualize the graph (either save or show)
        visualize_graph(circuit_graph, args.verilog_file, args.output_image)
        
        # Save the graph object if requested
        if args.save_graph:
            try:
                nx.write_gpickle(circuit_graph, args.save_graph)
                print(f"💾 NetworkX graph object saved to: {args.save_graph}")
            except Exception as e:
                print(f"Could not save graph object: {e}")

if __name__ == "__main__":
    main()