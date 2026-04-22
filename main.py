"""
 Author: Prudhvi Raj Belide
   File Name: main.py
   File Description: Entry point for the 5G NR MAC Scheduler Simulation.
                     Configures UEs, runs both Round Robin and Proportional
                     Fair schedulers for the same scenario, prints a summary
                     table, and saves result plots to results/. 
"""

import copy
from src.ue         import UserEquipment
from src.scheduler  import RoundRobinScheduler, ProportionalFairScheduler
from src.simulation import create_ues, run_simulation, compute_jain_fairness
from src.plot       import (plot_throughput_over_time,
                             plot_avg_throughput_bar,
                             plot_rb_allocation,
                             plot_snr_profiles,
                             print_summary_table)


# ─── Simulation Configuration ────────────────────────────────────────────────

NUM_TTIS = 300       # Number of TTIs to simulate (1 TTI = 0.5ms in 5G NR)
SEED     = 42        # Random seed — change to get different channel realizations

# UE distances from base station (meters)
# Mix of near, mid, and far UEs to see scheduler behavior clearly
UE_DISTANCES = [50, 150, 300, 500]

# ─────────────────────────────────────────────────────────────────────────────


def main():
    print("\n5G NR MAC Scheduler Simulation")
    print("================================")
    print(f"UEs        : {len(UE_DISTANCES)}")
    print(f"Distances  : {UE_DISTANCES} meters")
    print(f"TTIs       : {NUM_TTIS}")
    print(f"Total RBs  : 106 (20 MHz, numerology 0)\n")

    num_ues = len(UE_DISTANCES)

    # Create two independent sets of UEs — one for each scheduler
    # (same distances and seed so the comparison is fair)
    ues_rr = create_ues(num_ues, UE_DISTANCES, seed=SEED)
    ues_pf = create_ues(num_ues, UE_DISTANCES, seed=SEED)

    # ── Round Robin ──────────────────────────────────────────────────────────
    print("Running Round Robin scheduler...")
    rr_scheduler = RoundRobinScheduler()
    rr_results   = run_simulation(rr_scheduler, ues_rr, NUM_TTIS, seed=SEED)

    # ── Proportional Fair ────────────────────────────────────────────────────
    print("Running Proportional Fair scheduler...")
    pf_scheduler = ProportionalFairScheduler()
    pf_results   = run_simulation(pf_scheduler, ues_pf, NUM_TTIS, seed=SEED)

    # ── Fairness Metrics ─────────────────────────────────────────────────────
    rr_tputs    = [rr_results[i]["avg_throughput_mbps"] for i in range(num_ues)]
    pf_tputs    = [pf_results[i]["avg_throughput_mbps"] for i in range(num_ues)]
    rr_fairness = compute_jain_fairness(rr_tputs)
    pf_fairness = compute_jain_fairness(pf_tputs)

    # ── Print Summary ────────────────────────────────────────────────────────
    print_summary_table(rr_results, pf_results, rr_fairness, pf_fairness, num_ues)

    # ── Generate Plots ───────────────────────────────────────────────────────
    print("Generating plots...")
    plot_throughput_over_time(rr_results, pf_results, num_ues)
    plot_avg_throughput_bar(rr_results, pf_results, num_ues)
    plot_rb_allocation(rr_results, pf_results, num_ues)
    plot_snr_profiles(rr_results, num_ues)

    print("\nDone. Check results/ folder for plots.")


if __name__ == "__main__":
    main()
