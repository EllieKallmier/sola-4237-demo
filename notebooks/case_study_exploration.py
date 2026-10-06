import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px

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
    RESULTS_DIR = mo.notebook_dir().parent / "data" / "results"
    return DATA_DIR, RESULTS_DIR


@app.cell
def _(DATA_DIR, RESULTS_DIR, pd):
    circuit_data = pd.read_parquet(DATA_DIR / "vpp_circuit_data.parquet")
    site_metadata = pd.read_csv(DATA_DIR / "site_metadata.csv")
    bill_results = pd.read_csv(RESULTS_DIR / "all_site_bills.csv")
    monthly_throughput = pd.read_csv(RESULTS_DIR / "monthly_vpp_throughput.csv")
    return (circuit_data,)


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
    # initial exploration of the raw data: circuit_data, site_metadata, bill_results, monthly_throughput
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### 1.1 Data spec

    #### Guiding questions:
    1. What formats are the data given in?
    2. What types of data do we actually have?
    3. Is the raw data in long or wide format?
    4. What are the present fields, and what units are they given in?
    5. What timezone is the data (a) given to us in and (b) situated in?
    6. How long are timeseries intervals? Are they start/end labelled?
    7. Is there a polarity convention across the dataset - what is it?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 1.2 Transforms to make life easier

    Sometimes it's just worth doing a few small transforms to the data you're working with, for a few reasons - like avoiding issues down the track with daylight savings times, or if you know you'll forget that these data are in Wh not kWh.

    Things like:
    - Reshaping from long->wide (or vice versa)
    - Converting units (power<->energy, orders of magnitude)
    - Renaming columns to be more obvious/clear
    - Localising datetime dtypes to the wall-clock timezone (being careful not to lose information)
    """)
    return


@app.cell
def _():
    # apply any quality-of-life transforms that you want
    # make sure you're using clear, distinct variable names - particularly in marimo notebooks but also everywhere!!
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 2. Statistical information

    What do we want to understand about the *contents* of the data itself (before we start combining things)?

    If we need to report back about any issues in the circuit data - what issues might we expect to see, and how can we test for them?
    """)
    return


@app.cell
def _():
    # describe - high level
    return


@app.function
def count_missing_by_circuit(data):
    # A quick helper to get started:
    """Number of NaN values per site (rows) and circuit (columns)."""
    return (
        data.assign(missing=data["value"].isna())
        .groupby(["site_id", "circuit"])["missing"]
        .sum()
        .unstack("circuit")
    )


@app.cell
def _():
    # run and observe results for missing data counts
    return


@app.cell
def _():
    # anything else useful or interesting to check out here?
    return


@app.cell
def _(circuit_data, mo):
    # Marimo built-in dropdown: lets us pick a single site's circuit data to explore
    site_picker = mo.ui.dropdown(
        options=sorted(circuit_data["site_id"].unique()),
        value="site_001",
        label="Site",
    )
    site_picker
    return (site_picker,)


@app.cell
def _(circuit_data, site_picker):
    site_data = circuit_data[circuit_data["site_id"] == site_picker.value]
    return


@app.cell
def _():
    # Sense-check: quick visualisation to look at a single site's circuit data
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.1 Challenge

    Can you identify all the 'issues' within the `circuit_data` dataset?

    Create a brief summary of the types of issues, number and ID of sites affected by each, whether the issue is 'fixable' and if so, how you would fix it.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Combine & explore results

    If you don't already have a specific visualisation or result that you've been asked to prepare, it's choose your own adventure.

    Question: ?

    Hypothesis: ?

    What data/combinations do you need to start answering your question?
    """)
    return


@app.cell
def _():
    # Get started with some pseudo-code
    return


if __name__ == "__main__":
    app.run()
