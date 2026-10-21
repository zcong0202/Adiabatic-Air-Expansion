"""Dry-air source limits. Illustrative calculations, not a jet/CFD prediction."""
import argparse
import json
import math
from pathlib import Path


def calculate(ambient_c, recovered_cold_c, actual_cold_l_min, diameters_mm):
    if not all(math.isfinite(v) for v in [ambient_c, recovered_cold_c, actual_cold_l_min, *diameters_mm]):
        raise ValueError("Inputs must be finite")
    if recovered_cold_c <= -273.15 or actual_cold_l_min <= 0 or not diameters_mm or min(diameters_mm) <= 0:
        raise ValueError("Temperature, flow or diameter outside physical range")
    pressure_pa, gas_constant, cp = 101325.0, 287.05, 1005.0
    density = pressure_pa / (gas_constant * (recovered_cold_c + 273.15))
    volume_m3_s = actual_cold_l_min / 60000.0
    mass_kg_s = density * volume_m3_s
    return {
        "status": "Assumed inputs; no measured AA performance inferred",
        "inputs": {"ambient_c": ambient_c, "recovered_cold_c": recovered_cold_c,
                   "actual_cold_l_min": actual_cold_l_min, "cold_pressure_pa": pressure_pa},
        "cold_mass_flow_kg_s": mass_kg_s,
        "source_sensible_capacity_w": mass_kg_s * cp * (ambient_c - recovered_cold_c),
        "outlets": [{"equivalent_diameter_mm": d,
                     "mean_exit_speed_m_s": volume_m3_s / (math.pi * (d / 1000.0) ** 2 / 4.0),
                     "actual_flow_for_2_m_s_l_min": 2.0 * math.pi * (d / 1000.0) ** 2 / 4.0 * 60000.0}
                    for d in diameters_mm],
        "limitations": ["Near-atmospheric dry air, constant cp, recovered cold temperature.",
                        "Actual cold-branch L/min; inlet SLPM is not interchangeable.",
                        "2 m/s is an illustration, not a comfort limit or required speed.",
                        "No prediction of reach, entrainment, skin cooling, source response or wind.",
                        "More source flow can change vortex cold temperature; these are not independent measured controls."]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ambient", type=float, default=35)
    parser.add_argument("--cold", type=float, default=5)
    parser.add_argument("--flow", type=float, default=100)
    parser.add_argument("--diameters", type=float, nargs="+", default=[10, 20, 30, 40, 50])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = calculate(args.ambient, args.cold, args.flow, args.diameters)
    payload = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(payload + "\n")
    else:
        print(payload)
