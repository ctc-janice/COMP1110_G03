"""
validator.py — Input Validation
=================================
WHAT THIS FILE DOES:
    Before we do any routing, we need to make sure the user's inputs make sense.
    This file checks every piece of user input and returns clear error messages.

    Think of it as a bouncer — nothing gets into the routing engine unless it passes here.

WHAT WE VALIDATE:
    1. Stop IDs       — Does the stop actually exist in our network?
    2. Origin/Dest    — Are they different stops? (Can't travel to where you already are)
    3. Preference     — Is it exactly one of: 'fastest', 'cheapest', 'fewest'?

DESIGN PRINCIPLE:
    Every function returns a tuple: (is_valid: bool, error_message: str)
    This makes it easy to check in main.py without crashing:
        ok, msg = validate_stop("HK999", stops)
        if not ok:
            print(msg)

USAGE:
    from validator import validate_stop, validate_journey_request, validate_preference
"""


# Valid preference keywords — single source of truth
# SUGGESTION: If you add more preference modes later (e.g., "balanced"), add them here.
VALID_PREFERENCES = {"fastest", "cheapest", "fewest_segments"}


# ─────────────────────────────────────────────
# INDIVIDUAL VALIDATION FUNCTIONS
# ─────────────────────────────────────────────

def validate_stop(stop_input, stops):
    """
    Check that a stop ID or name exists in the loaded network.

    Args:
        stop_input (str): Whatever the user typed
        stops (dict):     The loaded stops dictionary from io_handler

    Returns:
        (True, stop_id)       if valid   ← note: returns the canonical ID, not just True
        (False, error_msg)    if invalid

    Example:
        ok, result = validate_stop("hk001", stops)
        # ok=True, result="HK001"  (we normalise to uppercase)

        ok, result = validate_stop("HK999", stops)
        # ok=False, result="Stop 'HK999' was not found in the network. ..."
    """
    if not stop_input or not stop_input.strip():
        return False, "Stop input cannot be empty. Please enter a stop ID (e.g. HK001)."

    # Normalise: strip whitespace and uppercase for case-insensitive matching
    normalised = stop_input.strip().upper()

    if normalised in stops:
        return True, normalised

    # Stop not found — give a helpful hint
    # Show a few similar IDs so the user can self-correct
    close_matches = [sid for sid in stops if normalised in sid or normalised in stops[sid]["name"].upper()]
    hint = ""
    if close_matches:
        hint = f" Did you mean: {', '.join(close_matches[:3])}?"
    else:
        hint = f" Available stops: {', '.join(list(stops.keys())[:5])}... (see stops.csv for full list)"

    return False, f"Stop '{stop_input}' was not found in the network.{hint}"


def validate_origin_destination(origin_id, destination_id):
    """
    Check that origin and destination are not the same stop.

    Call this AFTER validate_stop() has confirmed both stops exist.

    Args:
        origin_id      (str): Validated origin stop ID
        destination_id (str): Validated destination stop ID

    Returns:
        (True, None)        if they are different
        (False, error_msg)  if they are the same
    """
    if origin_id == destination_id:
        return False, (
            f"Origin and destination cannot be the same stop ('{origin_id}'). "
            "Please choose two different stops."
        )
    return True, None


def validate_preference(preference_input):
    """
    Check that the user's chosen preference is one of the three valid modes.

    Args:
        preference_input (str): Whatever the user typed

    Returns:
        (True, preference)     if valid   ← returns the normalised lowercase string
        (False, error_msg)     if invalid

    Example:
        ok, result = validate_preference("FASTEST")
        # ok=True, result="fastest"

        ok, result = validate_preference("quickest")
        # ok=False, result="Invalid preference 'quickest'. ..."
    """
    if not preference_input or not preference_input.strip():
        return False, f"Preference cannot be empty. Choose one of: {', '.join(sorted(VALID_PREFERENCES))}."

    normalised = preference_input.strip().lower()

    if normalised in VALID_PREFERENCES:
        return True, normalised

    return False, (
        f"Invalid preference '{preference_input}'. "
        f"Please choose exactly one of: {', '.join(sorted(VALID_PREFERENCES))}."
    )


def validate_journey_request(origin_input, destination_input, preference_input, stops):
    """
    ★ MASTER VALIDATION — validates all three inputs in one call.

    This is the function main.py should call before routing.
    It runs all checks in order and returns the first error encountered,
    or returns all validated values if everything is OK.

    Args:
        origin_input      (str):  User's raw origin input
        destination_input (str):  User's raw destination input
        preference_input  (str):  User's raw preference input
        stops             (dict): Loaded network stops

    Returns:
        On success: (True,  { "origin": "HK001", "destination": "HK005", "preference": "fastest" })
        On failure: (False, "Human-readable error message explaining what went wrong")

    Example (main.py usage):
        ok, result = validate_journey_request("hk001", "HK005", "Fastest", stops)
        if not ok:
            print(f"Input Error: {result}")
        else:
            plan_route(result["origin"], result["destination"], result["preference"])
    """
    # Step 1: Validate origin
    ok, origin_result = validate_stop(origin_input, stops)
    if not ok:
        return False, f"Invalid origin — {origin_result}"

    # Step 2: Validate destination
    ok, destination_result = validate_stop(destination_input, stops)
    if not ok:
        return False, f"Invalid destination — {destination_result}"

    # Step 3: Check they're not the same
    ok, err = validate_origin_destination(origin_result, destination_result)
    if not ok:
        return False, err

    # Step 4: Validate preference
    ok, preference_result = validate_preference(preference_input)
    if not ok:
        return False, preference_result
    # All good — return cleaned, normalised values
    return True, {
        "origin":      origin_result,
        "destination": destination_result,
        "preference":  preference_result,
    }


# ─────────────────────────────────────────────
# EDGE CASE TEST SUITE
# Run this file directly to see all test results
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # We need a mock stops dict for testing (no file needed)
    mock_stops = {
        "HK001": {"name": "Central MTR",      "transport_type": "MTR"},
        "HK002": {"name": "Admiralty MTR",     "transport_type": "MTR"},
        "HK005": {"name": "Tsim Sha Tsui MTR", "transport_type": "MTR"},
    }

    test_cases = [
        # Format: (description, origin, destination, preference, expect_valid)
        ("Normal valid request",            "HK001", "HK005", "fastest",   True),
        ("Case-insensitive stop ID",         "hk001", "hk005", "CHEAPEST",  True),
        ("Case-insensitive preference",      "HK001", "HK005", "Fewest_Segments", True),
        ("Same origin and destination",      "HK001", "HK001", "fastest",   False),
        ("Non-existent origin",              "HK999", "HK005", "fastest",   False),
        ("Non-existent destination",         "HK001", "HK999", "fastest",   False),
        ("Invalid preference",               "HK001", "HK005", "quickest",  False),
        ("Empty origin",                     "",      "HK005", "fastest",   False),
        ("Empty destination",                "HK001", "",      "fastest",   False),
        ("Empty preference",                 "HK001", "HK005", "",          False),
        ("Whitespace-only input",            "   ",   "HK005", "fastest",   False),
        ("Completely wrong stop format",     "MOON",  "HK005", "fastest",   False),
    ]

    print("=" * 60)
    print("VALIDATOR TEST SUITE")
    print("=" * 60)

    passed = 0
    failed = 0

    for desc, origin, dest, pref, expect_valid in test_cases:
        ok, result = validate_journey_request(origin, dest, pref, mock_stops)
        status = "✓ PASS" if ok == expect_valid else "✗ FAIL"
        if ok == expect_valid:
            passed += 1
        else:
            failed += 1

        print(f"\n[{status}] {desc}")
        if ok:
            print(f"         Result: {result}")
        else:
            print(f"         Error:  {result}")

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")