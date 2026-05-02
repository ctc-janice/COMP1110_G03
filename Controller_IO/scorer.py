"""
scorer.py — Journey Evaluation: Scoring & Ranking
===================================================
WHAT THIS FILE DOES:
    Given a list of candidate routes (paths through the network), this file:
      1. Computes stats for each route (total time, total cost, number of segments)
      2. Sorts them by the user's chosen preference
      3. Returns the top 3 results, formatted for display

WHERE DO CANDIDATE PATHS COME FROM?
    This file does NOT find paths — that's the router's job (router.py, done by a teammate).
    The router gives scorer a list of paths. Each path is a list of segment dicts:
        [
          { "from": "HK001", "to": "HK002", "duration": 3, "cost": 6.50, "transport_type": "MTR" },
          { "from": "HK002", "to": "HK005", "duration": 8, "cost": 17.0, "transport_type": "MTR" },
        ]

HOW SEGMENTS ARE COUNTED:
    A "segment" is one individual leg of the journey — one connection between two stops.
    Example: MTR -> MTR -> BUS = 3 segments (regardless of mode changes).
    Fewest segments means the route with the least number of legs/hops.

USAGE:
    from scorer import evaluate_and_rank

    top3 = evaluate_and_rank(candidate_paths, preference="fastest")
    for journey in top3:
        print_journey(journey)  # also defined in this file
"""


# ---------------------------------------------
# MAIN PUBLIC FUNCTION
# ---------------------------------------------

def evaluate_and_rank(candidate_paths, preference, stops=None):
    """
    Score and rank a list of candidate paths, return the top 3.

    Args:
        candidate_paths (list): List of paths. Each path = list of segment dicts.
        preference      (str):  One of 'fastest', 'cheapest', 'fewest_segments'
        stops           (dict): used to look up stop names for display

    Returns:
        List of up to 3 evaluated journey dicts, sorted by preference.
        Each journey dict contains:
            {
                "segments":        [...],  # original path
                "duration":        float,  # total minutes
                "cost":            float,  # total HK$
                "segments_count":  int,    # number of legs in the journey
                "rank":            int,    # 1 = best
            }

    Raises:
        ValueError if preference is not one of the three valid modes.
    """
    if not candidate_paths:
        return []  # No routes found -- router handles messaging this to the user

    VALID = {"fastest", "cheapest", "fewest_segments"}
    if preference not in VALID:
        raise ValueError(f"[Scorer] Unknown preference '{preference}'. Must be one of: {VALID}")

    # Step 1: Evaluate each path into a scored journey dict
    evaluated = [_evaluate_path(path) for path in candidate_paths]

    # Step 2: Sort by preference (primary) with tiebreakers
    sorted_journeys = _sort_journeys(evaluated, preference)

    # Step 3: Take top 3 and add rank numbers
    top3 = sorted_journeys[:3]
    for i, journey in enumerate(top3):
        journey["rank"] = i + 1

    return top3


# ---------------------------------------------
# STEP 1: EVALUATE A SINGLE PATH
# ---------------------------------------------

def _evaluate_path(path):
    """
    Compute total duration, cost, and segment count for one candidate path.

    Args:
        path (list): List of segment dicts

    Returns:
        {
            "segments":       path,
            "duration":       total_duration,
            "cost":           total_cost,
            "segments_count": number of legs,
        }
    """
    total_duration = sum(seg["duration"] for seg in path)
    total_cost     = sum(seg["cost"]     for seg in path)
    segments_count = _count_segments(path)

    return {
        "segments":       path,
        "duration":       round(total_duration, 1),
        "cost":           round(total_cost, 2),
        "segments_count": segments_count,
    }


def _count_segments(path):
    """
    Count the number of legs (individual connections) in a path.

    This is simply the length of the path list -- each dict in the list
    is one leg from one stop to another.

    Example:
        [MTR, MTR, BUS] -> 3 segments
        [MTR, MTR]      -> 2 segments
        [BUS]           -> 1 segment

    Args:
        path (list): List of segment dicts

    Returns:
        int: Number of legs
    """
    return len(path)


# ---------------------------------------------
# STEP 2: SORT BY PREFERENCE
# ---------------------------------------------

def _sort_journeys(journeys, preference):
    """
    Sort evaluated journeys by the user's preference.

    Tiebreaker logic (when primary metric is equal):
        - fastest         -> sort by cost, then segments_count
        - cheapest        -> sort by duration, then segments_count
        - fewest_segments -> sort by duration, then cost

    This ensures a consistent, fair ranking even with identical primary scores.

    Args:
        journeys   (list): List of evaluated journey dicts
        preference (str):  'fastest', 'cheapest', or 'fewest_segments'

    Returns:
        Sorted list (best first)
    """
    if preference == "fastest":
        # Primary: duration (low is best), tiebreak: cost, then segments_count
        return sorted(journeys, key=lambda j: (j["duration"], j["cost"], j["segments_count"]))

    elif preference == "cheapest":
        # Primary: cost (low is best), tiebreak: duration, then segments_count
        return sorted(journeys, key=lambda j: (j["cost"], j["duration"], j["segments_count"]))

    elif preference == "fewest_segments":
        # Primary: segments_count (low is best), tiebreak: duration, then cost
        return sorted(journeys, key=lambda j: (j["segments_count"], j["duration"], j["cost"]))

    # Should never reach here -- validator.py catches invalid preferences first
    raise ValueError(f"Unknown preference: {preference}")


# ---------------------------------------------
# STEP 3: FORMAT FOR DISPLAY
# ---------------------------------------------

def format_journey(journey, stops=None):
    """
    Format a single ranked journey into a human-readable string block.

    Args:
        journey (dict): An evaluated+ranked journey dict
        stops   (dict): Optional -- maps stop IDs to names for prettier output

    Returns:
        str: Multi-line formatted string ready to print
    """
    rank = journey.get("rank", "?")
    lines = []
    lines.append(f"\n{'─'*42}")
    lines.append(f"  #{rank}  Journey")
    lines.append(f"{'─'*42}")
    lines.append(f"Duration : {journey['duration']:.0f} mins")
    lines.append(f"Cost     : HK${journey['cost']:.2f}")
    lines.append(f"Segments : {journey['segments_count']}")
    lines.append(f"{'─'*42}")
    lines.append(f"  Route:")

    for seg in journey["segments"]:
        from_name = _get_stop_name(seg["from"], stops)
        to_name   = _get_stop_name(seg["to"],   stops)
        lines.append(f"    {from_name} -> {to_name}  [{seg['transport_type']}  {seg['duration']:.0f}min  HK${seg['cost']:.2f}]")

    lines.append(f"{'─'*42}")
    return "\n".join(lines)


def print_results(top3, preference, stops=None):
    """
    Print all top-3 results with a header.

    Args:
        top3       (list): Output from evaluate_and_rank()
        preference (str):  The user's chosen preference (for display)
        stops      (dict): Optional stop name lookup
    """
    label = {"fastest": "Fastest", "cheapest": "Cheapest", "fewest_segments": "Fewest Segments"}
    print(f"\n{'═'*42}")
    print(f"  TOP {len(top3)} ROUTES  ·  Sorted by: {label.get(preference, preference)}")
    print(f"{'═'*42}")

    if not top3:
        print("  No routes found between these stops.")
        return

    for journey in top3:
        print(format_journey(journey, stops))


def _get_stop_name(stop_id, stops):
    """Return a stop's display name, or just its ID if stops dict not provided."""
    if stops and stop_id in stops:
        return f"{stops[stop_id]['name']} ({stop_id})"
    return stop_id


# ---------------------------------------------
# INTEGRATION TEST -- run this file directly
# Tests that ranking changes correctly when preference changes
# ---------------------------------------------

if __name__ == "__main__":
    # Mock candidate paths -- normally these come from router.py
    # Path A: Fast but expensive, 2 segments
    path_a = [
        {"from": "HK001", "to": "HK002", "duration": 3,  "cost": 6.50,  "transport_type": "MTR"},
        {"from": "HK002", "to": "HK005", "duration": 8,  "cost": 17.00, "transport_type": "MTR"},
    ]

    # Path B: Slow but cheap, 2 segments (WALK to bus terminal, then BUS)
    path_b = [
        {"from": "HK001", "to": "HK008", "duration": 2,  "cost": 0.00, "transport_type": "WALK"},
        {"from": "HK008", "to": "HK004", "duration": 20, "cost": 4.50, "transport_type": "BUS"},
    ]

    # Path C: Medium everything, 3 segments (MTR, then WALK, then BUS)
    path_c = [
        {"from": "HK001", "to": "HK002", "duration": 3,  "cost": 6.50, "transport_type": "MTR"},
        {"from": "HK002", "to": "HK008", "duration": 4,  "cost": 0.00, "transport_type": "WALK"},
        {"from": "HK008", "to": "HK004", "duration": 20, "cost": 4.50, "transport_type": "BUS"},
    ]

    candidates = [path_a, path_b, path_c]

    print("=" * 42)
    print("SCORER INTEGRATION TEST")
    print("Verifying that ranking order changes with preference")
    print("=" * 42)

    for pref in ["fastest", "cheapest", "fewest_segments"]:
        results = evaluate_and_rank(candidates, preference=pref)
        print_results(results, preference=pref)

    print("\nIf #1 changes between preferences above, the scorer is working correctly.")