import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd

    return mo, pd


@app.cell
def _(mo):
    mo.md(r"""
    # VPP trial case study: getting to know the data

    Household circuit data for sites participating in a VPP trial, measured by
    a smart (IoT) device and shared with us via a third party.
    """)
    return


@app.cell
def _(mo):
    # mo.notebook_dir() is the folder this file lives in, so paths work
    # regardless of which directory marimo was launched from
    DATA_DIR = mo.notebook_dir().parent / "data" / "case_study"
    return (DATA_DIR,)


@app.cell
def _(DATA_DIR, pd):
    circuit_data = pd.read_parquet(DATA_DIR / "vpp_circuit_data.parquet")
    site_metadata = pd.read_csv(DATA_DIR / "site_metadata.csv")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 1. Structural information

    What format is the data in? What's the internal structure? What does each
    field mean, and what units is it in? If it's timeseries: what features are important
    to know and have documented for your reference later?
    """)
    return


@app.cell
def _():
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Data spec

    | Field | Notes |
    |---|---|
    | File format(s) | |
    | Structure (long / wide) | |
    | Fields + units | |
    | Timezone | |
    | Interval length + labelling | |
    | Polarity conventions | |
    | Open questions for the data provider | |
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 2. Statistical information

    What do we need to understand about the *contents* of the data itself? Is there
    anything that you're curious about that we can explore here?
    """)
    return


@app.cell
def _():
    INTERVALS_PER_DAY = 288  # 5-minute intervals

    def average_daily_by_circuit(data):
        """Average daily total per site (rows) and circuit (columns), in source units.

        Uses mean interval value x intervals per day rather than summing calendar
        days: this avoids picking a day boundary (i.e. a timezone), and missing
        intervals don't drag the average down.
        """
        return (
            data.groupby(["site_id", "circuit"])["value"]
            .mean()
            .mul(INTERVALS_PER_DAY)
            .unstack("circuit")
        )

    def count_missing_by_circuit(data):
        """Number of NaN values per site (rows) and circuit (columns)."""
        return (
            data.assign(missing=data["value"].isna())
            .groupby(["site_id", "circuit"])["missing"]
            .sum()
            .unstack("circuit")
        )

    return


@app.cell
def _():
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 3. Sense-checking

    What do we expect household load, solar and battery data to look like?
    Does this data match?
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
