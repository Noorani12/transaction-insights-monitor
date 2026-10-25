
# Transaction Insights & Risk Monitor

A Flask-based transaction dashboard for monitoring payment activity, reviewing transaction statuses, and identifying potentially high-value transactions using configurable rule-based checks.

## Screenshots

### Dashboard
![Dashboard](https://github.com/user-attachments/assets/7022c03b-a3df-4c14-9e95-0e2b7e573ea0)

### Transaction Records and Filters
![Transaction records and filters](https://github.com/user-attachments/assets/a6775b9e-8c2e-4f61-a7b2-0537df95ae42)

### Edit Transaction
![Edit transaction](https://github.com/user-attachments/assets/64882d99-6075-4944-9c79-c3c7c1145bf3)

## Features

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
