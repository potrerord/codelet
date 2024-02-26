import csv
from datetime import datetime, timedelta
import pytz
import requests
import subprocess
from typing import Any, Callable
import urllib.parse
import uuid

from flask import redirect, render_template, session
from functools import wraps


def apology(message: str, code: int = 400) -> tuple[str, int]:
    """Render an error message to the user.
    :param message: TODO
    :param code: TODO
    """

    def escape_special_chars(arg_str: str) -> str:
        """Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """

        old_char: str
        new_char: str
        for old_char, new_char in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            escaped_str: str = arg_str.replace(old_char, new_char)
        return escaped_str

    return render_template("apology.html", top=code, bottom=escape_special_chars(message)), code


def login_required(func: Callable) -> Callable:
    """Decorate functions to require login before accessing routes.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """

    @wraps(func)
    def decorated_function(*args: Any, **kwargs: Any) -> Callable:
        """Redirect user to login if current session has no user_id."""

        if session.get("user_id") is None:
            return redirect("/login")
        return func(*args, **kwargs)

    return decorated_function


def lookup(symbol: str) -> dict[str, str | float] | None:
    """Look up quote for stock symbol argument."""

    # Prepare API request with stock symbol, current time, and start time.
    symbol = symbol.upper()
    end = datetime.now(pytz.timezone("US/Eastern"))
    start = end - timedelta(days=7)

    # Yahoo Finance API
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{urllib.parse.quote_plus(symbol)}"
        f"?period1={int(start.timestamp())}"
        f"&period2={int(end.timestamp())}"
        f"&interval=1d&events=history&includeAdjustedClose=true"
    )

    # Query API
    try:
        response = requests.get(
            url,
            cookies={"session": str(uuid.uuid4())},
            headers={"User-Agent": "python-requests", "Accept": "*/*"},
        )
        response.raise_for_status()

        # CSV header: Date,Open,High,Low,Close,Adj Close,Volume
        quotes = list(csv.DictReader(response.content.decode("utf-8").splitlines()))
        quotes.reverse()
        price = round(float(quotes[0]["Adj Close"]), 2)

        # Return dictionary
        return {"name": symbol, "price": price, "symbol": symbol}
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None


def sqlf_datetime(raw_datetime: datetime) -> str:
    """Format a datetime in SQL format."""

    # Format according to the SQL datetime structure.
    formatted_datetime = raw_datetime.strftime("%Y-%m-%d %H:%M:%S")

    return formatted_datetime


def usd(value: float) -> str:
    """Format value as USD."""
    return f"${value:,.2f}"
