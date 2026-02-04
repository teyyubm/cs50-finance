# C$50 Finance

A virtual stock portfolio web application. Register, get real-time quotes, buy and sell shares, and view your transaction history—all with simulated cash.

**Stock portfolio simulator:** user auth, Alpha Vantage quotes, buy/sell, transaction history. Python/Flask, SQLite, Bootstrap 5.

---

## Features

| Feature | Description |
|--------|-------------|
| **Register / Log in** | Create an account or sign in. New users start with **$10,000** virtual cash. |
| **Quote** | Look up a stock by symbol and see its current price. |
| **Buy** | Purchase shares of any stock (whole shares only). |
| **Sell** | Sell shares you own. |
| **History** | View all your past buy and sell transactions. |
| **Portfolio** | Home page shows your holdings, cash balance, and total portfolio value. |
| **Change password** | Update your password from the navbar. |

---

## Tech stack

- **Backend:** [Flask](https://flask.palletsprojects.com/) (Python)
- **Database:** SQLite via [CS50 SQL](https://cs50.readthedocs.io/libraries/cs50/python/)
- **Auth:** [Werkzeug](https://werkzeug.palletsprojects.com/) password hashing, server-side sessions (filesystem)
- **Frontend:** Jinja2 templates, [Bootstrap 5](https://getbootstrap.com/)
- **Quotes:** [Alpha Vantage](https://www.alphavantage.co/) API (with mock fallback when no API key or offline)

---

## Prerequisites

- Python 3.8+
- pip (or use `py -m pip` on Windows)

---

## Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/teyyubm/cs50-finance.git
   cd cs50-finance
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   py -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   py -m pip install -r requirements.txt
   ```
   Or, if `pip` is on your PATH:
   ```bash
   pip install -r requirements.txt
   ```

4. **Optional: stock quotes**
   For live stock prices, get a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key) and create a `.env` file in the project root:
   ```
   API_KEY=your_alphavantage_api_key_here
   ```
   Without an API key, the app uses mock data for a few symbols (e.g. AAPL, GOOGL, MSFT, NFLX, TSLA).

---

## Running the app

From the project directory:

```bash
py -m flask run
```

Then open **http://127.0.0.1:5000** in your browser.

- First time: click **Register** to create an account.
- Use **Quote** to look up a symbol, **Buy** / **Sell** to trade, and **History** to see past transactions.

---

## Project structure

```
cs50-finance/
├── app.py              # Flask app, routes, DB setup
├── helpers.py           # apology, login_required, lookup, usd
├── requirements.txt    # Python dependencies
├── finance.db          # SQLite DB (created on first run; not in repo)
├── .env                 # API key (optional; not in repo)
├── flask_session/      # Session files (not in repo)
├── static/
│   ├── favicon.ico
│   ├── styles.css
│   └── I_heart_validator.png
└── templates/
    ├── layout.html     # Base template, navbar
    ├── index.html      # Portfolio
    ├── login.html
    ├── register.html
    ├── quote.html / quoted.html
    ├── buy.html
    ├── sell.html
    ├── history.html
    ├── password.html
    └── apology.html    # Error page
```

---

## Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Portfolio (holdings + cash + total) |
| `/login` | GET, POST | Log in |
| `/logout` | GET | Log out |
| `/register` | GET, POST | Create account |
| `/quote` | GET, POST | Look up stock quote |
| `/buy` | GET, POST | Buy shares |
| `/sell` | GET, POST | Sell shares |
| `/history` | GET | Transaction history |
| `/password` | GET, POST | Change password |

---

## License

This project is licensed under the Apache License 2.0—see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [CS50](https://cs50.harvard.edu/) — Harvard’s introduction to computer science. This project is part of the CS50x 2026 problem set **Finance**.
