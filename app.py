import math
from flask import Flask, render_template, request, redirect, url_for, flash,abort
import sqlite3
import csv
import io
from flask import Response
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-before-deployment"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "transactions.db"

app.config["DATABASE"] = str(DB_PATH)

RISK_THRESHOLD = 10000


def get_db():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

        if count == 0:
            samples = [
                ("Book Store", 850, "Success"),
                ("Grocery Market", 1450, "Success"),
                ("Electronics Store", 18500, "Pending"),
                ("Coffee Shop", 320, "Success"),
                ("Travel Booking", 12500, "Failed"),
            ]
            conn.executemany("""
                INSERT INTO transactions
                (merchant, amount, status, created_at)
                VALUES (?, ?, ?, ?)
            """, [
                (m, a, s, datetime.now().strftime("%Y-%m-%d %H:%M"))
                for m, a, s in samples
            ])


def is_flagged(amount):
    # Demo rule only; not a real fraud detection model.
    return amount >= RISK_THRESHOLD
def parse_amount(value):
    try:
        amount = float(value)
    except (ValueError, TypeError):
        return None

    if not math.isfinite(amount):
        return None

    if not (0 < amount <= 1_000_000_000):
        return None

    return amount



@app.route("/")
def index():
    page = request.args.get("page", default=1, type=int)

    if page is None or page < 1:
        abort(400, description="Page must be a positive integer.")

    per_page = 10
    offset = (page - 1) * per_page
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()

    # Validate dates before using them in database queries.
    for value in (from_date, to_date):
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                abort(400, description="Invalid date format. Use YYYY-MM-DD.")

    if from_date and to_date and from_date > to_date:
        abort(400, description="Start date cannot be after end date.")

    conditions = []
    params = []

    if from_date:
        conditions.append("SUBSTR(created_at, 1, 10) >= ?")
        params.append(from_date)

    if to_date:
        conditions.append("SUBSTR(created_at, 1, 10) <= ?")
        params.append(to_date)

    search = request.args.get("search", "").strip()
    selected_status = request.args.get("status", "").strip()
    selected_risk = request.args.get("risk", "").strip()

    if len(search) > 100:
        abort(400, description="Search must be 100 characters or fewer.")

    if selected_status not in {"", "Success", "Pending", "Failed"}:
        abort(400, description="Invalid transaction status.")

    if selected_risk not in {"", "flagged", "normal"}:
        abort(400, description="Invalid risk filter.")
    if search:
        conditions.append("merchant LIKE ?")
        params.append(f"%{search}%")

    if selected_status:
        conditions.append("status = ?")
        params.append(selected_status)

    if selected_risk == "flagged":
        conditions.append("amount >= ?")
        params.append(RISK_THRESHOLD)
    elif selected_risk == "normal":
        conditions.append("amount < ?")
        params.append(RISK_THRESHOLD)

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions else ""
    )

    with get_db() as conn:
        total_transactions = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM transactions
            {where_clause}
            """,
            params
        ).fetchone()[0]

        total_pages = max(
            1,
            (total_transactions + per_page - 1) // per_page
        )

        if page > total_pages:
            page = total_pages

        offset = (page - 1) * per_page
        transactions = conn.execute(
            f"""
            SELECT * FROM transactions
            {where_clause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset]
        ).fetchall()

        stats = conn.execute(
            f"""
            SELECT
                COUNT(*) AS total_count,
                COALESCE(SUM(amount), 0) AS total_amount,
                COALESCE(SUM(CASE WHEN status = 'Success'
                    THEN 1 ELSE 0 END), 0) AS successful_count
            FROM transactions
            {where_clause}
            """,
            params
        ).fetchone()

        status_rows = conn.execute(
            f"""
            SELECT status, COUNT(*) AS count
            FROM transactions
            {where_clause}
            GROUP BY status
            """,
            params
        ).fetchall()

        daily_rows = conn.execute(
            f"""
            SELECT SUBSTR(created_at, 1, 10) AS day,
                   SUM(amount) AS total
            FROM transactions
            {where_clause}
            GROUP BY day
            ORDER BY day DESC
            LIMIT 7
            """,
            params
        ).fetchall()
        flagged_count = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM transactions
            {where_clause}
            {"AND" if where_clause else "WHERE"} amount >= ?
            """,
            params + [RISK_THRESHOLD]
        ).fetchone()[0]

    status_counts = {
        "Success": 0,
        "Pending": 0,
        "Failed": 0
    }

    for row in status_rows:
        status_counts[row["status"]] = row["count"]

    daily_rows = list(reversed(daily_rows))
    daily_labels = [row["day"] for row in daily_rows]
    daily_values = [row["total"] for row in daily_rows]


    return render_template(
        "index.html",
        transactions=transactions,
        stats=stats,
        flagged_count=flagged_count,
        threshold=RISK_THRESHOLD,
        status_labels=list(status_counts.keys()),
        status_values=list(status_counts.values()),
        daily_labels=daily_labels,
        daily_values=daily_values,
        from_date=from_date,
        to_date=to_date,
        page=page,
        total_pages=total_pages,
        total_transactions=total_transactions,
        search=search,
        selected_status=selected_status,
        selected_risk=selected_risk
    )

@app.route("/export")
def export_transactions():
    search = request.args.get("search", "").strip()
    selected_status = request.args.get("status", "").strip()
    selected_risk = request.args.get("risk", "").strip()
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()

    # Validate the same filter values as the dashboard.
    if len(search) > 100:
        abort(400, description="Search must be 100 characters or fewer.")

    if selected_status not in {"", "Success", "Pending", "Failed"}:
        abort(400, description="Invalid transaction status.")

    if selected_risk not in {"", "flagged", "normal"}:
        abort(400, description="Invalid risk filter.")

    conditions = []
    params = []

    if from_date:
        try:
            datetime.strptime(from_date, "%Y-%m-%d")
        except ValueError:
            abort(400, description="Invalid start date.")
        conditions.append("date(created_at) >= date(?)")
        params.append(from_date)

    if to_date:
        try:
            datetime.strptime(to_date, "%Y-%m-%d")
        except ValueError:
            abort(400, description="Invalid end date.")
        conditions.append("date(created_at) <= date(?)")
        params.append(to_date)

    if from_date and to_date and from_date > to_date:
        abort(400, description="Start date must be before end date.")

    if search:
        conditions.append("merchant LIKE ?")
        params.append(f"%{search}%")

    if selected_status:
        conditions.append("status = ?")
        params.append(selected_status)

    if selected_risk == "flagged":
        conditions.append("amount >= ?")
        params.append(RISK_THRESHOLD)
    elif selected_risk == "normal":
        conditions.append("amount < ?")
        params.append(RISK_THRESHOLD)

    where_clause = (
        "WHERE " + " AND ".join(conditions) if conditions else ""
    )

    with get_db() as conn:
        transactions = conn.execute(
            f"""
            SELECT id, merchant, amount, status, created_at
            FROM transactions
            {where_clause}
            ORDER BY created_at DESC, id DESC
            """,
            params,
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Merchant", "Amount", "Status", "Risk rule", "Date"
    ])

    def safe_csv_text(value):
        value = str(value if value is not None else "")
        # Prevent spreadsheet formulas in text fields.
        if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
            return "'" + value
        return value

    for transaction in transactions:
        writer.writerow([
            transaction["id"],
            safe_csv_text(transaction["merchant"]),
            transaction["amount"],
            transaction["status"],
            "Flagged" if is_flagged(transaction["amount"]) else "Normal",
            safe_csv_text(transaction["created_at"]),
        ])

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                "attachment; filename=transactions.csv"
        },
    )



@app.route("/transactions", methods=["POST"])
def add_transaction():
    merchant = request.form.get("merchant", "").strip()
    amount_text = request.form.get("amount", "").strip()
    status = request.form.get("status", "").strip()

    if not merchant or len(merchant) > 100:
        flash("Enter a merchant name (up to 100 characters).", "error")
        return redirect(url_for("index"))

    amount = parse_amount(amount_text)

    if amount is None:
        flash(
            "Enter a valid amount greater than zero "
            "and no greater than ₹1,000,000,000.",
            "error"
        )
        return redirect(url_for("index"))

    if status not in {"Success", "Pending", "Failed"}:
        flash("Select a valid transaction status.", "error")
        return redirect(url_for("index"))

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    with get_db() as conn:
        conn.execute("""
            INSERT INTO transactions
            (merchant, amount, status, created_at)
            VALUES (?, ?, ?, ?)
        """, (merchant, amount, status, created_at))

    flash("Transaction added successfully.", "success")
    return redirect(url_for("index"))

@app.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
def delete_transaction(transaction_id):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM transactions WHERE id = ?",
            (transaction_id,)
        )

    flash("Transaction deleted successfully.", "success")
    return redirect(url_for("index"))


@app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    with get_db() as conn:
        transaction = conn.execute(
            "SELECT * FROM transactions WHERE id = ?",
            (transaction_id,)
        ).fetchone()

        if transaction is None:
            flash("Transaction not found.", "error")
            return redirect(url_for("index"))

        if request.method == "POST":
            merchant = request.form.get("merchant", "").strip()
            amount_text = request.form.get("amount", "").strip()
            status = request.form.get("status", "").strip()

            if not merchant or len(merchant) > 100:
                flash("Enter a valid merchant name.", "error")
                return redirect(url_for(
                    "edit_transaction", transaction_id=transaction_id
                ))

            amount = parse_amount(amount_text)

            if amount is None:
                flash(
                    "Enter a valid amount greater than zero "
                    "and no greater than ₹1,000,000,000.",
                    "error"
                )
                return redirect(url_for(
                    "edit_transaction",
                    transaction_id=transaction_id
                ))

            if status not in {"Success", "Pending", "Failed"}:
                flash("Select a valid status.", "error")
                return redirect(url_for(
                    "edit_transaction", transaction_id=transaction_id
                ))

            conn.execute("""
                UPDATE transactions
                SET merchant = ?, amount = ?, status = ?
                WHERE id = ?
            """, (merchant, amount, status, transaction_id))

            flash("Transaction updated successfully.", "success")
            return redirect(url_for("index"))

    return render_template("edit.html", transaction=transaction)




if __name__ == "__main__":
    init_db()
    app.run(debug=True)
