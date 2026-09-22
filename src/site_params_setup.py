import random

import pandas as pd

random.seed(4237)

BATTERY_OPTIONS = {
    "tesla_3_10kW_doubled": dict(
        usable_storage_capacity=13.5 * 2, power=10 * 2, round_trip_efficiency=0.89
    ),
    "tesla_2_doubled": dict(
        usable_storage_capacity=13.5 * 2, power=5 * 2, round_trip_efficiency=0.9
    ),
    "sungrow_doubled": dict(
        usable_storage_capacity=16 * 2, power=9.6 * 2, round_trip_efficiency=0.9
    ),
    "byd_doubled": dict(
        usable_storage_capacity=16.56 * 2, power=7.6 * 2, round_trip_efficiency=0.96
    ),
    "enphase_double_doubled": dict(
        usable_storage_capacity=10.0 * 2, power=7.68 * 2, round_trip_efficiency=0.96
    ),
    "tesla_3_10kW": dict(
        usable_storage_capacity=13.5, power=10, round_trip_efficiency=0.89
    ),
    "tesla_2": dict(usable_storage_capacity=13.5, power=5, round_trip_efficiency=0.9),
    "sungrow": dict(usable_storage_capacity=16, power=9.6, round_trip_efficiency=0.9),
    "byd": dict(usable_storage_capacity=16.56, power=7.6, round_trip_efficiency=0.96),
    "enphase_double": dict(
        usable_storage_capacity=10.0, power=7.68, round_trip_efficiency=0.96
    ),
}


def set_starting_params(site_ids: set[str]):
    starting_battery_params = []
    for site in site_ids:
        battery_name = random.choice(list(BATTERY_OPTIONS.keys()))
        battery = BATTERY_OPTIONS[battery_name]
        starting_params = dict(
            site_id=site,
            battery_name=battery_name,
            usable_storage_capacity=battery["usable_storage_capacity"],
            power_rating=battery["power"],
            round_trip_efficiency=battery["round_trip_efficiency"],
            starting_soc=0.3,  # allocate same starting SoC for all sites - assume some overnight consumption
        )

        starting_battery_params.append(starting_params)
    return pd.DataFrame(starting_battery_params)


def get_site_characteristics() -> tuple[pd.DataFrame, set[str]]:
    all_sites_data = pd.read_parquet(
        "data/meter_data/household_load_pv_5min_2025.parquet"
    )
    all_sites_data["local_datetime"] = pd.to_datetime(
        all_sites_data["datetime"], utc=True
    ).dt.tz_convert("Australia/Sydney")

    by_site = all_sites_data.groupby("site_id")

    characteristics = []
    site_ids = []
    for site, data in by_site:
        data = data.set_index("local_datetime").sort_index()

        data["net_load"] = data["load_kwh"] - data["pv_kwh"]

        charcteristic_dict = {
            "site_id": site,
            "gross_load": data["load_kwh"].sum(),
            "gross_gen": data["pv_kwh"].sum(),
            "net_import": data[data["net_load"] > 0]["net_load"].sum(),
            "net_export": data[data["net_load"] < 0]["net_load"].sum(),
        }
        characteristics.append(charcteristic_dict)
        site_ids.append(str(site))

    return pd.DataFrame(characteristics), set(site_ids)


def combine_site_level_info(
    characteristics: pd.DataFrame, starting_params: pd.DataFrame
) -> pd.DataFrame:
    return pd.merge(
        characteristics.set_index("site_id"),
        starting_params.set_index("site_id"),
        how="outer",
        on="site_id",
    )


if __name__ == "__main__":
    characteristics, site_ids = get_site_characteristics()
    starting_params = set_starting_params(site_ids)
    site_level_setup = combine_site_level_info(characteristics, starting_params)

    pv_metadata = pd.read_csv("data/metadata.csv")
    with_pv_metadata = site_level_setup.merge(
        pv_metadata.set_index("site_id"), how="outer", on="site_id"
    )

    with_pv_metadata.to_csv("data/site_params.csv")
