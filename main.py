import os
import sys
import yaml
import subprocess
from pathlib import Path
from sqlalchemy import select

from db import get_db_session, engine
from models.base import Base
from models.finance import Account, Transaction, Currency

def show_license_info():
    print_header("Legal Information")
    print("This program comes with ABSOLUTELY NO WARRANTY.")
    print("This is free software, and you are welcome to redistribute it")
    print("under certain conditions (GNU GPL v3).")
    print("\nFor the full license, see the LICENSE.md file in the root directory.")
    get_input("\nPress Enter to return to menu")

# --- Utilities ---

def ensure_directories():
    Path("importers").mkdir(exist_ok=True)

def run_shell_transform(command: str, input_str: str) -> str:
    """Feeds input_str into stdin of command, returns stdout stripped."""
    try:
        result = subprocess.run(
            command,
            input=input_str,
            text=True,
            shell=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e.stderr}")
        return None

# --- UI Functions ---

def print_header(text):
    print(f"\n--- {text} ---")

def get_input(prompt):
    return input(f"{prompt}: ").strip()

def select_account(session):
    accounts = session.scalars(select(Account)).all()
    if not accounts:
        print("No accounts found.")
        return None

    print("\nSelect Account:")
    for idx, acc in enumerate(accounts, 1):
        print(f"{idx}. {acc.name} ({acc.currency.value})")
    
    choice = get_input("Enter number (or 'c' to cancel)")
    if choice.lower() == 'c': return None
    
    try:
        return accounts[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return None

def create_account(session):
    print_header("Create New Account")
    name = get_input("Account Name")
    curr = get_input("Currency (USD, EUR, CHF, GBP)").upper()
    
    try:
        currency_enum = Currency(curr)
        new_acc = Account(name=name, currency=currency_enum)
        session.add(new_acc)
        session.commit()
        
        # Create folder for importers
        Path(f"importers/{name}").mkdir(parents=True, exist_ok=True)
        print(f"Account '{name}' created and importer folder initialized.")
    except ValueError:
        print("Invalid currency code.")
    except Exception as e:
        print(f"Error creating account: {e}")

def run_importer_wizard(session, account):
    # 1. Select YAML Config
    importer_dir = Path(f"importers/{account.name}")
    if not importer_dir.exists():
        print(f"Directory {importer_dir} does not exist.")
        return

    yamls = list(importer_dir.glob("*.yaml"))
    if not yamls:
        print("No .yaml configuration files found for this account.")
        return

    print(f"\nAvailable Importers for {account.name}:")
    for idx, f in enumerate(yamls, 1):
        print(f"{idx}. {f.name}")
    
    choice = get_input("Select importer")
    try:
        config_path = yamls[int(choice) - 1]
    except (ValueError, IndexError):
        return

    # 2. Select CSV File
    csv_path = get_input("Enter full path to CSV file")
    if not os.path.exists(csv_path):
        print("File not found.")
        return

    # 3. Process
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    transformations = config.get('transformations', {})
    header_lines = config.get('header_lines', 0)
    
    pending_transactions = []

    print("\nProcessing file...")
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Skip headers
        data_lines = lines[header_lines:]
        
        for i, line in enumerate(data_lines):
            line = line.strip()
            if not line: continue

            # Extract fields using shell commands
            desc = run_shell_transform(transformations['description'], line)
            orig_val = run_shell_transform(transformations['original_value'], line)
            orig_curr = run_shell_transform(transformations['original_currency'], line)
            acc_val = run_shell_transform(transformations['value_in_account_currency'], line)
            date_str = run_shell_transform(transformations['date'], line)

            # Basic Validation
            if not all([desc, orig_val, orig_curr, acc_val, date_str]):
                print(f"Skipping line {i+header_lines+1}: Transformation returned empty values.")
                continue

            try:
                t = Transaction(
                    account_id=account.id,
                    description=desc,
                    original_value=float(orig_val),
                    original_currency=Currency(orig_curr),
                    value_in_account_currency=float(acc_val),
                    date_str=date_str
                )
                pending_transactions.append(t)
            except ValueError as e:
                print(f"Data error on line {i+header_lines+1}: {e}")

    except Exception as e:
        print(f"Critical error during processing: {e}")
        return

    # 4. Review
    print_header("Review Transactions")
    print(f"{'Date':<12} | {'Description':<30} | {'Amount':<10} | {'Curr'}")
    print("-" * 65)
    for t in pending_transactions:
        print(f"{t.date_str:<12} | {t.description[:28]:<30} | {t.value_in_account_currency:<10} | {t.original_currency.value}")

    confirm = get_input(f"\nImport {len(pending_transactions)} transactions? (y/n)")
    if confirm.lower() == 'y':
        session.add_all(pending_transactions)
        session.commit()
        print("Import successful!")
    else:
        print("Import cancelled.")

# --- Main Entry Point ---

def main():
    ensure_directories()

    while True:
        print(r"""
  __  __                       _____                     
 |  \/  |                     / ____|                    
 | \  / | ___  _ __   ___ _ _| |  __ _ __ ___ _ __      
 | |\/| |/ _ \| '_ \ / _ \ ' \ | |_ | '__/ _ \ '_ \     
 | |  | | (_) | | | |  __/ | | |__| | | |  __/ |_) |    
 |_|  |_|\___/|_| |_|\___|_|  \_____|_|  \___| .__/     
                MoneyGrep v0                | |        
                                            |_|        """)
        
        # The GPL-required startup notice (brief version)
        print(f"Copyright (C) 2026 Philipp Heller")
        print("MoneyGrep comes with ABSOLUTELY NO WARRANTY. This is free software.")
        print("Type '9' for license details.")
        print("-" * 30)

        print("1. Select Account / Import")
        print("2. Create New Account")
        print("9. Show License & Warranty")
        print("0. Exit")
        
        choice = get_input("Choice")

        with get_db_session() as session:
            if choice == '1':
                acc = select_account(session)
                if acc:
                    run_importer_wizard(session, acc)
            elif choice == '2':
                create_account(session)
            elif choice == '9':
                show_license_info()
            elif choice == '0':
                sys.exit()
            else:
                print("Invalid choice")

if __name__ == "__main__":
    main()