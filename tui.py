"""
tui.py — Retro Terminal UI for Smart Public Transport Advisor
=============================================================
Green-on-black TUI using Python's built-in curses library.
Dynamically redraws — no scrolling, no clutter.

Screens:
  1. Boot splash       — animated logo on startup
  2. Main menu         — arrow-key navigation
  3. Stop selector     — arrow keys + live type-to-search
  4. Preference picker — arrow keys
  5. Loading screen    — spinning animation while DFS runs
  6. Results screen    — top 3 routes in bordered box
  7. Error screen      — red bordered error message

Controls (shown on every screen):
  UP / DOWN   — navigate
  ENTER       — confirm selection
  BACKSPACE   — go back / clear search
  Q           — quit from main menu

Compatibility:
  Mac/Linux : works out of the box (curses is built in)
  Windows   : run  pip install windows-curses  first
"""

import curses
import time
import textwrap

# ── Try importing project modules ──────────────────────────────────────────────
try:
    from Team_2.io_handler import load_network
    from Team_2.validator  import validate_journey_request
    from Team_2.scorer     import evaluate_and_rank
    IO_AVAILABLE = True
except ImportError:
    IO_AVAILABLE = False

try:
    from Team_3.DFS_algorithm import createAdjList, recursive_journeyGenerator
    DFS_AVAILABLE = True
except ImportError:
    DFS_AVAILABLE = False

# ── Colour pair IDs ────────────────────────────────────────────────────────────
C_NORMAL   = 1   # green on black
C_BRIGHT   = 2   # bright green on black
C_SELECTED = 3   # black on green  (highlighted row)
C_DIM      = 4   # dark green on black (borders, decorations)
C_ERROR    = 5   # red on black
C_TITLE    = 6   # bright green on black + bold (headers)
C_YELLOW   = 7   # yellow on black (prompts / hints)


def init_colours():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(C_NORMAL,   curses.COLOR_GREEN,  curses.COLOR_BLACK)
    curses.init_pair(C_BRIGHT,   curses.COLOR_GREEN,  curses.COLOR_BLACK)
    curses.init_pair(C_SELECTED, curses.COLOR_BLACK,  curses.COLOR_GREEN)
    curses.init_pair(C_DIM,      curses.COLOR_GREEN,  curses.COLOR_BLACK)
    curses.init_pair(C_ERROR,    curses.COLOR_RED,    curses.COLOR_BLACK)
    curses.init_pair(C_TITLE,    curses.COLOR_GREEN,  curses.COLOR_BLACK)
    curses.init_pair(C_YELLOW,   curses.COLOR_YELLOW, curses.COLOR_BLACK)


# ── Drawing helpers ────────────────────────────────────────────────────────────

def safe_addstr(win, y, x, text, attr=0):
    """addstr that silently ignores out-of-bounds writes."""
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x < 0:
        return
    max_len = w - x - 1
    if max_len <= 0:
        return
    try:
        win.addstr(y, x, text[:max_len], attr)
    except curses.error:
        pass


def draw_box(win, y, x, h, w, colour_pair, title=""):
    """Draw a single-line Unicode box."""
    attr = curses.color_pair(colour_pair)
    # top
    safe_addstr(win, y,     x,     "┌" + "─" * (w - 2) + "┐", attr)
    # sides
    for row in range(1, h - 1):
        safe_addstr(win, y + row, x,         "│", attr)
        safe_addstr(win, y + row, x + w - 1, "│", attr)
    # bottom
    safe_addstr(win, y + h - 1, x, "└" + "─" * (w - 2) + "┘", attr)
    # optional title centred on top border
    if title:
        label = f" {title} "
        tx = x + max(1, (w - len(label)) // 2)
        safe_addstr(win, y, tx, label, attr | curses.A_BOLD)


def centre_text(win, y, text, attr=0):
    _, w = win.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    safe_addstr(win, y, x, text, attr)


def clear_screen(win):
    win.erase()
    win.bkgd(' ', curses.color_pair(C_NORMAL))


# ── Boot splash ────────────────────────────────────────────────────────────────

LOGO = [
    "  ██████╗ ██╗   ██╗██████╗ ██╗     ██╗ ██████╗",
    " ██╔══██╗██║   ██║██╔══██╗██║     ██║██╔════╝",
    " ██████╔╝██║   ██║██████╔╝██║     ██║██║     ",
    " ██╔═══╝ ██║   ██║██╔══██╗██║     ██║██║     ",
    " ██║     ╚██████╔╝██████╔╝███████╗██║╚██████╗",
    " ╚═╝      ╚═════╝ ╚═════╝ ╚══════╝╚═╝ ╚═════╝",
]

SUBTITLE = "SMART PUBLIC TRANSPORT ADVISOR"
GROUP    = "COMP1110  ·  Group G03  ·  Topic B"


def boot_splash(win):
    """Animated boot screen — logo fades in line by line."""
    clear_screen(win)
    h, w = win.getmaxyx()
    start_y = max(2, h // 2 - len(LOGO) - 3)
    attr_bright = curses.color_pair(C_BRIGHT) | curses.A_BOLD
    attr_dim    = curses.color_pair(C_DIM)

    # Draw logo line by line with a tiny delay
    for i, line in enumerate(LOGO):
        safe_addstr(win, start_y + i, max(0, (w - len(line)) // 2), line, attr_bright)
        win.refresh()
        time.sleep(0.07)

    centre_text(win, start_y + len(LOGO) + 1, SUBTITLE, attr_bright)
    centre_text(win, start_y + len(LOGO) + 2, GROUP,    attr_dim)

    # Animated "INITIALISING" dots
    dots_y = start_y + len(LOGO) + 4
    base   = "  INITIALISING"
    for n in range(12):
        dots = "." * (n % 4)
        msg  = base + dots.ljust(3)
        centre_text(win, dots_y, msg, attr_dim)
        win.refresh()
        time.sleep(0.12)

    time.sleep(0.3)


# ── Main menu ──────────────────────────────────────────────────────────────────

MENU_ITEMS = [
    ("PLAN A JOURNEY",      "Find and rank routes between two stops"),
    ("BROWSE STOPS",        "View all stops in the network"),
    ("NETWORK OVERVIEW",    "Summary of stops, segments and transport modes"),
    ("LOAD NETWORK FILE",   "Switch to a different stops / segments CSV"),
    ("EXIT",                "Quit the program"),
]


def draw_main_menu(win, selected, stops, segments):
    clear_screen(win)
    h, w = win.getmaxyx()
    attr_title    = curses.color_pair(C_TITLE)  | curses.A_BOLD
    attr_normal   = curses.color_pair(C_NORMAL)
    attr_sel      = curses.color_pair(C_SELECTED) | curses.A_BOLD
    attr_dim      = curses.color_pair(C_DIM)
    attr_hint     = curses.color_pair(C_YELLOW)

    # Outer border
    draw_box(win, 0, 0, h - 1, w, C_DIM, "SMART PUBLIC TRANSPORT ADVISOR")

    # Status bar (stop/segment count)
    if stops:
        status = f"  Network loaded: {len(stops)} stops  ·  {len(segments)//2} segments  "
    else:
        status = "  No network loaded  "
    safe_addstr(win, h - 2, 2, status, attr_dim)

    # Menu box
    box_h = len(MENU_ITEMS) * 2 + 4
    box_w = min(60, w - 6)
    box_y = max(3, (h - box_h) // 2)
    box_x = max(2, (w - box_w) // 2)
    draw_box(win, box_y, box_x, box_h, box_w, C_DIM, "MAIN MENU")

    for i, (label, hint) in enumerate(MENU_ITEMS):
        row_y = box_y + 2 + i * 2
        prefix = f"  [{i+1}]  "
        text   = prefix + label.ljust(box_w - len(prefix) - 4)
        if i == selected:
            safe_addstr(win, row_y, box_x + 1, text, attr_sel)
        else:
            safe_addstr(win, row_y, box_x + 1, text, attr_normal)
        # hint line below selected
        if i == selected:
            safe_addstr(win, row_y + 1, box_x + 5, hint, attr_dim)

    # Controls footer
    controls = " ↑↓ Navigate   ENTER Select   Q Quit "
    safe_addstr(win, h - 2, w - len(controls) - 2, controls, attr_hint)
    win.refresh()


def main_menu_screen(win, stops, segments):
    """Returns index 0-4 for selected action."""
    selected = 0
    curses.curs_set(0)
    win.keypad(True)
    win.timeout(100)

    while True:
        draw_main_menu(win, selected, stops, segments)
        key = win.getch()

        if key in (curses.KEY_UP, ord('k')):
            selected = (selected - 1) % len(MENU_ITEMS)
        elif key in (curses.KEY_DOWN, ord('j')):
            selected = (selected + 1) % len(MENU_ITEMS)
        elif key in (curses.KEY_ENTER, 10, 13):
            return selected
        elif key in (ord('q'), ord('Q')):
            return 4  # EXIT
        elif ord('1') <= key <= ord('5'):
            return key - ord('1')


# ── Stop selector (arrow + type-to-search) ────────────────────────────────────

def stop_selector(win, stops, prompt):
    """
    Full-screen stop picker.
    UP/DOWN to navigate, type letters to filter live, ENTER to confirm,
    ESC/backspace to cancel.
    Returns stop_id string, or None if cancelled.
    """
    curses.curs_set(1)
    win.keypad(True)
    win.timeout(50)

    query    = ""
    selected = 0
    all_stops = [(sid, info["name"], info["transport_type"])
                 for sid, info in stops.items()]

    while True:
        # Filter by query
        q = query.upper()
        filtered = [(sid, name, tt) for sid, name, tt in all_stops
                    if q in sid or q in name.upper()]
        if not filtered:
            filtered = all_stops  # never show empty list
        selected = max(0, min(selected, len(filtered) - 1))

        # Draw
        clear_screen(win)
        h, w = win.getmaxyx()
        attr_title  = curses.color_pair(C_TITLE) | curses.A_BOLD
        attr_normal = curses.color_pair(C_NORMAL)
        attr_sel    = curses.color_pair(C_SELECTED) | curses.A_BOLD
        attr_dim    = curses.color_pair(C_DIM)
        attr_hint   = curses.color_pair(C_YELLOW)

        draw_box(win, 0, 0, h - 1, w, C_DIM, prompt)

        # Search bar
        search_label = "  SEARCH: "
        safe_addstr(win, 2, 2, search_label, attr_dim)
        cursor_x = 2 + len(search_label)
        safe_addstr(win, 2, cursor_x, (query + "_").ljust(w - cursor_x - 3), attr_title)
        safe_addstr(win, 3, 2, "─" * (w - 4), attr_dim)

        # Stop list
        list_y  = 4
        visible = h - list_y - 3
        start   = max(0, selected - visible // 2)

        for i, (sid, name, tt) in enumerate(filtered[start:start + visible]):
            idx  = start + i
            row  = list_y + i
            line = f"  {sid:<8} {name:<30} [{tt}]"
            if idx == selected:
                safe_addstr(win, row, 1, line.ljust(w - 2), attr_sel)
            else:
                safe_addstr(win, row, 1, line, attr_normal)

        # Scroll hint
        if len(filtered) > visible:
            pct = int(100 * selected / max(1, len(filtered) - 1))
            safe_addstr(win, h - 2, w - 12, f"  {pct:3d}%  ▓ ", attr_dim)

        controls = " ↑↓ Navigate   Type to Search   ENTER Select   ESC Cancel "
        safe_addstr(win, h - 2, 2, controls, attr_hint)
        win.refresh()

        # Input
        key = win.getch()
        if key == curses.KEY_UP:
            selected = max(0, selected - 1)
        elif key == curses.KEY_DOWN:
            selected = min(len(filtered) - 1, selected + 1)
        elif key in (curses.KEY_ENTER, 10, 13):
            curses.curs_set(0)
            return filtered[selected][0]  # return stop_id
        elif key == 27:  # ESC
            curses.curs_set(0)
            return None
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            query    = query[:-1]
            selected = 0
        elif 32 <= key <= 126:
            query   += chr(key)
            selected = 0


# ── Preference picker ─────────────────────────────────────────────────────────

PREFERENCES = [
    ("fastest",         "Minimise total travel time"),
    ("cheapest",        "Minimise total fare cost"),
    ("fewest_segments", "Minimise number of connections / transfers"),
]


def preference_picker(win):
    """Returns preference string, or None if cancelled."""
    curses.curs_set(0)
    win.keypad(True)
    selected = 0

    while True:
        clear_screen(win)
        h, w = win.getmaxyx()
        attr_normal = curses.color_pair(C_NORMAL)
        attr_sel    = curses.color_pair(C_SELECTED) | curses.A_BOLD
        attr_dim    = curses.color_pair(C_DIM)
        attr_hint   = curses.color_pair(C_YELLOW)

        box_h = len(PREFERENCES) * 2 + 5
        box_w = min(56, w - 6)
        box_y = max(2, (h - box_h) // 2)
        box_x = max(2, (w - box_w) // 2)
        draw_box(win, box_y, box_x, box_h, box_w, C_DIM, "SELECT PREFERENCE")

        for i, (pref, desc) in enumerate(PREFERENCES):
            row_y = box_y + 2 + i * 2
            label = f"  [{i+1}]  {pref.upper().replace('_',' ')}"
            if i == selected:
                safe_addstr(win, row_y,     box_x + 1, label.ljust(box_w - 2), attr_sel)
                safe_addstr(win, row_y + 1, box_x + 7, desc, attr_dim)
            else:
                safe_addstr(win, row_y, box_x + 1, label, attr_normal)

        controls = " ↑↓ Navigate   ENTER Select   ESC Back "
        safe_addstr(win, h - 2, 2, controls, attr_hint)
        win.refresh()

        key = win.getch()
        if key == curses.KEY_UP:
            selected = (selected - 1) % len(PREFERENCES)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(PREFERENCES)
        elif key in (curses.KEY_ENTER, 10, 13):
            return PREFERENCES[selected][0]
        elif key == 27:
            return None
        elif ord('1') <= key <= ord('3'):
            return PREFERENCES[key - ord('1')][0]


# ── Loading screen ─────────────────────────────────────────────────────────────

def loading_screen(win, message="SEARCHING FOR ROUTES"):
    """
    Animated loading screen with all three styles combined:
      - Spinning line in the centre
      - Progress bar below
      - Pulsing dots in the label
    Runs for a fixed number of frames — caller does the actual work after.
    """
    curses.curs_set(0)
    h, w = win.getmaxyx()
    attr_bright = curses.color_pair(C_BRIGHT) | curses.A_BOLD
    attr_dim    = curses.color_pair(C_DIM)
    attr_yellow = curses.color_pair(C_YELLOW)

    spinner_chars = ['|', '/', '─', '\\']
    bar_width     = min(40, w - 10)
    frames        = 24   # ~3 seconds at ~8fps

    for frame in range(frames):
        clear_screen(win)
        draw_box(win, 0, 0, h - 1, w, C_DIM, "PLEASE WAIT")

        spin    = spinner_chars[frame % 4]
        dots    = "." * ((frame % 4))
        label   = f"  {spin}  {message}{dots.ljust(3)}  {spin}  "
        centre_text(win, h // 2 - 2, label, attr_bright)

        # Progress bar
        filled   = int(bar_width * frame / frames)
        bar      = "[" + "=" * filled + ">" + " " * (bar_width - filled - 1) + "]"
        pct      = int(100 * frame / frames)
        bar_line = f"{bar}  {pct:3d}%"
        centre_text(win, h // 2, bar_line, attr_yellow)

        # Pulse line
        pulse_chars = "·  ··  ···  ··  ·"
        pulse = pulse_chars[(frame * 2) % len(pulse_chars):][:bar_width]
        centre_text(win, h // 2 + 2, pulse.center(bar_width + 8), attr_dim)

        win.refresh()
        time.sleep(0.12)


# ── Results screen ─────────────────────────────────────────────────────────────

def results_screen(win, top3, origin_name, dest_name, preference, stops):
    """Display top 3 routes in a retro bordered box. Press any key to continue."""
    curses.curs_set(0)
    win.keypad(True)

    pref_label = preference.upper().replace("_", " ")

    while True:
        clear_screen(win)
        h, w = win.getmaxyx()
        attr_bright = curses.color_pair(C_BRIGHT) | curses.A_BOLD
        attr_normal = curses.color_pair(C_NORMAL)
        attr_dim    = curses.color_pair(C_DIM)
        attr_sel    = curses.color_pair(C_SELECTED) | curses.A_BOLD
        attr_hint   = curses.color_pair(C_YELLOW)

        title = f"TOP {len(top3)} ROUTES  ·  {pref_label}"
        draw_box(win, 0, 0, h - 1, w, C_DIM, title)

        row = 2
        route_label = f"  FROM: {origin_name}   →   TO: {dest_name}"
        safe_addstr(win, row, 2, route_label, attr_bright)
        row += 1
        safe_addstr(win, row, 2, "─" * (w - 4), attr_dim)
        row += 1

        for journey in top3:
            rank  = journey["rank"]
            dur   = journey["duration"]
            cost  = journey["cost"]
            segs  = journey["segments_count"]

            # Route header
            header = f"  #{rank}   {dur:.0f} min   HK${cost:.2f}   {segs} segment(s)"
            safe_addstr(win, row, 2, header, attr_sel)
            row += 1

            # Each segment
            for seg in journey["segments"]:
                def name(sid):
                    if stops and sid in stops:
                        return f"{stops[sid]['name']} ({sid})"
                    return sid
                seg_line = (f"      {name(seg['from'])} → {name(seg['to'])}"
                            f"   [{seg['transport_type']}  {seg['duration']:.0f}min"
                            f"  HK${seg['cost']:.2f}]")
                if row < h - 3:
                    safe_addstr(win, row, 2, seg_line, attr_normal)
                row += 1

            if row < h - 3:
                safe_addstr(win, row, 2, "─" * (w - 4), attr_dim)
            row += 1

            if row >= h - 3:
                break

        safe_addstr(win, h - 2, 2,
                    " Press any key to return to main menu ",
                    attr_hint)
        win.refresh()

        key = win.getch()
        if key != curses.ERR:
            return


# ── Error / info screen ────────────────────────────────────────────────────────

def error_screen(win, message, title="ERROR"):
    """Red-bordered error box. Press any key to dismiss."""
    curses.curs_set(0)
    win.keypad(True)

    while True:
        clear_screen(win)
        h, w = win.getmaxyx()
        attr_err  = curses.color_pair(C_ERROR)  | curses.A_BOLD
        attr_hint = curses.color_pair(C_YELLOW)
        attr_dim  = curses.color_pair(C_DIM)

        box_w = min(60, w - 6)
        lines = textwrap.wrap(message, box_w - 4)
        box_h = len(lines) + 6
        box_y = max(2, (h - box_h) // 2)
        box_x = max(2, (w - box_w) // 2)

        draw_box(win, box_y, box_x, box_h, box_w, C_ERROR, f"  ✗  {title}  ")

        for i, line in enumerate(lines):
            safe_addstr(win, box_y + 2 + i, box_x + 3, line, attr_err)

        safe_addstr(win, h - 2, 2,
                    " Press any key to continue ",
                    attr_hint)
        win.refresh()

        key = win.getch()
        if key != curses.ERR:
            return


# ── Browse stops screen ────────────────────────────────────────────────────────

def browse_stops_screen(win, stops):
    """Scrollable stop browser."""
    curses.curs_set(0)
    win.keypad(True)
    win.timeout(50)

    all_stops = [(sid, info["name"], info["transport_type"])
                 for sid, info in stops.items()]
    selected  = 0

    while True:
        clear_screen(win)
        h, w = win.getmaxyx()
        attr_normal = curses.color_pair(C_NORMAL)
        attr_sel    = curses.color_pair(C_SELECTED) | curses.A_BOLD
        attr_dim    = curses.color_pair(C_DIM)
        attr_hint   = curses.color_pair(C_YELLOW)

        draw_box(win, 0, 0, h - 1, w, C_DIM, f"ALL STOPS  ({len(all_stops)} total)")

        visible = h - 5
        start   = max(0, selected - visible // 2)

        for i, (sid, name, tt) in enumerate(all_stops[start:start + visible]):
            idx  = start + i
            row  = 2 + i
            line = f"  {sid:<8}  {name:<34}  [{tt}]"
            if idx == selected:
                safe_addstr(win, row, 1, line.ljust(w - 2), attr_sel)
            else:
                safe_addstr(win, row, 1, line, attr_normal)

        safe_addstr(win, h - 2, 2,
                    " ↑↓ Navigate   ESC / Q  Return to menu ",
                    attr_hint)
        win.refresh()

        key = win.getch()
        if key == curses.KEY_UP:
            selected = max(0, selected - 1)
        elif key == curses.KEY_DOWN:
            selected = min(len(all_stops) - 1, selected + 1)
        elif key in (27, ord('q'), ord('Q')):
            return


# ── Network overview screen ────────────────────────────────────────────────────

def network_overview_screen(win, stops, segments):
    """Static summary screen."""
    curses.curs_set(0)
    win.keypad(True)

    stop_types = {}
    for info in stops.values():
        t = info["transport_type"]
        stop_types[t] = stop_types.get(t, 0) + 1

    seg_types = {}
    for seg in segments:
        t = seg["transport_type"]
        seg_types[t] = seg_types.get(t, 0) + 1

    while True:
        clear_screen(win)
        h, w = win.getmaxyx()
        attr_bright = curses.color_pair(C_BRIGHT) | curses.A_BOLD
        attr_normal = curses.color_pair(C_NORMAL)
        attr_dim    = curses.color_pair(C_DIM)
        attr_hint   = curses.color_pair(C_YELLOW)

        draw_box(win, 0, 0, h - 1, w, C_DIM, "NETWORK OVERVIEW")

        row = 2
        safe_addstr(win, row, 4,
                    f"Total stops    :  {len(stops)}", attr_bright)
        row += 1
        for t, n in sorted(stop_types.items()):
            safe_addstr(win, row, 8, f"{t:<10}  {n}", attr_normal)
            row += 1

        row += 1
        total_segs = len(segments) // 2
        safe_addstr(win, row, 4,
                    f"Total segments :  {total_segs}  (bidirectional)",
                    attr_bright)
        row += 1
        for t, n in sorted(seg_types.items()):
            safe_addstr(win, row, 8, f"{t:<10}  {n // 2}", attr_normal)
            row += 1

        row += 1
        modes = ", ".join(sorted(seg_types.keys()))
        safe_addstr(win, row, 4, f"Transport modes:  {modes}", attr_normal)

        safe_addstr(win, h - 2, 2,
                    " Press any key to return to main menu ",
                    attr_hint)
        win.refresh()

        key = win.getch()
        if key != curses.ERR:
            return


# ── Load network screen ────────────────────────────────────────────────────────

def load_network_screen(win):
    """
    Prompt for new CSV paths with a simple inline editor.
    Returns (stops, segments) or (None, None) if cancelled / failed.
    """
    curses.curs_set(1)
    win.keypad(True)

    default_stops = "Team_2/sample_data/stops.csv"
    default_segs  = "Team_2/sample_data/segments.csv"
    fields        = [list(default_stops), list(default_segs)]
    labels        = ["STOPS CSV PATH   ", "SEGMENTS CSV PATH"]
    active        = 0

    while True:
        clear_screen(win)
        h, w = win.getmaxyx()
        attr_bright = curses.color_pair(C_BRIGHT) | curses.A_BOLD
        attr_normal = curses.color_pair(C_NORMAL)
        attr_sel    = curses.color_pair(C_SELECTED)
        attr_dim    = curses.color_pair(C_DIM)
        attr_hint   = curses.color_pair(C_YELLOW)

        draw_box(win, 0, 0, h - 1, w, C_DIM, "LOAD NETWORK FILE")

        for i, (label, field) in enumerate(zip(labels, fields)):
            row = h // 2 - 2 + i * 3
            safe_addstr(win, row,     4, label, attr_dim)
            val = "".join(field)
            if i == active:
                safe_addstr(win, row + 1, 4,
                            (val + "_").ljust(w - 8), attr_sel)
            else:
                safe_addstr(win, row + 1, 4, val.ljust(w - 8), attr_normal)

        safe_addstr(win, h - 2, 2,
                    " TAB Switch field   ENTER Load   ESC Cancel ",
                    attr_hint)
        win.refresh()

        key = win.getch()
        if key == 9:  # TAB
            active = 1 - active
        elif key in (curses.KEY_ENTER, 10, 13):
            stops_path = "".join(fields[0]).strip() or default_stops
            segs_path  = "".join(fields[1]).strip() or default_segs
            try:
                curses.curs_set(0)
                # Brief loading flash
                clear_screen(win)
                centre_text(win, h // 2,
                            f"  Loading {stops_path} ...",
                            attr_bright)
                win.refresh()
                time.sleep(0.4)
                stops, segs = load_network(stops_path, segs_path)
                return stops, segs
            except SystemExit:
                return None, None
            except Exception as e:
                return None, None
        elif key == 27:
            curses.curs_set(0)
            return None, None
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if fields[active]:
                fields[active].pop()
        elif 32 <= key <= 126:
            fields[active].append(chr(key))


# ── Main application loop ─────────────────────────────────────────────────────

def run(stdscr):
    init_colours()
    stdscr.bkgd(' ', curses.color_pair(C_NORMAL))
    curses.curs_set(0)

    # Boot
    boot_splash(stdscr)

    # Load default network
    stops, segments = {}, []
    if IO_AVAILABLE:
        try:
            stops, segments = load_network(
                "Team_2/sample_data/stops.csv",
                "Team_2/sample_data/segments.csv"
            )
        except Exception:
            pass

    # Main loop
    while True:
        choice = main_menu_screen(stdscr, stops, segments)

        # ── 0: PLAN A JOURNEY ──────────────────────────────────────────────────
        if choice == 0:
            if not stops:
                error_screen(stdscr, "No network loaded. Use 'Load Network File' first.")
                continue
            if not DFS_AVAILABLE:
                error_screen(stdscr,
                    "Journey search is not yet available. "
                    "The DFS module (Team_3/DFS_algorithm.py) is missing "
                    "or does not yet export recursive_journeyGenerator.",
                    title="MODULE NOT READY")
                continue

            origin = stop_selector(stdscr, stops, "SELECT ORIGIN STOP")
            if origin is None:
                continue

            dest = stop_selector(stdscr, stops, "SELECT DESTINATION STOP")
            if dest is None:
                continue

            pref = preference_picker(stdscr)
            if pref is None:
                continue

            # Validate
            ok, result = validate_journey_request(origin, dest, pref, stops)
            if not ok:
                error_screen(stdscr, result)
                continue

            # Search with loading animation
            loading_screen(stdscr)

            adj_list       = createAdjList(segments)
            candidate_paths = recursive_journeyGenerator(adj_list, origin, dest)

            if not candidate_paths:
                error_screen(stdscr,
                    f"No routes found between "
                    f"{stops[origin]['name']} and {stops[dest]['name']}. "
                    "Try a different origin or destination.",
                    title="NO ROUTES FOUND")
                continue

            top3 = evaluate_and_rank(candidate_paths, preference=pref, stops=stops)
            results_screen(stdscr, top3,
                           stops[origin]["name"],
                           stops[dest]["name"],
                           pref, stops)

        # ── 1: BROWSE STOPS ───────────────────────────────────────────────────
        elif choice == 1:
            if not stops:
                error_screen(stdscr, "No network loaded.")
            else:
                browse_stops_screen(stdscr, stops)

        # ── 2: NETWORK OVERVIEW ───────────────────────────────────────────────
        elif choice == 2:
            if not stops:
                error_screen(stdscr, "No network loaded.")
            else:
                network_overview_screen(stdscr, stops, segments)

        # ── 3: LOAD NETWORK FILE ──────────────────────────────────────────────
        elif choice == 3:
            new_stops, new_segs = load_network_screen(stdscr)
            if new_stops:
                stops, segments = new_stops, new_segs
            else:
                error_screen(stdscr,
                    "Could not load the network file. "
                    "Check the file path and CSV format.",
                    title="LOAD FAILED")

        # ── 4: EXIT ───────────────────────────────────────────────────────────
        elif choice == 4:
            clear_screen(stdscr)
            h, w = stdscr.getmaxyx()
            centre_text(stdscr, h // 2,
                        "  GOODBYE  ·  SAFE TRAVELS  ",
                        curses.color_pair(C_BRIGHT) | curses.A_BOLD)
            stdscr.refresh()
            time.sleep(1.2)
            return


def main():
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()