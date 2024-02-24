Anthony Narag\
2024-02-23-fri

# Codelet

This is Codelet, a (work-in-progress) flashcard web app designed specifically for studying code.

The backend of this app runs on Python/Flask, using Jinja to create HTML/CSS/JavaScript webpages on the front end. Card and user information is stored in SQL databases, with some basic security measures like password hashing to allow for individual user login sessions.

## Getting started

```
$ python -m env .venv
```

Create a Python virtual environment named `.venv/` in the local directory.

```
$ source .venv/bin/activate
```

Activate the Python virtual environment.

```
$ export FLASK_DEBUG=1
```

Enable the Flask debugger, which allows you to run Codelet on your local system with live changes as the code is updated.

```
$ flask run
```

Initiate a session on your local server. You should see `* Debug mode: on` if the debugger is active.

```
* Running on https://###.#.#.#:####
```

`Cmd + click` on the URL to render the login page on your default browser. You can now use Codelet!

```
⌃CTRL + C
```

Exit the Flask session.

## SQL Databases

```
$ sqlite3 codelet.db
sqlite> .schema
```

Access and view the SQL databases containing card and user data.

## Notes

I only recently began using Git and GitHub in earnest, so my next stage here involves cleaning up some experimentation I've added since the first working version of this app was complete and organizing the workflow with branches. I made the original version of this app for my Harvard CS50 final project, but I would like to decentralize some of the CS50-related dependencies as this project evolves.

It has also been a bit since I've taken a look at the code here so one of my first plans is to create more useful documentation, if anything just to help me hit the ground running when I come back to this project after a hiatus.

## todo
- Debug mode: on (app.debug = True, export FLASK_DEBUG=1)
- User email: not currently required
- Revert changes from most recent experiment with syntax highlighting
