import os
import sqlite3
try:
    from dotenv import load_dotenv
    load_dotenv()  # load API_KEY from .env when package is installed
except ImportError:
    pass  # run without .env file; use shell env or mock quotes
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

app = Flask(__name__)
app.jinja_env.filters["usd"] = usd
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# cs50.SQL requires the database file to exist; create it if missing
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finance.db")
if not os.path.exists(db_path):
    sqlite3.connect(db_path).close()

db = SQL("sqlite:///finance.db")

# Ensure users and transactions tables exist (for fresh installs)
db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        hash TEXT NOT NULL,
        cash REAL NOT NULL DEFAULT 10000.00
    )
""")
db.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        shares INTEGER NOT NULL,
        price REAL NOT NULL,
        type TEXT NOT NULL,
        transacted DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
""")
db.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions (user_id)")
db.execute(
    "CREATE INDEX IF NOT EXISTS idx_transactions_user_symbol ON transactions (user_id, symbol)"
)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks."""
    user_id = session["user_id"]
    rows = db.execute(
        """
        SELECT symbol,
               SUM(CASE WHEN type = 'buy' THEN shares ELSE -shares END) AS shares
        FROM transactions
        WHERE user_id = :user_id
        GROUP BY symbol
        HAVING shares > 0
        """,
        user_id=user_id,
    )
    holdings = []
    total_stocks = 0.0
    for row in rows:
        quote = lookup(row["symbol"])
        if quote:
            value = row["shares"] * quote["price"]
            total_stocks += value
            holdings.append(
                {
                    "symbol": row["symbol"],
                    "name": quote["name"],
                    "shares": row["shares"],
                    "price": quote["price"],
                }
            )
    user = db.execute("SELECT cash FROM users WHERE id = :id", id=user_id)
    cash = user[0]["cash"] if user else 0
    total = cash + total_stocks
    return render_template("index.html", holdings=holdings, cash=cash, total=total)


@app.route("/buy", methods=["GET", "POST"], strict_slashes=False)
@login_required
def buy():
    """Buy shares of stock."""
    if request.method == "GET":
        return render_template("buy.html")

    symbol = request.form.get("symbol", "").strip()
    shares_str = request.form.get("shares", "").strip()
    if not symbol:
        return apology("must provide symbol")
    if not shares_str:
        return apology("must provide number of shares")

    try:
        if "." in shares_str:
            return apology("shares must be a whole number")
        shares = int(shares_str)
    except ValueError:
        return apology("shares must be a positive integer")
    if shares < 1:
        return apology("shares must be a positive integer")

    quote = lookup(symbol)
    if not quote:
        return apology("invalid symbol")

    user_id = session["user_id"]
    rows = db.execute("SELECT cash FROM users WHERE id = :id", id=user_id)
    cash = rows[0]["cash"]
    cost = quote["price"] * shares
    if cost > cash:
        return apology("can't afford that many shares")

    db.execute(
        "UPDATE users SET cash = cash - :cost WHERE id = :id",
        cost=cost,
        id=user_id,
    )
    db.execute(
        """
        INSERT INTO transactions (user_id, symbol, shares, price, type)
        VALUES (:user_id, :symbol, :shares, :price, 'buy')
        """,
        user_id=user_id,
        symbol=quote["symbol"],
        shares=shares,
        price=quote["price"],
    )
    flash("Bought!")
    return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    user_id = session["user_id"]
    rows = db.execute(
        """
        SELECT symbol, shares, price, type, transacted
        FROM transactions
        WHERE user_id = :user_id
        ORDER BY transacted DESC
        """,
        user_id=user_id,
    )
    history_list = [
        {
            "symbol": r["symbol"],
            "shares": r["shares"],
            "price": r["price"],
            "type": r["type"].capitalize(),
            "transacted": r["transacted"],
        }
        for r in rows
    ]
    return render_template("history.html", history=history_list)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""
    session.clear()
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not username:
        return apology("must provide username")
    if not password:
        return apology("must provide password")

    rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
        return apology("invalid username and/or password")

    session["user_id"] = rows[0]["id"]
    flash("Welcome back!")
    return redirect("/")


@app.route("/logout")
def logout():
    """Log user out."""
    session.clear()
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")

    symbol = request.form.get("symbol", "").strip()
    if not symbol:
        return apology("must provide symbol")

    quote_result = lookup(symbol)
    if not quote_result:
        return apology("invalid symbol")

    return render_template(
        "quoted.html",
        name=quote_result["name"],
        symbol=quote_result["symbol"],
        price=quote_result["price"],
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirmation = request.form.get("confirmation", "")
    if not username:
        return apology("must provide username")
    if not password:
        return apology("must provide password")
    if not confirmation:
        return apology("must confirm password")
    if password != confirmation:
        return apology("passwords do not match")

    try:
        db.execute(
            "INSERT INTO users (username, hash) VALUES (:username, :hash)",
            username=username,
            hash=generate_password_hash(password),
        )
    except ValueError:
        return apology("username already exists")

    rows = db.execute("SELECT id FROM users WHERE username = :username", username=username)
    session["user_id"] = rows[0]["id"]
    flash("Registered!")
    return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    user_id = session["user_id"]
    if request.method == "GET":
        rows = db.execute(
            """
            SELECT symbol,
                   SUM(CASE WHEN type = 'buy' THEN shares ELSE -shares END) AS shares
            FROM transactions
            WHERE user_id = :user_id
            GROUP BY symbol
            HAVING shares > 0
            """,
            user_id=user_id,
        )
        return render_template("sell.html", symbols=rows)

    symbol = request.form.get("symbol", "").strip()
    shares_str = request.form.get("shares", "").strip()
    if not symbol:
        return apology("must select a symbol")
    if not shares_str:
        return apology("must provide number of shares")

    try:
        if "." in shares_str:
            return apology("shares must be a whole number")
        shares = int(shares_str)
    except ValueError:
        return apology("shares must be a positive integer")
    if shares < 1:
        return apology("shares must be a positive integer")

    rows = db.execute(
        """
        SELECT SUM(CASE WHEN type = 'buy' THEN shares ELSE -shares END) AS shares
        FROM transactions
        WHERE user_id = :user_id AND symbol = :symbol
        GROUP BY symbol
        """,
        user_id=user_id,
        symbol=symbol,
    )
    if not rows or rows[0]["shares"] < shares:
        return apology("you don't own that many shares")

    quote = lookup(symbol)
    if not quote:
        return apology("symbol lookup failed")

    proceeds = quote["price"] * shares
    db.execute(
        "UPDATE users SET cash = cash + :proceeds WHERE id = :id",
        proceeds=proceeds,
        id=user_id,
    )
    db.execute(
        """
        INSERT INTO transactions (user_id, symbol, shares, price, type)
        VALUES (:user_id, :symbol, :shares, :price, 'sell')
        """,
        user_id=user_id,
        symbol=symbol,
        shares=shares,
        price=quote["price"],
    )
    flash("Sold!")
    return redirect("/")


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Change password (personal touch)."""
    if request.method == "GET":
        return render_template("password.html")

    current = request.form.get("current", "")
    password = request.form.get("password", "")
    confirmation = request.form.get("confirmation", "")
    if not current:
        return apology("must provide current password")
    if not password:
        return apology("must provide new password")
    if not confirmation:
        return apology("must confirm new password")
    if password != confirmation:
        return apology("new passwords do not match")

    user_id = session["user_id"]
    rows = db.execute("SELECT hash FROM users WHERE id = :id", id=user_id)
    if not rows or not check_password_hash(rows[0]["hash"], current):
        return apology("current password is wrong")

    db.execute(
        "UPDATE users SET hash = :hash WHERE id = :id",
        hash=generate_password_hash(password),
        id=user_id,
    )
    flash("Password updated!")
    return redirect("/")
