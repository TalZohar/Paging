import networkx as nx
import matplotlib.pyplot as plt


def visualize_solution(G, requests, flow_dict=None):
    pos = {}

    labels = {}
    # Constants for recovering real costs from graph weights
    LARGE_VAL = 1_000_000
    # Threshold to decide if a weight includes the -LARGE reward
    # (Any weight smaller than -half_large definitely includes it)
    LARGE_THRESHOLD = -500_000

    # Identify layers
    layers = [n[0] for n in G.nodes if isinstance(n, tuple)]
    if not layers:
        return
    max_layer = max(layers)

    scale_x = 4.0
    scale_y = 1.0

    pos["source"] = (-scale_x, 0)
    pos["sink"] = ((max_layer + 1) * scale_x, 0)
    labels["source"] = "S"
    labels["sink"] = "T"

    for node in G.nodes:
        if isinstance(node, str):
            continue

        # Node structure: (layer, type, index_or_suffix)
        layer = node[0]
        ntype = node[1]

        x = layer * scale_x
        y = 0

        if "page" in ntype:
            idx = node[2]
            base_y = (idx + 1) * scale_y + 1
            if ntype == "page_in":
                y = base_y + 0.2
                labels[node] = f"P{idx}_in"
            else:
                y = base_y - 0.2
                x += 0.3  # slight offset
                labels[node] = f"P{idx}_out"

        elif "slot" in ntype:
            if ntype == "slot_in":
                y = -1.5
                labels[node] = "S_in"
            else:
                y = -2.5
                x += 0.3
                labels[node] = "S_out"

        pos[node] = (x, y)

    plt.figure(figsize=(18, 10))

    # Draw Nodes
    nx.draw_networkx_nodes(
        G, pos, node_size=250, node_color="#eeeeee", edgecolors="gray"
    )
    nx.draw_networkx_nodes(
        G, pos, nodelist=["source", "sink"], node_color="orange", node_size=500
    )
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=7)

    # Process Edges
    active_edges = []
    inactive_edges = []
    edge_cost_labels = {}

    for u, v, d in G.edges(data=True):
        is_active = False
        # Check if flow exists and is > 0 (using tolerance for floats)
        if flow_dict and u in flow_dict and v in flow_dict[u]:
            if flow_dict[u][v] > 0.9:
                is_active = True

        if is_active:
            active_edges.append((u, v))

            # --- Calculate real transition cost for label ---
            raw_weight = d.get("weight", 0)
            real_cost = 0.0

            # If weight is very negative, it means it includes the -LARGE reward.
            # Add LARGE back to get the actual page weight penalty.
            if raw_weight < LARGE_THRESHOLD:
                real_cost = float(raw_weight + LARGE_VAL)
            else:
                real_cost = float(raw_weight)

            # Only label positive costs (actual penalties) to reduce clutter.
            # Ignore 0-cost edges (holding pages, internal node edges).
            if real_cost > 0.001:
                # Format as integer if it's very close to one for cleaner labels
                if abs(real_cost - round(real_cost)) < 0.001:
                    cost_str = f"{int(round(real_cost))}"
                else:
                    cost_str = f"{real_cost:.1f}"
                edge_cost_labels[(u, v)] = cost_str

        else:
            inactive_edges.append((u, v))

    # Draw Inactive Edges (Faint background)
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=inactive_edges,
        edge_color="#e0e0e0",
        width=0.5,
        arrows=False,
        alpha=0.4,
    )

    # Draw Active Edges (Thick Blue)
    nx.draw_networkx_edges(
        G, pos, edgelist=active_edges, edge_color="blue", width=2.0, arrowsize=12
    )

    # Draw Edge Cost Labels
    # Use red text with a white box background for readability over edge lines
    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_cost_labels,
        font_size=9,
        font_color="red",
        bbox=dict(
            facecolor="white", edgecolor="none", alpha=0.7, boxstyle="round,pad=0.1"
        ),
    )

    plt.title(
        "Layered Solution with Transition Costs shown on Active Edges", fontsize=14
    )
    plt.axis("off")
    plt.tight_layout()
    plt.show()
