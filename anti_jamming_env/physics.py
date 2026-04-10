"""
Wireless Communication Physics Simulation
Implements realistic channel models, path loss, fading, and interference
"""

from enum import Enum
from typing import Optional, Tuple

import numpy as np


class ModulationScheme(Enum):
    """Modulation schemes with bits per symbol."""

    BPSK = 1
    QPSK = 2
    QAM16 = 4
    QAM64 = 6


class CodingRate(Enum):
    """Forward Error Correction coding rates."""

    RATE_1_2 = 0.5
    RATE_2_3 = 0.667
    RATE_3_4 = 0.75
    RATE_5_6 = 0.833


class WirelessChannel:
    """
    Simulates a realistic wireless communication channel.

    Models:
    - Free-space path loss
    - Rayleigh fading (multipath)
    - Additive White Gaussian Noise (AWGN)
    - Interference from jammers
    """

    def __init__(
        self,
        frequency_ghz: float = 2.4,
        distance_m: float = 100.0,
        bandwidth_mhz: float = 20.0,
        noise_figure_db: float = 5.0,
        num_channels: int = 64,
        random_seed: Optional[int] = None,
    ) -> None:
        self.frequency_ghz = frequency_ghz
        self.distance_m = distance_m
        self.bandwidth_mhz = bandwidth_mhz
        self.noise_figure_db = noise_figure_db
        self.num_channels = num_channels

        self.rng = np.random.RandomState(random_seed)

        # Channel state (fading coefficients)
        self.fading_coefficients = self.rng.rayleigh(1.0, num_channels)

        # Thermal noise power (dBm)
        self.thermal_noise_dbm = (
            -174 + 10 * np.log10(bandwidth_mhz * 1e6) + noise_figure_db
        )

    def path_loss_db(self, distance_m: Optional[float] = None) -> float:
        """
        Calculate free-space path loss.

        FSPL(dB) = 20*log10(d) + 20*log10(f) + 20*log10(4π/c)
        """
        d = distance_m if distance_m is not None else self.distance_m
        f_hz = self.frequency_ghz * 1e9

        fspl_db = (
            20 * np.log10(d)
            + 20 * np.log10(f_hz)
            + 20 * np.log10(4 * np.pi / 3e8)
        )

        return fspl_db

    def apply_fading(self, channel_idx: int) -> float:
        """
        Apply Rayleigh fading to the signal.
        Returns fading gain in dB.
        """
        self.fading_coefficients[channel_idx] = (
            0.9 * self.fading_coefficients[channel_idx]
            + 0.1 * self.rng.rayleigh(1.0)
        )

        fading_db = 20 * np.log10(self.fading_coefficients[channel_idx] + 1e-10)

        return fading_db

    def calculate_snr(self, tx_power_dbm: float, channel_idx: int) -> float:
        """
        Calculate Signal-to-Noise Ratio.

        SNR = Received Power - Noise Power
        Received Power = TX Power - Path Loss + Fading
        """
        path_loss = self.path_loss_db()
        fading = self.apply_fading(channel_idx)

        rx_power_dbm = tx_power_dbm - path_loss + fading
        snr_db = rx_power_dbm - self.thermal_noise_dbm

        return snr_db

    def calculate_sinr(
        self, tx_power_dbm: float, channel_idx: int, interference_power_dbm: float
    ) -> Tuple[float, float]:
        """
        Calculate Signal-to-Interference-plus-Noise Ratio.

        SINR = Signal / (Interference + Noise)

        Returns:
            (sinr_db, snr_db)
        """
        snr_db = self.calculate_snr(tx_power_dbm, channel_idx)

        signal_power = 10 ** (snr_db / 10)

        if interference_power_dbm > -150:
            interference_linear = 10 ** (
                (interference_power_dbm - self.thermal_noise_dbm) / 10
            )
        else:
            interference_linear = 0.0

        sinr_linear = signal_power / (1.0 + interference_linear)
        sinr_db = 10 * np.log10(sinr_linear + 1e-10)

        return sinr_db, snr_db

    def calculate_throughput(
        self,
        sinr_db: float,
        modulation: str,
        coding_rate: str,
        enable_fhss: bool = False,
        enable_dsss: bool = False,
    ) -> float:
        """
        Calculate achievable throughput based on SINR and modulation.

        Shannon capacity: C = BW * log2(1 + SINR)
        Practical: R = BW * code_rate * bits_per_symbol * efficiency

        Returns:
            Throughput in Mbps
        """
        mod_bits = {
            "BPSK": 1,
            "QPSK": 2,
            "16QAM": 4,
            "64QAM": 6,
        }

        code_rates = {
            "1/2": 0.5,
            "2/3": 0.667,
            "3/4": 0.75,
            "5/6": 0.833,
        }

        bits_per_symbol = mod_bits[modulation]
        code_rate = code_rates[coding_rate]

        required_sinr = {
            "BPSK": 6,
            "QPSK": 9,
            "16QAM": 15,
            "64QAM": 21,
        }

        if sinr_db < required_sinr[modulation]:
            penalty_factor = 10 ** ((sinr_db - required_sinr[modulation]) / 10)
            penalty_factor = max(0.01, min(1.0, penalty_factor))
        else:
            penalty_factor = 1.0

        base_throughput = self.bandwidth_mhz * bits_per_symbol * code_rate

        if enable_fhss:
            base_throughput *= 0.9
        if enable_dsss:
            base_throughput *= 0.8

        throughput_mbps = base_throughput * penalty_factor

        return throughput_mbps

    def calculate_packet_error_rate(self, sinr_db: float, modulation: str) -> float:
        """
        Estimate Packet Error Rate based on SINR.

        Uses simplified BER formulas for each modulation.
        """
        sinr_linear = 10 ** (sinr_db / 10)

        if modulation == "BPSK":
            ber = 0.5 * np.exp(-sinr_linear)
        elif modulation == "QPSK":
            ber = 0.5 * np.exp(-sinr_linear)
        elif modulation == "16QAM":
            ber = 0.75 * np.exp(-sinr_linear / 5)
        elif modulation == "64QAM":
            ber = 0.9 * np.exp(-sinr_linear / 10)
        else:
            ber = 0.5

        per = 1 - (1 - ber) ** 1000
        per = max(0.0, min(1.0, per))

        return per

    def transmission_success(
        self, sinr_db: float, modulation: str, enable_notch_filter: bool = False
    ) -> bool:
        """
        Determine if transmission is successful based on PER.

        Returns:
            True if packet received successfully
        """
        per = self.calculate_packet_error_rate(sinr_db, modulation)

        if enable_notch_filter:
            per *= 0.8

        success = self.rng.random() > per

        return success

    def calculate_energy_consumed(
        self, tx_power_dbm: float, transmission_duration_ms: float = 1.0
    ) -> float:
        """
        Calculate energy consumed for transmission.

        E = P * t

        Returns:
            Energy in millijoules (mJ)
        """
        tx_power_w = 10 ** ((tx_power_dbm - 30) / 10)

        energy_j = tx_power_w * (transmission_duration_ms / 1000)
        energy_mj = energy_j * 1000

        return energy_mj


# Utility functions

def dbm_to_watts(dbm: float) -> float:
    """Convert dBm to Watts."""
    return 10 ** ((dbm - 30) / 10)


def watts_to_dbm(watts: float) -> float:
    """Convert Watts to dBm."""
    return 10 * np.log10(watts) + 30


def db_to_linear(db: float) -> float:
    """Convert dB to linear scale."""
    return 10 ** (db / 10)


def linear_to_db(linear: float) -> float:
    """Convert linear to dB scale."""
    return 10 * np.log10(linear + 1e-10)
