This README explains the three components File I/O + Input Validation + Scoring & Ranking. Each component is one Python file. Run each file directly (python io_handler.py, etc.) to see it in action.

Structure and Logic of files:

Controller_IO/
│
├── io_handler.py ← Loads stops.csv and segments.csv into memory
├── validator.py ← Validates all user input before routing
├── scorer.py ← Scores and ranks candidate routes (top 3)
│
├── sample_data/
│ ├── stops.csv ← Network stops (stations, terminals)
│ └── segments.csv ← Connections between stops (time, cost, mode)
│
└── README.md ← Current file

---

## Component 1: File I/O (`io_handler.py`)

### What it does

Reads the transport network from two CSV files and loads everything into Python dictionaries/lists that the rest of the system can access.

### File Schemas

#### `stops.csv`

Each row is one station or stop in the network.

| Column           | Type   | Description                    | Example              |
| ---------------- | ------ | ------------------------------ | -------------------- |
| `stop_id`        | string | Unique identifier for the stop | `HK001`              |
| `stop_name`      | string | Human-readable name            | `Central MTR`        |
| `transport_type` | string | Primary mode at this stop      | `MTR`, `BUS`, `WALK` |

```csv
stop_id,stop_name,transport_type
HK001,Central MTR,MTR
HK002,Admiralty MTR,MTR
HK008,Central Bus Terminal,BUS
```

#### `segments.csv`

Each row is a one-way connection between two stops.

| Column           | Type   | Description                              | Example  |
| ---------------- | ------ | ---------------------------------------- | -------- |
| `segment_id`     | string | Unique identifier for this segment       | `SEG001` |
| `from_stop`      | string | Origin stop ID (must exist in stops.csv) | `HK001`  |
| `to_stop`        | string | Destination stop ID                      | `HK002`  |
| `duration_mins`  | float  | Travel time in minutes (must be > 0)     | `3`      |
| `cost_hkd`       | float  | One-way fare in HK$ (0 = free/walking)   | `6.50`   |
| `transport_type` | string | Mode of transport for this segment       | `MTR`    |

```csv
segment_id,from_stop,to_stop,duration_mins,cost_hkd,transport_type
SEG001,HK001,HK002,3,6.50,MTR
SEG009,HK008,HK004,20,4.50,BUS
```

> **Note:** Segments in the CSV are **automatically reversed** (A→B becomes B→A too), since most routes run both directions. If you have one-way segments, flag this for discussion.

### How to use it

```python
from io_handler import load_network

all_stops, all_segments = load_network("sample_data/stops.csv", "sample_data/segments.csv")

# all_stops is a dict:   { "HK001": { "name": "Central MTR", "transport_type": "MTR" } }
# all_segments is a list: [ { "from": "HK001", "to": "HK002", "duration": 3, "cost": 6.5, ... } ]
```

### Error handling

The loader will print a clear message and exit for:

- File not found
- Missing required columns
- Non-numeric duration or cost values
- Negative duration (must be > 0)
- Negative cost (must be ≥ 0)
- Stop references in segments.csv that don't exist in stops.csv
- Duplicate stop IDs (handling will be a warning and automatic skip)
- Empty files

---

## Component 2: Input Validation (`validator.py`)

### What it does

Before any routing happens, every user input is checked. Invalid inputs return a clear error message instead of crashing the program.

### How to use it

```python
from validator import validate_journey_request

ok, result = validate_journey_request(
    origin_input="hk001",              # raw user input
    destination_input="HK005",
    preference_input="Fastest",
    stops=all_stops                    # from io_handler
)

if not ok:
    print(f"Error: {result}")          # result is an error string
else:
    # result is a clean dict with normalised values
    print(result)
    # → { "origin": "HK001", "destination": "HK005", "preference": "fastest" }
```

### Validation rules

| Check                | Rule                                                | Example bad input          | Error message                                  |
| -------------------- | --------------------------------------------------- | -------------------------- | ---------------------------------------------- |
| Stop exists          | Must be a valid stop_id in the network              | `"HK999"`                  | "Stop 'HK999' was not found..."                |
| Stop not empty       | Cannot be blank or whitespace                       | `""`                       | "Stop input cannot be empty..."                |
| Origin ≠ Destination | Cannot travel to where you are                      | Origin=Destination=`HK001` | "Origin and destination cannot be the same..." |
| Valid preference     | Must be `fastest`, `cheapest`, or `fewest_segments` | `"quickest"`               | "Invalid preference 'quickest'..."             |
| Preference not empty | Cannot be blank                                     | `""`                       | "Preference cannot be empty..."                |

### Running the test suite

```bash
python validator.py
```

Expected output shows 12 test cases (PASS / FAIL) covering all edge cases.

---

## Component 3: Scoring & Ranking (`scorer.py`)

### What it does

Takes a list of candidate paths from the router and returns the **top 3**, ranked by the user's preference.

### Three metrics per journey

| Metric       | How it is calculated                                         |
| ------------ | ------------------------------------------------------------ |
| **Duration** | Sum of `duration` across all segments                        |
| **Cost**     | Sum of `cost` across all segments                            |
| **Segments** | Total number of legs (individual connections) in the journey |

### Preference modes and tiebreakers

| Preference        | Primary sort | Tiebreaker 1 | Tiebreaker 2 |
| ----------------- | ------------ | ------------ | ------------ |
| `fastest`         | Duration ↑   | Cost ↑       | Segments ↑   |
| `cheapest`        | Cost ↑       | Duration ↑   | Segments ↑   |
| `fewest_segments` | Segments ↑   | Duration ↑   | Cost ↑       |

↑ = lower is better (ascending sort)

### How to use it

```python
from scorer import evaluate_and_rank, print_results

# candidate_paths comes from router.py (From Depth-First Search algorithm)
top3 = evaluate_and_rank(candidate_paths, preference="fastest", stops=all_stops)

print_results(top3, preference="fastest", stops=all_stops)
```

### Sample output

```
══════════════════════════════════════════
  TOP 3 ROUTES  ·  Sorted by: Fastest
══════════════════════════════════════════
──────────────────────────────────────────
  #1  Journey
──────────────────────────────────────────
  🕐  Duration : 11 mins
  💰  Cost     : HK$23.50
  🔢  Segments : 2
──────────────────────────────────────────
  Route:
    Central MTR (HK001) → Admiralty MTR (HK002)  [MTR  3min  HK$6.50]
    Admiralty MTR (HK002) → Tsim Sha Tsui (HK005)  [MTR  8min  HK$17.00]
──────────────────────────────────────────
```

### Running the integration test

```bash
python scorer.py
```

This test verifies that **ranking order changes correctly** when the preference is swapped between `fastest`, `cheapest`, and `fewest_segments`. If #1 changes between modes, the scorer is working.

---
