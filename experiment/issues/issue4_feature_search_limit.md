# Add a limit option to search()

I often only need the first few matches (e.g. "show the latest 5 errors"), but search() always builds the full list, and I have to slice it myself. On bigger tables that is wasteful.

    db.search(where('level') == 'error')[:5]     # computes every match first

Feature request: an optional limit argument.

    db.search(where('level') == 'error', limit=5)

Expected: returns at most 5 matches, in the same order search() already returns. limit=None (default) keeps today's behaviour, and a limited search shouldn't change what a later unlimited search returns.

TinyDB commit edff96a.
