# Personal Cash Flow Simulator & Reporter

A command-line tool for simulating personal cash flow and generating financial reports. This tool helps you track your finances, identify uncategorized transactions, and make intelligent decisions about surplus funds.

More elegant GUIs and solutions exist, but this is a functional implementation to manage an operating account (checking) and avoid overdrafts. The opportunity cost is too high to allow money to earn virtually 0% in a checking, so we aim to keep the minimum amount in here. Parking core investments and surplus cash in equities, HYSAs, treasuries, crypto, etc... makes more sense.

## Features

- **Monthly P&L Summaries**: Generate profit and loss reports for any month
- **Cash Flow Simulation**: Project your future cash flow based on forecasted transactions
- **Intelligent Transfer Recommendations**: Get smart recommendations for handling surplus funds
- **Uncategorized Transaction Detection**: Identify and export transactions with invalid categories

## Installation

Clone the repository and install the package:

```bash
git clone https://github.com/cdoors/finance-sim.git
cd finance-sim
pip install .
```

## Usage

The tool provides two main commands:

### Summarize Command

Generate a P&L summary for a specific month:

```bash
python -m src.cli summarize --user <username> --month <YYYYMM>
```

Example:
```bash
python -m src.cli summarize --user john --month 202312
```

This will:
- Generate a P&L report for December 2023
- Identify any uncategorized transactions
- Save uncategorized transactions to a CSV file

### Simulator Command

Project cash flow over a given time window:

```bash
python -m src.cli simulator --user <username> --window <days>
```

Example:
```bash
python -m src.cli simulator --user john --window 90
```

This will:
- Simulate cash flow for the next 90 days
- Identify any periods where your balance falls below your target
- Calculate intelligent transfer recommendations for surplus funds
- Save the simulation results to a CSV file

## File Structure

### Required User Files

- `users/<username>/config.yaml`: User configuration file
  ```yaml
  account_nickname: My Account
  current_balance: 5000.00
  target_balance: 2000.00
  categories:
    - Revenue       # Income categories must include "Revenue" or end with "Income"
    - Fixed         # Expense categories (negative amounts in ledger)
    - Variable      # Expense categories (negative amounts in ledger)
    - Misc Income   # Additional income category
    - Misc Expense  # Additional expense category
  ```

  **Important Category Rules:**
  - Income categories must either be named exactly "Revenue" or end with "Income" (e.g., "Misc Income")
  - All other categories are treated as expenses
  - The P&L report will group transactions by these categories
  - Any transaction with a category not listed here will be flagged as "uncategorized"

- `users/<username>/ledger.csv`: Transaction ledger
  ```csv
  date,amount,description,category,forecast
  2023-12-01,2000.00,Paycheck,Revenue,0
  2023-12-15,-1200.00,Rent,Fixed,0
  2024-01-01,2000.00,Paycheck,Revenue,1
  ```
  
  **Ledger Format Requirements:**
  - `date`: YYYY-MM-DD format
  - `amount`: Positive for income, negative for expenses
  - `category`: Must match one of the categories defined in config.yaml
  - `description`: Text description of the transaction
  - `forecast`: 
    - `0` for historical transactions
    - `1` for forecasted future transactions
  
  **Note:** For proper P&L calculation, ensure that income transactions use income categories and have positive amounts, while expense transactions use expense categories and have negative amounts.

### Output Files

- `users/<username>/uncategorized_<date>.csv`: Uncategorized transactions
- `users/<username>/simulation_output_<date>.csv`: Simulation results

## Intelligent Transfer Rule

The simulator uses a sophisticated algorithm to recommend transfers:

1. At month-end, it calculates any surplus above your target balance
2. It performs a 30-day look-ahead stress test to identify future dips
3. It recommends a transfer amount that ensures you maintain your target balance

This helps you maximize the use of your funds while maintaining financial security.
