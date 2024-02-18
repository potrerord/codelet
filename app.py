"""
Quizlet-style coding app.

Environment command:
    source env/bin/activate

Test considerations to be changed in the future:
  - Debug mode: on (app.debug = True, export FLASK_DEBUG=1)
  - User email: not required
"""

from datetime import datetime, timedelta
import json
import re  # regex searches
import sqlite3
from typing import Any, Dict, Tuple, Union  # used in type hints

from cs50 import SQL  # contains SQL setup
from flask import Flask, render_template, redirect, request, Response as flaskResponse, session
from flask_session import Session  # store session data on server side
import pytz  # timezone functionality
from werkzeug import Response as werkzeugResponse
from werkzeug.security import check_password_hash, generate_password_hash

import helpers

# Configure Flask application in current file in debug mode.
app = Flask(__name__)
app.debug = True

# Configure Flask to store sessions on local disk (not signed cookies).
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Create database file if it does not exist.
conn = sqlite3.connect("codelet.db")

# Create SQL class object from CS50 library with codelet.db database.
db = SQL("sqlite:///codelet.db")

# TODO: make email not null (when secure)
# Create users table if it does not already exist.
db.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id               INTEGER  NOT NULL PRIMARY KEY,
        username         TEXT     NOT NULL,
        hash             TEXT     NOT NULL,
        email            TEXT,
        registration_utc DATETIME NOT NULL DEFAULT (datetime('now', 'utc'))
    )
    """
)

# Create table for flashcard sets if it does not already exist.
db.execute(
    """
    CREATE TABLE IF NOT EXISTS sets (
        id              INTEGER  NOT NULL PRIMARY KEY,
        user_id         INTEGER  NOT NULL,
        title           TEXT     NOT NULL,
        description     TEXT,
        number_of_cards INTEGER  NOT NULL,
        creation_utc    DATETIME NOT NULL DEFAULT (datetime('now', 'utc')),
        update_utc      DATETIME NOT NULL DEFAULT (datetime('now', 'utc')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
)

# Create table for flashcards if it does not already exist.
db.execute(
    """
    CREATE TABLE IF NOT EXISTS flashcards (
        id           INTEGER  NOT NULL PRIMARY KEY,
        set_id       INTEGER  NOT NULL,
        term         TEXT,
        definition   TEXT,
        language     TEXT,
        creation_utc DATETIME NOT NULL DEFAULT (datetime('now', 'utc')),
        update_utc   DATETIME NOT NULL DEFAULT (datetime('now', 'utc')),
        FOREIGN KEY (set_id) REFERENCES sets(id)
    )
    """
)


@app.after_request
def after_request(response: flaskResponse) -> flaskResponse:
    """Ensure responses aren't cached."""

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@helpers.login_required
def index() -> str:
    """Show user's sets."""

    # Get user's username.
    user_username = db.execute(
        """
        SELECT users.username
          FROM users
         WHERE users.id = ?
        """,
        session["user_id"],
    )[0]["username"]
    
    # Get user's current sets.
    user_sets = db.execute(
        """
        SELECT *
          FROM sets
         WHERE sets.user_id = ?
         ORDER BY sets.update_utc DESC
        """,
        session["user_id"],
    )

    # Get current datetime.
    current_datetime = datetime.now(pytz.utc)

    # Initialize empty lists to organize user sets by update time.
    past_day_sets = []
    past_week_sets = []
    past_month_sets = []
    past_ever_sets = []

    # Create timedelta objects for comparisons to time differences.
    one_day = timedelta(days=1)
    one_week = timedelta(days=7)
    one_month = timedelta(days=30)

    for set in user_sets:
        # Create date object for update UTC from SQL and make timezone-aware.
        update_utc = datetime.strptime(set["update_utc"], "%Y-%m-%d %H:%M:%S")
        update_utc = pytz.utc.localize(update_utc)

        if current_datetime - update_utc < one_day:
            past_day_sets.append(set)
        elif current_datetime - update_utc < one_week:
            past_week_sets.append(set)
        elif current_datetime - update_utc < one_month:
            past_month_sets.append(set)
        else:
            past_ever_sets.append(set)
        
    # Render index with relevant variables for Jinja templating.
    return render_template("index.html",
                           user_username=user_username,
                           past_day_sets=past_day_sets,
                           past_week_sets=past_week_sets,
                           past_month_sets=past_month_sets,
                           past_ever_sets=past_ever_sets
                          )


@app.route("/create", methods=["GET", "POST"])
@helpers.login_required
def create() -> Union[Tuple[str, int], werkzeugResponse, str]:
    """Create flashcards."""

    # If user arrived to /create via POST,
    if request.method == "POST":
        # Verify that form has input.
        if not request.form:
            return helpers.apology("Empty submission.")

        # Initialize empty dictionary for parsing flashcard data.
        flashcards = {}

        # Parse flashcard data from form submissions.
        for html_name, html_value in request.form.items():
            # Check if the HTML name contains "term".
            if "term" in html_name:
                # Parse the number found at the end of the name.
                number = re.findall(r'\d+$', html_name)[0]

                # Save the term.
                if number not in flashcards:
                    flashcards[number]= {"term": html_value}
                else:
                    flashcards[number]["term"] = html_value
            # If not, do the same for "definition".
            elif "definition" in html_name:
                # Parse the number found at the end of the name.
                number = re.findall(r'\d+$', html_name)[0]

                # Save the definition.
                if number not in flashcards:
                    flashcards[number]= {"definition": html_value}
                else:
                    flashcards[number]["definition"] = html_value

        # Update set database.
        db.execute(
            """
            INSERT INTO sets (title, user_id, number_of_cards)
            VALUES (?, ?, ?)
            """,
            request.form["input-title"],
            session["user_id"],
            len(flashcards)
        )

        # Get autoincremented set id.
        set_id = db.execute(
            """
            SELECT sets.id
              FROM sets
             WHERE title = ?
               AND user_id = ?
             """,
            request.form["input-title"],
            session["user_id"]
        )[0]["id"]

        # Iterate through each side of each flashcard.
        for number in flashcards:
            # Return empty string if term or definition does not exist.
            term = flashcards[number].get("term", "")
            definition = flashcards[number].get("definition", "")

            # Insert term and definition into database.
            db.execute(
                """
                INSERT INTO flashcards (set_id, term, definition)
                VALUES (?, ?, ?)
                """,
                set_id,
                term,
                definition
            )
        
        # Redirect to homepage after successful save.
        return redirect("/")

    # If user arrived to /create via GET, render page.
    else:
        return render_template("create.html")
    

@app.route("/edit/<int:set_id>", methods=["GET", "POST"])
@helpers.login_required
def edit(set_id: int) -> Union[Tuple[str, int], werkzeugResponse, str]:
    """Edit flashcards."""

    # If user arrived to /edit via POST,
    if request.method == "POST":
        # Verify that form has input.
        if not request.form:
            return helpers.apology("Empty submission.")

        # Initialize empty dictionary for parsing flashcard data.
        new_flashcards = {}

        # For each name/value pair in form submissions,
        for html_name, html_value in request.form.items():
            # If  html_name matches the hidden "delete" input, delete cards.
            if "input-deleted-cards-list" in html_name:
                # Skip if the deleted cards list is empty.
                if not html_value:
                    continue

                # Convert the JSON string into a Python list.
                deleted_cards_list = json.loads(html_value)

                # Get card id numbers from the list in the html_value.
                for deleted_card_name in deleted_cards_list:
                    # Parse the number found at the end of the name if possible.
                    deleted_card_id = re.findall(r'\d+$', deleted_card_name)

                    # Delete existing flashcard data.
                    db.execute(
                        """
                        DELETE FROM flashcards
                         WHERE id = ?
                        """,
                        deleted_card_id
                    )

            # If the html_name contains "new", it's a new card.
            if "new" in html_name:
                # Check if the HTML name contains "term".
                if "term" in html_name:
                    # Parse the number found at the end of the name.
                    html_number = re.findall(r'\d+$', html_name)[0]

                    # Save the term.
                    if html_number not in new_flashcards:
                        new_flashcards[html_number]= {"term": html_value}
                    else:
                        new_flashcards[html_number]["term"] = html_value
                
                # If "term" is not in the HTML name, check "definition".
                elif "definition" in html_name:
                    # Parse the number found at the end of the name.
                    html_number = re.findall(r'\d+$', html_name)[0]

                    # Save the definition.
                    if html_number not in new_flashcards:
                        new_flashcards[html_number]= {"definition": html_value}
                    else:
                        new_flashcards[html_number]["definition"] = html_value

            # If it's not new, update the existing card in the database.
            else:
                # If the form submission item is a term,
                if "term" in html_name:
                    # Get number from html_name (should match flashcard id).
                    existing_flashcard_id = re.findall(r'\d+$', html_name)[0]

                    # Update existing flashcard term data.
                    db.execute(
                        """
                        UPDATE flashcards
                           SET term = ?
                         WHERE id = ?
                        """,
                        html_value,
                        existing_flashcard_id
                    )

                # If the form submission item is a definition,
                elif "definition" in html_name:
                    # Get number from html_name (should match flashcard id).
                    existing_flashcard_id = re.findall(r'\d+$', html_name)[0]

                    # Update existing flashcard definition data.
                    db.execute(
                        """
                        UPDATE flashcards
                            SET definition = ?
                          WHERE id = ?
                        """,
                        html_value,
                        existing_flashcard_id
                    )

        # Create new flashcards.
        for html_number in new_flashcards:
            # Return empty string if term or definition does not exist.
            new_term = new_flashcards[html_number].get("term", "")
            new_definition = new_flashcards[html_number].get("definition", "")

            # Insert term and definition into database.
            # New card id will autoincrement.
            db.execute(
                """
                INSERT INTO flashcards (set_id, term, definition)
                VALUES (?, ?, ?)
                """,
                set_id,
                new_term,
                new_definition
            )

        number_of_cards = db.execute(
            """
            SELECT COUNT(*) AS count
              FROM flashcards
             WHERE set_id = ?
            """,
            set_id
        )[0]["count"]
        
        # Update set database.
        db.execute(
            """
            UPDATE sets
               SET title = ?,
                   description = ?,
                   number_of_cards = ?,
                   update_utc = ?
             WHERE user_id = ?
               AND id = ?
            """,
            request.form["input-title"],
            request.form["input-description"],
            number_of_cards,
            datetime.now(pytz.timezone("UTC")),
            session["user_id"],
            set_id,
        )

        # Redirect to homepage after successful save.
        return redirect(f"/set/{set_id}")


    # If user arrived to /edit via GET, render page.
    else:
        # Get user's current set ids.
        user_sets = db.execute(
            """
            SELECT sets.id
            FROM sets
            WHERE sets.user_id = ?
            """,
            session["user_id"],
        )

        # Check to make sure set belongs to user.
        user_set_ids = []
        for set in user_sets:
            user_set_ids.append(set["id"])

        # Redirect to index if they are trying to access an invalid set.
        if set_id not in user_set_ids:
            return redirect("/")
        
        # Get set data.
        set_data = db.execute(
            """
            SELECT *
            FROM sets
            WHERE sets.id = ?
            AND sets.user_id = ?
            """,
            set_id,
            session["user_id"]
        )[0]

        # Get flashcard data.
        flashcard_data = db.execute(
            """
            SELECT *
            FROM flashcards AS f
            WHERE f.set_id = ?
            """,
            set_id
        )

        return render_template("edit.html", flashcard_data=flashcard_data,
                                set_data=set_data)

@app.route("/login", methods=["GET", "POST"])
def login() -> Union[Tuple[str, int], werkzeugResponse, str]:
    """Log user in."""

    # Clear all session data from session directory.
    session.clear()

    # If user reached login route via POST (e.g. submitting a POST form)
    if request.method == "POST":
        # Ensure username was submitted.
        form_username = request.form.get("username")
        if not form_username:
            return helpers.apology("must provide username", 403)

        # Ensure password was submitted.
        form_password = request.form.get("password")
        if not form_password:
            return helpers.apology("must provide password", 403)

        # Query codelet.db database for username.
        rows = db.execute(
            """
            SELECT *
              FROM users
             WHERE users.username = ?
            """,
            form_username,
        )

        # Ensure username exists in database and password is correct.
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], form_password):
            return helpers.apology("invalid username and/or password", 403)

        # Assign user's codelet.db id to their current session user_id.
        session["user_id"] = rows[0]["id"]

        # Redirect the user to the homepage.
        return redirect("/")

    # If user reached login route via GET (e.g. clicking link; redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout() -> Union[werkzeugResponse, str]:
    """Log user out."""

    # Clear all session data from session directory.
    session.clear()

    # Redirect user to the login form.
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register() -> Union[Tuple[str, int], werkzeugResponse, str]:
    """Register user into codelet.db database via a form."""

    # If user navs to /register via POST (e.g. through form submission)
    if request.method == "POST":
        # Retrieve user data from database.
        users = db.execute("SELECT * FROM users")

        # Apologize if no username was entered.
        form_username = request.form.get("username")
        if not form_username:
            return helpers.apology("Must enter a username.")

        # Apologize if username already exists.
        username_exists = False
        for user in users:
            if user["username"] == form_username:
                return helpers.apology("Username already exists.")

        # Apologize if username has forbidden characters or length.
        if (
            re.search("[^a-zA-Z0-9_-]", form_username)
            or not 3 <= len(form_username) <= 16
        ):
            return helpers.apology(
                "Username must only contain alphanumeric characters/"
                "underscores/hyphens and have a length of 3-16 characters."
            )

        # Apologize if no password was entered.
        form_password = request.form.get("password")
        form_password_confirm = request.form.get("confirmation")
        if not form_password or not form_password_confirm:
            return helpers.apology("Must enter a password and password confirmation.")

        # Apologize if passwords do not match.
        if form_password != form_password_confirm:
            return helpers.apology("Passwords do not match.")

        # Apologize if password is incorrect length.
        if not 8 <= len(form_password) <= 20:
            return helpers.apology("Password must have a length of 8-20 characters.")

        # Initialize list of dicts for password requirements.
        password_reqs = [
            {
                "id": "lower",
                "check": "[a-z]",
                "met": True,
                "message": "Password does not contain lowercase character.",
            },
            {
                "id": "upper",
                "check": "[A-Z]",
                "met": True,
                "message": "Password does not contain uppercase character.",
            },
            {
                "id": "numeral",
                "check": "[\\d]",
                "met": True,
                "message": "Password does not contain numeral 0-9.",
            },
            {
                "id": "special",
                "check": "[\\W_-]",
                "met": True,
                "message": "Password does not contain special character.",
            },
            {
                "id": "no_username",
                "check": form_username,
                "met": True,
                "message": "Password contains username.",
            },
        ]

        # Check if password fails to match requirements.
        valid_password = True
        for req in password_reqs:
            # Mark password invalid if requisite char is not found.
            if not re.search(rf"{req['check']}", form_password):
                if req["id"] != "no_username":
                    req["met"] = False
                    valid_password = False

            # Mark password invalid if username is found.
            else:
                if req["id"] == "no_username":
                    req["met"] = False
                    valid_password = False

        # If password fails to match reqs, apologize with specific error.
        if not valid_password:
            invalid_pw_message = "Password contained the following errors:"
            for req in password_reqs:
                if not req["met"]:
                    invalid_pw_message += f"\n{req['message']}"
            return helpers.apology(invalid_pw_message)

        # Hash password and clear reference to form_password variable data.
        hashed_form_password = generate_password_hash(form_password)
        form_password = None

        # Save new user into database; let id autoincrement in database.
        db.execute(
            """
            INSERT INTO users (username, hash)
            VALUES (?, ?)
            """,
            form_username,
            hashed_form_password
        )

        # Query database for user id.
        new_user = db.execute(
            """
            SELECT *
              FROM users
             WHERE username = ?
            """,
            form_username
        )

        # After successful registration, log user in and redirect home.
        if new_user:
            session["user_id"] = new_user[0]["id"]
            return redirect("/")

        # If new user does not exist, apologize for unknown error.
        else:
            return helpers.apology("Unknown error occurred.")

    # Render page if user did not arrive via POST.
    else:
        return render_template("register.html")


@app.route("/set/<int:set_id>", methods=["GET", "POST"])
@helpers.login_required
def set(set_id: int) -> Union[Tuple[str, int], werkzeugResponse, str]:
    """Display specific set with unique id."""

    # Get user's current set ids.
    user_sets = db.execute(
        """
        SELECT sets.id
        FROM sets
        WHERE sets.user_id = ?
        """,
        session["user_id"],
    )

    # Check to make sure set belongs to user.
    user_set_ids = []
    for set in user_sets:
        user_set_ids.append(set["id"])

    # Redirect to index if they are trying to access an invalid set.
    if set_id not in user_set_ids:
        return redirect("/")
    
    # Get set data.
    set_data = db.execute(
        """
        SELECT *
          FROM sets
         WHERE sets.id = ?
           AND sets.user_id = ?
        """,
        set_id,
        session["user_id"]
    )[0]

    # Get flashcard data.
    flashcard_data = db.execute(
        """
        SELECT *
          FROM flashcards AS f
         WHERE f.set_id = ?
        """,
        set_id
    )

    return render_template("set.html", flashcard_data=flashcard_data,
                           set_data=set_data)