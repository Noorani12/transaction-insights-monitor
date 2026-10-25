
# Transaction Insights & Risk Monitor

A Flask-based transaction dashboard for monitoring payment activity, reviewing transaction statuses, and identifying potentially high-value transactions using configurable rule-based checks.

## Features

- Dashboard with transaction summary metrics
- Add, edit, and delete transactions
- Search and filter by merchant, status, risk, and date
- Rule-based risk flagging for transactions of ₹10,000 or more
- Transaction status and daily transaction value charts
- Server-side pagination
- Export filtered transactions to CSV
- Input validation for transaction amounts
- Automated tests using pytest

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Charts:** Chart.js
- **Testing:** pytest

## Getting Started

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd transaction-insights-monitor
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser.

### 5. Run tests

```bash
python -m pytest -v
```

## Risk Flagging

Transactions with an amount greater than or equal to ₹10,000 are flagged by a rule-based threshold. This is a demonstration rule, not a machine-learning model or a production fraud detection system.

## Database

The application uses SQLite and initializes sample transactions when the database is empty.
