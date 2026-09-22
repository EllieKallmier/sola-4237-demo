import os

import numpy as np
import pandas as pd

# -------------------------
# Utility: make result dirs
# -------------------------
RESULTS_DIR = "results"

for d in [RESULTS_DIR]:
    os.makedirs(d, exist_ok=True)


# -------------------------
# Parameters
# -------------------------
VPP_EVENT_MIN_DISCHARGE_PRICE = 300
MIN_CAPACITY_LIMIT = 0.2  # minimum SoC left in battery for owner = 20%
MONTHLY_CUMSUM_ALLOCATION = 250 / 12

TIMESTEP_HOURS = 5 / 60  # 5 minute intervals = 1/12h for power<->energy conversion

battery_starting_params = pd.read_csv("data/site_params.csv", index_col="site_id")

# -------------------------
# Input Data
# -------------------------
wholesale_prices = pd.read_parquet("data/nsw_wholesale_price.parquet")

all_sites_load_and_pv = pd.read_parquet(
    "data/meter_data/household_load_pv_5min_2025.parquet"
)
all_sites_load_and_pv["local_datetime"] = pd.to_datetime(
    all_sites_load_and_pv["datetime"], utc=True
).dt.tz_convert("Australia/Sydney")


def get_site_load_data(all_sites: pd.DataFrame, site_id: str) -> pd.DataFrame:
    site_data = (
        all_sites[all_sites["site_id"] == site_id].copy().set_index("local_datetime")
    )
    # add wholesale prices:
    with_prices = pd.merge(site_data, wholesale_prices, on="local_datetime", how="left")
    # and net load:
    with_prices["net_load"] = with_prices["load_kwh"] - with_prices["pv_kwh"]
    return with_prices


# -------------------------
# Operation
# -------------------------


def self_consumption(
    prev_soe: float,
    net_load: float,
    power_rating: float,
    max_capacity: float,
    efficiency: float,
):
    # net_load is already kWh per interval, so no TIMESTEP_HOURS conversion here
    # (only the kW power_rating needs converting to kWh)
    charge_energy = max(0.0, -net_load) * efficiency
    discharge_energy = max(0.0, net_load) / efficiency

    c = min(
        charge_energy,
        power_rating * TIMESTEP_HOURS * efficiency,
        max_capacity - prev_soe,
    )
    d = min(
        discharge_energy, power_rating * TIMESTEP_HOURS / efficiency, prev_soe - 0.0
    )
    new_soe = np.clip(prev_soe + c - d, 0.0, max_capacity)

    return new_soe, c, d


def event_discharge(
    prev_soe: float,
    power_rating: float,
    max_capacity: float,
    efficiency: float,
):
    min_soe = max_capacity * MIN_CAPACITY_LIMIT
    discharge_energy = power_rating * TIMESTEP_HOURS / efficiency

    c = 0.0
    d = min(
        discharge_energy,
        prev_soe - min_soe,
    )
    new_soe = np.clip(prev_soe + c - d, min_soe, max_capacity)

    return new_soe, c, d


def battery_operation_loop(
    site_data: pd.DataFrame,
    max_capacity: float,
    power_rating: float,
    round_trip_efficiency: float,
    starting_soc: float,
):
    prices = site_data["RRP"]
    net_load = site_data["net_load"]

    # losses are split evenly between charging and discharging, so each direction
    # gets sqrt(round trip) and a full charge -> discharge cycle costs round trip
    efficiency = np.sqrt(round_trip_efficiency)
    min_event_soe = max_capacity * MIN_CAPACITY_LIMIT

    monthly_cumsum = 0.0
    total_cumsum = 0.0
    prev_soe = starting_soc * max_capacity
    prev_month = site_data.index[0].month
    result_rows = [
        {
            "local_datetime": site_data.index[0],
            "soe": prev_soe,
            "charge": 0.0,
            "discharge": 0.0,
            "event": False,
        }
    ]
    for timestamp in site_data.index[1:]:
        if timestamp.month != prev_month:
            # reset monthly cumsum each calendar month - used to help spread
            # discharging across the year; can mean some under-use of total allowance!
            monthly_cumsum = 0.0
            prev_month = timestamp.month

        # the orchestrator can only dispatch while there's charge above the 20%
        # owner reserve (the owner can still use the battery down to 0%)
        discharge_event = (
            prices[timestamp].astype(float) > VPP_EVENT_MIN_DISCHARGE_PRICE
            and prev_soe > min_event_soe
        )
        close_to_total_cumsum_limit = total_cumsum > 248
        passed_monthly_cumsum_allocation = monthly_cumsum >= MONTHLY_CUMSUM_ALLOCATION

        vpp_discharge = 0.0
        if close_to_total_cumsum_limit or passed_monthly_cumsum_allocation:
            new_soe, charge, discharge = self_consumption(
                prev_soe, net_load[timestamp], power_rating, max_capacity, efficiency
            )
            event = False
        elif discharge_event:
            new_soe, charge, discharge = event_discharge(
                prev_soe, power_rating, max_capacity, efficiency
            )
            vpp_discharge = discharge
            event = True
        else:
            new_soe, charge, discharge = self_consumption(
                prev_soe, net_load[timestamp], power_rating, max_capacity, efficiency
            )
            event = False

        res = {
            "local_datetime": timestamp,
            "soe": new_soe,
            "charge": charge,
            "discharge": discharge,
            "event": event,
        }
        result_rows.append(res)

        prev_soe = new_soe
        monthly_cumsum += vpp_discharge
        total_cumsum += vpp_discharge

    return pd.DataFrame(result_rows).set_index("local_datetime")


# -------------------------
# Workflow
# -------------------------


def run_site(site_id: str) -> pd.DataFrame:
    site_params = battery_starting_params.loc[site_id]
    site_data = get_site_load_data(all_sites_load_and_pv, site_id)

    battery_results = battery_operation_loop(
        site_data,
        max_capacity=site_params["usable_storage_capacity"],
        power_rating=site_params["power_rating"],
        round_trip_efficiency=site_params["round_trip_efficiency"],
        starting_soc=site_params["starting_soc"],
    )
    # keep the inputs alongside the battery behaviour so each site's output
    # can be checked/plotted on its own
    site_results = site_data[["load_kwh", "pv_kwh", "net_load", "RRP"]].join(
        battery_results
    )
    # charge/discharge are the change in energy stored in the battery, so convert
    # them to what actually flows through the house's connection before adding
    # to net_load. Positive = importing from the grid, negative = exporting.
    one_way_efficiency = np.sqrt(site_params["round_trip_efficiency"])
    site_results["grid_net_load"] = (
        site_results["net_load"]
        + site_results["charge"] / one_way_efficiency
        - site_results["discharge"] * one_way_efficiency
    )
    site_results["site_id"] = site_id
    return site_results


def run_all_sites() -> pd.DataFrame:
    all_results = [run_site(site_id) for site_id in battery_starting_params.index]
    return pd.concat(all_results)


if __name__ == "__main__":
    results = run_all_sites()
    results.to_parquet(os.path.join(RESULTS_DIR, "vpp_operation_results.parquet"))
