# partitioner.py
"""
Implements the hybrid circuit partitioning algorithm for the 2-Fold Synthesizer project.

This script takes a collapsed circuit graph (as a NetworkX object saved in a 
.gpickle file) and partitions it using a hybrid approach:
1. Coarse Partitioning: Uses K-way Spectral Clustering to find functionally
   related clusters of gates.
2. Boundary Refinement: Iteratively applies the Kernighan-Lin (KL) algorithm
   to pairs of adjacent partitions to minimize the cut size (wire crossings).
3. I/O Balancing: Performs a final greedy pass to improve I/O balance for
   each partition without significantly increasing the cut size.

To use this script:
1. First, generate the collapsed graph using your team's verilog_to_graph.py script:
   python verilog_to_graph.py your_circuit.v --collapse-wires -s circuit_graph.gpickle

2. Then, run this script on the generated graph file:
   python partitioner.py circuit_graph.gpickle --target-size 150 --kl-iter 10
"""

import argparse
import math
import pickle
import itertools
from collections import defaultdict

import networkx as nx
import numpy as np
from sklearn.cluster import SpectralClustering


def _calculate_cut_size(graph: nx.DiGraph, partitions: list[set]) -> int:
    """Calculates the total number of edges between all partitions."""
    cut_size = 0
    # Create a mapping from node to its partition index for quick lookups
    node_to_partition = {node: i for i, p in enumerate(partitions) for node in p}
    
    for u, v in graph.edges():
        if node_to_partition.get(u) != node_to_partition.get(v):
            cut_size += 1
            
    return cut_size

def _get_io_for_partition(graph: nx.DiGraph, partition_nodes: set) -> tuple[int, int]:
    """Calculates the number of input and output signals for a single partition."""
    inputs = set()
    outputs = set()
    
    for node in partition_nodes:
        # Check predecessors for external inputs
        for pred in graph.predecessors(node):
            if pred not in partition_nodes:
                inputs.add(pred)
        # Check successors for external outputs
        for succ in graph.successors(node):
            if succ not in partition_nodes:
                outputs.add(succ)
                
    return len(inputs), len(outputs)

def _find_adjacent_partitions(graph: nx.DiGraph, partitions: list[set]) -> list[tuple[int, int]]:
    """Finds pairs of partition indices that have edges between them."""
    adj_pairs = set()
    
    for i, part_A in enumerate(partitions):
        for j, part_B in enumerate(partitions):
            if i >= j:
                continue
            
            # Use itertools.product for an efficient cartesian product of nodes
            is_adjacent = any(
                graph.has_edge(u, v) or graph.has_edge(v, u)
                for u, v in itertools.product(part_A, part_B)
            )
            
            if is_adjacent:
                adj_pairs.add((i, j))
                
    return list(adj_pairs)

def hybrid_partitioner(
    graph: nx.DiGraph, 
    target_partition_size: int, 
    kl_max_iter: int = 10,
    io_balance_alpha: float = 0.1
) -> list[set]:
    """
    Executes the full hybrid partitioning algorithm.

    Args:
        graph (nx.DiGraph): The collapsed circuit graph to partition.
        target_partition_size (int): The desired average size for each partition.
        kl_max_iter (int): The max number of iterations for each Kernighan-Lin run.
        io_balance_alpha (float): A weighting factor for how strongly to prioritize
                                 I/O balance over cut size during the final pass.

    Returns:
        list[set]: A list where each element is a set of nodes representing a partition.
    """
    num_nodes = graph.number_of_nodes()
    if num_nodes == 0:
        return []

    # === 1. Coarse Partitioning with Spectral Clustering ===
    print(f"🔬 1. Starting Coarse Partitioning (Spectral Clustering)...")
    
    # Calculate k, the number of partitions
    k = math.ceil(num_nodes / target_partition_size)
    if k < 2:
        print("   - Graph is too small to partition further. Returning single partition.")
        return [set(graph.nodes())]

    print(f"   - Target partitions (k): {k}")
    
    # Spectral clustering works on the adjacency matrix of an undirected graph
    # to capture the notion of 'closeness' or 'community'.
    undirected_graph = graph.to_undirected()
    adj_matrix = nx.to_scipy_sparse_array(undirected_graph, format='csr')
    
    # Fix for scikit-learn on Windows: force sparse matrix indices to be 32-bit
    adj_matrix.indices = adj_matrix.indices.astype(np.int32)
    adj_matrix.indptr = adj_matrix.indptr.astype(np.int32)
    
    sc = SpectralClustering(
        n_clusters=k, 
        assign_labels='kmeans', 
        affinity='precomputed',
        random_state=42
    )
    labels = sc.fit_predict(adj_matrix)
    
    partitions = [set() for _ in range(k)]
    node_list = list(undirected_graph.nodes())
    for i, node in enumerate(node_list):
        partitions[labels[i]].add(node)
    
    print(f"   - Initial cut size: {_calculate_cut_size(graph, partitions)}")

    # === 2. Boundary Refinement with Kernighan-Lin ===
    print(f"\n⚡ 2. Starting Boundary Refinement (Kernighan-Lin)...")
    print(f"   - KL max iterations per pair: {kl_max_iter}")

    # Find which partitions are physically connected
    adjacent_pairs = _find_adjacent_partitions(graph, partitions)
    print(f"   - Found {len(adjacent_pairs)} adjacent partition pairs to refine.")

    for i, j in adjacent_pairs:
        # Create a subgraph containing only the nodes from the two adjacent partitions
        part_A, part_B = partitions[i], partitions[j]
        subgraph_nodes = list(part_A.union(part_B))
        subgraph = graph.subgraph(subgraph_nodes).to_undirected()

        # Run KL bisection to re-partition this subgraph
        # The seed ensures that the initial partition is consistent
        refined_A, refined_B = nx.community.kernighan_lin_bisection(
            subgraph, max_iter=kl_max_iter, seed=42
        )
        
        # Update the main partitions list with the refined sets
        partitions[i] = refined_A
        partitions[j] = refined_B
        
    print(f"   - Cut size after KL refinement: {_calculate_cut_size(graph, partitions)}")
    
    # === 3. I/O Balancing (Greedy Post-Processing) ===
    print(f"\n⚖️  3. Starting I/O Balancing...")
    
    # This is a greedy approach. It repeatedly finds the best node to move
    # based on a cost function that considers both cut size and I/O balance.
    node_to_partition = {node: i for i, p in enumerate(partitions) for node in p}

    # Failsafe: Limit the number of I/O balancing iterations. One pass per node is a reasonable upper bound.
    MAX_IO_BALANCE_ITERATIONS = graph.number_of_nodes()
    for iteration in range(MAX_IO_BALANCE_ITERATIONS): # Failsafe to prevent infinite loops
        best_move = {'node': None, 'target_partition': -1, 'cost_improvement': -np.inf}
        
        # Find all nodes on the boundaries of partitions
        boundary_nodes = {
            node for u, v in graph.edges() 
            for node in (u, v) 
            if node_to_partition.get(u) != node_to_partition.get(v)
        }

        if not boundary_nodes:
            break # No more boundary nodes to move
            
        for node in boundary_nodes:
            current_part_idx = node_to_partition[node]
            
            # Find which partitions this node is connected to
            neighbor_partitions = {
                node_to_partition[neighbor] 
                for neighbor in nx.all_neighbors(graph, node) 
                if neighbor in node_to_partition
            }
            
            for target_part_idx in neighbor_partitions:
                if target_part_idx == current_part_idx:
                    continue

                # --- Calculate the cost of moving this node ---
                # 1. Change in Cut Size (Gain)
                cut_gain = 0
                for neighbor in nx.all_neighbors(graph, node):
                    if not neighbor in node_to_partition: continue
                    
                    neighbor_part_idx = node_to_partition[neighbor]
                    if neighbor_part_idx == current_part_idx:
                        cut_gain -= 1 # Moving away from an internal node increases cut
                    elif neighbor_part_idx == target_part_idx:
                        cut_gain += 1 # Moving towards an external node decreases cut
                
                # 2. Change in I/O Imbalance
                io_before_move = 0
                io_after_move = 0
                
                # Analyze partitions affected by the move
                for part_idx in {current_part_idx, target_part_idx}:
                    # Simulate the state before and after the move for this partition
                    nodes_before = partitions[part_idx]
                    if part_idx == current_part_idx:
                        nodes_after = nodes_before - {node}
                    else: # target_part_idx
                        nodes_after = nodes_before | {node}

                    i_before, o_before = _get_io_for_partition(graph, nodes_before)
                    i_after, o_after = _get_io_for_partition(graph, nodes_after)
                    
                    io_before_move += abs(i_before - o_before)
                    io_after_move += abs(i_after - o_after)

                io_gain = io_before_move - io_after_move
                
                # Total cost combines cut size gain and I/O balance gain
                total_gain = cut_gain + io_balance_alpha * io_gain
                
                if total_gain > best_move['cost_improvement']:
                    best_move = {
                        'node': node, 
                        'target_partition': target_part_idx,
                        'cost_improvement': total_gain
                    }

        if best_move['cost_improvement'] > 0:
            # Perform the best move found in this pass
            node_to_move = best_move['node']
            target_idx = best_move['target_partition']
            current_idx = node_to_partition[node_to_move]

            partitions[current_idx].remove(node_to_move)
            partitions[target_idx].add(node_to_move)
            node_to_partition[node_to_move] = target_idx
        else:
            # No move provides improvement, so we are done
            break 
            
    print(f"   - Final cut size after I/O balancing: {_calculate_cut_size(graph, partitions)}")
    
    # Filter out any empty partitions that may have been created
    final_partitions = [p for p in partitions if p]
    
    return final_partitions


def main():
    """Main function to run the partitioner from the command line."""
    parser = argparse.ArgumentParser(description="Hybrid Circuit Partitioner")
    parser.add_argument(
        "graph_file", 
        help="Path to the input .gpickle file containing the NetworkX graph."
    )
    parser.add_argument(
        "--target-size", 
        type=int, 
        required=True, 
        help="The target number of nodes per partition."
    )
    parser.add_argument(
        "--kl-iter", 
        type=int, 
        default=10, 
        help="Max iterations for the Kernighan-Lin algorithm. (Default: 10)"
    )
    parser.add_argument(
        "--io-factor", 
        type=float, 
        default=0.1, 
        help="Weighting factor for I/O balance vs. cut size. (Default: 0.1)"
    )
    parser.add_argument(
        "-o", "--output-file", 
        help="Path to save the final partition data as a text file."
    )
    args = parser.parse_args()

    # Load the graph
    try:
        with open(args.graph_file, 'rb') as f:
            circuit_graph = pickle.load(f)
        print(f"✅ Graph '{args.graph_file}' loaded successfully.")
        print(f"   - Nodes: {circuit_graph.number_of_nodes()}, Edges: {circuit_graph.number_of_edges()}")
    except FileNotFoundError:
        print(f"❌ Error: The file '{args.graph_file}' was not found.")
        return
    except Exception as e:
        print(f"❌ Error: Could not load the graph file. Reason: {e}")
        return

    # Run the partitioning algorithm
    final_partitions = hybrid_partitioner(
        circuit_graph, 
        args.target_size, 
        args.kl_iter,
        args.io_factor
    )

    # Print and save results
    print("\n" + "="*30)
    print("      PARTITIONING COMPLETE")
    print("="*30)
    print(f"Total Partitions Created: {len(final_partitions)}\n")
    
    output_lines = []
    for i, p in enumerate(final_partitions):
        num_inputs, num_outputs = _get_io_for_partition(circuit_graph, p)
        line1 = f"--- Partition {i} ---"
        line2 = f"  - Size: {len(p)} nodes"
        line3 = f"  - I/O: {num_inputs} inputs, {num_outputs} outputs"
        print(line1, line2, line3, sep='\n')
        if args.output_file:
            output_lines.append(line1)
            output_lines.append(line2)
            output_lines.append(line3)
            output_lines.append(f"  - Nodes: {sorted(list(p))}\n")
    
    if args.output_file:
        try:
            with open(args.output_file, 'w') as f:
                f.write('\n'.join(output_lines))
            print(f"\n💾 Partition data saved to: {args.output_file}")
        except Exception as e:
            print(f"\n❌ Could not save output file. Reason: {e}")


if __name__ == "__main__":
    main()
