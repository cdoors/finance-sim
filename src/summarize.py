# Summarize module for Personal Cash Flow Simulator & Reporter
import pandas as pd
import datetime


def find_uncategorized(transactions_df, valid_categories):
    """
    Find transactions with categories that are not in the valid_categories list.
    
    Args:
        transactions_df (pandas.DataFrame): Transaction ledger
        valid_categories (list): List of valid category names
        
    Returns:
        pandas.DataFrame: Filtered DataFrame containing only uncategorized transactions
    """
    # Filter transactions where category is not in valid_categories
    uncategorized_mask = ~transactions_df['category'].isin(valid_categories)
    return transactions_df[uncategorized_mask].copy()


def calculate_pnl(transactions_df, month_str, valid_categories):
    """
    Calculate profit and loss summary for a specific month.
    
    Args:
        transactions_df (pandas.DataFrame): Transaction ledger
        month_str (str): Month in YYYYMM format
        valid_categories (list): List of valid category names
        
    Returns:
        dict: Nested dictionary with P&L data by category and structured cash flow summary
    """
    # Convert month_str to start and end dates
    year = int(month_str[:4])
    month = int(month_str[4:])
    
    # Create a copy of the DataFrame to avoid modifying the original
    df = transactions_df.copy()
    
    # Convert date strings to datetime objects
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter for the specified month
    start_date = pd.Timestamp(year=year, month=month, day=1)
    if month == 12:
        end_date = pd.Timestamp(year=year+1, month=1, day=1) - pd.Timedelta(days=1)
    else:
        end_date = pd.Timestamp(year=year, month=month+1, day=1) - pd.Timedelta(days=1)
    
    month_mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    month_df = df[month_mask]
    
    # Filter out uncategorized transactions
    categorized_mask = month_df['category'].isin(valid_categories)
    categorized_df = month_df[categorized_mask].copy()
    
    # Convert amount to numeric (using copy to avoid SettingWithCopyWarning)
    categorized_df['amount'] = pd.to_numeric(categorized_df['amount'])
    
    # Initialize result dictionary with categories and cash flow structure
    pnl = {category: {} for category in valid_categories}
    pnl['summary'] = {
        'Revenue': 0,
        'Fixed Expenses': 0,
        'Variable Expenses': 0,
        'Profit Margin': 0,
        'Misc Income': 0,
        'Misc Expenses': 0,
        'Net Income': 0
    }
    
    # If no transactions for the month, return the initialized dictionary
    if categorized_df.empty:
        return pnl
    
    # Group by category and description, sum amounts
    grouped = categorized_df.groupby(['category', 'description'])['amount'].sum()
    
    # Populate the pnl dictionary
    for (category, description), amount in grouped.items():
        pnl[category][description] = amount
        
        # Update summary totals based on category
        if category == 'Revenue':
            pnl['summary']['Revenue'] += amount
        elif category == 'Fixed':
            pnl['summary']['Fixed Expenses'] += -abs(amount)  # Ensure negative
        elif category == 'Variable':
            pnl['summary']['Variable Expenses'] += -abs(amount)  # Ensure negative
        elif category == 'Misc Income':
            pnl['summary']['Misc Income'] += abs(amount)  # Ensure positive
        elif category == 'Misc Expense':
            pnl['summary']['Misc Expenses'] += -abs(amount)  # Ensure negative
    
    # Calculate profit margin and net income
    pnl['summary']['Profit Margin'] = (
        pnl['summary']['Revenue'] + 
        pnl['summary']['Fixed Expenses'] + 
        pnl['summary']['Variable Expenses']
    )
    
    pnl['summary']['Net Income'] = (
        pnl['summary']['Profit Margin'] + 
        pnl['summary']['Misc Income'] + 
        pnl['summary']['Misc Expenses']
    )
    
    return pnl


def generate_summary_report(ledger_df, config, month):
    """
    Generate a complete P&L summary report.
    
    Args:
        ledger_df (pandas.DataFrame): Transaction ledger
        config (dict): User configuration
        month (str): Month in YYYYMM format
        
    Returns:
        tuple: (pnl_data, uncategorized_df)
    """
    valid_categories = config.get('categories', [])
    
    # Find uncategorized transactions
    uncategorized_df = find_uncategorized(ledger_df, valid_categories)
    
    # Calculate P&L
    pnl_data = calculate_pnl(ledger_df, month, valid_categories)
    
    return pnl_data, uncategorized_df


def format_pnl_output(pnl_data):
    """
    Format P&L data as a string for console output.
    
    Args:
        pnl_data (dict): P&L data from calculate_pnl
        
    Returns:
        str: Formatted P&L report
    """
    output = []
    output.append("CASH FLOW SUMMARY")
    output.append("=" * 40)
    
    # Add categories and their transactions
    for category in pnl_data:
        if category != 'summary' and pnl_data[category]:
            output.append(f"\n{category}:")
            for description, amount in pnl_data[category].items():
                output.append(f"  {description}: {amount:.2f}")
    
    # Add structured cash flow summary section
    output.append("\nCASH FLOW STATEMENT:")
    output.append(f"  Revenue: {pnl_data['summary']['Revenue']:.2f}")
    output.append(f"  Fixed Expenses: {pnl_data['summary']['Fixed Expenses']:.2f}")
    output.append(f"  Variable Expenses: {pnl_data['summary']['Variable Expenses']:.2f}")
    output.append(f"  Profit Margin: {pnl_data['summary']['Profit Margin']:.2f}")
    output.append(f"  Misc Income: {pnl_data['summary']['Misc Income']:.2f}")
    output.append(f"  Misc Expenses: {pnl_data['summary']['Misc Expenses']:.2f}")
    output.append(f"  Net Income: {pnl_data['summary']['Net Income']:.2f}")
    
    return "\n".join(output)
