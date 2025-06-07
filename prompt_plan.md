### **Phase 1: The Blueprint**

Here is a detailed, step-by-step blueprint for building the Personal Cash Flow Simulator. This plan prioritizes building a solid foundation and then adding features incrementally.

#### **Core Idea: Isolate, Build, Test, Integrate**

We will build each piece of logic in isolation first (e.g., P&L calculation, simulation engine) with its own unit tests. Once the core logic is proven, we will integrate it into the CLI and write integration tests to ensure the pieces work together with the file system.

---

#### **High-Level Iterative Chunks**

1.  **Chunk 1: Project Scaffolding & Data Loading.**
    *   **Goal:** Set up the basic project structure, dependencies, and create reliable functions to load the `config.yaml` and `ledger.csv` files.
    *   **Why first?** Nothing else can happen without being able to access the core data. Testing this in isolation prevents file I/O errors from complicating later steps.

2.  **Chunk 2: Basic CLI Structure.**
    *   **Goal:** Create the main entry point (`cli.py`) using `argparse`. Define the `simulator` and `summarize` subcommands and their arguments (`--user`, `--window`, `--month`).
    *   **Why second?** This creates the skeleton of the application. The commands won't *do* anything yet, but we can test that the argument parsing works correctly, which is a common source of bugs.

3.  **Chunk 3: The `summarize` Command - Logic & Integration.**
    *   **Goal:** Implement the full functionality of the `summarize` command. This is chosen before the `simulator` because it's less complex.
    *   **Sub-steps:**
        *   A) Implement the P&L calculation logic as a pure function.
        *   B) Implement the uncategorized transaction identification logic as a pure function.
        *   C) Integrate these functions into the `summarize` CLI handler, connecting them to the data loaders and file system outputs.

4.  **Chunk 4: The `simulator` Command - Core Engine.**
    *   **Goal:** Build the basic day-by-day simulation engine.
    *   **Why this scope?** We'll focus *only* on iterating through days, applying transactions, and calculating the running balance. We will explicitly *exclude* the complex "Intelligent Transfer Rule" for now. This isolates the core looping mechanism.

5.  **Chunk 5: The `simulator` Command - Intelligent Transfer Rule.**
    *   **Goal:** Implement the "Intelligent Transfer Rule" with its look-ahead stress test.
    *   **Why a separate chunk?** This is the most complex piece of business logic. It needs dedicated, careful unit tests against multiple scenarios (full surplus, partial surplus with holdback, no surplus) before we attempt to integrate it.

6.  **Chunk 6: The `simulator` Command - Full Integration.**
    *   **Goal:** Combine the core engine (Chunk 4) and the intelligent transfer rule (Chunk 5) into a final simulation function. Then, wire this complete function into the `simulator` CLI handler, generating the final console and CSV outputs.

---

### **Phase 2: Detailed, "Right-Sized" Steps & Prompts**

Now, let's break down those chunks into smaller, actionable steps and formulate the corresponding LLM prompts. Each prompt is designed to be a self-contained unit of work that includes testing.

---
### **Prompt 1: Project Setup and Dependencies**

**Context:** This is the first step. We need the basic directory structure and a way to manage dependencies. We will use `pyproject.toml` for modern Python project management.

```text
We are starting a new Python project: a "Personal Cash Flow Simulator & Reporter". The full specification is provided below for your reference.

Your first task is to set up the project's basic file structure and dependency management file.

1.  Create the following directory and file structure. The Python files should be empty for now, but the `__init__.py` files are important for packaging.

    ```
    personal_finance/
    ├── pyproject.toml
    ├── src/
    │   ├── __init__.py
    │   ├── cli.py
    │   ├── simulator.py
    │   └── summarize.py
    └── tests/
        └── __init__.py
    ```

2.  Populate the `pyproject.toml` file. We need `pytest` and `pytest-mock` for testing, `pyfakefs` for filesystem mocking, `pandas` for data handling, and `PyYAML` for configuration. Specify a Python version of 3.10 or higher.

**Project Specification (for context):**
<PASTE THE ENTIRE spec.md HERE>
```

---
### **Prompt 2: Data Models and Loading Functions (TDD)**

**Context:** Before we can build any features, we must be able to reliably load our data sources: `config.yaml` and `ledger.csv`. We will create dedicated functions for this and test them thoroughly using a mocked filesystem.

```text
We are building a personal finance CLI. In the previous step, we set up the project structure. Now, we will create and test the data loading functions. We will use a Test-Driven Development (TDD) approach.

**Task: Create and test functions to load `config.yaml` and `ledger.csv`.**

**1. Create the Test File and Test User Directory:**
Create a new file: `tests/test_data_loader.py`. In this file, write `pytest` tests for two functions that don't exist yet: `load_config` and `load_ledger`. 

Instead of using mocks, we'll create actual test user directories with real files:

1. Create a directory structure:
   ```
   users/
   ├── testuser/
   │   ├── config.yaml
   │   └── ledger.csv
   └── empty_user/
       ├── config.yaml
       └── ledger.csv (with just headers)
   ```

2. The tests should cover:
   - `test_load_config`: Successfully loads the YAML file and returns a dictionary.
   - `test_load_ledger`: Successfully loads the CSV file and returns a pandas DataFrame.
   - `test_load_ledger_handles_empty`: Gracefully handles an empty (or headers-only) `ledger.csv`.
   - `test_load_config_file_not_found`: Raises a `FileNotFoundError` if `config.yaml` is missing.
   - `test_load_ledger_file_not_found`: Raises a `FileNotFoundError` if `ledger.csv` is missing.

**`tests/test_data_loader.py`:**
```python
import pytest
import pandas as pd
from pathlib import Path

# Assume the functions will be in `src.data_loader`
from src.data_loader import load_config, load_ledger

@pytest.fixture
def user_dir(fs):
    """Create a fake user directory using pyfakefs."""
    user_path = Path("/fake_users/testuser")
    fs.create_dir(user_path)

    # Create fake config.yaml
    config_content = """
account_nickname: Test Account
current_balance: 1000.00
target_balance: 500.00
categories:
  - Revenue
  - Fixed
  - Variable
"""
    fs.create_file(user_path / "config.yaml", contents=config_content)

    # Create fake ledger.csv
    ledger_content = """date,amount,description,category,forecast
2023-01-01,-100.00,Rent,Fixed,0
2023-01-05,2000.00,Paycheck,Revenue,0
"""
    fs.create_file(user_path / "ledger.csv", contents=ledger_content)

    return user_path

def test_load_config(user_dir):
    config = load_config(user_dir)
    assert config is not None
    assert config['current_balance'] == 1000.00
    assert "Fixed" in config['categories']

def test_load_ledger(user_dir):
    ledger_df = load_ledger(user_dir)
    assert not ledger_df.empty
    assert len(ledger_df) == 2
    assert 'date' in ledger_df.columns
    # Ensure date is parsed as an object/string for now
    assert ledger_df['date'].dtype == 'object'

def test_load_ledger_handles_empty(fs):
    user_path = Path("/fake_users/empty_user")
    fs.create_dir(user_path)
    fs.create_file(user_path / "ledger.csv", contents="date,amount,description,category,forecast\n")
    
    ledger_df = load_ledger(user_path)
    assert ledger_df.empty
    assert list(ledger_df.columns) == ["date", "amount", "description", "category", "forecast"]

def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config(Path("/non_existent_user"))

def test_load_ledger_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_ledger(Path("/non_existent_user"))

```

**2. Create the Implementation File:**
Now, create a new file `src/data_loader.py`. Write the `load_config` and `load_ledger` functions to make the tests pass. Use `pathlib`, `PyYAML`, and `pandas`.

- `load_config` should take a `Path` object to the user directory and return a dictionary.
- `load_ledger` should take a `Path` object to the user directory and return a pandas DataFrame. Ensure the `dtype` for all columns is explicitly set to `str` during CSV read to avoid pandas auto-parsing dates and numbers in ways we don't want yet. We will handle type
conversions later. Set `keep_default_na=False` to prevent empty strings from being read as `NaN`.

**Project Specification (for context):**
<PASTE THE ENTIRE spec.md HERE>
```

---
### **Prompt 3: CLI Skeleton with `argparse`**

**Context:** We have our data loaders. Now let's build the command-line interface framework. The commands won't have any logic yet, but we'll set up the entire parser structure and test that it correctly identifies commands and arguments.

```text
We have successfully created data loading functions. The next step is to build the CLI skeleton using Python's `argparse` module. We will define the main command and its two subcommands, `summarize` and `simulator`, along with their respective arguments.

**Task: Implement the CLI argument parser in `src/cli.py`.**

**1. Update the Test File:**
Create a new test file: `tests/test_cli.py`. Write tests to verify the `argparse` setup. These tests should not execute any logic, but rather inspect the parsed arguments.

The tests should cover:
- Parsing the `summarize` command with its required arguments (`--user`, `--month`).
- Parsing the `simulator` command with its required (`--user`) and optional (`--window`) arguments.
- Checking the default value for `--window` is 60.
- Testing that the parser raises an error if required arguments are missing.

**`tests/test_cli.py`:**
```python
import pytest
from src.cli import create_parser

def test_parser_for_summarize_command():
    parser = create_parser()
    args = parser.parse_args(['summarize', '--user', 'chad', '--month', '202312'])
    assert args.command == 'summarize'
    assert args.user == 'chad'
    assert args.month == '202312'

def test_parser_for_simulator_command():
    parser = create_parser()
    args = parser.parse_args(['simulator', '--user', 'chad', '--window', '90'])
    assert args.command == 'simulator'
    assert args.user == 'chad'
    assert args.window == 90

def test_parser_for_simulator_default_window():
    parser = create_parser()
    args = parser.parse_args(['simulator', '--user', 'chad'])
    assert args.window == 60

def test_parser_missing_user():
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['summarize', '--month', '202312'])

def test_parser_missing_month():
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['summarize', '--user', 'chad'])
```

**2. Implement the Parser in `src/cli.py`:**
Modify the `src/cli.py` file. Create a function `create_parser()` that builds and returns the `argparse.ArgumentParser`. Then, create a `main()` function that uses this parser. For now, the `main()` function will just parse the args and print them.

**`src/cli.py`:**
```python
import argparse
from pathlib import Path

def create_parser():
    parser = argparse.ArgumentParser(description="Personal Cash Flow Simulator & Reporter.")
    
    # Base path for user data
    base_user_path = Path("./users")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Summarize command
    parser_summarize = subparsers.add_parser("summarize", help="Generate a P&L summary for a specific month.")
    parser_summarize.add_argument("--user", type=str, required=True, help="The name of the user directory.")
    parser_summarize.add_argument("--month", type=str, required=True, help="The month to summarize in YYYYMM format.")
    
    # Simulator command
    parser_simulator = subparsers.add_parser("simulator", help="Project cash flow over a given time window.")
    parser_simulator.add_argument("--user", type=str, required=True, help="The name of the user directory.")
    parser_simulator.add_argument("--window", type=int, default=60, help="The number of days to simulate (default: 60).")

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()
    
    print(f"Executing command: {args.command}")
    # We will add logic to call handlers in a later step.
    # For now, this is just a placeholder.
    if args.command == "summarize":
        print(f"User: {args.user}, Month: {args.month}")
    elif args.command == "simulator":
        print(f"User: {args.user}, Window: {args.window}")

if __name__ == "__main__":
    main()

```
Make sure `src/cli.py` can be run as a module via `python -m src.cli`. This means the `main()` function should be called within a `if __name__ == "__main__":` block.
```

---
### **Prompt 4: `summarize` Command Core Logic (TDD)**

**Context:** We are now ready to build the first piece of business logic. To ensure it's correct and reusable, we'll create the P&L calculation and uncategorized transaction filtering as *pure functions* in `src/summarize.py`. They will operate on DataFrames, not files.

```text
We have a working CLI parser. Now we'll implement the core logic for the `summarize` command. This will be done in a TDD fashion, focusing on pure functions that we can integrate into the CLI later.

**Task: Create and test functions for P&L calculation and finding uncategorized transactions.**

**1. Create the Test File:**
Create a new file: `tests/test_summarize.py`. Write `pytest` tests for two new functions: `find_uncategorized` and `calculate_pnl`.

The tests should cover:
- `find_uncategorized`: Correctly identifies rows where the 'category' is not in the provided list of valid categories.
- `calculate_pnl`:
    - Correctly filters transactions for a given month (e.g., '2023-12').
    - Correctly groups by category and sums the amounts.
    - Handles cases with no transactions in the given month.
    - Correctly calculates derived totals like 'Total Revenue', 'Total Expense', and 'Net Surplus/Deficit'.

**`tests/test_summarize.py`:**
```python
import pytest
import pandas as pd
from src.summarize import find_uncategorized, calculate_pnl

@pytest.fixture
def sample_transactions():
    data = {
        'date': ['2023-12-05', '2023-12-15', '2023-12-20', '2023-12-25', '2024-01-01'],
        'amount': [2000.00, -1200.00, -50.00, -75.50, -1200.00],
        'description': ['Paycheck', 'Rent', 'Gas', 'Grokeries', 'Rent'],
        'category': ['Revenue', 'Fixed', 'Variable', 'Varaible', 'Fixed'], # Note the typos
        'forecast': [0, 0, 0, 0, 1]
    }
    return pd.DataFrame(data)

@pytest.fixture
def valid_categories():
    return ['Revenue', 'Fixed', 'Variable', 'Misc Income', 'Misc Expense', 'Investment']

def test_find_uncategorized(sample_transactions, valid_categories):
    uncategorized_df = find_uncategorized(sample_transactions, valid_categories)
    assert len(uncategorized_df) == 2
    assert 'Grokeries' in uncategorized_df['description'].values
    assert 'Varaible' in uncategorized_df['category'].values

def test_calculate_pnl(sample_transactions, valid_categories):
    pnl = calculate_pnl(sample_transactions, '202312', valid_categories)
    
    assert pnl['Revenue']['Paycheck'] == 2000.00
    assert pnl['Fixed']['Rent'] == -1200.00
    assert pnl['Variable']['Gas'] == -50.00
    
    # Check that the uncategorized transaction is NOT included
    assert 'Grokeries' not in pnl.get('Variable', {})
    
    # Check that transactions from other months are excluded
    assert len(pnl.get('Fixed', {})) == 1

    # Check summary calculations
    assert pnl['summary']['Total Revenue'] == 2000.00
    assert pnl['summary']['Total Expense'] == -1250.00
    assert pnl['summary']['Net Surplus/Deficit'] == 750.00

def test_calculate_pnl_no_transactions():
    empty_df = pd.DataFrame(columns=['date', 'amount', 'description', 'category', 'forecast'])
    pnl = calculate_pnl(empty_df, '202312', ['Revenue', 'Fixed'])
    
    assert pnl['summary']['Total Revenue'] == 0
    assert pnl['summary']['Total Expense'] == 0
    assert pnl['summary']['Net Surplus/Deficit'] == 0
```

**2. Implement the Logic in `src/summarize.py`:**
Now, in `src/summarize.py`, write the `find_uncategorized` and `calculate_pnl` functions to make the tests pass.

- The functions should accept a pandas DataFrame and other necessary parameters, not file paths.
- For `calculate_pnl`, ensure you correctly handle date filtering. The input month is `YYYYMM`. You'll need to convert the 'date' column in the DataFrame to datetime objects for reliable filtering.
- The P&L logic should create a nested dictionary structure for easy reporting.

**Project Specification (for context):**
<PASTE THE ENTIRE spec.md HERE>
```

---
### **Prompt 5: Integrate `summarize` Logic into the CLI**

**Context:** We have tested, pure functions for our `summarize` logic. Now is the time for integration. We will modify `cli.py` to call these functions and produce the final output as described in the spec, including console messages and file outputs. This requires an integration test.

```text
We have our core `summarize` logic functions tested and ready. The next step is to integrate them into our CLI. We will create a handler function for the `summarize` command that uses our existing data loaders and the new logic functions to produce the final output.

**Task: Create a `summarize_handler` and wire it into the main CLI function.**

**1. Create an Integration Test:**
Update `tests/test_cli.py` to include a full integration test for the `summarize` command. This test MUST use `pyfakefs` to simulate the user directory, `config.yaml`, and `ledger.csv`. It should also use the `capsys` fixture to capture `stdout`.

The test should:
- Create a user directory with a ledger that has both valid and invalid categories.
- Run the `main` CLI function with `summarize` arguments.
- Assert that the correct P&L summary is printed to the console.
- Assert that `WARNING` messages for uncategorized items are printed.
- Assert that an `uncategorized_{date}.csv` file is created and contains the correct data.

**Add this test to `tests/test_cli.py`:**
```python
from src.cli import main
from unittest.mock import patch
import datetime

def test_summarize_integration(fs, capsys):
    # Setup mock filesystem
    user_path = Path("/fake_users/integration_user")
    fs.create_dir(user_path)
    config_content = "categories:\n  - Revenue\n  - Fixed\n  - Variable"
    fs.create_file(user_path / "config.yaml", contents=config_content)
    ledger_content = (
        "date,amount,description,category,forecast\n"
        "2023-12-05,2000.00,Paycheck,Revenue,0\n"
        "2023-12-15,-1200.00,Rent,Fixed,0\n"
        "2023-12-20,-75.00,TypoCategory,Fun,0\n" # This is uncategorized
    )
    fs.create_file(user_path / "ledger.csv", contents=ledger_content)
    
    # Mock the command-line arguments using patch
    test_args = ['cli.py', 'summarize', '--user', 'integration_user', '--month', '202312']
    with patch('sys.argv', test_args):
        # We also need to patch the Path to our fake users directory
        with patch('src.cli.base_user_path', Path("/fake_users")):
            main()

    # Assertions
    captured = capsys.readouterr()
    
    # Check for warning in console output
    assert "WARNING: Uncategorized transaction found" in captured.out
    assert "TypoCategory" in captured.out
    
    # Check for correct P&L summary in console output
    assert "Total Revenue: 2000.00" in captured.out
    assert "Total Expense: -1200.00" in captured.out
    assert "Net Surplus/Deficit: 800.00" in captured.out
    
    # Check that the uncategorized file was created
    today_str = datetime.date.today().strftime('%Y%m%d')
    uncategorized_file = user_path / f"uncategorized_{today_str}.csv"
    assert uncategorized_file.exists()
    
    with open(uncategorized_file, 'r') as f:
        content = f.read()
        assert "TypoCategory" in content
        assert "Paycheck" not in content
```

**2. Update `src/cli.py` and `src/summarize.py`:**
Refactor your code to make the test pass.

**In `src/summarize.py`:**
- Create a new top-level function `generate_summary_report(ledger_df, config, month)`. This function will orchestrate calls to `find_uncategorized` and `calculate_pnl`. It should return a tuple: `(pnl_data, uncategorized_df)`.
- Create another function `format_pnl_output(pnl_data)` that takes the P&L dictionary and returns a nicely formatted string for printing to the console.

**In `src/cli.py`:**
- Import the necessary functions from `data_loader` and `summarize`.
- Create a new function `summarize_handler(args)`.
- This handler will:
    a. Construct the user path: `base_user_path / args.user`.
    b. Call `load_config` and `load_ledger`.
    c. Call `generate_summary_report`.
    d. Print warnings for each row in the returned `uncategorized_df`.
    e. Print the formatted P&L report to the console.
    f. If `uncategorized_df` is not empty, save it to `uncategorized_{date}.csv`.
- Modify the `main` function to call `summarize_handler(args)` when the command is "summarize".

This structure cleanly separates CLI parsing, orchestration, and core logic.
```

---
### **Prompt 6: `simulator` Core Engine (TDD)**

**Context:** Now we'll start on the simulator. The first step is to build the core engine that iterates day-by-day and calculates a running balance. We will specifically *exclude* the intelligent transfer rule for now to keep the logic focused.

```text
The `summarize` command is complete. We now begin work on the `simulator`. Our first step is to build the core daily simulation engine. This function will take a starting balance and a list of transactions and produce a day-by-day breakdown of the cash flow. We will ignore the "Intelligent Transfer Rule" for now.

**Task: Create and test the basic daily simulation logic.**

**1. Create the Test File:**
Create a new file `tests/test_simulator.py`. Write `pytest` tests for a new function `run_simulation_engine`.

The tests should cover:
- A simple simulation with a few transactions, verifying the `start_balance`, `net_change`, and `end_balance` for each day.
- A simulation where multiple transactions occur on the same day.
- A simulation where the balance drops below the target balance, verifying the `alert_type` is correctly set to `BELOW_TARGET`.
- A simulation with no transactions, which should just carry the start balance forward each day.

**`tests/test_simulator.py`:**
```python
import pytest
import pandas as pd
from datetime import date, timedelta
from src.simulator import run_simulation_engine

@pytest.fixture
def sample_sim_transactions():
    # Transactions for a 10-day window
    data = {
        'date': ['2024-01-02', '2024-01-05', '2024-01-05', '2024-01-08'],
        'amount': [-1500.00, 2500.00, -50.00, -800.00],
        'description': ['Rent', 'Paycheck', 'Spotify', 'Car Payment'],
        'category': ['Fixed', 'Revenue', 'Variable', 'Fixed'],
        'forecast': [1, 1, 1, 1]
    }
    df = pd.DataFrame(data)
    # Ensure date column is datetime for sorting and comparison
    df['date'] = pd.to_datetime(df['date'])
    return df

def test_run_simulation_engine_basic(sample_sim_transactions):
    start_date = date(2024, 1, 1)
    window_days = 10
    start_balance = 2000.00
    target_balance = 1000.00
    
    sim_results_df = run_simulation_engine(
        start_balance, target_balance, sample_sim_transactions, start_date, window_days
    )

    assert len(sim_results_df) == window_days
    
    # Day 1 (Jan 1) - No transactions
    day1 = sim_results_df.iloc[0]
    assert day1['start_balance'] == 2000.00
    assert day1['net_change'] == 0
    assert day1['end_balance'] == 2000.00
    assert day1['alert_type'] == 'OK'

    # Day 2 (Jan 2) - Rent payment
    day2 = sim_results_df.iloc[1]
    assert day2['start_balance'] == 2000.00
    assert day2['net_change'] == -1500.00
    assert day2['end_balance'] == 500.00
    assert day2['alert_type'] == 'BELOW_TARGET'
    
    # Day 5 (Jan 5) - Paycheck and Spotify
    day5 = sim_results_df.iloc[4]
    assert day5['start_balance'] == 500.00 # End balance of previous day
    assert day5['net_change'] == 2450.00
    assert day5['end_balance'] == 2950.00
    assert day5['alert_type'] == 'OK'
```

**2. Implement the Logic in `src/simulator.py`:**
In `src/simulator.py`, write the `run_simulation_engine` function to make the tests pass.

- The function signature should be `run_simulation_engine(start_balance, target_balance, transactions_df, start_date, window_days)`.
- Internally, it should loop from `start_date` for `window_days`.
- For each day, it should:
    a. Filter `transactions_df` for transactions on that day.
    b. Calculate `net_change`.
    c. Calculate `end_balance`.
    d. Determine the `alert_type` by comparing `end_balance` to `target_balance`.
    e. Store the results for each day (a list of dictionaries is a good intermediate format).
- Finally, return a pandas DataFrame with the schema specified in `spec.md` (`date`, `start_balance`, `transactions_summary`, `net_change`, `end_balance`, `alert_type`).
- **Important:** This function will NOT include the intelligent transfer logic yet.
```

---
### **Prompt 7: Intelligent Transfer Rule Logic (TDD)**

**Context:** This is the most complex piece of logic. We need to implement and test the "Intelligent Transfer Rule" in complete isolation before integrating it into the main simulation loop.

```text
With the core simulation engine built, we will now tackle the most complex feature: the Intelligent Transfer Rule. We will create a dedicated function for this logic and test it against various scenarios to ensure its robustness.

**Task: Create and test the `calculate_intelligent_transfer` function.**

**1. Create the Test File:**
Add new tests to `tests/test_simulator.py` for a function named `calculate_intelligent_transfer`.

The tests must cover three key scenarios:
- **Scenario 1: Full Transfer.** The month-end balance is high, and the look-ahead stress test shows the balance never drops below the target in the next 30 days. The function should recommend transferring the full surplus.
- **Scenario 2: Partial Transfer with Holdback.** The month-end balance is high, but the stress test predicts a future dip below the target (e.g., due to a large rent payment). The function should calculate a holdback amount and recommend a smaller transfer.
- **Scenario 3: No Transfer.** The month-end balance is already below the target, so no transfer should be recommended.

**Add these tests to `tests/test_simulator.py`:**
```python
from src.simulator import calculate_intelligent_transfer

def test_calculate_intelligent_transfer_full_surplus():
    # End-of-month balance is 5000, target is 2500. Surplus = 2500.
    # Future 30-day projection has a lowest balance of 3000, which is > target.
    # Should recommend transferring the full 2500.
    month_end_balance = 5000.00
    target_balance = 2500.00
    
    # Mock a future projection where the minimum is well above target
    future_30_day_balances = pd.Series([4000, 3500, 3000, 4500])
    
    recommended_transfer = calculate_intelligent_transfer(
        month_end_balance, target_balance, future_30_day_balances
    )
    assert recommended_transfer == 2500.00

def test_calculate_intelligent_transfer_with_holdback():
    # End-of-month balance is 5000, target is 2500. Surplus = 2500.
    # Future 30-day projection has a lowest balance of 1500.
    # Shortfall = 2500 (target) - 1500 (lowest) = 1000.
    # Recommended transfer = 2500 (surplus) - 1000 (holdback) = 1500.
    month_end_balance = 5000.00
    target_balance = 2500.00
    
    # Mock a future projection with a dip below target
    future_30_day_balances = pd.Series([4000, 1500, 2000, 3500])
    
    recommended_transfer = calculate_intelligent_transfer(
        month_end_balance, target_balance, future_30_day_balances
    )
    assert recommended_transfer == 1500.00

def test_calculate_intelligent_transfer_no_surplus():
    # End-of-month balance is below target. No surplus to transfer.
    month_end_balance = 2000.00
    target_balance = 2500.00
    future_30_day_balances = pd.Series([1500, 1000, 500])
    
    recommended_transfer = calculate_intelligent_transfer(
        month_end_balance, target_balance, future_30_day_balances
    )
    assert recommended_transfer == 0

def test_calculate_intelligent_transfer_holdback_exceeds_surplus():
    # Surplus is 500. Shortfall is 1000. Holdback (1000) > Surplus (500).
    # Recommended transfer should be 0, not negative.
    month_end_balance = 3000.00
    target_balance = 2500.00
    future_30_day_balances = pd.Series([2000, 1500, 2500])
    
    recommended_transfer = calculate_intelligent_transfer(
        month_end_balance, target_balance, future_30_day_balances
    )
    assert recommended_transfer == 0.0
```

**2. Implement the Logic in `src/simulator.py`:**
Now, in `src/simulator.py`, write the `calculate_intelligent_transfer` function to make the tests pass.

- The function signature should be `calculate_intelligent_transfer(month_end_balance, target_balance, future_30_day_balances)`.
- It takes the balance at the end of the month, the target balance, and a pandas Series containing the projected `end_balance` for the *next 30 days*.
- Implement the decision logic exactly as described in the specification and tested above. Ensure the recommended transfer cannot be negative.
```

---
### **Prompt 8: Integrate Simulator and Finalize CLI**

**Context:** This is the final step. We have the core simulation engine and the intelligent transfer logic. Now we will combine them into a single, high-level simulation function and wire it into the `simulator` CLI command.

```text
This is the final implementation step. We will now integrate the "Intelligent Transfer Rule" into the main simulation loop and connect the entire simulator feature to the CLI. This involves creating a top-level orchestration function in `simulator.py` and a handler in `cli.py`.

**Task: Fully integrate the simulator logic and connect it to the CLI.**

**1. Create the Final Integration Test:**
Update `tests/test_cli.py` with a full integration test for the `simulator` command. Use `pyfakefs` and `capsys`.

This test case is crucial. It must set up a scenario that triggers the intelligent transfer rule.
- Create a user directory with config/ledger.
- The ledger should cause a large surplus at the end of the first month, but have a large expense (e.g., rent) early in the second month.
- Run the `main` CLI function with `simulator` arguments.
- Assert that the console output includes a "SYSTEM_TRANSFER" recommendation with the *correctly reduced* holdback amount.
- Assert that the `simulation_output_{date}.csv` file is created.
- Read the CSV and verify that the virtual transfer transaction appears on the 1st of the next month and that the balances reflect this.

**Add this test to `tests/test_cli.py`:**
```python
def test_simulator_integration_with_intelligent_transfer(fs, capsys):
    # Setup mock filesystem
    user_path = Path("/fake_users/sim_user")
    fs.create_dir(user_path)
    config_content = "current_balance: 3000.00\ntarget_balance: 2500.00"
    fs.create_file(user_path / "config.yaml", contents=config_content)
    # End of Jan surplus, but big rent payment on Feb 2nd will cause a dip
    ledger_content = (
        "date,amount,description,category,forecast\n"
        "2024-01-30,4000.00,Big Project,Revenue,1\n"  # EOM balance will be high
        "2024-02-02,-3000.00,Rent,Fixed,1\n" # This causes the future dip
    )
    fs.create_file(user_path / "ledger.csv", contents=ledger_content)
    
    # Mock date to be Jan 1st, 2024 for predictable simulation
    with patch('datetime.date', new=datetime.date(2024, 1, 1)):
        test_args = ['cli.py', 'simulator', '--user', 'sim_user', '--window', '60']
        with patch('sys.argv', test_args):
            with patch('src.cli.base_user_path', Path("/fake_users")):
                main()

    captured = capsys.readouterr()
    # Check for the system transfer recommendation in the console
    assert "SYSTEM_TRANSFER" in captured.out
    # Check that transfer is < 5000 (initial surplus is ~4500)
    # EOM Balance on 1/31: 3000+4000=7000. Surplus=4500.
    # Lookahead lowpoint on 2/2: Bal on 2/1 is 7000, Bal on 2/2 is 4000.
    # Re-sim from 1/31 with transfer: bal=7000. transfer=4500. bal on 2/1=2500. Bal on 2/2 = -500.
    # shortfall = 2500 - (-500) = 3000. recommended = 4500 - 3000 = 1500.
    assert "Recommended Transfer: 1500.00" in captured.out 
    
    today_str = datetime.date(2024, 1, 1).strftime('%Y%m%d')
    output_file = user_path / f"simulation_output_{today_str}.csv"
    assert output_file.exists()
    
    # Verify the virtual transaction was added in the output CSV
    sim_df = pd.read_csv(output_file)
    transfer_day = sim_df[sim_df['date'] == '2024-02-01']
    assert not transfer_day.empty
    assert 'Surplus Transfer' in transfer_day.iloc[0]['transactions_summary']
    assert transfer_day.iloc[0]['net_change'] == -1500.00
```

**2. Update `src/simulator.py` and `src/cli.py`:**

**In `src/simulator.py`:**
- Create a new, top-level function `generate_simulation_report(start_balance, target_balance, transactions_df, start_date, window_days)`.
- This function will be the main orchestrator. It will:
    a. Loop day-by-day.
    b. At the end of each day's calculation, check if it's the last business day of a month.
    c. If so, it will perform the look-ahead stress test by running a *temporary, in-memory* simulation for the next 30 days.
    d. It will then call `calculate_intelligent_transfer` with the results of the stress test.
    e. If a transfer is recommended, it will create a *virtual transaction* (a new row for the `transactions_df`) for the 1st of the next month. This virtual transaction must only exist for the lifetime of the simulation run and NOT be saved to the user's `ledger.csv`.
- This function should return the final simulation DataFrame.

**In `src/cli.py`:**
- Create a `simulator_handler(args)` function.
- This handler will:
    a. Load config and ledger.
    b. Prepare data (e.g., convert date strings to datetime objects).
    c. Get `start_date` (today) and other parameters from the config and args.
    d. Call the new `generate_simulation_report` function.
    e. Format and print a console summary, highlighting any alerts.
    f. Save the returned DataFrame to `simulation_output_{date}.csv`.
- Modify the `main` function to call `simulator_handler(args)` when the command is "simulator".

This completes the project, wiring all tested logic into the final CLI application.

