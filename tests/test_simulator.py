import pytest
import pandas as pd
from datetime import date, timedelta
from src.simulator import run_simulation_engine, calculate_intelligent_transfer


@pytest.fixture
def sample_sim_transactions():
    # Transactions for a 10-day window
    data = {
        'date': ['2024-01-02', '2024-01-05', '2024-01-05', '2024-01-08'],
        'amount': ['-1500.00', '2500.00', '-50.00', '-800.00'],
        'description': ['Rent', 'Paycheck', 'Spotify', 'Car Payment'],
        'category': ['Fixed', 'Revenue', 'Variable', 'Fixed'],
        'forecast': ['1', '1', '1', '1']
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
    assert day1['date'] == pd.Timestamp(2024, 1, 1)
    assert day1['start_balance'] == 2000.00
    assert day1['net_change'] == 0
    assert day1['end_balance'] == 2000.00
    assert day1['alert_type'] == 'OK'

    # Day 2 (Jan 2) - Rent payment
    day2 = sim_results_df.iloc[1]
    assert day2['date'] == pd.Timestamp(2024, 1, 2)
    assert day2['start_balance'] == 2000.00
    assert day2['net_change'] == -1500.00
    assert day2['end_balance'] == 500.00
    assert day2['alert_type'] == 'BELOW_TARGET'
    
    # Day 5 (Jan 5) - Paycheck and Spotify
    day5 = sim_results_df.iloc[4]
    assert day5['date'] == pd.Timestamp(2024, 1, 5)
    assert day5['start_balance'] == 500.00  # End balance of previous day
    assert day5['net_change'] == 2450.00
    assert day5['end_balance'] == 2950.00
    assert day5['alert_type'] == 'OK'


def test_run_simulation_engine_multiple_transactions_same_day(sample_sim_transactions):
    start_date = date(2024, 1, 5)
    window_days = 1
    start_balance = 1000.00
    target_balance = 500.00
    
    sim_results_df = run_simulation_engine(
        start_balance, target_balance, sample_sim_transactions, start_date, window_days
    )

    assert len(sim_results_df) == window_days
    
    # Day 1 (Jan 5) - Paycheck and Spotify
    day1 = sim_results_df.iloc[0]
    assert day1['date'] == pd.Timestamp(2024, 1, 5)
    assert day1['start_balance'] == 1000.00
    assert day1['net_change'] == 2450.00
    assert day1['end_balance'] == 3450.00
    assert day1['alert_type'] == 'OK'
    assert 'Paycheck: 2500.00' in day1['transactions_summary']
    assert 'Spotify: -50.00' in day1['transactions_summary']


def test_run_simulation_engine_no_transactions():
    start_date = date(2024, 1, 1)
    window_days = 5
    start_balance = 1500.00
    target_balance = 1000.00
    
    # Empty transactions DataFrame
    empty_transactions = pd.DataFrame(columns=['date', 'amount', 'description', 'category', 'forecast'])
    empty_transactions['date'] = pd.to_datetime(empty_transactions['date'])
    
    sim_results_df = run_simulation_engine(
        start_balance, target_balance, empty_transactions, start_date, window_days
    )

    assert len(sim_results_df) == window_days
    
    # All days should have the same balance and no changes
    for i in range(window_days):
        day = sim_results_df.iloc[i]
        assert day['start_balance'] == 1500.00
        assert day['net_change'] == 0
        assert day['end_balance'] == 1500.00
        assert day['alert_type'] == 'OK'
        assert day['transactions_summary'] == ''


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
