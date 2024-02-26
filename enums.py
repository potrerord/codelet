"""
Constant page name definitions for Codelet (not necessarily "enum" 
types, but similar intent).
"""


class HtmlPageName:
    """HTML filenames to help render pages."""

    # View all sets of cards for the user.
    INDEX: str = "index.html"

    # Create a set of cards.
    CREATE: str = "create.html"

    # Edit a set of cards.
    EDIT: str = "edit.html"

    # Login to a user account.
    LOGIN: str = "login.html"

    # Register a new account.
    REGISTER: str = "register.html"

    # View a set of cards.
    SET: str = "set.html"

    # Display an error.
    APOLOGY: str = "apology.html"


class RequestMethod:
    """HTTP request types to check flask.request."""

    GET: str = "GET"
    POST: str = "POST"


class UrlExt:
    """URL extensions for each page, used in @app.route()."""
    
    # View all sets of cards for the user.
    INDEX: str = "/"

    # Create a set of cards.
    CREATE: str = "/create"

    # Edit a set of cards. TODO: "/edit/<int:set_id>"
    EDIT: str = "/edit"

    # Login to a user account.
    LOGIN: str = "/login"

    # Logout confirmation.
    LOGOUT: str = "/logout"

    # Register a new account.
    REGISTER: str = "/register"

    # View a set of cards. TODO: "/set/<int:set_id>"
    SET: str = "/set"

    # Display an error.
    APOLOGY: str = "/apology"
