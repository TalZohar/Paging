from abc import ABC, abstractmethod
from typing import Set, List, Dict, Optional, Tuple, Any
from paging_model import Page, Request, Chain

class EvictionOracle(ABC):
    """
    Abstract interface for Subroutine F: Determines which page to evict
    when no domination rule applies.
    """
    @abstractmethod
    def select_eviction(self, 
                        current_cache: Set[Page], 
                        current_time: int, 
                        future_requests: List[Request]) -> Page:
        pass

class DominationStrategy(ABC):
    """
    Abstract interface for finding if a page dominates a set of chains.
    """
    @abstractmethod
    def find_domination(self, 
                        current_cache: Set[Page], 
                        future_requests: List[Request],
                        labels: Dict[int, float]) -> Optional[Tuple[Page, List[Chain]]]:
        pass

# --- Concrete Implementations ---

class FurthestInFutureOracle(EvictionOracle):
    """
    Standard greedy heuristic: evict the page requested furthest in the future.
    """
    def select_eviction(self, current_cache: Set[Page], current_time: int, future_requests: List[Request]) -> Page:
        next_use = {p: float('inf') for p in current_cache}
        
        for req in future_requests:
            if req.page in current_cache and next_use[req.page] == float('inf'):
                next_use[req.page] = req.time_step
        
        # Evict page with max distance to next use.
        # Tie-break: max weight (greedy heuristic), then ID.
        return max(current_cache, key=lambda p: (next_use[p], p.weight, p.id))

class NoOpDominationStrategy(DominationStrategy):
    """
    Default strategy that never finds a domination. 
    This reduces the algorithm to just using the Oracle (Rule 2).
    Implement a complex flow-based checker here to enable Rule 1.
    """
    def find_domination(self, current_cache, future_requests, labels):
        return None
