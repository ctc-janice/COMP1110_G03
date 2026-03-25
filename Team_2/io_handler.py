"""
io_handler.py: Data Input and File I/O
======================================
WHAT THIS FILE DOES:
    Loads the transport network from two CSV files:
      - stops.csv   : All stations/stops in the network
      - segments.csv: All connections between stops (with time, cost, type)

    Think of it like loading a map — stops are the dots, segments are the lines between them.

HOW IT WORKS:
    1. load_network() is the main function — call this to get everything loaded
    2. It calls _load_stops() and _load_segments() internally
    3. Returns two dictionaries: stops{} and segments[]
    4. All errors are caught and reported clearly

USAGE:
    from io_handler import load_network
    all_stops, all_segments = load_network("sample_data/stops.csv", "sample_data/segments.csv")
"""

import csv
import os


# ─────────────────────────────────────────────
# MAIN PUBLIC FUNCTION — call this from main.py
# ─────────────────────────────────────────────

def load_network(stops_filepath, segments_filepath):
    """
    Load the full transport network from two CSV files.

    Returns:
        stops    (dict): { stop_id -> { name, transport_type} }
        segments (list): [ { from, to, duration, cost, transport_type }, ... ]

    Raises:
        SystemExit if files are missing, empty, or badly formatted.
    """
    print(f"[IO] Loading stops from:    {stops_filepath}")
    print(f"[IO] Loading segments from: {segments_filepath}")

    stops    = _load_stops(stops_filepath)
    segments = _load_segments(segments_filepath, stops)

    print(f"[IO] ✓ Loaded {len(stops)} stops and {len(segments)} segments successfully.\n")
    return stops, segments


# ─────────────────────────────────────────────
# INTERNAL HELPERS (prefixed with _ by convention)
# ─────────────────────────────────────────────

def _load_stops(filepath):
    """
    Parse stops.csv into a dictionary.

    Expected CSV columns: stop_id, stop_name, transport_type

    Returns:
        { "HK001": { "name": "Central MTR", "transport_type": "MTR", ... }
    """
    _check_file_exists(filepath)

    stops = {}
    required_columns = {"stop_id", "stop_name", "transport_type"}

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate the header row has the right columns
        _check_columns(reader.fieldnames, required_columns, filepath)

        for line_number, row in enumerate(reader, start=2):  # start=2 because row 1 is header
            stop_id = row.get("stop_id", "").strip()

            if not stop_id:
                continue

            # Warn about duplicate stop IDs
            if stop_id in stops:
                print(f"[IO] ⚠ Warning: Duplicate stop_id '{stop_id}' on line {line_number}. Skipping.")
                continue

            stops[stop_id] = {
                "name":           row["stop_name"].strip(),
                "transport_type": row["transport_type"].strip().upper(),
            }

    _check_not_empty(stops, filepath)
    return stops


def _load_segments(filepath, stops):
    """
    Parse segments.csv into a list of connection dictionaries.

    Expected CSV columns: segment_id, from_stop, to_stop, duration_mins, cost_hkd, transport_type

    NOTE: Segments are one-directional in the file.
          We automatically add the reverse direction (B→A) for each row,
          since most transit routes run both ways.

    Returns:
        [
          { "segment_id": "SEG001", "from": "HK001", "to": "HK002",
            "duration": 3, "cost": 6.50, "transport_type": "MTR" },
          ...
        ]
    """
    _check_file_exists(filepath)

    segments = []
    required_columns = {"segment_id", "from_stop", "to_stop", "duration_mins", "cost_hkd", "transport_type"}
    errors = []  # Collect all errors, report together at the end

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        _check_columns(reader.fieldnames, required_columns, filepath)

        for line_number, row in enumerate(reader, start=2):
            segment_id = row.get("segment_id", "").strip()
            from_stop  = row.get("from_stop",  "").strip()
            to_stop    = row.get("to_stop",    "").strip()

            if not segment_id:
                continue

            # ── Validate stop references exist in stops.csv ──
            if from_stop not in stops:
                errors.append(f"  Line {line_number}: from_stop '{from_stop}' not found in stops.")
                continue
            if to_stop not in stops:
                errors.append(f"  Line {line_number}: to_stop '{to_stop}' not found in stops.")
                continue

            # ── Validate numeric fields ──
            duration = _parse_positive_number(row["duration_mins"], "duration_mins", line_number, errors)
            cost     = _parse_non_negative_number(row["cost_hkd"],  "cost_hkd",     line_number, errors)

            if duration is None or cost is None:
                continue

            segment = {
                "segment_id":     segment_id,
                "from":           from_stop,
                "to":             to_stop,
                "duration":       duration,
                "cost":           cost,
                "transport_type": row["transport_type"].strip().upper(),
            }

            segments.append(segment)

            # Auto-add reverse direction (B → A) with same cost/duration
            # SUGGESTION: If your routes are one-way (e.g., a one-way bus loop),
            # remove this block and mark segments as directional in the CSV if we decide to add the feature.
            reverse = segment.copy()
            reverse["segment_id"] = segment_id + "_REV"
            reverse["from"] = to_stop
            reverse["to"]   = from_stop
            segments.append(reverse)

    # Report all validation errors at once
    if errors:
        print(f"[IO] ✗ Errors found in {filepath}:")
        for e in errors:
            print(e)
        print("[IO] Fix the above errors and restart.\n")
        raise SystemExit(1)

    _check_not_empty(segments, filepath)
    return segments


# ─────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────

def _check_file_exists(filepath):
    """Stop immediately if the file doesn't exist."""
    if not os.path.isfile(filepath):
        print(f"[IO] ✗ ERROR: File not found → '{filepath}'")
        print(f"[IO]   Make sure the file exists relative to where you run the script.")
        raise SystemExit(1)


def _check_columns(actual_fields, required, filepath):
    """Stop if any required column headers are missing."""
    if actual_fields is None:
        print(f"[IO] ✗ ERROR: '{filepath}' appears to be empty (no header row).")
        raise SystemExit(1)

    actual = {f.strip() for f in actual_fields}
    missing = required - actual
    if missing:
        print(f"[IO] ✗ ERROR: '{filepath}' is missing required columns: {missing}")
        print(f"[IO]   Found columns: {actual}")
        raise SystemExit(1)


def _check_not_empty(data, filepath):
    """Stop if the file loaded zero valid records."""
    if not data:
        print(f"[IO] ✗ ERROR: '{filepath}' contains no valid data rows.")
        raise SystemExit(1)


def _parse_positive_number(value, field_name, line_number, errors):
    """Parse a number that must be > 0 (e.g. duration). Returns None on failure."""
    try:
        num = float(value.strip())
        if num <= 0:
            errors.append(f"  Line {line_number}: '{field_name}' must be > 0, got {num}")
            return None
        return num
    except ValueError:
        errors.append(f"  Line {line_number}: '{field_name}' must be a number, got '{value}'")
        return None


def _parse_non_negative_number(value, field_name, line_number, errors):
    """Parse a number that must be >= 0 (e.g. cost — walking is free). Returns None on failure."""
    try:
        num = float(value.strip())
        if num < 0:
            errors.append(f"  Line {line_number}: '{field_name}' must be >= 0, got {num}")
            return None
        return num
    except ValueError:
        errors.append(f"  Line {line_number}: '{field_name}' must be a number, got '{value}'")
        return None


# ─────────────────────────────────────────────
# QUICK TEST: run this file directly to verify
# ─────────────────────────────────────────────

if __name__ == "__main__":
    all_stops, all_segments = load_network(
        "sample_data/stops.csv",
        "sample_data/segments.csv"
    )

    print("=== STOPS ===")
    for sid, info in all_stops.items():
        print(f"  {sid}: {info['name']} ({info['transport_type']})")

    print(f"\n=== SEGMENTS (first 5 of {len(all_segments)}) ===")
    for seg in all_segments[:5]:
        print(f"  {seg['segment_id']}: {seg['from']} → {seg['to']} | {seg['duration']}min | HK${seg['cost']}")