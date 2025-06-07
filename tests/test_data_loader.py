import pytest
import pandas as pd
from pathlib import Path
import os
import yaml

# Import the functions from src.data_loader
from src.data_loader import load_config, load_ledger

# Use actual test directories
TEST_USERS_DIR = Path("./users")

@pytest.fixture(scope="session", autouse=True)
def setup_test_users():
    """Create test user directories and files for testing"""
    # Create test directories
    testuser_dir = TEST_USERS_DIR / "testuser"
    empty_user_dir = TEST_USERS_DIR / "empty_user"
    
    os.makedirs(testuser_dir, exist_ok=True)
    os.makedirs(empty_user_dir, exist_ok=True)
    
    # Create config.yaml for testuser
    testuser_config = {
        "account_nickname": "Test Account",
        "current_balance": 1000.00,
        "target_balance": 500.00,
        "categories": ["Revenue", "Fixed", "Variable"]
    }
    
    with open(testuser_dir / "config.yaml", "w") as f:
        yaml.dump(testuser_config, f)
    
    # Create ledger.csv for testuser
    with open(testuser_dir / "ledger.csv", "w") as f:
        f.write("date,amount,description,category,forecast\n")
        f.write("2023-01-01,-100.00,Rent,Fixed,0\n")
        f.write("2023-01-05,2000.00,Paycheck,Revenue,0\n")
    
    # Create config.yaml for empty_user
    empty_user_config = {
        "account_nickname": "Empty Account",
        "current_balance": 0.00,
        "target_balance": 0.00,
        "categories": ["Revenue", "Fixed", "Variable"]
    }
    
    with open(empty_user_dir / "config.yaml", "w") as f:
        yaml.dump(empty_user_config, f)
    
    # Create empty ledger.csv for empty_user
    with open(empty_user_dir / "ledger.csv", "w") as f:
        f.write("date,amount,description,category,forecast\n")
    
    yield
    
    # Cleanup is optional - you might want to keep the files for debugging

def test_load_config():
    user_path = TEST_USERS_DIR / "testuser"
    config = load_config(user_path)
    
    assert config is not None
    assert config['current_balance'] == 1000.00
    assert "Fixed" in config['categories']

def test_load_ledger():
    user_path = TEST_USERS_DIR / "testuser"
    ledger_df = load_ledger(user_path)
    
    assert not ledger_df.empty
    assert len(ledger_df) == 2
    assert 'date' in ledger_df.columns

def test_load_ledger_handles_empty():
    user_path = TEST_USERS_DIR / "empty_user"
    ledger_df = load_ledger(user_path)
    
    assert ledger_df.empty
    assert list(ledger_df.columns) == ["date", "amount", "description", "category", "forecast"]

def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config(TEST_USERS_DIR / "non_existent_user")

def test_load_ledger_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_ledger(TEST_USERS_DIR / "non_existent_user")
