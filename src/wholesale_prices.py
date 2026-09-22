import pandas as pd
from nemosis import dynamic_data_compiler

RAW_DATA_CACHE = "set/this/path/where/you/want"

SAVE_FILE_NAME = "nsw_wholesale_price"

PRICE_TABLE = "DISPATCHPRICE"
PRICE_COLUMNS = ["REGIONID", "SETTLEMENTDATE", "RRP"]

REGION = "NSW1"


def get_wholesale_prices(start_date: str, end_date: str):
    price_data = _fetch_data_table(PRICE_TABLE, start_date, end_date, PRICE_COLUMNS)
    return _clean_data_table(price_data)


def _fetch_data_table(
    table: str, start_date: str, end_date: str, columns: list[str]
) -> pd.DataFrame:
    return dynamic_data_compiler(
        start_time=start_date,
        end_time=end_date,
        table_name=table,
        raw_data_location=RAW_DATA_CACHE,
        select_columns=columns,
        filter_cols=["REGIONID"],
        filter_values=([REGION],),
        fformat="parquet",
        keep_csv=False,
    )


def _clean_data_table(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["SETTLEMENTDATE", "REGIONID"], keep="first")
    df["SETTLEMENTDATE"] = pd.to_datetime(df["SETTLEMENTDATE"])
    df = (
        df.sort_values(by="SETTLEMENTDATE")
        .reset_index(drop=True)
        .set_index("SETTLEMENTDATE")
    )
    df["local_datetime"] = df.index.tz_localize("Australia/Brisbane").tz_convert(
        "Australia/Sydney"
    )

    return df.reset_index(drop=True).set_index("local_datetime")


if __name__ == "__main__":
    prices = get_wholesale_prices("2024/12/31 00:00:00", "2026/01/01 12:00:00")
    prices.to_parquet(f"data/{SAVE_FILE_NAME}.parquet")
