"""
 Author: Prudhvi Raj Belide
   File Name: scheduler.py
   File Description: Implements two MAC layer scheduling algorithms:
                     1. Round Robin (RR)  — fair time sharing, ignores channel quality
                     2. Proportional Fair (PF) — balances fairness and throughput
                        by considering both current SNR and past average throughput.
                     In 5G NR, the MAC scheduler runs every TTI (Transmission Time
                     Interval = 1 slot = 0.5ms for numerology 1). This file simulates
                     that decision loop in software. 
"""

import numpy as np


# Total downlink resource blocks available per TTI
# 5G NR 20 MHz bandwidth, numerology 0 (SCS=15kHz) -> 106 RBs
TOTAL_RBS = 106


class RoundRobinScheduler:
    """
    Round Robin MAC Scheduler.

    Allocates an equal share of RBs to each UE every TTI,
    regardless of channel quality. Simple and fair in time,
    but wastes capacity on UEs with poor channels.

    Real-world use: legacy LTE systems, voice traffic
    """

    def __init__(self, total_rbs=TOTAL_RBS):
        self.total_rbs  = total_rbs
        self.ue_pointer = 0   # tracks whose turn it is

    def schedule(self, ue_list):
        """
        Allocate RBs equally across all active UEs.

        Args:
            ue_list (list[UserEquipment]): List of UEs to schedule

        Returns:
            dict: {ue_id: num_rbs_allocated}
        """
        if not ue_list:
            return {}

        num_ues     = len(ue_list)
        rbs_each    = self.total_rbs // num_ues
        remainder   = self.total_rbs  % num_ues

        allocation = {}
        for i, ue in enumerate(ue_list):
            # Give one extra RB to the first (remainder) UEs
            extra = 1 if i < remainder else 0
            allocation[ue.ue_id] = rbs_each + extra

        return allocation


class ProportionalFairScheduler:
    """
    Proportional Fair (PF) MAC Scheduler.

    PF is the industry-standard scheduler used in LTE and 5G NR.
    It maximizes cell throughput while maintaining fairness by computing
    a priority metric for each UE every TTI:

        PF_metric = instant_rate / average_past_throughput

    UEs with good current channel AND relatively low recent throughput
    get higher priority. This prevents strong UEs from always winning.

    Reference: 3GPP TS 36.321 (LTE MAC), 3GPP TS 38.321 (NR MAC)
    """

    def __init__(self, total_rbs=TOTAL_RBS, averaging_window=20):
        self.total_rbs         = total_rbs
        self.averaging_window  = averaging_window  # TTIs to average throughput over
        # Stores rolling average throughput per UE (bits/TTI)
        self.avg_throughput    = {}

    def _get_avg_throughput(self, ue_id):
        """Return running average throughput, defaulting to small value to avoid div/0."""
        return self.avg_throughput.get(ue_id, 1.0)

    def _update_avg_throughput(self, ue_id, bits_this_tti):
        """
        Exponential moving average update.
        alpha = 1/window gives smooth averaging without storing history.
        """
        alpha   = 1.0 / self.averaging_window
        old_avg = self._get_avg_throughput(ue_id)
        new_avg = (1.0 - alpha) * old_avg + alpha * bits_this_tti
        self.avg_throughput[ue_id] = new_avg

    def compute_pf_metrics(self, ue_list):
        """
        Compute PF priority metric for each UE.

        Args:
            ue_list: List of UserEquipment objects

        Returns:
            dict: {ue_id: pf_metric}
        """
        metrics = {}
        for ue in ue_list:
            instant_rate  = ue.get_bits_per_rb()          # bits if given 1 RB now
            avg_rate      = self._get_avg_throughput(ue.ue_id)
            metrics[ue.ue_id] = instant_rate / avg_rate
        return metrics

    def schedule(self, ue_list):
        """
        Allocate RBs based on PF priority metric.

        Strategy: Sort UEs by PF metric (descending), allocate RBs
        proportional to their metric weight.

        Args:
            ue_list (list[UserEquipment]): UEs to schedule

        Returns:
            dict: {ue_id: num_rbs_allocated}
        """
        if not ue_list:
            return {}

        metrics    = self.compute_pf_metrics(ue_list)
        total_metric = sum(metrics.values())

        allocation = {}
        rbs_assigned = 0

        # Sort by metric descending so higher priority UEs get exact RBs first
        sorted_ues = sorted(ue_list, key=lambda u: metrics[u.ue_id], reverse=True)

        for i, ue in enumerate(sorted_ues):
            weight = metrics[ue.ue_id] / total_metric

            if i == len(sorted_ues) - 1:
                # Last UE gets remaining RBs (avoids rounding loss)
                rbs = self.total_rbs - rbs_assigned
            else:
                rbs = max(1, int(weight * self.total_rbs))
                rbs = min(rbs, self.total_rbs - rbs_assigned)

            allocation[ue.ue_id] = rbs
            rbs_assigned += rbs

        return allocation

    def update_history(self, ue_list, allocation):
        """
        Update average throughput after each TTI.
        Must be called after schedule() to keep metrics current.

        Args:
            ue_list    : List of UEs
            allocation : {ue_id: rbs} from schedule()
        """
        for ue in ue_list:
            rbs       = allocation.get(ue.ue_id, 0)
            bits_sent = rbs * ue.get_bits_per_rb()
            self._update_avg_throughput(ue.ue_id, bits_sent)
