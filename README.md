# SOLA4237 Demo

This repository contains code and sample datasets used in a demo-lecture for the UNSW SPREE course SOLA4237.

## Description

A case study in getting to know a new dataset before analysing it. We've been given one month of
5-minute household circuit data (load, solar, battery, grid) for sites participating in a virtual
power plant (VPP) trial, measured by a smart device and shared via a third party. The
[marimo](https://marimo.io) notebook in `notebooks/` walks through exploring the data's structure,
checking its contents, and identifying any data quality issues.

The notebook is a demo prop for the session rather than a finished analysis. Many cells are
intentionally left empty to be filled in live.

## Getting Started

### Prerequisites

- **uv**, a Python package and project manager. Install it by following the
  [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) for your
  operating system. You don't need to install Python separately: uv will download the right
  version for this project.
- **git** (optional), if you'd like to clone the repository rather than download a ZIP.

### Installing

1. **Get a copy of the code**, either by cloning with git:

    ```bash
    git clone https://github.com/EllieKallmier/sola-4237-demo.git
    cd sola-4237-demo
    ```

    or by clicking the green **Code** button on GitHub, choosing **Download ZIP**, and unzipping it.

    The data files are included in the repository, in the `data/` folder:

    ```text
    data/
    ├── case_study/
    │   ├── nsw_wholesale_price.parquet
    │   ├── site_metadata.csv
    │   └── vpp_circuit_data.parquet
    ├── results/
    │   ├── all_site_bills.csv
    │   └── monthly_vpp_throughput.csv
    └── tariff.json
    ```

2. **Set up the environment.** Open a terminal in the project folder (the one containing
   `pyproject.toml`) and run:

    ```bash
    uv sync
    ```

    This creates a virtual environment in a `.venv/` folder, installs Python 3.13 if you don't
    already have it, and installs the exact package versions listed in `uv.lock`. Nothing is
    installed globally, so it won't interfere with your other projects.

### Running the notebook

From the project folder, run:

```bash
uv run marimo edit notebooks/case_study_exploration.py
```

`uv run` runs the command inside this project's virtual environment, so there's no need to
activate it first. marimo will open the notebook in your web browser. To stop it, go back to the
terminal and press `Ctrl + C`.

### Troubleshooting

- **`uv: command not found`** (or "not recognised" on Windows): close and reopen your terminal
  after installing uv, so it can find the newly installed program.
- **`FileNotFoundError` when the notebook loads data**: check the data files are still in the
  folders shown in step 1, with the same file names.

## Authors

Ellie Kallmier

Email: [e.kallmier@unsw.edu.au](mailto:e.kallmier@unsw.edu.au)
