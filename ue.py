"""
 Author: Prudhvi Raj Belide
   File Name: ue.py
   File Description: Defines the UserEquipment class.
                     Each UE has an ID, distance from the base station,
                     a pending data buffer, and a current SNR value.
                     This models the UE state that the MAC scheduler
                     reads before making allocation decisions — similar
                     to how a real gNB tracks UE context in 5G NR. 
"""

from dataclasses import dataclass, field


# Modulation and Coding Scheme (MCS) thresholds based on SNR (dB)
# Simplified mapping — real 5G NR uses 3GPP TS 38.214 Table 5.1.3.1
# Format: (min_snr_db, mcs_index, modulation_name, bits_per_symbol)
MCS_TABLE = [
    (  0.0,  0, "BPSK",    1),
    ( 20.0,  5, "QPSK",    2),
    ( 35.0, 10, "16-QAM",  4),
    ( 50.0, 15, "64-QAM",  6),
    ( 60.0, 20, "256-QAM", 8),
]


def snr_to_mcs(snr_db):
    """
    Map a UE's SNR to an MCS index and modulation scheme.

    In 5G NR, the UE reports CQI (Channel Quality Indicator),
    and the gNB maps it to an MCS. Here we directly use SNR
    for simplicity.

    Args:
        snr_db (float): UE's current SNR in dB

    Returns:
        tuple: (mcs_index, modulation_name, bits_per_symbol)
    """
    selected = MCS_TABLE[0]  # Default to lowest MCS
    for (min_snr, mcs_idx, mod_name, bps) in MCS_TABLE:
        if snr_db >= min_snr:
            selected = (mcs_idx, mod_name, bps)
    return selected


@dataclass
class UserEquipment:
    """
    Represents a single UE connected to the base station.

    Attributes:
        ue_id         : Unique identifier (e.g., 0, 1, 2 ...)
        distance_m    : Distance from base station in meters
        buffer_bits   : Pending data in the transmission buffer (bits)
        snr_db        : Current channel SNR in dB (updated each TTI)
        total_bits_tx : Cumulative bits transmitted (for throughput tracking)
        rbs_allocated : Resource blocks allocated in current TTI
    """
    ue_id          : int
    distance_m     : float
    buffer_bits    : int   = 0
    snr_db         : float = 0.0
    total_bits_tx  : int   = 0
    rbs_allocated  : int   = 0

    # Per-TTI history for plotting
    snr_history         : list = field(default_factory=list)
    throughput_history  : list = field(default_factory=list)
    rb_history          : list = field(default_factory=list)

    def get_mcs(self):
        """Return current MCS tuple based on live SNR."""
        return snr_to_mcs(self.snr_db)

    def get_bits_per_rb(self):
        """
        Compute how many bits one resource block carries at current MCS.

        5G NR: 1 RB = 12 subcarriers x 14 OFDM symbols = 168 resource elements
        Bits per RB = resource_elements * bits_per_symbol * code_rate (0.75 approx)
        """
        _, _, bits_per_symbol = self.get_mcs()
        resource_elements = 12 * 14       # 1 RB in one slot (5G NR numerology 0)
        code_rate         = 0.75          # Simplified: rate-3/4 coding
        return int(resource_elements * bits_per_symbol * code_rate)

    def refill_buffer(self, bits):
        """Add new data to UE buffer (simulates application layer traffic)."""
        self.buffer_bits += bits

    def consume_rbs(self, num_rbs):
        """
        Transmit data using allocated RBs. Drains the buffer accordingly.

        Args:
            num_rbs (int): Number of resource blocks allocated by scheduler

        Returns:
            int: Actual bits transmitted this TTI
        """
        bits_per_rb  = self.get_bits_per_rb()
        bits_possible = num_rbs * bits_per_rb
        bits_sent     = min(bits_possible, self.buffer_bits)

        self.buffer_bits  -= bits_sent
        self.total_bits_tx += bits_sent
        self.rbs_allocated  = num_rbs

        return bits_sent

    def __repr__(self):
        mcs_idx, mod, _ = self.get_mcs()
        return (f"UE{self.ue_id} | dist={self.distance_m}m | "
                f"SNR={self.snr_db:.1f}dB | MCS={mcs_idx}({mod}) | "
                f"buffer={self.buffer_bits}b")
