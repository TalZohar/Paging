import networkx as nx
import matplotlib.pyplot as plt

def visualize_solution(G, requests, flow_dict=None):
    pos = {}
    labels = {}
    
    # Identify layers
    layers = [n[0] for n in G.nodes if isinstance(n, tuple)]
    if not layers: return
    max_layer = max(layers)
    
    scale_x = 4.0
    scale_y = 1.0
    
    pos['source'] = (-scale_x, 0)
    pos['sink'] = ((max_layer + 1) * scale_x, 0)
    labels['source'] = 'S'
    labels['sink'] = 'T'
    
    for node in G.nodes:
        if isinstance(node, str): continue
        
        # Node structure: (layer, type, index_or_suffix)
        layer = node[0]
        ntype = node[1]
        
        x = layer * scale_x
        y = 0
        
        if 'page' in ntype:
            idx = node[2]
            base_y = (idx + 1) * scale_y + 1
            if ntype == 'page_in':
                y = base_y + 0.2
                labels[node] = f"P{idx}_in"
            else:
                y = base_y - 0.2
                x += 0.3 # slight offset
                labels[node] = f"P{idx}_out"
                
        elif 'slot' in ntype:
            if ntype == 'slot_in':
                y = -1.5
                labels[node] = "S_in"
            else:
                y = -2.5
                x += 0.3
                labels[node] = "S_out"
            
        pos[node] = (x, y)
        
    plt.figure(figsize=(18, 10))
    
    # Draw Nodes
    nx.draw_networkx_nodes(G, pos, node_size=250, node_color='#eeeeee', edgecolors='gray')
    nx.draw_networkx_nodes(G, pos, nodelist=['source', 'sink'], node_color='orange', node_size=500)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=7)
    
    # Process Edges
    active_edges = []
    inactive_edges = []
    
    for u, v in G.edges:
        is_active = False
        if flow_dict and u in flow_dict and v in flow_dict[u]:
            if flow_dict[u][v] > 0:
                is_active = True
        
        if is_active:
            active_edges.append((u, v))
        else:
            inactive_edges.append((u, v))
    
    # Draw Inactive
    
    nx.draw_networkx_edges(G, pos, edgelist=inactive_edges, edge_color='#e0e0e0', width=0.5, arrows=False, alpha=0.4)
    
    # Draw Active
    nx.draw_networkx_edges(G, pos, edgelist=active_edges, edge_color='blue', width=2.0, arrowsize=12)
    
    plt.title("Layered Solution (Split Nodes for Pages and Slots)", fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.show()
