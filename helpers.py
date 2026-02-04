import os
import requests
from functools import wraps
from flask import redirect, render_template, request, session


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """Decorate routes to require login."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


# Mock quotes when no API key or when API fails (for demo / offline use)
_MOCK_QUOTES = {
    "AAPL": {"name": "Apple Inc.", "price": 185.50, "symbol": "AAPL"},
    "GOOGL": {"name": "Alphabet Inc.", "price": 142.20, "symbol": "GOOGL"},
    "MSFT": {"name": "Microsoft Corporation", "price": 415.00, "symbol": "MSFT"},
    "NFLX": {"name": "Netflix Inc.", "price": 485.00, "symbol": "NFLX"},
    "TSLA": {"name": "Tesla Inc.", "price": 248.00, "symbol": "TSLA"},
}


def lookup(symbol):
    """Look up quote for symbol. Returns dict with name, price, symbol or None.
    Uses Alpha Vantage API (IEX Cloud retired Aug 2024). Free key: alphavantage.co
    """
    symbol = symbol.strip().upper()
    if not symbol:
        return None
    api_key = os.environ.get("API_KEY") or os.environ.get("ALPHAVANTAGE_API_KEY")
    try:
        if api_key:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": api_key,
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            quote = data.get("Global Quote")
            if quote and isinstance(quote, dict) and quote.get("05. price"):
                price = float(quote["05. price"])
                sym = (quote.get("01. symbol") or symbol).strip().upper()
                return {
                    "name": sym,  # GLOBAL_QUOTE has no company name; use symbol
                    "price": price,
                    "symbol": sym,
                }
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass
    # Fallback: mock data when no key or API unreachable
    if symbol in _MOCK_QUOTES:
        return dict(_MOCK_QUOTES[symbol])
    return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
