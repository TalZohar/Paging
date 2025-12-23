from typing import List
from paging_model import Page, Request
from online_algorithm import OnlineVariableCacheSystem
from offline_solver import OfflineOptimalSolver
from offline_solver_visualization import visualize_solution
from recursive_request_sequence import generate_recursive_sequence


def run_experiment():
    # --- Configuration - --
    N = 3  # Number of pages
    T_val = 2  # Base weight t
    A_val = 3

    # Generate Sequence
    pages, requests = generate_recursive_sequence(N, T_val, A_val)

    # Create simple Capacity Schedule (Constant k=1 just to force evictions)
    # Length of sequence
    L = len(requests)
    capacities = {i: 2 for i in range(1, L + 2)}

    print("==========================================")
    print(f"Experiment: {requests}")
    print(f"Capacities: {capacities}")
    print("==========================================\n")

    # 2. Run Online Algorithm
    print(">>> Running Online Algorithm (Greedy Oracle)...")
    online_sys = OnlineVariableCacheSystem(pages, capacities)
    online_cost, on_states = online_sys.run(requests)
    print(f"Online Total Cost: {online_cost}\n")
    print("Online Schedule:")
    for s in on_states:
        print(f"  {s}")

    # 3. Run Offline Optimal Solver
    print(">>> Running Offline Optimal Solver (Min-Cost Flow)...")
    offline_solver = OfflineOptimalSolver(pages, requests, capacities)
    off_cost, off_states = offline_solver.solve()

    print(f"Offline Optimal Cost: {off_cost}")
    print("Offline Schedule:")
    for s in off_states:
        print(f"  {s}")

    print("\nVisualizing...")
    G, flow = offline_solver.get_graph_for_viz()
    flow_cost = offline_solver._calculate_real_cost_from_flow(G, flow, True)
    # visualize_solution(G, requests, flow)
    print(f"flow cost {flow_cost}")

    # 4. Comparison
    print("\n==========================================")
    print(f"Summary:")
    print(f"  Online Cost:  {online_cost}")
    print(f"  Optimal Cost: {off_cost}")
    print(
        f"  Competitive Ratio (Approx): {online_cost / off_cost if off_cost > 0 else 'inf'}"
    )
    print("==========================================")


if __name__ == "__main__":
    run_experiment()
