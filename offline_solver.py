import networkx as nx
from typing import List, Dict, Tuple
from paging_model import Page, Request, CacheState

class OfflineOptimalSolver:
    def __init__(self, pages: List[Page], requests: List[Request], capacities: Dict[int, int]):
        self.requests = requests
        self.capacities = capacities
        self.SOURCE = 'source'
        self.SINK = 'sink'

    def solve(self) -> Tuple[float, List[CacheState]]:
        G = self._build_graph()
        try:
            flow_dict = nx.min_cost_flow(G)
        except nx.NetworkXUnfeasible:
            print("Graph infeasible.")
            return 0.0, []
        return self._reconstruct(G, flow_dict)

    def _build_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()
        T = len(self.requests)
        max_k = max(self.capacities.values()) if self.capacities else 1

        G.add_node(self.SOURCE, demand=-max_k)
        G.add_node(self.SINK, demand=max_k)

        # 1. Create Split Nodes and Bottlenecks
        for i in range(T):
            u_in = f"{i}_in"
            u_out = f"{i}_out"
            G.add_node(u_in)
            G.add_node(u_out)
            
            # Bottleneck Edge: Enforces k_{t}
            # Capacity is k-1 because current request takes 1 mandatory slot
            k_t = self.capacities.get(i + 1, 1)
            cap = max(0, k_t - 1)
            G.add_edge(u_in, u_out, capacity=cap, weight=0, type='bottleneck')

        # 2. Backbone (Time) Edges
        # Connect i_out -> (i+1)_in
        for i in range(T - 1):
            u_out = f"{i}_out"
            v_in = f"{i+1}_in"
            G.add_edge(u_out, v_in, capacity=max_k, weight=0, type='backbone')

        # 3. Interval Edges (Savings)
        last_seen = {}
        for i, req in enumerate(self.requests):
            if req.page.id in last_seen:
                prev = last_seen[req.page.id]
                u_out = f"{prev}_out"
                v_in = f"{i}_in"
                # Keep page from after 'prev' until start of 'i'
                G.add_edge(u_out, v_in, capacity=1, weight=-req.page.weight, type='interval', page=req.page)
            last_seen[req.page.id] = i

        # 4. Circulation Bypass
        G.add_edge(self.SOURCE, "0_in", capacity=max_k, weight=0)
        G.add_edge(f"{T-1}_out", self.SINK, capacity=max_k, weight=0)
        G.add_edge(self.SOURCE, self.SINK, capacity=max_k, weight=0)

        return G

    def _reconstruct(self, G, flow) -> Tuple[float, List[CacheState]]:
        base_cost = sum(r.page.weight for r in self.requests)
        savings = 0.0
        active_intervals = set()

        for u, neighbors in flow.items():
            for v, f in neighbors.items():
                if f > 0:
                    data = G.get_edge_data(u, v)
                    if data.get('type') == 'interval':
                        savings += (-data['weight'])
                        # Edge u->v corresponds to nodes {prev}_out -> {i}_in
                        # Extract indices from node names strings
                        prev_idx = int(u.split('_')[0])
                        curr_idx = int(v.split('_')[0])
                        active_intervals.add((prev_idx, curr_idx, data['page']))

        states = []
        for i, req in enumerate(self.requests):
            t = i + 1
            k = self.capacities.get(t, 1)
            pages = {req.page}
            
            for start, end, p in active_intervals:
                # Page is kept in cache AFTER request 'start' until request 'end'
                if start < i < end:
                    pages.add(p)
                # Boundary condition: At step 'start', page is req. At step 'end', page is req.
                # Between them (start < i < end), it consumes backbone capacity.
            
            states.append(CacheState(t, k, pages))

        return base_cost - savings, states
