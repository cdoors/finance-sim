# `todo.md`

This document outlines the development tasks for the **Personal Cash Flow Simulator & Reporter** project. It follows a structured, test-driven, and iterative approach.

## Phase 1: Project Scaffolding & Foundation

*   [x] **1.1: Initialize Project Structure**
    *   [x] Create `personal_finance/` root directory.
    *   [x] Create `src/` directory with `__init__.py`, `cli.py`, `simulator.py`, `summarize.py`.
    *   [x] Create `tests/` directory with `__init__.py`.
*   [x] **1.2: Setup Dependency Management**
    *   [x] Create `pyproject.toml`.
    *   [x] Add project metadata (name, version, authors).
    *   [x] Specify Python version (`>=3.10`).
    *   [x] Add production dependencies: `pandas`, `PyYAML`.
    *   [x] Add development dependencies: `pytest`, `pytest-mock`, `pyfakefs`.

## Phase 2: Data Loading Layer (TDD)

*   [x] **2.1: Write Tests for Data Loaders**
    *   [x] Create `tests/test_data_loader.py`.
    *   [x] Create a test user directory with sample config.yaml and ledger.csv files.
    *   [x] Write `test_load_config` to verify successful YAML parsing using the real test files.
    *   [x] Write `test_load_ledger` to verify successful CSV parsing into a DataFrame.
    *   [x] Write `test_load_ledger_handles_empty` for a CSV with only headers.
    *   [x] Write `test_load_config_file_not_found` to check for `FileNotFoundError`.
    *   [x] Write `test_load_ledger_file_not_found` to check for `FileNotFoundError`.
*   [x] **2.2: Implement Data Loader Functions**
    *   [x] Create `src/data_loader.py`.
    *   [x] Implement `load_config(user_dir)` function using `PyYAML` and `pathlib`.
    *   [x] Implement `load_ledger(user_dir)` function using `pandas` and `pathlib`.
    *   [x] Ensure all tests in `tests/test_data_loader.py` pass.

## Phase 3: CLI Skeleton

*   [x] **3.1: Write Tests for `argparse` Skeleton**
    *   [x] Create `tests/test_cli.py`.
    *   [x] Write `test_parser_for_summarize_command` to check arguments (`--user`, `--month`).
    *   [x] Write `test_parser_for_simulator_command` to check arguments (`--user`, `--window`).
    *   [x] Write `test_parser_for_simulator_default_window` to verify the default value (60).
    *   [x] Write tests for missing required arguments (`test_parser_missing_user`, `test_parser_missing_month`).
*   [x] **3.2: Implement `argparse` Skeleton**
    *   [x] In `src/cli.py`, implement `create_parser()` function.
    *   [x] Define the main parser and subparsers for `summarize` and `simulator`.
    *   [x] Add all specified arguments and their properties (required, type, default).
    *   [x] Create a `main()` function that calls the parser.
    *   [x] Ensure `src/cli.py` is runnable via `python -m src.cli`.
    *   [x] Ensure all tests in `tests/test_cli.py` pass.

## Phase 4: `summarize` Command Implementation (TDD)

*   [x] **4.1: Develop Core Logic (Unit Tests)**
    *   [x] Create `tests/test_summarize.py`.
    *   [x] Write tests for `find_uncategorized()` function.
    *   [x] Write tests for `calculate_pnl()` function, covering:
        *   [x] Correct monthly filtering.
        *   [x] Correct grouping and summation by category.
        *   [x] Correct calculation of summary fields (Total Revenue, Total Expense, Net).
        *   [x] Graceful handling of months with no transactions.
*   [x] **4.2: Implement Core Logic**
    *   [x] In `src/summarize.py`, implement `find_uncategorized(transactions_df, valid_categories)`.
    *   [x] In `src/summarize.py`, implement `calculate_pnl(transactions_df, month_str, valid_categories)`.
    *   [x] Ensure all unit tests in `tests/test_summarize.py` pass.
*   [x] **4.3: Integrate `summarize` Logic into CLI (Integration Test)**
    *   [x] Add `test_summarize_integration` to `tests/test_cli.py`.
    *   [x] Use `unittest.mock` to mock file operations for `config.yaml` and `ledger.csv`.
    *   [x] The test `ledger.csv` must contain uncategorized items.
    *   [x] Use `capsys` to capture `stdout`.
    *   [x] Assert correct P&L summary is printed.
    *   [x] Assert `WARNING` messages for uncategorized items are printed.
    *   [x] Assert `uncategorized_{date}.csv` is created with the correct content.
*   [x] **4.4: Implement CLI Handler**
    *   [x] In `src/summarize.py`, create orchestration and formatting functions:
        *   [x] `generate_summary_report(ledger_df, config, month)`
        *   [x] `format_pnl_output(pnl_data)`
    *   [x] In `src/cli.py`, create `summarize_handler(args)`.
    *   [x] Wire the handler to call data loaders and `generate_summary_report`.
    *   [x] Implement console printing and file-saving logic within the handler.
    *   [x] Update `main()` to dispatch to `summarize_handler`.
    *   [x] Ensure the new integration test passes.

## Phase 5: `simulator` Command Implementation (TDD)

*   [x] **5.1: Develop Core Simulation Engine (Unit Tests)**
    *   [x] Create `tests/test_simulator.py`.
    *   [x] Write tests for `run_simulation_engine()` function, covering:
        *   [x] Correct day-by-day balance calculation.
        *   [x] Correct handling of multiple transactions on one day.
        *   [x] Correct flagging of `BELOW_TARGET` alerts.
        *   [x] Correct handling of days with no transactions.
*   [x] **5.2: Implement Core Simulation Engine**
    *   [x] In `src/simulator.py`, implement `run_simulation_engine(...)`.
    *   [x] Ensure the function returns a DataFrame with the correct schema.
    *   [x] Ensure all `run_simulation_engine` tests pass.
*   [x] **5.3: Develop Intelligent Transfer Rule (Unit Tests)**
    *   [x] Add tests for `calculate_intelligent_transfer()` to `tests/test_simulator.py`.
    *   [x] Test "Full Transfer" scenario (no future shortfall).
    *   [x] Test "Partial Transfer with Holdback" scenario (predicted future shortfall).
    *   [x] Test "No Transfer" scenario (no initial surplus).
    *   [x] Test edge case where holdback exceeds surplus (should result in zero transfer).
*   [x] **5.4: Implement Intelligent Transfer Rule**
    *   [x] In `src/simulator.py`, implement `calculate_intelligent_transfer(...)`.
    *   [x] Ensure the logic is isolated and does not depend on file I/O.
    *   [x] Ensure all `calculate_intelligent_transfer` tests pass.
*   [x] **5.5: Integrate `simulator` Logic into CLI (Integration Test)**
    *   [x] Add `test_simulator_integration_with_intelligent_transfer` to `tests/test_cli.py`.
    *   [x] Use `unittest.mock` to set up a scenario that triggers the holdback logic.
    *   [x] Use `capsys` to capture `stdout`.
    *   [x] Assert the correct "SYSTEM_TRANSFER" message and amount is printed.
    *   [x] Assert `simulation_output_{date}.csv` is created.
    *   [x] Assert the virtual transfer appears correctly in the output CSV on the correct date.
*   [x] **5.6: Implement CLI Handler**
    *   [x] In `src/simulator.py`, create top-level orchestrator `generate_simulation_report(...)`.
    *   [x] This function will contain the main loop, call the look-ahead stress test, call `calculate_intelligent_transfer`, and inject virtual transactions.
    *   [x] In `src/cli.py`, create `simulator_handler(args)`.
    *   [x] Wire the handler to call data loaders and `generate_simulation_report`.
    *   [x] Implement console summary and CSV saving logic.
    *   [x] Update `main()` to dispatch to `simulator_handler`.
    *   [x] Ensure the new `simulator` integration test passes.

## Phase 6: Finalization & Documentation

*   [x] **6.1: Create User-Facing Documentation**
    *   [x] Create `README.md` with:
        *   [x] Project description.
        *   [x] Installation instructions (`pip install .`).
        *   [x] Usage examples for `summarize` and `simulator` commands.
        *   [x] Description of the file structure (`users/`, `config.yaml`, `ledger.csv`).
*   [x] **6.2: Code Review and Refinement**
    *   [x] Review all code for clarity, comments, and adherence to best practices.
    *   [x] Ensure docstrings are present for all public functions.
    *   [x] Perform a final manual, end-to-end test with a sample user directory.
*   [x] **6.3: Final Project Cleanup**
    *   [x] Ensure `.gitignore` is comprehensive (e.g., includes `__pycache__/`, `*.egg-info`, `dist/`).
    *   [x] Remove any temporary or debug code.
    *   [x] Tag the final version in git.

