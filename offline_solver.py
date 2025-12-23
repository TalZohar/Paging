import networkx as nx
from typing import List, Dict, Tuple, Any
from paging_model import Page, Request, CacheState


class OfflineOptimalSolver:
    def __init__(
        self, pages: List[Page], requests: List[Request], capacities: Dict[int, int]
    ):
        self.pages = pages
        self.requests = requests
        self.capacities = capacities
        self.page_to_idx = {p.id: i for i, p in enumerate(pages)}
        self.idx_to_page = {i: p for i, p in enumerate(pages)}
        self.LARGE = 1_000_000

    def solve(self) -> Tuple[float, List[CacheState]]:
        G = self._build_layered_graph()
        max_k = max(self.capacities.values()) if self.capacities else 1

        try:
            flow_dict = nx.min_cost_flow(G)
        except nx.NetworkXUnfeasible:
            print("Graph is infeasible.")
            return 0.0, []

        states = self._reconstruct(G, flow_dict)
        real_cost = self._calculate_real_cost(states, True)
        return real_cost, states

    def _calculate_real_cost_from_flow(self, G, flow_dict, verbose=False) -> float:
        """
        Calculates the real paging cost by summing positive weights on active flow edges.
        Ignores negative reward weights (-LARGE) and zero weights.
        """
        total_cost = 0.0
        if verbose:
            print("\n=== Cost Breakdown (From Graph Edges) ===")

        # Iterate over all nodes in flow dict
        for u, neighbors in flow_dict.items():
            for v, flow in neighbors.items():
                if flow > 0.9:  # Flow exists

                    # Get edge weight
                    weight = G[u][v]["weight"]

                    # In this formulation:
                    # Positive Weight = Cost to Load/Switch Page
                    # Negative Weight = Reward (-LARGE)
                    # Zero Weight     = Free action (Hold/Evict)

                    if weight > 0:
                        total_cost += weight

                        if verbose:
                            # Format output for readability
                            u_str = self._format_node(u)
                            v_str = self._format_node(v)
                            print(
                                f"Edge ({u_str} -> {v_str}): Flow={int(flow)} * Weight={weight} = {weight}"
                            )

        if verbose:
            print(f"--- Total Real Cost: {total_cost} ---\n")

        return total_cost

    def _format_node(self, node):
        if isinstance(node, str):
            return node
        if len(node) == 2:
            layer, ntype = node
            return f"L{layer}:{ntype}"
        layer, ntype, idx = node
        if "page" in ntype:
            p_id = self.idx_to_page[idx].id
            return f"L{layer}:P({p_id})_{ntype.split('_')[1]}"
        return f"L{layer}:{ntype}"

    def get_graph_for_viz(self):
        G = self._build_layered_graph()
        flow_dict = nx.min_cost_flow(G)
        return G, flow_dict

    def _build_layered_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()
        n = len(self.pages)
        max_k = max(self.capacities.values()) if self.capacities else 1
        T = len(self.requests)

        G.add_node("source", demand=-max_k)
        G.add_node("sink", demand=max_k)

        # --- 1. Initial State (Layer 0) ---
        initial_k = self.capacities.get(1, 1)

        # A. Create Split Page Nodes for Layer 0
        for i in range(n):
            # Internal Edge: Page_In -> Page_Out with Cap 1
            G.add_edge((0, "page_in", i), (0, "page_out", i), capacity=1, weight=0)
            # Source -> Page_In
            G.add_edge("source", (0, "page_in", i), capacity=1, weight=0)

        # B. Create Split Active Slot Node for Layer 0
        slot_cap = max(0, max_k - initial_k)
        G.add_edge(
            (0, "slot_in"), (0, "slot_out"), capacity=slot_cap, weight=-self.LARGE
        )
        G.add_edge("source", (0, "slot_in"), capacity=max_k, weight=0)

        # --- 2. Build Layers (Transitions) ---
        for t in range(T):
            req = self.requests[t]
            req_p_idx = self.page_to_idx[req.page.id]

            # Transitioning from Layer t -> Layer t+1

            # Create Split Nodes for Layer t+1
            # 1. Page Nodes
            for i in range(n):
                weight = 0
                if i == req_p_idx:
                    weight -= self.LARGE
                G.add_edge(
                    (t + 1, "page_in", i),
                    (t + 1, "page_out", i),
                    capacity=1,
                    weight=weight,
                )

            # 2. Active Slot Node
            curr_k = self.capacities.get(t + 1, 1)  # Capacity at step t+1
            # "Active Slot" flow represents items NOT in the main cache (slack)
            # Capacity is max_k - curr_k
            slot_cap = max(0, max_k - curr_k)
            G.add_edge(
                (t + 1, "slot_in"),
                (t + 1, "slot_out"),
                capacity=slot_cap,
                weight=-self.LARGE,
            )

            # --- Define Edges from Layer t (OUT nodes) to Layer t+1 (IN nodes) ---

            # A. Page to Page (Fully Connected)
            for i in range(n):
                for j in range(n):
                    weight = 0
                    if i != j:
                        weight = self.pages[j].weight  # Switching Cost

                    # From Page_Out(t) -> Page_In(t+1)
                    G.add_edge(
                        (t, "page_out", i),
                        (t + 1, "page_in", j),
                        capacity=1,
                        weight=weight,
                    )

            # B. Page to Active Slot
            for i in range(n):
                # Weight 0
                G.add_edge((t, "page_out", i), (t + 1, "slot_in"), capacity=1, weight=0)

            # C. Active Slot to Page
            for j in range(n):
                weight = self.pages[j].weight  # Loading cost

                G.add_edge(
                    (t, "slot_out"), (t + 1, "page_in", j), capacity=1, weight=weight
                )

            # D. Active Slot to Active Slot
            G.add_edge((t, "slot_out"), (t + 1, "slot_in"), capacity=max_k, weight=0)
            G.add_edge((t, "slot_in"), (t + 1, "slot_in"), capacity=max_k, weight=0)

        # --- 3. Connect Last Layer to Sink ---
        last_t = T

        # Connect Page_Out to Sink
        for i in range(n):
            G.add_edge((last_t, "page_out", i), "sink", capacity=1, weight=0)

        # Connect Slot_Out to Sink
        G.add_edge((last_t, "slot_out"), "sink", capacity=max_k, weight=0)
        G.add_edge((last_t, "slot_in"), "sink", capacity=max_k, weight=0)

        return G

    def _reconstruct(self, G, flow_dict) -> List[CacheState]:
        states = []
        n = len(self.pages)
        T = len(self.requests)

        for t in range(1, T + 1):
            k = self.capacities.get(t, 1)
            pages_in_cache = set()

            for i in range(n):
                # Check flow passing through the internal node
                # edge: page_in -> page_out
                u = (t, "page_in", i)
                v = (t, "page_out", i)

                flow = 0
                if flow_dict and u in flow_dict and v in flow_dict[u]:
                    flow = flow_dict[u][v]

                if flow > 0.9:
                    pages_in_cache.add(self.idx_to_page[i])

            states.append(CacheState(t, k, pages_in_cache))
        return states

    def _calculate_real_cost(
        self, states: List[CacheState], verbose: bool = False
    ) -> float:
        """
        Calculates pure paging cost (sum of weights of loaded pages).
        If verbose=True, prints the breakdown of costs to stdout.
        """
        cost = 0.0
        if not states:
            return 0.0

        if verbose:
            print("\n--- Cost Breakdown ---")

        # 1. Initial Load (t=1)
        # We assume the cache starts empty, so everything present at t=1 is a 'load'
        current_pages = states[0].pages
        step_cost = sum(p.weight for p in current_pages)
        cost += step_cost

        if verbose:
            p_ids = sorted([p.id for p in current_pages])
            print(
                f"t=1 [Initial]: Loaded {p_ids}. Cost += {step_cost} (Current Total: {cost})"
            )

        # 2. Transitions (t=2 to T)
        for i in range(1, len(states)):
            t = states[i].time_step
            prev = states[i - 1].pages
            curr = states[i].pages

            # Identify pages that are in the current state but weren't in the previous
            new_pages = curr - prev
            step_cost = sum(p.weight for p in new_pages)
            cost += step_cost

            if verbose:
                if new_pages:
                    p_ids = sorted([p.id for p in new_pages])
                    print(
                        f"t={t} [Load]   : Loaded {p_ids}. Cost += {step_cost} (Current Total: {cost})"
                    )
                else:
                    print(f"t={t} [Hit/Hold]: No new pages loaded.")

        if verbose:
            print(f"--- Final Real Cost: {cost} ---\n")

        return cost
