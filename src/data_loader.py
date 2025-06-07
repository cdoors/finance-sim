# Data loader module for Personal Cash Flow Simulator & Reporter
import yaml
import pandas as pd
from pathlib import Path


def load_config(user_dir):
    """
    Load user configuration from config.yaml
    
    Args:
        user_dir (Path): Path to the user directory
        
    Returns:
        dict: User configuration
        
    Raises:
        FileNotFoundError: If config.yaml doesn't exist
    """
    config_path = user_dir / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def load_ledger(user_dir):
    """
    Load user transaction ledger from ledger.csv
    
    Args:
        user_dir (Path): Path to the user directory
        
    Returns:
        pandas.DataFrame: Transaction ledger
        
    Raises:
        FileNotFoundError: If ledger.csv doesn't exist
    """
    ledger_path = user_dir / "ledger.csv"
    if not ledger_path.exists():
        raise FileNotFoundError(f"Ledger file not found: {ledger_path}")
    
    # Read CSV with explicit dtypes to avoid automatic parsing
    # Keep empty strings as empty strings, not NaN
    ledger_df = pd.read_csv(
        ledger_path,
        dtype=str,
        keep_default_na=False
    )
    
    return ledger_df
