# online_algorithm.py
from typing import List, Dict, Set, Tuple
from paging_model import Page, Request, CacheState
from online_strategies import EvictionOracle, DominationStrategy, FurthestInFutureOracle, NoOpDominationStrategy

class OnlineVariableCacheSystem:
    def __init__(self, 
                 pages: List[Page], 
                 capacities: Dict[int, int],
                 oracle: EvictionOracle = FurthestInFutureOracle(),
                 domination_strategy: DominationStrategy = NoOpDominationStrategy()):
        
        self.capacities = capacities
        self.oracle = oracle
        self.domination_strategy = domination_strategy
        
        # State
        self.cache: Set[Page] = set()
        self.total_cost = 0.0
        self.history: List[CacheState] = []
        self.labels: Dict[int, float] = {} # Map request_index -> label value

    def run(self, requests: List[Request]) -> Tuple[float, List[CacheState]]:
        print("\n--- Starting Online Simulation ---")
        
        # Initialize labels for all requests to 0
        for req in requests:
            self.labels[req.index] = 0.0

        for i, req in enumerate(requests):
            t = req.time_step
            k_t = self.capacities.get(t, 1)
            
            # 1. Load Page
            if req.page not in self.cache:
                self.cache.add(req.page)
                self.total_cost += req.page.weight
                print(f"[t={t}] MISS: Loaded {req.page.id}. Cost += {req.page.weight}")
            else:
                print(f"[t={t}] HIT: {req.page.id} is present.")

            # 2. Maintain Capacity
            while len(self.cache) > k_t:
                self._evict(i, t, requests)

            # Record state
            self.history.append(CacheState(t, k_t, set(self.cache)))

        return self.total_cost, self.history

    def _evict(self, current_req_idx: int, current_time: int, all_requests: List[Request]):
        future_reqs = all_requests[current_req_idx+1:]
        
        # Rule 1: Check Domination
        dom_result = self.domination_strategy.find_domination(
            self.cache, future_reqs, self.labels
        )

        if dom_result:
            p, chains = dom_result
            print(f"    -> Rule 1: Domination by {p.id}")
            
            # Find q in cache with w_q <= w_p maximizing next request time
            candidates = [q for q in self.cache if q.weight <= p.weight]
            if not candidates:
                q = p # Fallback
            else:
                q = self._get_furthest(candidates, future_reqs)
                
            self.cache.remove(q)
            
            # Update labels
            for chain in chains:
                for r in chain.requests:
                    self.labels[r.index] = p.weight
        else:
            # Rule 2: Oracle
            q = self.oracle.select_eviction(self.cache, current_time, future_reqs)
            print(f"    -> Rule 2 (Oracle): Evicting {q.id}")
            self.cache.remove(q)

    def _get_furthest(self, pages: List[Page], future_reqs: List[Request]) -> Page:
        # Helper to find furthest page among specific candidates
        next_use = {p: float('inf') for p in pages}
        for r in future_reqs:
            if r.page in next_use and next_use[r.page] == float('inf'):
                next_use[r.page] = r.time_step
        return max(pages, key=lambda p: next_use[p])
