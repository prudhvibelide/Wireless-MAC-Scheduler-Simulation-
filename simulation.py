"""
 Author: Prudhvi Raj Belide
   File Name: simulation.py
   File Description: Main simulation loop — runs TTI by TTI, updates
                     channel conditions, calls the scheduler, allocates
                     RBs, and records per-UE throughput and fairness.
                     This mirrors how a real gNB MAC layer runs:
                     every slot, it checks channel state, runs the
                     scheduler, and hands off transport blocks to PHY. 
"""

import numpy as np
from src.channel import compute_snr_db, add_channel_variation
from src.ue      import UserEquipment
from src.scheduler import RoundRobinScheduler, ProportionalFairScheduler


# Base station transmit power in dBm (typical 5G NR small cell = 30 dBm)
TX_POWER_DBM = 30.0

# New data injected into each UE buffer every TTI (bits)
# Simulates a constant bit rate (CBR) application — e.g., video stream
BUFFER_REFILL_BITS = 50000


def create_ues(num_ues, distances_m, seed=42):
    """
    Create a list of UE objects with initial SNR values.

    Args:
        num_ues      (int):   Number of UEs
        distances_m  (list):  Distance of each UE from BS in meters
        seed         (int):   Random seed for reproducibility

    Returns:
        list[UserEquipment]
    """
    ues = []
    for i in range(num_ues):
        ue  = UserEquipment(ue_id=i, distance_m=distances_m[i])
        snr = compute_snr_db(TX_POWER_DBM, distances_m[i])
        ue.snr_db = add_channel_variation(snr, seed=seed + i)
        ues.append(ue)
    return ues


def run_simulation(scheduler, ues, num_ttis=200, seed=42):
    """
    Run the MAC scheduling simulation for a given number of TTIs.

    Each TTI (Transmission Time Interval):
      1. Refill UE buffers with new data
      2. Update channel SNR with small fading variation
      3. Run scheduler to get RB allocation
      4. Each UE consumes allocated RBs (transmits data)
      5. Record per-UE throughput and RB counts

    Args:
        scheduler : RoundRobinScheduler or ProportionalFairScheduler
        ues       : List of UserEquipment objects
        num_ttis  : Number of TTIs to simulate
        seed      : Base random seed

    Returns:
        dict: Results keyed by ue_id, containing throughput and rb history
    """
    rng = np.random.default_rng(seed)

    for tti in range(num_ttis):

        # Step 1: Refill buffers — new application data arrives each TTI
        for ue in ues:
            ue.refill_buffer(BUFFER_REFILL_BITS)

        # Step 2: Update SNR with small random fading (channel variation)
        for ue in ues:
            base_snr   = compute_snr_db(TX_POWER_DBM, ue.distance_m)
            shadow_db  = rng.normal(loc=0.0, scale=2.0)   # ±2 dB variation
            ue.snr_db  = base_snr + shadow_db
            ue.snr_history.append(ue.snr_db)

        # Step 3: Run scheduler
        allocation = scheduler.schedule(ues)

        # Step 4: Apply allocation — UEs transmit data
        for ue in ues:
            rbs       = allocation.get(ue.ue_id, 0)
            bits_sent = ue.consume_rbs(rbs)
            ue.throughput_history.append(bits_sent)
            ue.rb_history.append(rbs)

        # Step 5: PF scheduler updates its internal throughput averages
        if isinstance(scheduler, ProportionalFairScheduler):
            scheduler.update_history(ues, allocation)

    return _collect_results(ues)


def _collect_results(ues):
    """
    Package UE simulation results into a dict for plotting.

    Returns:
        dict: {ue_id: {throughput_history, rb_history, snr_history,
                       avg_throughput_mbps, distance_m}}
    """
    results = {}
    for ue in ues:
        avg_tp_mbps = np.mean(ue.throughput_history) / 1e6
        results[ue.ue_id] = {
            "throughput_history" : ue.throughput_history,
            "rb_history"         : ue.rb_history,
            "snr_history"        : ue.snr_history,
            "avg_throughput_mbps": avg_tp_mbps,
            "distance_m"         : ue.distance_m,
        }
    return results


def compute_jain_fairness(avg_throughputs):
    """
    Compute Jain's Fairness Index across UEs.

    Jain's index = (sum(xi))^2 / (n * sum(xi^2))
    Range: [1/n, 1.0] where 1.0 = perfectly fair

    This is the standard metric used in wireless systems to
    compare scheduler fairness — referenced in most 5G NR papers.

    Args:
        avg_throughputs (list): Average throughput per UE

    Returns:
        float: Jain's fairness index
    """
    x   = np.array(avg_throughputs)
    n   = len(x)
    if n == 0 or np.sum(x ** 2) == 0:
        return 0.0
    return (np.sum(x) ** 2) / (n * np.sum(x ** 2))
