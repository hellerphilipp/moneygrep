# MoneyGrep

A terminal-based tool to import and standardize bank transaction CSVs into an SQLite database. It uses YAML configuration files to map CSV columns to database fields using standard shell commands (like `cut`, `awk`, or `sed`).

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)

**⚠️ WARNING: THIS PROJECT WAS FULLY VIBE-CODED TO A WORKING STATE IN MINUTES.**

This tool was birthed through a high-bandwidth collaborative session between a human (me) and Gemini. It is the definition of "it works on my machine" and "I'll refactor it later (maybe)". Still decided it's worth sharing!

### The Vibe I gave as context to Gemini

* **Speed over perfection**: Architecture was decided in minutes based on previous projects I completed
* **Shell-Powered**: Why write complex Python parsers when `cut`, `awk`, and `sed` exist?
* **SQLite + SQLAlchemy**: Proper data integrity, but zero configuration overhead
* **Alembic migrations**: Because even vibe-coded projects deserve a path forward

### Known Gaps

* **Performance**: Every CSV row triggers multiple subprocess calls. If you import 10,000 rows, go make some coffee
* **Error Handling**: We assume your CSVs aren't actively trying to break us
* **UI**: It's a terminal menu. Use your number keys and your imagination
* **Data formats**: Room for optimization ;)

### The Verdict

**It works, and it is amazing.** It solves the monthly "export-to-uniform-CSV" headache using the power of the Unix philosophy.

### TODO list
- add "balance after transaction" field to identify already imported transactions
- add timestamps to dates
- implement some expense categorization logic

---

## Project Structure

```text
money_grep/
├── expense.db              # SQLite Database (auto-generated)
├── main.py                 # CLI Entrypoint
├── db.py                   # DB Config
├── models/                 # SQLAlchemy Models
├── importers/              # YAML rules per account
└── requirements.txt        # Dependencies

```

## Setup

1. **Install Dependencies**
```bash
pip install sqlalchemy alembic pyyaml

```


2. **Run the Tool**
The database tables are created automatically on the first run.
```bash
python main.py

```



## Workflow

1. **Create an Account:**
Select Option 2 in the main menu. Give it a name (e.g., `MyBank`) and currency (e.g., `EUR`).
2. **Create an Importer Rule:**
The tool creates a folder at `importers/MyBank/`. Create a `.yaml` file inside that folder (e.g., `default.yaml`) to define how to read your bank's CSV.
3. **Import Data:**
Select Option 1 in the main menu, choose your account, select the YAML file, and paste the path to your CSV.

## Configuration (YAML)

Importers define how to transform a single line of your CSV into database fields using terminal commands.

**Example `importers/MyBank/default.yaml`:**

```yaml
# Number of lines to skip at the top of the CSV
header_lines: 1

transformations:
  # Commands receive the CSV line via stdin.
  # Example CSV Line: 2023-10-01;"UBER";-25.50;EUR
  
  # Extract date (e.g., cut first column by semicolon)
  date: "cut -d';' -f1"
  
  # Extract description and remove quotes
  description: "cut -d';' -f2 | tr -d '\"'"
  
  # Extract amount
  original_value: "cut -d';' -f3"
  
  # Extract currency code
  original_currency: "cut -d';' -f4"
  
  # Value converted to account currency (usually same as original for simple imports)
  value_in_account_currency: "cut -d';' -f3"

```

## Notes

* **Database:** Stored locally as `expense.db`.
* **Shell Commands:** The script pipes CSV lines to the commands defined in YAML. Ensure you are on a system that supports these commands (Linux/macOS, or WSL/Git Bash on Windows).

