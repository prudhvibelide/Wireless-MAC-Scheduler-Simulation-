"""
 Author: Prudhvi Raj Belide
   File Name: channel.py
   File Description: Simulates a wireless channel for each UE.
                     Models path loss and AWGN noise to compute
                     the received SNR per resource block. In a real
                     5G NR system, this maps to the physical downlink
                     channel (PDSCH) quality reported via CQI feedback. 
"""

import numpy as np


# Free-space path loss exponent (typical urban = 3.5, free space = 2.0)
PATH_LOSS_EXPONENT = 3.5

# Thermal noise power in dBm at 1 Hz bandwidth (standard assumption)
NOISE_POWER_DBM = -174.0

# System bandwidth per resource block in Hz (5G NR: 1 RB = 180 kHz)
RB_BANDWIDTH_HZ = 180e3


def compute_noise_power_dbm(bandwidth_hz=RB_BANDWIDTH_HZ):
    """
    Compute thermal noise power over a given bandwidth.

    Formula: N = N0 + 10*log10(BW)
    where N0 = -174 dBm/Hz at room temperature (290 K)

    Args:
        bandwidth_hz (float): Bandwidth in Hz

    Returns:
        float: Noise power in dBm
    """
    noise_dbm = NOISE_POWER_DBM + 10.0 * np.log10(bandwidth_hz)
    return noise_dbm


def compute_path_loss_db(distance_m):
    """
    Compute free-space path loss using log-distance model.

    Formula: PL = 20*log10(d) * exponent  (simplified)
    Real 5G NR uses more complex models (3GPP TR 38.901)
    but this is sufficient for scheduler simulation.

    Args:
        distance_m (float): Distance from base station in meters

    Returns:
        float: Path loss in dB
    """
    if distance_m <= 0:
        raise ValueError("Distance must be greater than 0 meters")

    # 3GPP simplified urban macro model (carrier ~2 GHz)
    # PL(d) = 128.1 + 37.6 * log10(d_km)
    distance_km  = distance_m / 1000.0
    path_loss_db = 128.1 + 37.6 * np.log10(max(distance_km, 1e-3))
    return path_loss_db


def compute_snr_db(tx_power_dbm, distance_m, noise_figure_db=7.0):
    """
    Compute received SNR for a UE at a given distance.

    SNR = Tx_Power - Path_Loss - Noise_Power - Noise_Figure

    Args:
        tx_power_dbm  (float): Base station transmit power in dBm
        distance_m    (float): UE distance from BS in meters
        noise_figure_db(float): Receiver noise figure in dB (typical = 7 dB)

    Returns:
        float: SNR in dB
    """
    path_loss_db   = compute_path_loss_db(distance_m)
    noise_power_db = compute_noise_power_dbm()

    snr_db = tx_power_dbm - path_loss_db - noise_power_db - noise_figure_db
    return snr_db


def add_channel_variation(snr_db, seed=None):
    """
    Add small random fading variation to SNR (simulates slow fading / shadowing).

    In real 5G NR, UEs report CQI every 1-5 ms. This variation
    mimics that the channel is not perfectly static.

    Args:
        snr_db (float): Base SNR in dB
        seed   (int):   Optional random seed for reproducibility

    Returns:
        float: SNR with fading variation in dB
    """
    rng = np.random.default_rng(seed)
    # Shadowing standard deviation ~8 dB is common in urban models
    shadow_db = rng.normal(loc=0.0, scale=3.0)
    return snr_db + shadow_db
