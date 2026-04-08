"""
Tests for wireless physics simulation
"""

import pytest
import numpy as np
from anti_jamming_env.physics import WirelessChannel


def test_path_loss_increases_with_distance():
    """Path loss should increase with distance."""
    channel = WirelessChannel(frequency_ghz=2.4)
    
    loss_100m = channel.path_loss_db(distance_m=100)
    loss_200m = channel.path_loss_db(distance_m=200)
    
    assert loss_200m > loss_100m


def test_snr_decreases_with_lower_power():
    """SNR should decrease when transmit power decreases."""
    channel = WirelessChannel(random_seed=42)
    
    snr_high = channel.calculate_snr(tx_power_dbm=30.0, channel_idx=0)
    snr_low = channel.calculate_snr(tx_power_dbm=10.0, channel_idx=0)
    
    assert snr_high > snr_low


def test_sinr_worse_than_snr_with_interference():
    """SINR should be worse than SNR when interference present."""
    channel = WirelessChannel(random_seed=42)
    
    sinr, snr = channel.calculate_sinr(
        tx_power_dbm=20.0,
        channel_idx=10,
        interference_power_dbm=15.0  # Strong interference
    )
    
    assert sinr < snr


def test_throughput_increases_with_higher_modulation():
    """Higher modulation schemes should provide higher throughput."""
    channel = WirelessChannel(random_seed=42)
    
    sinr = 20.0  # Good SINR
    
    tp_bpsk = channel.calculate_throughput(sinr, "BPSK", "2/3")
    tp_64qam = channel.calculate_throughput(sinr, "64QAM", "2/3")
    
    assert tp_64qam > tp_bpsk


def test_energy_consumption_proportional_to_power():
    """Energy consumption should increase with transmit power."""
    channel = WirelessChannel()
    
    energy_low = channel.calculate_energy_consumed(tx_power_dbm=10.0)
    energy_high = channel.calculate_energy_consumed(tx_power_dbm=30.0)
    
    assert energy_high > energy_low