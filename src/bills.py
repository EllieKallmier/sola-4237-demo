import json

import pandas as pd


def calculate_all_site_bills(
    all_site_data: pd.DataFrame, tariff: dict, year: int | None = 2025
) -> pd.DataFrame:
    # Billing months are only meaningful for whole calendar months, so trim to a
    # single year by default. Pass year=None to bill whatever's in the data.
    if year is not None:
        all_site_data = all_site_data[all_site_data.index.year == year]
    sites = all_site_data.groupby("site_id")

    results = []
    for site, data in sites:
        site_bill = calculate_single_bill(data, tariff)
        site_bill["site_id"] = site
        results.append(site_bill)

    return pd.concat(results, axis=0)


def calculate_single_bill(site_data: pd.DataFrame, tariff: dict) -> pd.DataFrame:
    tou_charges = calculate_tou_charges(site_data, tariff)
    fit_credits = calculate_fit(site_data, tariff)
    fixed_charge_and_credit = calculate_fixed(site_data, tariff)
    wholesale_cost = calculate_wholesale_cost(site_data)

    combined = tou_charges.join(
        [fit_credits, fixed_charge_and_credit, wholesale_cost], how="outer"
    ).sort_index()
    # periods sort chronologically; the string label is for chart titles etc.
    combined.insert(0, "month_label", combined.index.strftime("%B %Y"))

    charge_cols = [c for c in combined.columns if c.endswith("_charge")]
    credit_cols = [c for c in combined.columns if c.endswith("_credit")]
    combined["total_monthly_bill"] = combined[charge_cols].sum(axis=1) - combined[
        credit_cols
    ].sum(axis=1)
    numeric_cols = charge_cols + credit_cols + ["wholesale_cost", "total_monthly_bill"]
    combined[numeric_cols] = combined[numeric_cols].round(2)
    return combined


def label_tou_periods(site_data: pd.DataFrame, tariff: dict) -> pd.DataFrame:
    site_data = site_data.copy().reset_index().set_index("local_datetime")
    if not isinstance(site_data.index, pd.DatetimeIndex):
        raise ValueError("site_data index is not datetime index!")

    site_data["TOU"] = ""

    params = tariff["Parameters"]
    tou_bands = params["TOU"]
    for band_type, band in tou_bands.items():
        months = set(band["Month"])
        mask = site_data.index.month.isin(months)

        weekdays = set([0, 1, 2, 3, 4]) if band["Weekday"] else set()
        weekends = set([5, 6]) if band["Weekend"] else set()
        mask &= site_data.index.weekday.isin(weekdays | weekends)

        time_mask = pd.Series(data=False, index=site_data.index)
        for start_str, end_str in band["TimeIntervals"].values():
            time_mask |= _interval_time_mask_helper(site_data, start_str, end_str)
        mask &= time_mask

        site_data.loc[mask, "TOU"] = band_type

    if any(site_data["TOU"] == ""):
        raise ValueError("some of the periods didn't get labelled!")

    return site_data


def _month_period(index: pd.DatetimeIndex) -> pd.PeriodIndex:
    """Month of each timestamp as a period, so months from different years don't
    collide and sort chronologically. Timestamps are already local time, so the
    timezone is dropped explicitly rather than by a pandas warning."""
    return index.tz_localize(None).to_period("M")


def _interval_time_mask_helper(df: pd.DataFrame, start: str, end: str) -> pd.Series:
    start_time = (pd.Timestamp(start) + pd.Timedelta(5, "minutes")).time()
    end_time = (pd.Timestamp(end) + pd.Timedelta(5, "minutes")).time()

    if start_time < end_time:
        return (df.index.time >= start_time) & (df.index.time < end_time)
    else:
        return (df.index.time >= start_time) | (df.index.time < end_time)


def calculate_tou_charges(data: pd.DataFrame, tariff: dict) -> pd.DataFrame:
    labelled = label_tou_periods(data, tariff)
    labelled["month"] = _month_period(labelled.index)
    labelled["import"] = labelled["grid_net_load"].clip(lower=0.0)

    monthly_totals = (
        labelled.groupby(["month", "TOU"])["import"].sum(skipna=True).reset_index()
    )
    monthly_totals["usage_charge"] = 0.0
    for band_name, band in tariff["Parameters"]["TOU"].items():
        charge = monthly_totals["TOU"] == band_name
        monthly_totals.loc[charge, "usage_charge"] = (
            monthly_totals.loc[charge, "import"] * band["Value"]
        )

    totals = monthly_totals.pivot(columns="TOU", index="month", values="usage_charge")
    totals = totals.rename(
        columns={
            col: f"{col.lower().replace(' ', '_')}_charge" for col in totals.columns
        }
    ).rename_axis(columns=None)
    return totals


def calculate_fit(site_data: pd.DataFrame, tariff: dict) -> pd.Series:
    data = site_data.copy()
    data["export"] = data["grid_net_load"].clip(upper=0.0) * -1.0
    data["month"] = _month_period(data.index)
    data["date"] = data.index.date

    daily_export = (
        data.groupby(["month", "date"])["export"].sum(skipna=True).reset_index()
    )
    daily_export["feed_in_credit"] = 0.0

    prev_bound = 0.0
    for block in tariff["Parameters"]["BlockDailyFiT"].values():
        high_bound = float(block["HighBound"])

        export_between = daily_export["export"].clip(upper=high_bound) - prev_bound
        daily_export["feed_in_credit"] += (
            export_between.clip(lower=0.0) * block["Value"]
        )
        prev_bound = high_bound

    return daily_export.groupby("month")["feed_in_credit"].sum(skipna=True)


def calculate_fixed(site_data: pd.DataFrame, tariff: dict) -> pd.DataFrame:
    data = site_data.copy()
    data["month"] = _month_period(data.index)
    data["date"] = data.index.date
    data = data.drop_duplicates(subset=["date"])

    days = data.groupby("month")["date"].count().reset_index()
    days["daily_charge"] = days["date"] * tariff["Parameters"]["Daily"]["Value"]
    days["monthly_vpp_credit"] = 15.00

    return days[["month", "daily_charge", "monthly_vpp_credit"]].set_index("month")


def calculate_wholesale_cost(site_data: pd.DataFrame) -> pd.Series:
    df = site_data.copy()
    df["month"] = _month_period(df.index)

    df["wholesale_cost"] = df["grid_net_load"] * (df["RRP"] / 1000)

    monthly = df.groupby("month")["wholesale_cost"].sum(skipna=True)
    return monthly


def read_tariff_json() -> dict:
    filename = "data/tariff.json"
    with open(filename, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    all_site_data = pd.read_parquet("results/vpp_operation_results.parquet")
    tariff = read_tariff_json()

    bills = calculate_all_site_bills(all_site_data, tariff)
    bills.to_csv("results/all_site_bills.csv")
