apology --
    Returns error messages.

layout --
    Nav bar and copyright.

register --
    Allows user to register with a username and password.

    Username must not be taken, and must only contain alphanumeric
    characters/underscores/hyphens and have a length of 3-16 characters.

    Password must contain at least one number, one uppercase letter, one
    lowercase letter, one special character, and have a length of 8-20
    characters.
    
    HTML validation is present as well as backend validation.

login --
    Logs the user in, creating a unique session in Flask and allowing
    access to all user pages.

create --
    Allows user to create a new flashcard set.

    Title and description are input fields, meant to be shorter in length.

    Flashcard fields contain a "term" and "definition" - the term is
    meant to contain coding language. Each new card is contained in a
    Bootstrap "card" component, and is labeled according to how many
    cards are present on the page.

    Click the "Add Card" button to create another card in the set.

    Textareas will dynamically size according to the size of the content,
    and the formatting will be retained and displayed in preformatted
    code.

index --
    Displays all user sets.

    Database is constructed specifically so all flashcards and sets have
    unique IDs, and the user will only be able to see their own.

    "Last updated" time automatically formats from UTC in the database to
    the user's time zone according to their session.

    Each set is clickable and contains information about the number of
    cards.

    All sets are sorted from top to bottom by the most recently updated.

set --
    Displays all flashcards in the set.

    Toggle syntax highlighting from Highlight.js. The theme is
    customizable in the source code by modifying the URL.

    Each individual flashcard has a syntax highlighting toggle, and all
    are affected by the global toggle at the top.

    Click "Edit set" to edit the set.

edit --
    Fills autosized textareas with the content from the set to edit.

    Updates database directly with changes and additions.

    Deletion functionality to come in future updates - for now, just
    creates new sets.

