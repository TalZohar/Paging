from typing import List
from paging_model import Page, Request
from online_algorithm import OnlineVariableCacheSystem
from offline_solver import OfflineOptimalSolver

def run_experiment():
    # 1. Setup Environment
    # Pages with different weights
    pages = [
        Page("A", 1.0),
        Page("B", 2.0),
        Page("C", 10.0),
        Page("D", 3.0)
    ]
    p_map = {p.id: p for p in pages}

    # Request Sequence
    raw_seq = ["A", "B", "C", "A", "D", "B"]
    
    # Variable Capacity
    # Note how t=3 forces a bottleneck (k=1)
    capacities = {
        1: 2, 2: 2, 
        3: 1, 
        4: 2, 5: 2, 6: 2
    }

    # Create Request Objects
    requests = [Request(i, p_map[pid], i+1) for i, pid in enumerate(raw_seq)]

    print("==========================================")
    print(f"Experiment: {raw_seq}")
    print(f"Capacities: {capacities}")
    print("==========================================\n")

    # 2. Run Online Algorithm
    print(">>> Running Online Algorithm (Greedy Oracle)...")
    online_sys = OnlineVariableCacheSystem(pages, capacities)
    online_cost = online_sys.run(requests)
    print(f"Online Total Cost: {online_cost}\n")

    # 3. Run Offline Optimal Solver
    print(">>> Running Offline Optimal Solver (Min-Cost Flow)...")
    offline_solver = OfflineOptimalSolver(pages, requests, capacities)
    off_cost, off_states = offline_solver.solve()
    
    print(f"Offline Optimal Cost: {off_cost}")
    print("Offline Schedule:")
    for s in off_states:
        print(f"  {s}")

    # 4. Comparison
    print("\n==========================================")
    print(f"Summary:")
    print(f"  Online Cost:  {online_cost}")
    print(f"  Optimal Cost: {off_cost}")
    print(f"  Competitive Ratio (Approx): {online_cost / off_cost if off_cost > 0 else 'inf'}")
    print("==========================================")

if __name__ == "__main__":
    run_experiment()
