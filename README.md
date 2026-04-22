# 5G NR MAC Scheduler Simulation

A Python simulation comparing Round Robin and Proportional Fair scheduling in a 5G NR downlink.

Built this to understand how the MAC layer actually decides which UE gets which resource blocks — something I kept seeing referenced in 5G NR specs but never fully clicked until I coded it myself.

---

## What it does

Four UEs are placed at different distances from a base station (50m, 150m, 300m, 500m). The simulation runs for 300 TTIs. Each TTI, both schedulers decide how to split 106 resource blocks across the UEs, and we track throughput, fairness, and channel quality over time.

The core question: does giving every UE equal airtime (Round Robin) actually produce equal throughput? Spoiler — it doesn't, because UEs farther away use lower modulation orders and get less data from the same number of RBs.

---

## Background

### Why OFDMA and Resource Blocks?

5G NR uses OFDMA (Orthogonal Frequency Division Multiple Access) in the downlink. The available spectrum is divided into resource blocks — each RB is 12 subcarriers × 14 OFDM symbols in one slot. For a 20 MHz carrier with 15 kHz subcarrier spacing (numerology 0), that works out to 106 RBs per slot.

The scheduler's job is to decide, every 0.5ms, which UE gets which RBs.

### MCS and Channel Quality

How much data fits in a resource block depends on the modulation and coding scheme (MCS). A nearby UE with good SNR can use 256-QAM (8 bits per symbol). A far UE with weak signal falls back to QPSK (2 bits per symbol). Same number of RBs, 4x the throughput difference.

In a real gNB, UEs report Channel Quality Indicator (CQI) feedback every few milliseconds. The scheduler uses this to make MCS decisions. Here we simulate SNR directly.

### Round Robin vs Proportional Fair

**Round Robin** is the naive approach — equal RBs to everyone, every TTI. Fair in terms of airtime, but wasteful if some UEs can carry far more data per RB.

**Proportional Fair** computes a priority metric each TTI:

```
PF_priority = instant_rate / average_past_throughput
```

A UE that currently has a good channel AND hasn't been served much recently gets higher priority. This balances throughput efficiency with fairness. It's the standard scheduler in commercial LTE and 5G deployments.

### Jain's Fairness Index

To quantify fairness:

```
J = (sum(xi))^2 / (n * sum(xi^2))
```

Range is [1/n, 1]. A score of 1.0 means all UEs get identical throughput. PF doesn't always score higher than RR on fairness — it trades some fairness for total cell throughput, but its fairness is time-averaged rather than per-TTI.

---

## Project structure

```
mac_scheduler/
├── main.py               # Entry point — configure and run simulation
├── requirements.txt
├── src/
│   ├── channel.py        # Path loss model, SNR computation
│   ├── ue.py             # UE class, MCS table, bits-per-RB calculation
│   ├── scheduler.py      # Round Robin and Proportional Fair schedulers
│   ├── simulation.py     # TTI loop, buffer management, result collection
│   └── plot.py           # All matplotlib plots
└── results/              # Output plots (auto-created)
```

---

## Setup and run

```bash
git clone https://github.com/prudhvibelide/5g-nr-mac-scheduler
cd 5g-nr-mac-scheduler

pip install -r requirements.txt

python main.py
```

Output plots go to `results/`. The terminal prints a summary table.

---

## Output

The simulation produces four plots:

- **throughput_over_time.png** — per-UE throughput across TTIs, RR vs PF side by side
- **avg_throughput_comparison.png** — bar chart of average throughput per UE
- **rb_allocation.png** — average RBs allocated per UE (RR is flat; PF is weighted)
- **snr_profiles.png** — SNR variation over time showing channel fading

Sample output:

```
UE    Dist(m)    RR Tput(Mbps)    PF Tput(Mbps)
UE0   50         0.027            0.027
UE1   150        0.014            0.014
UE2   300        0.011            0.012
UE3   500        0.007            0.007
Jain Fairness    0.7881           0.8016
```

---

## Things I simplified

This is a software simulation, not a full PHY implementation:

- No actual OFDM signal generation — the focus is MAC layer scheduling logic
- MCS thresholds are mapped directly from SNR rather than CQI tables
- Path loss uses a simplified 3GPP urban macro model (128.1 + 37.6·log10(d) dB)
- Fading is modeled as zero-mean Gaussian variation — no multipath or Doppler
- HARQ retransmissions are not modeled
- Uplink scheduling is not included

A natural next step would be adding HARQ and modeling CQI feedback delay, which is where a lot of real scheduler complexity lives.

---

## Requirements

- Python 3.9+
- numpy
- matplotlib
