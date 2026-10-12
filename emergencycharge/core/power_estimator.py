"""
Charging Measurement, Power Math, and Estimation Engine.
Calculates authentic power, CC/CV charging duration models,
and emergency energy transfer efficiency.
"""

from dataclasses import dataclass
import math
from typing import Optional, Tuple

from emergencycharge.config import DEFAULT_PHONE_CAPACITY_MAH, TYPICAL_BATTERY_NOMINAL_VOLTAGE, USB_SPECS


@dataclass
class ChargingEstimate:
    is_measurable: bool
    phone_power_w: Optional[float]           # Watts into phone
    laptop_discharge_w: Optional[float]      # Watts leaving laptop battery
    transfer_efficiency_pct: Optional[float] # % of laptop energy reaching phone
    time_to_80_mins: Optional[int]           # Fast charge CC phase
    time_to_100_mins: Optional[int]          # Full charge CC+CV phase
    charge_rate_pct_per_hour: Optional[float]
    estimation_notes: str


class PowerEstimator:
    """Calculates charging performance and energy transfer efficiency."""

    def __init__(self, phone_capacity_mah: float = DEFAULT_PHONE_CAPACITY_MAH):
        self.phone_capacity_mah = phone_capacity_mah
        # Total battery energy in Watt-hours
        self.phone_energy_wh = (self.phone_capacity_mah * TYPICAL_BATTERY_NOMINAL_VOLTAGE) / 1000.0

    def calculate_estimate(
        self,
        phone_percent: Optional[float],
        measured_power_w: Optional[float],
        port_spec_key: str = "USB_3_0",
        laptop_discharge_w: Optional[float] = None,
        phone_screen_on: bool = False,
        is_simulated: bool = False,
    ) -> ChargingEstimate:
        """
        Calculates power, charging times, and system efficiency.
        If real power is not measurable, falls back to port spec boundaries without fabricating.
        """
        spec = USB_SPECS.get(port_spec_key, USB_SPECS["USB_3_0"])

        # Determine effective charging power
        effective_power_w: float
        is_measurable = False

        if measured_power_w is not None and measured_power_w > 0.05:
            effective_power_w = measured_power_w
            is_measurable = True
        else:
            effective_power_w = spec.power_watts
            is_measurable = is_simulated  # Only considered measurable if simulation or real sensor

        # Internal phone consumption:
        # Screen off + standby: ~0.3W. Screen on with apps: ~2.0W - 2.5W!
        phone_internal_drain_w = 2.2 if phone_screen_on else 0.35
        dc_dc_efficiency = 0.88  # Typical phone PMIC switching buck regulator efficiency

        net_battery_power_w = max(0.1, (effective_power_w * dc_dc_efficiency) - phone_internal_drain_w)

        # Rate of charge (% per hour)
        rate_pct_per_hour = round((net_battery_power_w / self.phone_energy_wh) * 100.0, 1)

        # Time to full estimation using multi-stage CC/CV curve
        time_to_80_mins: Optional[int] = None
        time_to_100_mins: Optional[int] = None

        if phone_percent is not None and 0.0 <= phone_percent < 100.0:
            current_pct = phone_percent

            # Constant Current phase (up to 80%)
            if current_pct < 80.0:
                delta_to_80 = 80.0 - current_pct
                energy_needed_80_wh = (delta_to_80 / 100.0) * self.phone_energy_wh
                hours_80 = energy_needed_80_wh / net_battery_power_w
                time_to_80_mins = max(1, int(round(hours_80 * 60.0)))
            else:
                time_to_80_mins = 0

            # Constant Voltage phase (80% to 100%): current tapers, average power is ~50%
            if current_pct < 100.0:
                delta_to_100 = 100.0 - max(80.0, current_pct)
                energy_needed_100_wh = (delta_to_100 / 100.0) * self.phone_energy_wh
                # Tapered power during CV
                tapered_net_power = max(0.08, net_battery_power_w * 0.50)
                hours_cv = energy_needed_100_wh / tapered_net_power
                cv_mins = int(round(hours_cv * 60.0))

                time_to_100_mins = (time_to_80_mins or 0) + cv_mins

        # Emergency Energy Transfer Efficiency
        transfer_eff_pct: Optional[float] = None
        if laptop_discharge_w and laptop_discharge_w > 0.5:
            # Efficiency = (Power entering phone / Power leaving laptop battery) * 100%
            ratio = (effective_power_w / laptop_discharge_w) * 100.0
            transfer_eff_pct = round(min(100.0, ratio), 1)

        # Generate engineering notes
        notes = []
        if is_measurable:
            notes.append(f"Authentic telemetry: {effective_power_w:.2f}W measured.")
        else:
            notes.append(f"Port capability bound: {spec.name} ({spec.power_watts:.1f}W max).")

        if phone_screen_on:
            notes.append("WARNING: Phone display is ON, consuming ~2W internally. Turning display off triples net charging rate.")
        else:
            notes.append("Phone display standby: Internal phone quiescent load minimized (~0.35W).")

        if transfer_eff_pct:
            notes.append(f"Laptop-to-phone energy transfer efficiency: {transfer_eff_pct}% (Remaining energy powers laptop).")

        return ChargingEstimate(
            is_measurable=is_measurable,
            phone_power_w=round(effective_power_w, 2) if is_measurable else None,
            laptop_discharge_w=round(laptop_discharge_w, 2) if laptop_discharge_w else None,
            transfer_efficiency_pct=transfer_eff_pct,
            time_to_80_mins=time_to_80_mins,
            time_to_100_mins=time_to_100_mins,
            charge_rate_pct_per_hour=rate_pct_per_hour,
            estimation_notes=" | ".join(notes),
        )
