# Simulator module for Personal Cash Flow Simulator & Reporter
import pandas as pd
from datetime import date, timedelta
import numpy as np
import re


def run_simulation_engine(start_balance, target_balance, transactions_df, start_date, window_days):
    """
    Run the core simulation engine to project cash flow over a given time window.
    
    Args:
        start_balance (float): Starting account balance
        target_balance (float): Target minimum balance
        transactions_df (pandas.DataFrame): Transaction ledger with forecast transactions
        start_date (datetime.date): Start date for the simulation
        window_days (int): Number of days to simulate
        
    Returns:
        pandas.DataFrame: Day-by-day simulation results
    """
    # Initialize results list
    results = []
    
    # Ensure transactions_df has datetime index for easier filtering
    transactions_df = transactions_df.copy()
    
    # Current balance starts at the start_balance
    current_balance = start_balance
    
    # Loop through each day in the simulation window
    for day_offset in range(window_days):
        current_date = start_date + timedelta(days=day_offset)
        current_date_pd = pd.Timestamp(current_date)
        
        # Start balance for the day is the end balance from previous day
        day_start_balance = current_balance
        
        # Filter transactions for the current day
        day_transactions = transactions_df[transactions_df['date'].dt.date == current_date]
        
        # Calculate net change for the day
        if day_transactions.empty:
            day_net_change = 0
            transactions_summary = ''
        else:
            # Create a proper copy to avoid SettingWithCopyWarning
            day_transactions = day_transactions.copy()
            # Convert amounts to numeric for calculation
            day_transactions['amount'] = pd.to_numeric(day_transactions['amount'])
            day_net_change = day_transactions['amount'].sum()
            
            # Create a summary of the day's transactions
            summary_parts = []
            for _, tx in day_transactions.iterrows():
                summary_parts.append(f"{tx['description']}: {tx['amount']:.2f}")
            transactions_summary = ', '.join(summary_parts)
        
        # Calculate end balance for the day
        day_end_balance = day_start_balance + day_net_change
        
        # Determine alert type
        if day_end_balance < target_balance:
            alert_type = 'BELOW_TARGET'
            # Add SYSTEM recommendation for adding funds
            shortfall = target_balance - day_end_balance
            if transactions_summary:
                transactions_summary += f", SYSTEM: Add funds ({shortfall:.2f})"
            else:
                transactions_summary = f"SYSTEM: Add funds ({shortfall:.2f})"
        else:
            alert_type = 'OK'
        
        # Update current balance for the next day
        current_balance = day_end_balance
        
        # Add day's results to the results list
        results.append({
            'date': current_date_pd,
            'start_balance': day_start_balance,
            'transactions_summary': transactions_summary,
            'net_change': day_net_change,
            'end_balance': day_end_balance,
            'alert_type': alert_type
        })
    
    # Convert results list to DataFrame
    results_df = pd.DataFrame(results)
    
    return results_df


def calculate_intelligent_transfer(month_end_balance, target_balance, future_30_day_balances):
    """
    Calculate the recommended transfer amount based on the intelligent transfer rule.
    
    Args:
        month_end_balance (float): Balance at the end of the month
        target_balance (float): Target minimum balance
        future_30_day_balances (pandas.Series): Projected balances for the next 30 days
        
    Returns:
        float: Recommended transfer amount (0 or positive)
    """
    # Calculate surplus (if any)
    surplus = month_end_balance - target_balance
    
    # If no surplus, no transfer
    if surplus <= 0:
        return 0
    
    # Find the lowest projected balance in the next 30 days
    lowest_future_balance = future_30_day_balances.min()
    
    # Calculate shortfall below target (if any)
    shortfall = max(0, target_balance - lowest_future_balance)
    
    # Calculate recommended transfer
    # Surplus minus holdback (shortfall), but never negative
    recommended_transfer = max(0, surplus - shortfall)
    
    return recommended_transfer


def generate_simulation_report(start_balance, target_balance, transactions_df, start_date, window_days):
    """
    Generate a complete simulation report with intelligent transfer recommendations.
    
    Args:
        start_balance (float): Starting account balance
        target_balance (float): Target minimum balance
        transactions_df (pandas.DataFrame): Transaction ledger with forecast transactions
        start_date (datetime.date): Start date for the simulation
        window_days (int): Number of days to simulate
        
    Returns:
        tuple: (simulation_results_df, recommended_transfer_amount)
    """
    # Make a copy of the transactions DataFrame to avoid modifying the original
    transactions_df = transactions_df.copy()
    
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(transactions_df['date']):
        transactions_df['date'] = pd.to_datetime(transactions_df['date'])
    
    # Convert amounts to numeric
    transactions_df['amount'] = pd.to_numeric(transactions_df['amount'])
    
    # Run the initial simulation
    sim_results_df = run_simulation_engine(start_balance, target_balance, transactions_df, start_date, window_days)
    
    # Initialize recommended transfer amount
    recommended_transfer = 0.0
    
    # Check for month-end days in the simulation
    for i in range(len(sim_results_df) - 1):
        current_day = sim_results_df.iloc[i]['date'].date()
        next_day = sim_results_df.iloc[i + 1]['date'].date()
        
        # If current day is the last day of a month
        if current_day.month != next_day.month:
            # Get the end-of-month balance
            month_end_balance = sim_results_df.iloc[i]['end_balance']
            
            # Look ahead 30 days (or as many as available)
            look_ahead_days = min(30, len(sim_results_df) - i - 1)
            future_balances = sim_results_df.iloc[i+1:i+1+look_ahead_days]['end_balance']
            
            # Calculate recommended transfer
            recommended_transfer = calculate_intelligent_transfer(
                month_end_balance, target_balance, future_balances
            )
            
            # If a transfer is recommended, add a virtual transaction for the 1st of next month
            if recommended_transfer > 0:
                # Create a virtual transaction for the transfer
                next_month_first = next_day
                
                # Add the virtual transaction to the transactions DataFrame
                virtual_tx = pd.DataFrame({
                    'date': [pd.Timestamp(next_month_first)],
                    'amount': [-recommended_transfer],
                    'description': ['Surplus Transfer'],
                    'category': ['System'],
                    'forecast': ['1']
                })
                
                # Append the virtual transaction
                transactions_df = pd.concat([transactions_df, virtual_tx], ignore_index=True)
                
                # Re-run the simulation with the virtual transaction included
                sim_results_df = run_simulation_engine(
                    start_balance, target_balance, transactions_df, start_date, window_days
                )
                
                # Only process the first month-end we encounter
                break
    
    return sim_results_df, recommended_transfer
