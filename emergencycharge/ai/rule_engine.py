"""
AI Rule-Based Expert Advisor Engine.
Performs offline, deterministic engineering analysis of power telemetry,
identifies charging bottlenecks, cable/port constraints, and computes
safe optimization strategies. Never claims to override physical hardware limits.
"""

from dataclasses import dataclass, field
import logging
from typing import Dict, List, Optional

from emergencycharge.config import USB_SPECS
from emergencycharge.core.laptop_telemetry import LaptopBatteryInfo
from emergencycharge.core.phone_detector import PhoneConnectionInfo
from emergencycharge.core.power_estimator import ChargingEstimate

logger = logging.getLogger("emergencycharge.ai")


@dataclass
class OptimizationAction:
    category: str      # "Port Selection", "Phone Settings", "Laptop Energy", "Cable & Thermal"
    title: str
    detail: str
    impact: str        # e.g. "+200% Net Charge Rate", "Critical Safety", "+35% Transfer Efficiency"
    priority: int      # 1 = Highest


@dataclass
class AIAnalysisReport:
    summary: str
    bottlenecks: List[str]
    actions: List[OptimizationAction]
    port_advice: str
    power_advice: str
    thermal_advice: str
    physics_disclosure: str
    estimated_speed_boost_desc: str


class AIAdvisorEngine:
    """Intelligent hardware analysis and optimization engine."""

    def analyze(
        self,
        laptop_info: LaptopBatteryInfo,
        phone_info: PhoneConnectionInfo,
        estimate: ChargingEstimate,
        emergency_mode_active: bool = False,
    ) -> AIAnalysisReport:
        """Evaluates complete system telemetry and generates an optimization plan."""
        bottlenecks: List[str] = []
        actions: List[OptimizationAction] = []

        # 1. Connection check
        if not phone_info.is_connected:
            return AIAnalysisReport(
                summary="No smartphone detected. Connect your device via USB to initiate analysis.",
                bottlenecks=["No active electrical connection to smartphone."],
                actions=[
                    OptimizationAction(
                        category="Hardware Connection",
                        title="Connect Phone via USB-C or USB 3.0",
                        detail="Use a high-quality data cable plugged directly into a laptop USB port (avoid unpowered hubs).",
                        impact="Enables Emergency Power Transfer",
                        priority=1
                    )
                ],
                port_advice="Locate your laptop's USB Type-C or blue USB 3.0 port for optimal wattage.",
                power_advice="Keep laptop plugged into AC power if available, or conserve laptop battery for emergency use.",
                thermal_advice="Ensure both devices have clear ventilation.",
                physics_disclosure=(
                    "EmergencyCharge AI operates strictly within USB-IF specifications. "
                    "Software cannot exceed host motherboard current limits."
                ),
                estimated_speed_boost_desc="N/A (Device disconnected)"
            )

        # 2. Analyze Port & Measured Power
        power_w = estimate.phone_power_w or (phone_info.charging_power_w if phone_info.charging_power_w else None)
        current_ma = phone_info.charging_current_ma

        # Detect USB 2.0 limitation (approx 500mA / 2.5W)
        if power_w is not None and power_w <= 3.0:
            bottlenecks.append(
                f"Standard USB 2.0 Current Limit Detected ({power_w:.1f}W). The port is locked at 500mA Standard Downstream Port (SDP) contract."
            )
            actions.append(OptimizationAction(
                category="Port Selection",
                title="Migrate to a USB 3.0 (Blue) or USB-C Port",
                detail=(
                    "Your phone is currently drawing ~500mA (2.5W), characteristic of a legacy USB 2.0 port. "
                    "Switching to a USB 3.0 SuperSpeed port increases output to 900mA (4.5W, +80% faster), "
                    "while a Type-C port provides 1.5A to 3.0A (7.5W - 15W, up to 500% faster)."
                ),
                impact="+80% to +500% Wattage",
                priority=1
            ))
        elif power_w is not None and power_w <= 5.0:
            actions.append(OptimizationAction(
                category="Port Selection",
                title="Use USB-C Port if Available",
                detail="Port is delivering standard USB 3.0 power (~4.5W). If your laptop has a USB-C port, switching to it can provide 7.5W to 15W.",
                impact="+66% to +230% Wattage",
                priority=3
            ))

        # Check for Always-On Port (Battery Glyph)
        actions.append(OptimizationAction(
            category="Port Selection",
            title="Inspect for 'Always-On' Battery Icon Port",
            detail=(
                "Look on the sides of your laptop for a USB port with a small battery glyph or yellow tongue. "
                "These ports support USB Battery Charging (BC 1.2 CDP), delivering up to 1.5A (7.5W) even when the laptop is sleeping."
            ),
            impact="Powers Phone While Laptop Sleeps",
            priority=2
        ))

        # 3. Analyze Phone Screen & Internal Quiescent Consumption
        bottlenecks.append(
            "Phone Internal Quiescent Load: Running the phone display and background antennas consumes 1.5W - 2.5W internally."
        )
        actions.append(OptimizationAction(
            category="Phone Settings",
            title="Turn Screen OFF and Enable Airplane Mode",
            detail=(
                "A modern smartphone display and 5G cellular modem consume 1.8W - 2.8W. "
                "On a 2.5W - 4.5W laptop port, keeping the screen on leaves nearly ZERO net power for battery charging! "
                "Turning the screen off and enabling Airplane Mode triples net charging speed."
            ),
            impact="+200% Net Battery Charge Rate",
            priority=1
        ))

        # 4. Analyze Cable & USB Mode
        if phone_info.connection_mode.startswith("Windows PnP"):
            actions.append(OptimizationAction(
                category="Phone Settings",
                title="Switch Phone USB Mode to 'Charge Only'",
                detail=(
                    "When connecting an Android phone to Windows, pull down the notification shade and switch "
                    "from 'File Transfer / MTP' to 'Charge Only' (or 'Cancel' MTP). "
                    "This frees USB data endpoints and prevents MTP background sync from consuming phone battery."
                ),
                impact="+15% Faster Negotiation",
                priority=2
            ))

        # 5. Analyze Laptop Energy Preservation
        if not laptop_info.is_plugged:
            if laptop_info.percent <= 25.0:
                bottlenecks.append(f"Laptop Battery Depleted ({laptop_info.percent:.0f}%). Limited emergency reserves remaining.")
                actions.append(OptimizationAction(
                    category="Laptop Energy",
                    title="Engage Emergency Charge Mode & Lower Display Brightness",
                    detail=(
                        "Laptop is running on battery reserve. Lower your laptop display brightness to 0-10%. "
                        "Display backlights consume 4W-8W of laptop battery. Dimming the screen preserves power directly for your phone."
                    ),
                    impact="Preserves 4W-8W of Laptop Energy",
                    priority=1
                ))
            else:
                actions.append(OptimizationAction(
                    category="Laptop Energy",
                    title="Dim Laptop Screen to Maximize Energy Transfer Efficiency",
                    detail=(
                        f"Laptop is discharging at ~{laptop_info.discharge_rate_w or 16:.1f}W. "
                        "Dimming the laptop screen reduces internal laptop consumption by 30-50%, "
                        "meaning each percent of laptop battery lost transfers more energy into your smartphone."
                    ),
                    impact="+35% Transfer Efficiency",
                    priority=2
                ))

        # 6. Analyze Thermal State
        if phone_info.battery_temp_c is not None:
            if phone_info.battery_temp_c >= 38.0:
                bottlenecks.append(f"Thermal Throttling Risk: Phone battery temperature is {phone_info.battery_temp_c:.1f}°C.")
                actions.append(OptimizationAction(
                    category="Cable & Thermal",
                    title="Remove Protective Phone Case",
                    detail=(
                        "Smartphone charging controllers throttle charge current when battery temperature exceeds 38°C. "
                        "Remove thick silicone or leather cases and rest the phone on a cool, hard surface to maintain maximum charge rate."
                    ),
                    impact="Prevents Thermal Throttling",
                    priority=1
                ))

        # Sort actions by priority
        actions.sort(key=lambda a: a.priority)

        # Generate summary
        summary = (
            f"Analyzed {phone_info.device_name} on {laptop_info.power_source}. "
            f"Current effective charging: {power_w or 'Standard Port Bound'}W. "
            f"{len(bottlenecks)} optimization bottlenecks identified."
        )

        physics_disclosure = (
            "ENGINEERING PRINCIPLE & FIRMWARE CONSTRAINTS: "
            "USB power limits are physically enforced by motherboard power distribution switches (e.g. TI TPS2553) "
            "and Type-C CC line negotiation controllers (TCPC/TCPM). Windows software cannot modify physical PCB current-limiting resistors "
            "or bypass USB-IF electrical safety standards without specialized external hardware. "
            "Maximum charging speed is achieved by selecting high-output physical ports (USB 3.0 / Type-C) "
            "and eliminating quiescent power drain on both devices."
        )

        return AIAnalysisReport(
            summary=summary,
            bottlenecks=bottlenecks,
            actions=actions,
            port_advice="Use USB 3.0 (blue tongue) or USB-C port. Check for Always-On battery icon.",
            power_advice="Activate Emergency Mode to keep USB ports powered while allowing screen sleep.",
            thermal_advice="Keep phone cool and remove thick cases to avoid battery throttling.",
            physics_disclosure=physics_disclosure,
            estimated_speed_boost_desc="Following recommended optimizations (screen off + high-power port) delivers up to 3x faster net charging."
        )

    def answer_query(self, user_query: str, report: AIAnalysisReport) -> str:
        """Answers user natural language questions using the offline knowledge base."""
        q = user_query.lower()
        if "slow" in q or "why" in q:
            reasons = "\n".join([f"• {b}" for b in report.bottlenecks])
            return (
                f"### Why Charging is Slow:\n{reasons}\n\n"
                f"**Most impactful fix:** {report.actions[0].title if report.actions else 'Turn off phone screen'}.\n"
                f"{report.actions[0].detail if report.actions else ''}"
            )
        elif "hack" in q or "override" in q or "force" in q or "increase current" in q or "firmware" in q:
            return (
                f"### Hardware & Software Physics Explanation:\n\n"
                f"**Can software force more power through USB?**\n"
                f"No. Motherboard USB ports have hardware polyfuses and current-limiting ICs hardwired into the PCB. "
                f"The operating system (Windows) runs in Ring 0 / Ring 3 and cannot change the analog resistance ($R_{{ILIM}}$) "
                f"on the motherboard. Attempting to bypass these limits would trip motherboard over-current protection (OCP) or burn PCB traces.\n\n"
                f"**How to get real faster charging:**\n"
                f"1. Switch to a physical USB 3.0 (900mA / 4.5W) or USB-C (1.5A - 3.0A / 7.5W - 15W) port.\n"
                f"2. Look for the Always-On USB port (yellow tongue or battery icon).\n"
                f"3. Turn on Airplane mode and keep the phone screen off."
            )
        elif "laptop battery" in q or "drain" in q or "efficiency" in q:
            return (
                f"### Laptop Battery Preservation:\n\n"
                f"During an emergency, the laptop battery is your only energy reservoir. "
                f"A laptop running normally consumes 15W - 25W just powering its screen, CPU, and fans. "
                f"If you charge your phone at 4.5W while the laptop consumes 18W, only ~20% of your laptop's battery "
                f"actually reaches your phone! The other 80% is wasted running the laptop.\n\n"
                f"**EmergencyCharge AI Solution:**\n"
                f"Enable **Emergency Mode**. It locks USB power on, sets Windows to Away Mode, and allows you to "
                f"dim or turn off the laptop screen. This cuts laptop drain by half, doubling your energy transfer efficiency!"
            )
        elif "cable" in q:
            return (
                f"### Cable Quality & Voltage Drop:\n\n"
                f"Long or thin cables have high internal wire resistance ($R$). Under Ohm's Law ($V_{{drop}} = I \\times R$), "
                f"a 2-meter cheap cable can drop the 5.0V VBUS line down to 4.4V. "
                f"When a phone senses VBUS dropping below 4.5V, its charging IC automatically reduces charging current "
                f"from 1.5A to 500mA to prevent brownout!\n\n"
                f"**Recommendation:** Use a short (< 1 meter), thick OEM USB-C cable."
            )
        else:
            return (
                f"### EmergencyCharge AI Assessment:\n\n"
                f"{report.summary}\n\n"
                f"**Top Recommended Action:** {report.actions[0].title if report.actions else 'Keep phone screen off'}\n"
                f"{report.actions[0].detail if report.actions else ''}\n\n"
                f"**Hardware Port Advice:** {report.port_advice}\n\n"
                f"**Safe Limits:** {report.physics_disclosure}"
            )
