# COMP1110 Group G03 — Smart Public Transport Advisor

**Topic B | Semester 2, 2025–2026 | The University of Hong Kong**

---

## Overview

The Smart Public Transport Advisor is a terminal-based journey planning system
that models a hand-crafted Hong Kong transport network and generates ranked
route recommendations based on user preferences.

Given an origin stop, a destination stop, and a preference mode, the system
finds candidate journeys through the network and returns the top three results
ranked by total time, total cost, or number of segments.

The system uses no external databases, no live data feeds, and no graphical
frameworks. It runs entirely in the terminal.

---

## Requirements

- Python 3.8 or higher
- **Windows only:** `pip install windows-curses`
- Mac and Linux: no additional installs required (curses is built in)

---

## To install curses library

```bash
pip install windows-curses
```


---

## How to Run

From the project root directory:

```bash
python main.py
```

The program will automatically load the default network from:
- `Controller_IO/sample_data/stops.csv`
- `Controller_IO/sample_data/segments.csv`

---

## Controls

| Key | Action |
|-----|--------|
| ↑ / ↓ | Navigate menus and stop lists |
| Enter | Confirm selection |
| ESC | Go back / cancel |
| S | Swap origin and destination (on confirmation screen) |
| Q | Quit from main menu |
| Type | Filter stop list in real time |

---

## File Structure

```
COMP1110_G03/
│
├── main.py                  Entry point — loads network and launches TUI
├── tui.py                   Terminal User Interface (curses-based)
│
├── Controller_IO/
│   ├── io_handler.py        Loads stops.csv and segments.csv into memory
│   ├── validator.py         Validates all user inputs before routing
│   ├── scorer.py            Scores and ranks candidate routes (top 3)
│   └── sample_data/
│       ├── stops.csv        Network stops (16 stops)
│       └── segments.csv     Network connections (22 segments)
│
└── DFS_Algorithm/
    ├── DFS_algorithm.py     Route search using Depth-First Search
    └── test_dfs.py          Unit and integration tests for the DFS algorithm
```

---

## Network File Format

### stops.csv

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `stop_id` | string | Unique identifier | `HK005` |
| `stop_name` | string | Human-readable name | `Central MTR` |
| `transport_type` | string | Mode at this stop | `MTR`, `BUS`, `FERRY` |

### segments.csv

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `segment_id` | string | Unique identifier | `SEG001` |
| `from_stop` | string | Origin stop ID | `HK001` |
| `to_stop` | string | Destination stop ID | `HK005` |
| `duration_mins` | float | Travel time in minutes (must be > 0) | `8` |
| `cost_hkd` | float | One-way fare in HK$ (0 = free/walking) | `13.50` |
| `transport_type` | string | Mode for this segment | `MTR`, `BUS`, `WALK`, `FERRY` |

> **Note:** All segments are treated as bidirectional. The loader automatically
> adds a reverse direction for every row in segments.csv.

---

## Preference Modes

| Mode | What it optimises |
|------|-------------------|
| `fastest` | Minimises total travel time |
| `cheapest` | Minimises total fare cost |
| `fewest_segments` | Minimises number of network hops |

---

## Loading a Different Network

From the main menu, select **Load Network File** and enter the file paths
for alternative stops and segments CSV files. The program will validate
and load the new network without restarting.

---

## Sample Test Cases

| Origin | Destination | Preference | Expected Result |
|--------|-------------|------------|-----------------|
| Kennedy Town (HK001) | Central (HK005) | fastest | Direct MTR route via Island Line |
| Kennedy Town (HK001) | Tsim Sha Tsui (HK010) | cheapest | Bus + Walk + Ferry route |
| Kennedy Town (HK001) | Sheung Wan (HK004) | fewest_segments | Route with lowest hop count |
| Central (HK005) | Central (HK005) | any | Validation error — same stop |

---

## Run the DFS test suite:

From the DFS_Algorithm directory:

```bash
python test_dfs.py
```



## Known Limitations

- Fares are approximations based on real MTR ranges, not exact values
- Travel times are fixed and do not account for waiting or service frequency
- The network is static — it cannot reflect real-time disruptions
- "Fewest segments" counts network hops, not physical transfers

---

## Group Members

| Name | UID |
|------|------|
| Ali Soban | 3036670071 |
| Ayele Biruk Sisay | 3036478497 |
| Chan Tsz Ching | 3036589662 |
| George Adon Abraham | 3036476267 |
| Khandelwal Prakhar | 3036475380 |
| Nadeem Nabiha | 3036668298 |
