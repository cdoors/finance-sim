import pytest
import pandas as pd
from src.summarize import find_uncategorized, calculate_pnl, format_pnl_output


@pytest.fixture
def sample_transactions():
    data = {
        'date': ['2023-12-05', '2023-12-15', '2023-12-20', '2023-12-25', '2024-01-01'],
        'amount': [2000.00, -1200.00, -50.00, -75.50, -1200.00],
        'description': ['Paycheck', 'Rent', 'Gas', 'Groceries', 'Rent'],
        'category': ['Revenue', 'Fixed', 'Variable', 'Varaible', 'Fixed'],  # Note the typo
        'forecast': [0, 0, 0, 0, 1]
    }
    return pd.DataFrame(data)


@pytest.fixture
def valid_categories():
    return ['Revenue', 'Fixed', 'Variable', 'Misc Income', 'Misc Expense', 'Investment']


def test_find_uncategorized(sample_transactions, valid_categories):
    uncategorized_df = find_uncategorized(sample_transactions, valid_categories)
    assert len(uncategorized_df) == 1
    assert 'Groceries' in uncategorized_df['description'].values
    assert 'Varaible' in uncategorized_df['category'].values


def test_calculate_pnl(sample_transactions, valid_categories):
    pnl = calculate_pnl(sample_transactions, '202312', valid_categories)
    
    assert pnl['Revenue']['Paycheck'] == 2000.00
    assert pnl['Fixed']['Rent'] == -1200.00
    assert pnl['Variable']['Gas'] == -50.00
    
    # Check that the uncategorized transaction is NOT included
    assert 'Groceries' not in pnl.get('Variable', {})
    
    # Check that transactions from other months are excluded
    assert len(pnl.get('Fixed', {})) == 1

    # Check summary calculations
    assert pnl['summary']['Revenue'] == 2000.00
    assert pnl['summary']['Fixed Expenses'] == -1200.00
    assert pnl['summary']['Variable Expenses'] == -50.00
    assert pnl['summary']['Profit Margin'] == 750.00
    assert pnl['summary']['Net Income'] == 750.00


def test_calculate_pnl_no_transactions():
    empty_df = pd.DataFrame(columns=['date', 'amount', 'description', 'category', 'forecast'])
    pnl = calculate_pnl(empty_df, '202312', ['Revenue', 'Fixed', 'Variable', 'Misc Income', 'Misc Expense'])
    
    assert pnl['summary']['Revenue'] == 0
    assert pnl['summary']['Fixed Expenses'] == 0
    assert pnl['summary']['Variable Expenses'] == 0
    assert pnl['summary']['Profit Margin'] == 0
    assert pnl['summary']['Misc Income'] == 0
    assert pnl['summary']['Misc Expenses'] == 0
    assert pnl['summary']['Net Income'] == 0


def test_calculate_pnl_with_misc_categories():
    """Test P&L calculation with misc income and expense categories."""
    # Create test data with misc income and expense
    data = {
        'date': ['2023-12-05', '2023-12-10', '2023-12-15', '2023-12-20'],
        'amount': [2000.00, 100.00, -1200.00, -30.00],
        'description': ['Paycheck', 'Interest', 'Rent', 'Bank Fee'],
        'category': ['Revenue', 'Misc Income', 'Fixed', 'Misc Expense'],
        'forecast': [0, 0, 0, 0]
    }
    df = pd.DataFrame(data)
    
    # Define valid categories
    valid_categories = ['Revenue', 'Fixed', 'Variable', 'Misc Income', 'Misc Expense']
    
    # Calculate P&L
    pnl = calculate_pnl(df, '202312', valid_categories)
    
    # Check individual category values
    assert pnl['Revenue']['Paycheck'] == 2000.00
    assert pnl['Misc Income']['Interest'] == 100.00
    assert pnl['Fixed']['Rent'] == -1200.00
    assert pnl['Misc Expense']['Bank Fee'] == -30.00
    
    # Check summary calculations
    assert pnl['summary']['Revenue'] == 2000.00
    assert pnl['summary']['Fixed Expenses'] == -1200.00
    assert pnl['summary']['Variable Expenses'] == 0
    assert pnl['summary']['Profit Margin'] == 800.00
    assert pnl['summary']['Misc Income'] == 100.00
    assert pnl['summary']['Misc Expenses'] == -30.00
    assert pnl['summary']['Net Income'] == 870.00


def test_format_pnl_output():
    """Test the formatting of P&L output."""
    # Create a sample P&L data structure
    pnl_data = {
        'Revenue': {'Sales': 1000.0},
        'Fixed': {'Rent': -500.0},
        'Variable': {'Supplies': -200.0},
        'Misc Income': {'Interest': 50.0},
        'Misc Expense': {'Fees': -25.0},
        'summary': {
            'Revenue': 1000.0,
            'Fixed Expenses': -500.0,
            'Variable Expenses': -200.0,
            'Profit Margin': 300.0,
            'Misc Income': 50.0,
            'Misc Expenses': -25.0,
            'Net Income': 325.0
        }
    }
    
    # Format the output
    output = format_pnl_output(pnl_data)
    
    # Check that the output contains the expected sections and values
    assert "CASH FLOW SUMMARY" in output
    assert "Revenue:" in output
    assert "Fixed:" in output
    assert "Variable:" in output
    assert "Misc Income:" in output
    assert "Misc Expense:" in output
    assert "CASH FLOW STATEMENT:" in output
    assert "Revenue: 1000.00" in output
    assert "Fixed Expenses: -500.00" in output
    assert "Variable Expenses: -200.00" in output
    assert "Profit Margin: 300.00" in output
    assert "Misc Income: 50.00" in output
    assert "Misc Expenses: -25.00" in output
    assert "Net Income: 325.00" in output
