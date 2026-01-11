import curses
from time import sleep, time
from colors import Colors

import game_manager as gm

# Params
KEY_DELAY = 0.1
MESSAGE_TIME = 3
KEYBOARD_LAYOUT = [
    "`1234567890-=",
    "qwertyuiop[]",
    "asdfghjkl;'",
    "zxcvbnm,./"
]


def draw(screen, game_manager):
    """
    Complete unified draw function
    """
    screen.erase()
    screen.bkgd(' ', Colors.TEXT.pair)
    max_h, max_w = screen.getmaxyx()
    # renderer graphics
    draw_border(game_manager, screen, max_h, max_w, game_manager.phases.current_phase)
    # screen.border("║", "║", "═", "═", "╔", "╗", "╚", "╝")
    screen.addstr(0, 0, game_manager.log_message, Colors.TEXT.pair)
    draw_ui(screen, game_manager, max_h, max_w)
    draw_keyboard(screen, game_manager, max_h, max_w)
    screen.refresh()


def draw_border(game_manager, screen, max_h, max_w, curr_phase):
    """Draw a colored border around the entire window based on phase"""
    border_color = curr_phase.color.pair | curses.A_BOLD

    try:
        # Top border (double line for emphasis)
        screen.addstr(0, 0, "╔", border_color)
        screen.addstr(0, 1, "═" * (max_w - 2), border_color)
        screen.addstr(0, max_w - 1, "╗", border_color)

        # Side borders (double line)
        for i in range(1, max_h - 1):
            screen.addstr(i, 0, "║", border_color)
            screen.addstr(i, max_w - 1, "║", border_color)

        # Bottom border (double line)
        screen.addstr(max_h - 1, 0, "╚", border_color)
        screen.addstr(max_h - 1, 1, "═" * (max_w - 2), border_color)
        try:
            screen.addstr(max_h - 1, max_w - 1, "╝", border_color)
        except curses.error:
            pass  # this always crashes, expected error (curses bug, won't fix)

        # Phase indicator
        screen.addstr(0, 2, f" {curr_phase.name} ", border_color | curses.A_REVERSE)

    except curses.error:
        game_manager.log("DrawBorder failed")


def draw_keyboard(screen, game_manager, max_h, max_w):
    key_height = 5
    key_width = 9
    gap_x = 2
    gap_y = 1

    start_y = max_h - len(game_manager.keyboard.char_rows) * (key_height + gap_y) - 4
    if start_y < max_h // 2:
        start_y = max_h // 2

    for row_idx, row_str in enumerate(game_manager.keyboard.char_rows):
        row_len_px = len(row_str) * (key_width + gap_x)
        start_x = (max_w - row_len_px) // 2

        # Stagger
        match row_idx:
            case 0:
                start_x += 0
            case 1:
                start_x += 1
            case 2:
                start_x += 1
            case 3:
                start_x += 2

        current_y = start_y + (row_idx * (key_height + gap_y))

        for i, char in enumerate(row_str):
            current_x = start_x + (i * (key_width + gap_x))
            slot = game_manager.keyboard.get_by_char(char)

            # --- Colors ---
            bg_color = Colors.GREY_KEY.pair  # Default Grey
            is_active = (game_manager.active_key == char)

            # --- Key Press Offset Logic ---
            draw_y = current_y
            draw_x = current_x
            draw_shadow = True

            if is_active:
                bg_color = Colors.SUCCESS.pair  # Green Press
                draw_y += 1  # Offset down
                draw_x += 1  # Offset right
                draw_shadow = False  # No shadow when pressed

            elif slot:
                if slot.locked:
                    bg_color = Colors.ERROR.pair  # Red Locked
                elif not slot.active and game_manager.mode == gm.MODE_IDLE:
                    bg_color = Colors.WARNING.pair  # Yellow Activated (Wait next phase)
            # Draw the key box (with press offset and shadow logic)
            draw_rounded_key_box(game_manager, screen, draw_y, draw_x, key_height, key_width, bg_color,
                                 shadow=draw_shadow)

            # Fill the interior
            for row in range(1, key_height - 1):
                try:
                    screen.addstr(draw_y + row, draw_x + 1, " " * (key_width - 2), bg_color)
                except:
                    game_manager.log("DrawKeyboard failed at filling interior")

            # Character (bottom center)
            try:
                char_x = draw_x + (key_width // 2)
                screen.addstr(draw_y + key_height - 2, char_x, char.upper(), bg_color | curses.A_BOLD)
            except:
                game_manager.log("DrawKeyboard failed at characters")

            # Content (center)
            if slot:
                if slot.locked:
                    try:
                        cost_str = f"${slot.unlock_cost}"
                        screen.addstr(draw_y + 2, draw_x + (key_width - len(cost_str)) // 2, cost_str, bg_color)
                    except:
                        game_manager.log("DrawKeyboard failed at unlock cost")
                elif slot.building is not None:
                    try:
                        screen.addstr(draw_y + 2, draw_x + (key_width - 2) // 2, slot.building.symbol, bg_color)
                    except:
                        game_manager.log("DrawKeyboard failed at emojis")


def draw_rounded_key_box(game_manager, stdscr, y, x, h, w, color, shadow=True):
    """Draw a rounded box for keyboard keys, optionally with a drop shadow."""

    # -- SHADOW -- #
    if shadow:
        shadow_color = Colors.SHADOW.pair | curses.A_REVERSE

        try:
            # Draw the shadow for the side
            for i in range(h):
                stdscr.addch(y + i + 1, x + w, '▌', shadow_color)

            # Draw the shadow for the bottom (use spaces for background fill)
            for i in range(w - 1):
                stdscr.addch(y + h, x + i + 1, '▀', shadow_color)

            # Draw bottom-right corner shadow
            stdscr.addch(y + h, x + w, '▘', shadow_color)

        except curses.error:
            game_manager.log("DrawKeyBox failed at shadow")

    # -- Actual Box -- #
    try:
        # Top border
        stdscr.addstr(y, x, "╭", color)
        stdscr.addstr(y, x + 1, "─" * (w - 2), color)
        stdscr.addstr(y, x + w - 1, "╮", color)

        # Middle rows (filled)
        for i in range(1, h - 1):
            stdscr.addstr(y + i, x, "│", color)
            stdscr.addstr(y + i, x + 1, " " * (w - 2), color)
            stdscr.addstr(y + i, x + w - 1, "│", color)

        # Bottom border
        stdscr.addstr(y + h - 1, x, "╰", color)
        stdscr.addstr(y + h - 1, x + 1, "─" * (w - 2), color)
        stdscr.addstr(y + h - 1, x + w - 1, "╯", color)
    except curses.error:
        game_manager.log("DrawKeyBox failed at border")


def draw_ui(screen, game_manager, max_h, max_w):
    global MESSAGE_TIME
    phase_str = f" PHASE: {game_manager.phases.current_phase.name} | Day {game_manager.phases.day} "
    res_str = str(game_manager.resources)

    try:
        # Phase info (left side)
        screen.addstr(1, 3, phase_str, Colors.TEXT.pair | curses.A_BOLD)

        # Resources (center-right)
        screen.addstr(1, max_w // 2 - len(res_str) // 2, res_str, Colors.TEXT.pair)

        # Help hint (right side)
        hints = ["[TAB/ENTER: Next Phase]",
                 "[ESC: Exit]"]
        for i, hint in enumerate(hints):
            screen.addstr(1 + i, max_w - len(hint) - 3, hint, Colors.TEXT.pair | curses.A_DIM)
    except curses.error:
        game_manager.log("DrawUI failed at phase/resources/hint")
    if game_manager.mode == gm.MODE_GAME_OVER:
        MESSAGE_TIME = 1000.0
    if game_manager.message and time() - game_manager.message_time <= MESSAGE_TIME:
        try:
            for dy, message in enumerate(game_manager.message):
                c_x = (max_w - len(message)) // 2
                screen.addstr(3+dy, c_x, message, game_manager.message_color | curses.A_BOLD)
        except:
            game_manager.log("DrawUI failed at message")
    else:
        game_manager.reset(True, False)

    center_y = max_h // 4

    # --- Mode UI ---
    if game_manager.phases.is_night():
        # Night Battle Interface
        title = "--- NIGHT PHASE ---"
        try:
            screen.addstr(center_y - 2, (max_w - len(title)) // 2, title,
                          Colors.ERROR.pair | curses.A_BOLD)
            if game_manager.battle_report:
                for i, line in enumerate(game_manager.battle_report):
                    screen.addstr(center_y + i, (max_w - len(line)) // 2, line, Colors.TEXT.pair)
            else:
                msg = "The city sleeps... but something is out there."
                screen.addstr(center_y, (max_w - len(msg)) // 2, msg, Colors.TEXT.pair)
        except:
            game_manager.log("DrawUI failed at night")

    elif game_manager.mode == gm.MODE_TYPING:
        msg = f"ACTIVATING: {game_manager.current_key.building.name.upper()}"
        draw_typing_interface(game_manager, screen, msg, game_manager.current_text, game_manager.current_input,
                              center_y, max_w)

    elif game_manager.mode == gm.MODE_BUILDING_SELECT:
        # Build Menu Table
        title = "SELECT BUILDING TO CONSTRUCT"
        try:
            screen.addstr(center_y - 3, (max_w - len(title)) // 2, title,
                          Colors.TEXT.pair | curses.A_BOLD)

            # Show typed input
            curr_input_str = "".join(game_manager.current_input)
            input_lbl = f"CURRENTLY TYPING: {curr_input_str}_"
            screen.addstr(center_y - 1, (max_w - len(input_lbl)) // 2, input_lbl, Colors.WARNING.pair)

            # Table Header
            header = f"{'NAME':<10} {'ICON':<4} {'COST':<6} {'OUTPUT':<15} {'INPUT':<10}"
            start_x = (max_w - len(header)) // 2
            screen.addstr(center_y + 1, start_x, header, Colors.TEXT.pair | curses.A_UNDERLINE)

            # Rows
            row_offset = 2
            for building in game_manager.buildings:
                # Highlight match
                attr = Colors.SUCCESS.pair if (
                        game_manager.resources.money.amount >= building.purchase_cost) else Colors.ERROR.pair
                if building.name.lower().startswith(curr_input_str.lower()) and len(curr_input_str) > 0:
                    attr = attr | curses.A_REVERSE

                screen.addstr(center_y + row_offset, start_x, str(building), attr)
                row_offset += 1
        except:
            game_manager.log("DrawUI Failed on BUILDING_SELECT")

    elif game_manager.mode == gm.MODE_IDLE:
        # Idle
        lines = [
            "CITY MANAGEMENT",
            "Morning/Afternoon/Evening: Build & Produce",
            "Night: Defend your city with your Military",
            "",
            "Survive the nightly attacks for 5 days!",
            "",
            "Press [Key] to Select",
            "[Tab] or [Enter] to Next Phase",
            "[Esc] to Exit"
        ]
        for i, line in enumerate(lines):
            try:
                screen.addstr(center_y + i, (max_w - len(line)) // 2, line, Colors.TEXT.pair)
            except:
                game_manager.log("DrawUI failed on IDLE")


def draw_typing_interface(game_manager, screen, title, target, current_input, start_y, max_w):
    try:
        screen.addstr(start_y - 2, (max_w - len(title)) // 2, title, Colors.TEXT.pair | curses.A_DIM)

        start_x = (max_w - len(target)) // 2
        if start_x < 0:
            start_x = 0

        for i, char in enumerate(target):
            color = Colors.TEXT.pair
            # Check if the character is correctly typed
            if i < len(current_input):
                if current_input[i] == char:
                    color = Colors.SUCCESS.pair  # Correct
                elif char == ' ' and current_input[i] != ' ':
                    color = Colors.ERROR.pair  # Incorrect space input
                    screen.addch(start_y + 1, start_x + i, '¯', color)  # Red overline ASCII char for wrong space
                else:
                    color = Colors.ERROR.pair  # Incorrect
            screen.addch(start_y, start_x + i, char, color | curses.A_BOLD)

        cursor_idx = len(current_input)
        if cursor_idx < len(target):
            screen.addch(start_y + 1, start_x + cursor_idx, '^', Colors.TEXT.pair)
    except:
        game_manager.log("DrawTypingInterface failed")


def main(screen):
    curses.curs_set(0)
    curses.raw()
    curses.start_color()
    Colors.init()
    screen.nodelay(True)
    game_manager = gm.GameManager(KEYBOARD_LAYOUT)
    while True:
        draw(screen, game_manager)
        try:
            key = screen.getch()
        except:
            game_manager.log("Main failed on getch")
            key = -1

        if game_manager.active_key and (time() - game_manager.key_press_time > KEY_DELAY):
            game_manager.active_key = None

        try:
            game_manager.key_logic(key)
        except KeyboardInterrupt:
            break

        sleep(0.01)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
