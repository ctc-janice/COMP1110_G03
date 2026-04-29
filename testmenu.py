"""
main.py — Smart Public Transport Advisor
=========================================
COMP1110  ·  Group G03  ·  Topic B

Entry point for the application. Supports two modes:

  1. TUI mode (default)     — launches the retro curses interface (tui.py)
  2. CLI mode (--cli flag)  — plain text, no curses; useful for testing
                              or environments where curses is unavailable

Usage:
    python main.py            # launch TUI
    python main.py --cli      # launch plain CLI
    python main.py --help     # show this help

Dependencies (all in-project):
    Team_2/io_handler.py   — load_network()
    Team_2/validator.py    — validate_journey_request()
    Team_2/scorer.py       — evaluate_and_rank(), print_results()
    Team_3/DFS_algorithm.py — createAdjList(), iterativeDFS()
    tui.py                 — main()  (curses TUI)
"""

import sys
import os


# ── Default CSV paths (relative to project root) ──────────────────────────────
DEFAULT_STOPS_PATH    = "Team_2/sample_data/stops.csv"
DEFAULT_SEGMENTS_PATH = "Team_2/sample_data/segments.csv"


# ── Import project modules with clear feedback on failure ─────────────────────

def _import_modules():
    """
    Import all required modules and return them as a namespace dict.
    Prints a descriptive error and exits if a critical module is missing.
    """
    modules = {}

    # ── Team 2: I/O, validation, scoring ──────────────────────────────────────
    try:
        from Team_2.io_handler import load_network
        from Team_2.validator  import validate_journey_request
        from Team_2.scorer     import evaluate_and_rank, print_results
        modules["load_network"]             = load_network
        modules["validate_journey_request"] = validate_journey_request
        modules["evaluate_and_rank"]        = evaluate_and_rank
        modules["print_results"]            = print_results
        modules["io_ok"] = True
    except ImportError as e:
        print(f"[main] ERROR: Could not import Team 2 modules — {e}")
        print("[main] Make sure Team_2/__init__.py exists and the files are in place.")
        sys.exit(1)

    # ── Team 3: DFS routing ───────────────────────────────────────────────────
    try:
        from Team_3.DFS_algorithm import createAdjList, iterativeDFS
        modules["createAdjList"] = createAdjList
        modules["iterativeDFS"]  = iterativeDFS
        modules["dfs_ok"] = True
    except ImportError as e:
        # Non-fatal in TUI mode (tui.py handles the missing module gracefully).
        # Fatal in CLI mode — routing cannot work without it.
        modules["dfs_ok"] = False
        modules["dfs_error"] = str(e)

    return modules


# ═════════════════════════════════════════════════════════════════════════════
# CLI MODE
# ═════════════════════════════════════════════════════════════════════════════

def run_cli(mod):
    """
    Plain-text interactive CLI. No curses required.
    Loops: load network → plan journeys → exit.
    """
    _cli_banner()

    if not mod["dfs_ok"]:
        print(f"[main] WARNING: DFS module unavailable — {mod['dfs_error']}")
        print("[main] Journey planning will not work until Team_3/DFS_algorithm.py is ready.\n")

    # ── Load default network ──────────────────────────────────────────────────
    print(f"Loading network from default paths …")
    try:
        stops, segments = mod["load_network"](DEFAULT_STOPS_PATH, DEFAULT_SEGMENTS_PATH)
        print(f"  ✓  {len(stops)} stops  |  {len(segments)//2} segments loaded.\n")
    except SystemExit:
        print("[main] Failed to load default network. "
              "Edit DEFAULT_STOPS_PATH / DEFAULT_SEGMENTS_PATH in main.py.")
        sys.exit(1)

    # ── Main REPL ─────────────────────────────────────────────────────────────
    while True:
        _cli_menu()
        choice = input("Choice: ").strip()

        if choice == "1":
            _cli_plan_journey(stops, segments, mod)

        elif choice == "2":
            _cli_browse_stops(stops)

        elif choice == "3":
            _cli_network_overview(stops, segments)

        elif choice == "4":
            stops, segments = _cli_load_network(mod)

        elif choice in ("5", "q", "Q", "exit", "quit"):
            print("\nGoodbye. Safe travels!\n")
            sys.exit(0)

        else:
            print("  Invalid choice — enter a number 1–5.\n")


# ── CLI helpers ───────────────────────────────────────────────────────────────

def _cli_banner():
    print("=" * 56)
    print("  SMART PUBLIC TRANSPORT ADVISOR")
    print("  COMP1110  ·  Group G03  ·  Topic B")
    print("=" * 56)
    print()


def _cli_menu():
    print("─" * 40)
    print("  MAIN MENU")
    print("─" * 40)
    print("  [1]  Plan a journey")
    print("  [2]  Browse stops")
    print("  [3]  Network overview")
    print("  [4]  Load a different network file")
    print("  [5]  Exit")
    print("─" * 40)


def _cli_plan_journey(stops, segments, mod):
    """Walk the user through origin → destination → preference → results."""
    if not mod["dfs_ok"]:
        print("\n  [!] Journey planning unavailable — DFS module not loaded.\n")
        return

    print()

    # Origin
    origin_raw = input("  Enter ORIGIN stop ID (e.g. HK001): ").strip()

    # Destination
    dest_raw = input("  Enter DESTINATION stop ID (e.g. HK005): ").strip()

    # Preference
    print("  Preferences: fastest | cheapest | fewest_segments")
    pref_raw = input("  Enter preference: ").strip()

    # Validate all three together
    ok, result = mod["validate_journey_request"](origin_raw, dest_raw, pref_raw, stops)
    if not ok:
        print(f"\n  [!] Validation error: {result}\n")
        return

    origin    = result["origin"]
    dest      = result["destination"]
    preference = result["preference"]

    print(f"\n  Searching routes: {stops[origin]['name']} → {stops[dest]['name']} …")

    # Build adjacency list and run DFS
    adj_list        = mod["createAdjList"](segments)
    candidate_paths = mod["iterativeDFS"](adj_list, origin, dest)

    if not candidate_paths:
        print(f"  [!] No routes found between {stops[origin]['name']} "
              f"and {stops[dest]['name']}.")
        print("  Try a different origin or destination.\n")
        return

    # Score and print
    top3 = mod["evaluate_and_rank"](candidate_paths, preference=preference, stops=stops)
    mod["print_results"](top3, preference=preference, stops=stops)
    print()


def _cli_browse_stops(stops):
    """Print all stops in a simple table."""
    print(f"\n  {'ID':<8}  {'NAME':<28}  {'TYPE'}")
    print("  " + "─" * 52)
    for sid, info in stops.items():
        print(f"  {sid:<8}  {info['name']:<28}  {info['transport_type']}")
    print()


def _cli_network_overview(stops, segments):
    """Print a summary of the loaded network."""
    stop_types = {}
    for info in stops.values():
        t = info["transport_type"]
        stop_types[t] = stop_types.get(t, 0) + 1

    seg_types = {}
    for seg in segments:
        t = seg["transport_type"]
        seg_types[t] = seg_types.get(t, 0) + 1

    print(f"\n  Total stops    : {len(stops)}")
    for t, n in sorted(stop_types.items()):
        print(f"    {t:<12} {n}")

    print(f"\n  Total segments : {len(segments)//2}  (bidirectional)")
    for t, n in sorted(seg_types.items()):
        print(f"    {t:<12} {n//2}")

    modes = ", ".join(sorted(seg_types.keys()))
    print(f"\n  Transport modes: {modes}\n")


def _cli_load_network(mod):
    """Prompt for new CSV paths and reload."""
    stops_path = input(f"  Stops CSV path    [{DEFAULT_STOPS_PATH}]: ").strip()
    segs_path  = input(f"  Segments CSV path [{DEFAULT_SEGMENTS_PATH}]: ").strip()

    stops_path = stops_path or DEFAULT_STOPS_PATH
    segs_path  = segs_path  or DEFAULT_SEGMENTS_PATH

    try:
        stops, segments = mod["load_network"](stops_path, segs_path)
        print(f"  ✓  Loaded {len(stops)} stops and {len(segments)//2} segments.\n")
        return stops, segments
    except SystemExit:
        print("  [!] Failed to load network. Check the file paths and CSV format.\n")
        return {}, []


# ═════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def main():
    # ── Parse arguments ───────────────────────────────────────────────────────
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    use_cli = "--cli" in args

    # ── Import modules (always needed) ────────────────────────────────────────
    mod = _import_modules()

    # ── Launch chosen interface ───────────────────────────────────────────────
    if use_cli:
        run_cli(mod)
    else:
        # Default: TUI via curses
        try:
            from tui import main as tui_main
            tui_main()
        except ImportError:
            print("[main] tui.py not found — falling back to CLI mode.\n")
            run_cli(mod)
        except Exception as e:
            # Curses can fail on some terminals (e.g. piped output, certain CI envs)
            print(f"[main] TUI could not start ({e}).")
            print("[main] Run with --cli flag for plain-text mode.\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
