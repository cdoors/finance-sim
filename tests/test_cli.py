import pytest
from pathlib import Path
import pandas as pd
import datetime
from unittest.mock import patch, mock_open, MagicMock
import sys
import io

from src.cli import create_parser, main


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


@patch('src.cli.load_config')
@patch('src.cli.load_ledger')
@patch('src.cli.Path.exists')
@patch('builtins.open', new_callable=mock_open)
@patch('pandas.DataFrame.to_csv')
def test_summarize_integration(mock_to_csv, mock_file, mock_exists, mock_load_ledger, mock_load_config, capsys):
    # Setup mock data
    mock_exists.return_value = True
    
    # Mock config
    mock_config = {
        'categories': ['Revenue', 'Fixed', 'Variable']
    }
    mock_load_config.return_value = mock_config
    
    # Mock ledger data
    ledger_data = {
        'date': ['2023-12-05', '2023-12-15', '2023-12-20', '2023-12-25'],
        'amount': ['2000.00', '-1200.00', '-50.00', '-75.50'],
        'description': ['Paycheck', 'Rent', 'Gas', 'Groceries'],
        'category': ['Revenue', 'Fixed', 'Variable', 'Varaible'],  # Note the typo
        'forecast': ['0', '0', '0', '0']
    }
    mock_ledger = pd.DataFrame(ledger_data)
    mock_load_ledger.return_value = mock_ledger
    
    # Mock the command-line arguments
    test_args = ['cli.py', 'summarize', '--user', 'integration_user', '--month', '202312']
    with patch('sys.argv', test_args):
        main()

    # Assertions
    captured = capsys.readouterr()
    
    # Check for warning in console output
    assert "WARNING: Uncategorized transactions found" in captured.out
    assert "Groceries" in captured.out
    assert "Varaible" in captured.out
    
    # Check for correct P&L summary in console output
    assert "Revenue: 2000.00" in captured.out
    assert "Fixed Expenses: -1200.00" in captured.out
    assert "Variable Expenses: -50.00" in captured.out
    assert "Profit Margin: 750.00" in captured.out
    assert "Net Income: 750.00" in captured.out
    
    # Verify that to_csv was called (file was saved)
    assert mock_to_csv.called


@patch('src.cli.load_config')
@patch('src.cli.load_ledger')
@patch('src.cli.generate_simulation_report')
@patch('pandas.DataFrame.to_csv')
def test_simulator_integration_with_intelligent_transfer(mock_to_csv, mock_generate_report, mock_load_ledger, mock_load_config, capsys):
    # Setup mock data
    # Mock config
    mock_config = {
        'current_balance': 3000.00,
        'target_balance': 2500.00
    }
    mock_load_config.return_value = mock_config
    
    # Mock ledger data
    ledger_data = {
        'date': ['2024-01-30', '2024-02-02'],
        'amount': ['4000.00', '-3000.00'],
        'description': ['Big Project', 'Rent'],
        'category': ['Revenue', 'Fixed'],
        'forecast': ['1', '1']
    }
    mock_ledger = pd.DataFrame(ledger_data)
    mock_ledger['date'] = pd.to_datetime(mock_ledger['date'])
    mock_load_ledger.return_value = mock_ledger
    
    # Mock simulation report
    sim_data = {
        'date': [pd.Timestamp('2024-01-30'), pd.Timestamp('2024-01-31'), pd.Timestamp('2024-02-01')],
        'start_balance': [3000.00, 7000.00, 5500.00],
        'transactions_summary': ['Big Project: 4000.00', '', 'Surplus Transfer: -1500.00'],
        'net_change': [4000.00, 0.00, -1500.00],
        'end_balance': [7000.00, 7000.00, 4000.00],
        'alert_type': ['OK', 'OK', 'OK']
    }
    sim_df = pd.DataFrame(sim_data)
    mock_generate_report.return_value = (sim_df, 1500.00)  # Return simulation results and transfer amount
    
    # Mock the command-line arguments
    test_args = ['cli.py', 'simulator', '--user', 'sim_user', '--window', '60']
    with patch('sys.argv', test_args):
        with patch('datetime.date') as mock_date:
            mock_date.today.return_value = datetime.date(2024, 1, 1)
            main()

    # Assertions
    captured = capsys.readouterr()
    
    # Check for the system transfer recommendation in the console
    assert "SYSTEM_TRANSFER" in captured.out
    assert "Recommended Transfer: 1500.00" in captured.out
    
    # Verify that to_csv was called (file was saved)
    assert mock_to_csv.called
