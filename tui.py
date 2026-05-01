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
  5. Confirmation      — review / swap before searching
  6. Loading screen    — spinning animation while DFS runs
  7. Results screen    — top 3 routes in bordered box
  8. Error screen      — red bordered error / warning message

Controls (shown on every screen):
  UP / DOWN   — navigate
  ENTER       — confirm selection
  ESC         — go back / cancel
  Q           — quit from main menu

Compatibility:
  Mac/Linux : works out of the box (curses is built in)
  Windows   : run  pip install windows-curses  first
"""

import curses
import time
import textwrap
import io
import sys

# ── Try importing project modules ──────────────────────────────────────────────
try:
    from Team_2.io_handler import load_network
    from Team_2.validator  import validate_journey_request
    from Team_2.scorer     import evaluate_and_rank
    IO_AVAILABLE = True
except ImportError:
    IO_AVAILABLE = False

try:
    from Team_3.DFS_algorithm import createAdjList, recursive_journeyGenerator, iterativeDFS
    DFS_AVAILABLE = True
except ImportError:
    DFS_AVAILABLE = False

# ── Colour pair IDs ────────────────────────────────────────────────────────────
C_NORMAL   = 1
C_BRIGHT   = 2
C_SELECTED = 3
C_DIM      = 4
C_ERROR    = 5
C_TITLE    = 6
C_YELLOW   = 7


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
    attr = curses.color_pair(colour_pair)
    safe_addstr(win, y,         x,         "┌" + "─" * (w - 2) + "┐", attr)
    for row in range(1, h - 1):
        safe_addstr(win, y + row, x,         "│", attr)
        safe_addstr(win, y + row, x + w - 1, "│", attr)
    safe_addstr(win, y + h - 1, x,         "└" + "─" * (w - 2) + "┘", attr)
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


# ── Safe network loader — captures all io_handler prints ──────────────────────

def _safe_load_network(stops_path, segments_path):
    """
    Wraps load_network() and captures any print() output from io_handler
    (warnings, errors) so they do not bleed behind the curses screen.

    Returns:
        (stops, segments, captured_output)
        On failure: (None, None, captured_output)
    """
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()
    try:
        stops, segs = load_network(stops_path, segments_path)
        sys.stdout = old_stdout
        return stops, segs, captured.getvalue().strip()
    except SystemExit:
        sys.stdout = old_stdout
        return None, None, captured.getvalue().strip()
    except Exception:
        sys.stdout = old_stdout
        return None, None, captured.getvalue().strip()


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
    clear_screen(win)
    h, w = win.getmaxyx()
    start_y = max(2, h // 2 - len(LOGO) - 3)
    attr_bright = curses.color_pair(C_BRIGHT) | curses.A_BOLD
    attr_dim    = curses.color_pair(C_DIM)

    for i, line in enumerate(LOGO):
        safe_addstr(win, start_y + i, max(0, (w - len(line)) // 2), line, attr_bright)
        win.refresh()
        time.sleep(0.07)

    centre_text(win, start_y + len(LOGO) + 1, SUBTITLE, attr_bright)
    centre_text(win, start_y + len(LOGO) + 2, GROUP,    attr_dim)

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
    ("PLAN A JOURNEY",     "Find and rank routes between two stops"),
    ("BROWSE STOPS",       "View all stops in the network"),
    ("NETWORK OVERVIEW",   "Summary of stops, segments and transport modes"),
    ("LOAD NETWORK FILE",  "Switch to a different stops / segments CSV"),
    ("EXIT",               "Quit the program"),
]


def draw_main_menu(win, selected, stops, segments):
    clear_screen(win)
    h, w = win.getmaxyx()
    attr_normal = curses.color_pair(C_NORMAL)
    attr_sel    = curses.color_pair(C_SELECTED) | curses.A_BOLD
    attr_dim    = curses.color_pair(C_DIM)
    attr_hint   = curses.color_pair(C_YELLOW)

    draw_box(win, 0, 0, h - 1, w, C_DIM, "SMART PUBLIC TRANSPORT ADVISOR")

    if stops:
        status = f"  Network loaded: {len(stops)} stops  ·  {len(segments)//2} segments  "
    else:
        status = "  No network loaded  "
    safe_addstr(win, h - 2, 2, status, attr_dim)

    box_h = len(MENU_ITEMS) * 2 + 4
    box_w = min(60, w - 6)
    box_y = max(3, (h - box_h) // 2)
    box_x = max(2, (w - box_w) // 2)
    draw_box(win, box_y, box_x, box_h, box_w, C_DIM, "MAIN MENU")

    for i, (label, hint) in enumerate(MENU_ITEMS):
        row_y  = box_y + 2 + i * 2
        prefix = f"  [{i+1}]  "
        text   = prefix + label.ljust(box_w - len(prefix) - 4)
        if i == selected:
            safe_addstr(win, row_y,     box_x + 1, text, attr_sel)
            safe_addstr(win, row_y + 1, box_x + 5, hint, attr_dim)
        else:
            safe_addstr(win, row_y, box_x + 1, text, attr_normal)

    controls = " ↑↓ Navigate   ENTER Select   Q Quit "
    safe_addstr(win, h - 2, w - len(controls) - 2, controls, attr_hint)
    win.refresh()


def main_menu_screen(win, stops, segments):
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
            return 4
        elif ord('1') <= key <= ord('5'):
            return key - ord('1')


# ── Stop selector ─────────────────────────────────────────────────────────────

def stop_selector(win, stops, prompt):
    """
    Full-screen stop picker.
    UP/DOWN to navigate; type to filter the list live.
    ENTER confirms, ESC cancels.
    Returns stop_id string, or None if cancelled.
    """
    curses.curs_set(1)
    win.keypad(True)
    win.timeout(50)

    query     = ""
    selected  = 0
    all_stops = [(sid, info["name"], info["transport_type"])
                 for sid, info in stops.items()]

    while True:
        q        = query.upper()
        filtered = [(sid, name, tt) for sid, name, tt in all_stops
                    if q in sid or q in name.upper()]
        if not filtered:
            filtered = all_stops
        selected = max(0, min(selected, len(filtered) - 1))

        clear_screen(win)
        h, w = win.getmaxyx()
        attr_title  = curses.color_pair(C_TITLE) | curses.A_BOLD
        attr_normal = curses.color_pair(C_NORMAL)
        attr_sel    = curses.color_pair(C_SELECTED) | curses.A_BOLD
        attr_dim    = curses.color_pair(C_DIM)
        attr_hint   = curses.color_pair(C_YELLOW)

        draw_box(win, 0, 0, h - 1, w, C_DIM, prompt)

        search_label = "  SEARCH: "
        safe_addstr(win, 2, 2, search_label, attr_dim)
        cursor_x = 2 + len(search_label)
        safe_addstr(win, 2, cursor_x,
                    (query + "_").ljust(w - cursor_x - 3), attr_title)
        safe_addstr(win, 3, 2, "─" * (w - 4), attr_dim)

        col_id   = 8
        col_type = 10
        col_name = max(10, w - col_id - col_type - 8)

        hdr = f"  {'ID':<{col_id}} {'NAME':<{col_name}} {'TYPE':<{col_type}}"
        safe_addstr(win, 4, 1, hdr, attr_dim | curses.A_BOLD)
        safe_addstr(win, 5, 2, "─" * (w - 4), attr_dim)

        list_y  = 6
        visible = h - list_y - 3
        start   = max(0, selected - visible // 2)

        if q and not any(q in sid or q in n.upper() for sid, n, _ in all_stops):
            safe_addstr(win, list_y, 3,
                        "No matches — showing all stops", attr_hint)
            list_y  += 1
            visible -= 1

        for i, (sid, name, tt) in enumerate(filtered[start:start + visible]):
            idx  = start + i
            row  = list_y + i
            line = f"  {sid:<{col_id}} {name:<{col_name}} [{tt}]"
            if idx == selected:
                safe_addstr(win, row, 1, line.ljust(w - 2), attr_sel)
            else:
                safe_addstr(win, row, 1, line, attr_normal)

        if len(filtered) > visible:
            pct = int(100 * selected / max(1, len(filtered) - 1))
            safe_addstr(win, h - 2, w - 12, f"  {pct:3d}%  ▓ ", attr_dim)

        controls = " ↑↓ Navigate   Type to filter   ENTER Select   ESC Cancel "
        safe_addstr(win, h - 2, 2, controls, attr_hint)
        win.refresh()

        key = win.getch()
        if key == curses.KEY_UP:
            selected = max(0, selected - 1)
        elif key == curses.KEY_DOWN:
            selected = min(len(filtered) - 1, selected + 1)
        elif key in (curses.KEY_ENTER, 10, 13):
            curses.curs_set(0)
            return filtered[selected][0]
        elif key == 27:
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
            label = f"  [{i+1}]  {pref.upper().replace('_', ' ')}"
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


# ── Confirmation dialog ───────────────────────────────────────────────────────

def confirmation_dialog(win, origin_id, dest_id, preference, stops):
    curses.curs_set(0)
    win.keypad(True)

    origin_name = stops[origin_id]["name"] if origin_id in stops else origin_id
    dest_name   = stops[dest_id]["name"]   if dest_id   in stops else dest_id
    pref_label  = preference.upper().replace("_", " ")

    while True:
        clear_screen(win)
        h, w = win.getmaxyx()
        attr_bright = curses.color_pair(C_BRIGHT) | curses.A_BOLD
        attr_normal = curses.color_pair(C_NORMAL)
        attr_dim    = curses.color_pair(C_DIM)
        attr_hint   = curses.color_pair(C_YELLOW)

        box_w = min(56, w - 6)
        box_h = 12
        box_y = max(2, (h - box_h) // 2)
        box_x = max(2, (w - box_w) // 2)
        draw_box(win, box_y, box_x, box_h, box_w, C_DIM, "CONFIRM JOURNEY")

        inner_x = box_x + 4
        row = box_y + 2
        safe_addstr(win, row, inner_x,
                    f"FROM:  {origin_name} ({origin_id})", attr_bright)
        row += 2
        safe_addstr(win, row, inner_x,
                    f"  TO:  {dest_name} ({dest_id})", attr_bright)
        row += 2
        safe_addstr(win, row, inner_x,
                    f"PREF:  {pref_label}", attr_normal)
        row += 2
        safe_addstr(win, row, inner_x, "─" * (box_w - 8), attr_dim)
        row += 1
        safe_addstr(win, row, inner_x,
                    "ENTER Search   ESC Back   S Swap", attr_hint)

        controls = " ENTER Confirm   ESC Cancel   S Swap origin/dest "
        safe_addstr(win, h - 2, 2, controls, attr_hint)
        win.refresh()

        key = win.getch()
        if key in (curses.KEY_ENTER, 10, 13):
            return "confirm"
        elif key == 27:
            return "cancel"
        elif key in (ord('s'), ord('S')):
            return "swap"


# ── Loading screen ────────────────────────────────────────────────────────────

def loading_screen(win, message="SEARCHING FOR ROUTES"):
    curses.curs_set(0)
    h, w = win.getmaxyx()
    attr_bright = curses.color_pair(C_BRIGHT) | curses.A_BOLD
    attr_dim    = curses.color_pair(C_DIM)
    attr_yellow = curses.color_pair(C_YELLOW)

    spinner_chars = ['|', '/', '─', '\\']
    bar_width     = min(40, w - 10)
    frames        = 24

    for frame in range(frames):
        clear_screen(win)
        draw_box(win, 0, 0, h - 1, w, C_DIM, "PLEASE WAIT")

        spin     = spinner_chars[frame % 4]
        dots     = "." * (frame % 4)
        label    = f"  {spin}  {message}{dots.ljust(3)}  {spin}  "
        centre_text(win, h // 2 - 2, label, attr_bright)

        filled   = int(bar_width * frame / frames)
        bar      = "[" + "=" * filled + ">" + " " * (bar_width - filled - 1) + "]"
        pct      = int(100 * frame / frames)
        centre_text(win, h // 2, f"{bar}  {pct:3d}%", attr_yellow)

        pulse_chars = "·  ··  ···  ··  ·"
        pulse = pulse_chars[(frame * 2) % len(pulse_chars):][:bar_width]
        centre_text(win, h // 2 + 2, pulse.center(bar_width + 8), attr_dim)

        win.refresh()
        time.sleep(0.12)


# ── Results screen ────────────────────────────────────────────────────────────

def results_screen(win, top3, origin_name, dest_name, preference, stops):
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

        draw_box(win, 0, 0, h - 1, w, C_DIM,
                 f"TOP {len(top3)} ROUTES  ·  {pref_label}")

        row = 2
        safe_addstr(win, row, 2,
                    f"  FROM: {origin_name}   →   TO: {dest_name}",
                    attr_bright)
        row += 1
        safe_addstr(win, row, 2, "─" * (w - 4), attr_dim)
        row += 1

        def stop_name(sid):
            if stops and sid in stops:
                return f"{stops[sid]['name']} ({sid})"
            return sid

        for journey in top3:
            rank = journey["rank"]
            dur  = journey["duration"]
            cost = journey["cost"]
            segs = journey["segments_count"]

            route_box_h = len(journey["segments"]) + 4
            route_box_w = min(w - 6, 72)
            route_box_x = max(3, (w - route_box_w) // 2)

            if row + route_box_h >= h - 3:
                if row < h - 3:
                    safe_addstr(win, row, 3,
                                "(resize terminal to see more routes)",
                                attr_dim)
                break

            draw_box(win, row, route_box_x, route_box_h, route_box_w,
                     C_DIM, f" ROUTE #{rank} ")
            row += 1
            header = (f"  Time: {dur:.0f} min   "
                      f"Cost: HK${cost:.2f}   "
                      f"Segments: {segs}")
            safe_addstr(win, row, route_box_x + 2, header, attr_sel)
            row += 1
            safe_addstr(win, row, route_box_x + 2,
                        "─" * (route_box_w - 4), attr_dim)
            row += 1

            for seg in journey["segments"]:
                from_to  = f"{stop_name(seg['from'])}  ->  {stop_name(seg['to'])}"
                detail   = (f"[{seg['transport_type']}  "
                            f"{seg['duration']:.0f}min  "
                            f"HK${seg['cost']:.2f}]")
                avail     = route_box_w - 6
                from_to_w = avail - len(detail) - 1
                seg_line  = f"  {from_to:<{max(1, from_to_w)}} {detail}"
                if row < h - 3:
                    safe_addstr(win, row, route_box_x + 2, seg_line, attr_normal)
                row += 1

            row += 1

        safe_addstr(win, h - 2, 2,
                    " Press any key to return to main menu ",
                    attr_hint)
        win.refresh()

        if win.getch() != curses.ERR:
            return


# ── Error / warning screen ────────────────────────────────────────────────────

def error_screen(win, message, title="ERROR"):
    curses.curs_set(0)
    win.keypad(True)

    while True:
        clear_screen(win)
        h, w = win.getmaxyx()
        attr_err  = curses.color_pair(C_ERROR) | curses.A_BOLD
        attr_hint = curses.color_pair(C_YELLOW)

        box_w = min(60, w - 6)
        lines = textwrap.wrap(message, box_w - 4)
        box_h = len(lines) + 6
        box_y = max(2, (h - box_h) // 2)
        box_x = max(2, (w - box_w) // 2)

        draw_box(win, box_y, box_x, box_h, box_w, C_ERROR,
                 f"  ✗  {title}  ")

        for i, line in enumerate(lines):
            safe_addstr(win, box_y + 2 + i, box_x + 3, line, attr_err)

        safe_addstr(win, h - 2, 2,
                    " Press any key to continue ",
                    attr_hint)
        win.refresh()

        if win.getch() != curses.ERR:
            return


# ── Browse stops screen ───────────────────────────────────────────────────────

def browse_stops_screen(win, stops):
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

        draw_box(win, 0, 0, h - 1, w, C_DIM,
                 f"ALL STOPS  ({len(all_stops)} total)")

        col_id   = 8
        col_type = 10
        col_name = max(10, w - col_id - col_type - 10)

        hdr = f"  {'ID':<{col_id}}  {'NAME':<{col_name}}  {'TYPE':<{col_type}}"
        safe_addstr(win, 2, 1, hdr, attr_dim | curses.A_BOLD)
        safe_addstr(win, 3, 2, "─" * (w - 4), attr_dim)

        visible = h - 7
        start   = max(0, selected - visible // 2)

        for i, (sid, name, tt) in enumerate(all_stops[start:start + visible]):
            idx  = start + i
            row  = 4 + i
            line = f"  {sid:<{col_id}}  {name:<{col_name}}  [{tt}]"
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


# ── Network overview screen ───────────────────────────────────────────────────

def network_overview_screen(win, stops, segments):
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

        if win.getch() != curses.ERR:
            return


# ── Load network screen ───────────────────────────────────────────────────────

def load_network_screen(win):
    """
    Prompt for CSV paths, load the network, and return (stops, segments).
    All io_handler output is captured and shown through error_screen if needed.
    Returns (stops, segments) on success, or (None, None) on cancel/failure.
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
        attr_sel    = curses.color_pair(C_SELECTED)
        attr_dim    = curses.color_pair(C_DIM)
        attr_normal = curses.color_pair(C_NORMAL)
        attr_hint   = curses.color_pair(C_YELLOW)

        draw_box(win, 0, 0, h - 1, w, C_DIM, "LOAD NETWORK FILE")

        for i, (label, field) in enumerate(zip(labels, fields)):
            row = h // 2 - 2 + i * 3
            safe_addstr(win, row, 4, label, attr_dim)
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
        if key == 9:
            active = 1 - active
        elif key in (curses.KEY_ENTER, 10, 13):
            stops_path = "".join(fields[0]).strip() or default_stops
            segs_path  = "".join(fields[1]).strip() or default_segs

            curses.curs_set(0)
            clear_screen(win)
            centre_text(win, h // 2,
                        f"  Loading {stops_path} ...",
                        attr_bright)
            win.refresh()
            time.sleep(0.3)

            stops, segs, output = _safe_load_network(stops_path, segs_path)

            if stops is not None:
                # Show any warnings (e.g. duplicate stop IDs) before returning
                if output:
                    error_screen(win, output, title="NETWORK WARNINGS")
                return stops, segs
            else:
                # Show the captured error output from io_handler
                msg = output if output else (
                    "Could not load the network. "
                    "Check the file path and CSV format."
                )
                error_screen(win, msg, title="LOAD FAILED")
                curses.curs_set(1)
                # Stay in the load screen so user can correct the path

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

    boot_splash(stdscr)

    # Load default network — capture all io_handler output
    stops, segments = {}, []
    if IO_AVAILABLE:
        s, seg, output = _safe_load_network(
            "Team_2/sample_data/stops.csv",
            "Team_2/sample_data/segments.csv"
        )
        if s is not None:
            stops, segments = s, seg
            if output:
                error_screen(stdscr, output, title="NETWORK WARNINGS")
        else:
            msg = output if output else (
                "Default network files not found. "
                "Use 'Load Network File' to load your CSV files."
            )
            error_screen(stdscr, msg, title="NETWORK LOAD ERROR")

    # Main loop
    while True:
        choice = main_menu_screen(stdscr, stops, segments)

        # ── 0: PLAN A JOURNEY ─────────────────────────────────────────────────
        if choice == 0:
            if not stops:
                error_screen(stdscr,
                    "No network loaded. Use 'Load Network File' first.")
                continue
            if not DFS_AVAILABLE:
                error_screen(stdscr,
                    "Journey search is not available. "
                    "DFS_algorithm.py is missing or not yet complete.",
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

            while True:
                action = confirmation_dialog(stdscr, origin, dest, pref, stops)
                if action == "cancel":
                    break
                elif action == "swap":
                    origin, dest = dest, origin
                    continue

                # Validate
                ok, result = validate_journey_request(
                    origin, dest, pref, stops)
                if not ok:
                    error_screen(stdscr, result)
                    break

                # Search — iterative first, recursive fallback
                loading_screen(stdscr)
                adj_list        = createAdjList(segments)
                candidate_paths = iterativeDFS(adj_list, origin, dest)

                if not candidate_paths:
                    candidate_paths = recursive_journeyGenerator(
                        adj_list, origin, dest)

                if not candidate_paths:
                    error_screen(stdscr,
                        f"No routes found between "
                        f"{stops[origin]['name']} and "
                        f"{stops[dest]['name']}. "
                        "Try a different origin or destination.",
                        title="NO ROUTES FOUND")
                    break

                top3 = evaluate_and_rank(
                    candidate_paths, preference=pref, stops=stops)
                results_screen(stdscr, top3,
                               stops[origin]["name"],
                               stops[dest]["name"],
                               pref, stops)
                break

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
            result = load_network_screen(stdscr)
            if result[0] is not None:
                stops, segments = result

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