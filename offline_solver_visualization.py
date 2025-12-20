import networkx as nx
import matplotlib.pyplot as plt

def draw_paging_graph(G, requests):
    """
    Visualizes the Min-Cost Flow graph for Paging.
    """
    pos = {}
    T = len(requests)
    spacing = 3  # Spacing between time steps

    # --- 1. Define Node Positions ---
    # Source/Sink
    pos['source'] = (-2, 0)
    pos['sink'] = (spacing * T + 1, 0)

    # Time Step Nodes (Linear Layout)
    for i in range(T):
        # Input node (start of step t)
        pos[f"{i}_in"] = (spacing * i, 0)
        # Output node (end of step t) - placed slightly to the right
        pos[f"{i}_out"] = (spacing * i + 1, 0)

    plt.figure(figsize=(14, 6))

    # --- 2. Draw Nodes ---
    # Draw standard nodes
    nx.draw_networkx_nodes(G, pos, node_size=600, node_color='lightgrey', edgecolors='black')
    
    # Highlight Source/Sink
    nx.draw_networkx_nodes(G, pos, nodelist=['source', 'sink'], node_color='#ffcc00', node_size=700)
    
    # Labels
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold')

    # --- 3. Draw Edges by Type ---
    edges = G.edges(data=True)

    # A. Bottleneck Edges (Red, Straight)
    # These enforce the capacity k at each step
    bn_edges = [(u, v) for u, v, d in edges if d.get('type') == 'bottleneck']
    nx.draw_networkx_edges(G, pos, edgelist=bn_edges, edge_color='#d62728', width=2.5, arrowstyle='-|>', arrowsize=20)

    # B. Backbone Edges (Black, Straight)
    # These carry empty/unused slots to the next step
    bb_edges = [(u, v) for u, v, d in edges if d.get('type') == 'backbone']
    nx.draw_networkx_edges(G, pos, edgelist=bb_edges, edge_color='black', width=1.5, style='solid', alpha=0.6)

    # C. Interval Edges (Green, Curved)
    # These represent keeping a page in cache (Savings)
    # We curve them so they don't overlap the backbone
    iv_edges = [(u, v) for u, v, d in edges if d.get('type') == 'interval']
    nx.draw_networkx_edges(
        G, pos, edgelist=iv_edges, edge_color='#2ca02c', width=2, 
        style='dashed', connectionstyle="arc3,rad=-0.4", arrowsize=15
    )
    
    # D. Bypass/Circulation Edges (Faint)
    other_edges = [(u, v) for u, v, d in edges if d.get('type') is None]
    nx.draw_networkx_edges(G, pos, edgelist=other_edges, edge_color='grey', style='dotted', alpha=0.3, connectionstyle="arc3,rad=0.5")

    # --- 4. Draw Edge Labels ---
    edge_labels = {}
    for u, v, d in edges:
        if d.get('type') == 'bottleneck':
            # Show Capacity (k-1)
            edge_labels[(u, v)] = f"Cap:{d['capacity']}"
        elif d.get('type') == 'interval':
            # Show Savings (Weight)
            edge_labels[(u, v)] = f"Save:{abs(d['weight'])}"
            
    # Draw labels with a background box for readability
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, 
                                 bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

    plt.title("Min-Cost Flow Graph: Paging with Variable Cache", fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# --- Integration Example ---
if __name__ == "__main__":
    from offline_solver import OfflineOptimalSolver
    from paging_model import Page, Request
    
    # [Same setup code as main.py...]
    pages = [Page("A", 1), Page("B", 2), Page("C", 10)]
    reqs = [Request(i, pages[pid], i+1) for i, pid in enumerate([0, 1, 2, 0])] # A, B, C, A
    caps = {1: 2, 2: 2, 3: 1, 4: 2}

    solver = OfflineOptimalSolver(pages, reqs, caps)
    
    # Build the graph (accessing private method for visualization)
    G = solver._build_graph()
    
    # Draw it
    draw_paging_graph(G, reqs)
