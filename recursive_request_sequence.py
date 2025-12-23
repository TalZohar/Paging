from typing import List, Tuple
from paging_model import Page, Request


def generate_recursive_sequence(
    n_pages: int, t: int, a: int
) -> Tuple[List[Page], List[Request]]:
    """
    Generates a recursive sequence where between every two consecutive requests
    of page P_i (weight t^i), there are exactly a requests of page P_{i-1}.
    """
    m = int(a)

    # Create Pages P1..Pn with weights t^1...t^n
    pages = [Page(f"P{i}", float(t**i)) for i in range(1, n_pages + 1)]

    def build_sequence(level: int) -> List[Page]:
        # Base Case: Level 1 (Weight t^1)
        # Sequence S1 must contain 'm' instances of P1 to satisfy upper levels
        if level == 1:
            return [pages[0]] * m

        # Recursive Step
        # S_i = S_{i-1} + (P_i + S_{i-1}) * m
        # This ensures there are 'm' instances of P_i, separated by S_{i-1}
        # S_{i-1} contains 'm' instances of P_{i-1}, satisfying the condition.

        prev_seq = build_sequence(level - 1)
        current_page = pages[level - 1]

        new_seq = []
        new_seq.append(current_page)
        for _ in range(m - 1):
            new_seq.extend(prev_seq)
            new_seq.append(current_page)

        return new_seq

    # Generate raw page sequence
    raw_pages = build_sequence(n_pages)

    # Convert to Request objects
    requests = [Request(i, p, i + 1) for i, p in enumerate(raw_pages)]

    return pages, requests
