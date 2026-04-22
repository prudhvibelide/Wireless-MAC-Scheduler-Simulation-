"""
 Author: Prudhvi Raj Belide
   File Name: plot.py
   File Description: Generates all result plots for the simulation.
                     Produces 4 charts:
                     1. Per-UE throughput over time (both schedulers)
                     2. Average throughput comparison bar chart
                     3. Resource block allocation per UE
                     4. Jain's Fairness Index comparison
                     Saves all figures to the results/ directory. 
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


RESULTS_DIR = "results"
COLORS      = ["#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0", "#00BCD4"]


def _ensure_results_dir():
    os.makedirs(RESULTS_DIR, exist_ok=True)


def plot_throughput_over_time(rr_results, pf_results, num_ues):
    """
    Plot per-UE throughput (Mbps) over TTIs for both schedulers side by side.
    """
    _ensure_results_dir()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    fig.suptitle("Per-UE Throughput Over Time", fontsize=14, fontweight="bold")

    for ax, results, title in zip(axes,
                                   [rr_results, pf_results],
                                   ["Round Robin", "Proportional Fair"]):
        for ue_id in range(num_ues):
            tp  = np.array(results[ue_id]["throughput_history"]) / 1e6
            dist = results[ue_id]["distance_m"]
            # Smooth with a 10-TTI rolling average for readability
            smooth = np.convolve(tp, np.ones(10)/10, mode="valid")
            ax.plot(smooth, color=COLORS[ue_id % len(COLORS)],
                    label=f"UE{ue_id} ({dist}m)", linewidth=1.8)

        ax.set_title(title, fontsize=12)
        ax.set_xlabel("TTI")
        ax.set_ylabel("Throughput (Mbps)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, "throughput_over_time.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def plot_avg_throughput_bar(rr_results, pf_results, num_ues):
    """
    Bar chart comparing average throughput per UE for RR vs PF.
    Shows clearly that PF favors UEs with better channels.
    """
    _ensure_results_dir()

    ue_ids  = list(range(num_ues))
    rr_avgs = [rr_results[i]["avg_throughput_mbps"] for i in ue_ids]
    pf_avgs = [pf_results[i]["avg_throughput_mbps"] for i in ue_ids]
    dists   = [rr_results[i]["distance_m"]          for i in ue_ids]

    x      = np.arange(num_ues)
    width  = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    bars_rr = ax.bar(x - width/2, rr_avgs, width, label="Round Robin",
                     color="#2196F3", alpha=0.85)
    bars_pf = ax.bar(x + width/2, pf_avgs, width, label="Proportional Fair",
                     color="#F44336", alpha=0.85)

    ax.set_xlabel("UE (distance from BS)")
    ax.set_ylabel("Average Throughput (Mbps)")
    ax.set_title("Average Throughput: Round Robin vs Proportional Fair", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"UE{i}\n({dists[i]}m)" for i in ue_ids])
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)

    # Annotate bar values
    for bar in bars_rr:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=8)
    for bar in bars_pf:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, "avg_throughput_comparison.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def plot_rb_allocation(rr_results, pf_results, num_ues):
    """
    Stacked bar chart showing how RBs are distributed per UE.
    RR gives equal RBs; PF gives more to UEs with better channels.
    """
    _ensure_results_dir()

    rr_avg_rbs = [np.mean(rr_results[i]["rb_history"]) for i in range(num_ues)]
    pf_avg_rbs = [np.mean(pf_results[i]["rb_history"]) for i in range(num_ues)]
    dists      = [rr_results[i]["distance_m"]          for i in range(num_ues)]

    x     = np.arange(num_ues)
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width/2, rr_avg_rbs, width, label="Round Robin",  color="#2196F3", alpha=0.85)
    ax.bar(x + width/2, pf_avg_rbs, width, label="Prop. Fair",   color="#F44336", alpha=0.85)

    ax.set_xlabel("UE (distance from BS)")
    ax.set_ylabel("Average RBs Allocated per TTI")
    ax.set_title("Resource Block Allocation per UE", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"UE{i}\n({dists[i]}m)" for i in range(num_ues)])
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    ax.axhline(y=106/num_ues, color="gray", linestyle="--",
               linewidth=1, label="Equal share")

    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, "rb_allocation.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def plot_snr_profiles(rr_results, num_ues):
    """
    Plot SNR over time for each UE to show channel variation.
    """
    _ensure_results_dir()

    fig, ax = plt.subplots(figsize=(10, 4))
    for ue_id in range(num_ues):
        snr  = rr_results[ue_id]["snr_history"]
        dist = rr_results[ue_id]["distance_m"]
        ax.plot(snr, color=COLORS[ue_id % len(COLORS)],
                label=f"UE{ue_id} ({dist}m)", linewidth=1.2, alpha=0.8)

    ax.set_xlabel("TTI")
    ax.set_ylabel("SNR (dB)")
    ax.set_title("UE Channel SNR Over Time (with fading)", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, "snr_profiles.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def print_summary_table(rr_results, pf_results, rr_fairness, pf_fairness, num_ues):
    """
    Print a formatted summary table to terminal.
    """
    print("\n" + "="*65)
    print(f"{'UE':<5} {'Dist(m)':<10} {'RR Tput(Mbps)':<16} {'PF Tput(Mbps)':<16}")
    print("-"*65)
    for i in range(num_ues):
        dist   = rr_results[i]["distance_m"]
        rr_tp  = rr_results[i]["avg_throughput_mbps"]
        pf_tp  = pf_results[i]["avg_throughput_mbps"]
        print(f"UE{i:<3} {dist:<10.0f} {rr_tp:<16.3f} {pf_tp:<16.3f}")
    print("-"*65)
    print(f"{'Jain Fairness':<16} {rr_fairness:<15.4f} {pf_fairness:<15.4f}")
    print("="*65)
    print()
