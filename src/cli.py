# CLI module for Personal Cash Flow Simulator & Reporter
import argparse
import datetime
import re
from pathlib import Path
import pandas as pd

from src.data_loader import load_config, load_ledger
from src.summarize import generate_summary_report, format_pnl_output
from src.simulator import generate_simulation_report


# Base path for user data
base_user_path = Path("./users")


def create_parser():
    parser = argparse.ArgumentParser(description="Personal Cash Flow Simulator & Reporter.")

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


def summarize_handler(args):
    """
    Handle the summarize command.
    
    Args:
        args: Command line arguments
    """
    user_dir = base_user_path / args.user
    
    # Load user data
    config = load_config(user_dir)
    ledger_df = load_ledger(user_dir)
    
    # Generate the P&L report
    pnl_data, uncategorized_df = generate_summary_report(ledger_df, config, args.month)
    
    # Print the formatted P&L report
    print(format_pnl_output(pnl_data))
    
    # Handle uncategorized transactions
    if not uncategorized_df.empty:
        print("\nWARNING: Uncategorized transactions found:")
        for _, row in uncategorized_df.iterrows():
            print(f"  {row['date']} | {row['description']} | Category: '{row['category']}'")
        
        # Save uncategorized transactions to CSV
        today_str = datetime.date.today().strftime('%Y%m%d')
        output_file = user_dir / f"uncategorized_{today_str}.csv"
        uncategorized_df.to_csv(output_file, index=False)
        print(f"\nUncategorized transactions saved to: {output_file}")


def simulator_handler(args):
    """
    Handle the simulator command.
    
    Args:
        args: Command line arguments
    """
    user_dir = base_user_path / args.user
    
    try:
        # Load user data
        config = load_config(user_dir)
        ledger_df = load_ledger(user_dir)
        
        # Get simulation parameters
        start_balance = float(config.get('current_balance', 0))
        target_balance = float(config.get('target_balance', 0))
        window_days = args.window
        start_date = datetime.date.today()
        
        # Convert date strings to datetime objects
        ledger_df['date'] = pd.to_datetime(ledger_df['date'])
        
        # Filter for forecast transactions
        forecast_df = ledger_df[ledger_df['forecast'] == '1'].copy()
        
        # Generate the simulation report
        sim_results_df, recommended_transfer = generate_simulation_report(
            start_balance, target_balance, forecast_df, start_date, window_days
        )
        
        # Print simulation summary
        print("\nSIMULATION SUMMARY")
        print("=" * 40)
        
        # Print alerts
        alerts = sim_results_df[sim_results_df['alert_type'] == 'BELOW_TARGET']
        if not alerts.empty:
            print("\nALERTS:")
            for _, alert in alerts.iterrows():
                print(f"  {alert['date'].strftime('%Y-%m-%d')}: Balance drops to {alert['end_balance']:.2f} (below target of {target_balance:.2f})")
                
                # Check if there's a SYSTEM recommendation
                if 'SYSTEM: Add funds' in alert['transactions_summary']:
                    # Extract the amount from the transaction summary
                    match = re.search(r'SYSTEM: Add funds \(([0-9.]+)\)', alert['transactions_summary'])
                    if match:
                        amount = float(match.group(1))
                        print(f"    SYSTEM RECOMMENDATION: Add {amount:.2f} to reach target balance")
        
        # Print transfer recommendation
        if recommended_transfer > 0:
            print("\nSYSTEM_TRANSFER:")
            print(f"  Recommended Transfer: {recommended_transfer:.2f}")
            print(f"  A virtual transfer has been added to the simulation on {(start_date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d')}")
        
        # Save simulation results to CSV
        today_str = datetime.date.today().strftime('%Y%m%d')
        output_file = user_dir / f"simulation_output_{today_str}.csv"
        
        # Convert date column to string for CSV output
        sim_results_df['date'] = sim_results_df['date'].dt.strftime('%Y-%m-%d')
        sim_results_df.to_csv(output_file, index=False)
        
        print(f"\nSimulation results saved to: {output_file}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error during simulation: {e}")


def main():
    parser = create_parser()
    args = parser.parse_args()
    
    print(f"Executing command: {args.command}")
    
    if args.command == "summarize":
        summarize_handler(args)
    elif args.command == "simulator":
        simulator_handler(args)


if __name__ == "__main__":
    main()
