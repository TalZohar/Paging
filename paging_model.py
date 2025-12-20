# paging_model.py
from dataclasses import dataclass, field
from typing import Set, List

@dataclass(frozen=True)
class Page:
    """Represents a unique page with a specific weight."""
    id: str
    weight: float

    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return isinstance(other, Page) and self.id == other.id
    
    def __repr__(self):
        return f"{self.id}(w={self.weight})"

@dataclass
class Request:
    """Represents a request at a specific time step."""
    index: int          # Global sequence index (0, 1, ... T-1)
    page: Page          # The page requested
    time_step: int      # Discrete time step (usually index + 1)

    def __repr__(self):
        return f"Req(t={self.time_step}, {self.page.id})"

@dataclass
class Chain:
    """Represents a Chain of requests for the Domination Strategy."""
    requests: List[Request]

    @property
    def cost(self) -> float:
        return sum(r.page.weight for r in self.requests)

    @property
    def interval(self):
        if not self.requests:
            return (0, 0)
        return (self.requests[0].time_step, self.requests[-1].time_step)

@dataclass
class CacheState:
    """Used for reporting results."""
    time_step: int
    capacity: int
    pages: Set[Page]

    def __repr__(self):
        p_ids = sorted([p.id for p in self.pages])
        return f"[t={self.time_step}] k={self.capacity} | Cache: {p_ids}"
