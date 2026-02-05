import curses
import os
from time import sleep, time
from colors import Colors

import game_manager as gm
from game_manager import GameManager

# Params
KEY_DELAY = 0.1
MESSAGE_TIME = 5.0
KEYBOARD_LAYOUT = [
    "`1234567890-=",
    "qwertyuiop[]",
    "asdfghjkl;'",
    "zxcvbnm,./"
]

LOGO: list[str] = [
    r" _  __             _                           _   _  _                     _",
    r"| |/ / ___ _   _  | |__   ___   __ _  _ __  __| | | |/ /(_) _ __   __ _  __| |  ___   _ __ ___   ___ ",
    r"| ' / / _ \ | | | | '_ \ / _ \ / _` || '__|/ _` | | ' / | || '_ \ / _` |/ _` | / _ \ | '_ ` _ \ / __|",
    r"| . \|  __/ |_| | | |_) | (_) | (_| || |  | (_| | | . \ | || | | | (_| | (_| || (_) || | | | | |\__ \ ",
    r"|_|\_\\___| \__,| |_.__/ \___/ \__,_||_|   \__,_| |_|\_\|_||_| |_|\__, |\__,_| \___/ |_| |_| |_||___/",
    r"            |___/                                                  |___/"
]

# Messages
INITIAL_MESSAGE: list[str] = [
    "Welcome to Keyboard Kingdoms!",
    "",
    "In this game you are tasked with managing your own city built on a keyboard.",
    f"The main goal is to survive {gm.DAYS_TO_SURVIVE} days.",
    "Raiders come to attack you every night with a raising difficulty shown in the middle.",
    "",
    "The way you prevent those raiders from stealing your livelihood is by defeating them with your military.",
    "",
    "+--------------+---------------------------------------------------------------+",
    "| Resource     | Description                                                   |",
    "+--------------+---------------------------------------------------------------+",
    "| 🪙 Money     | Used to purchase buildings on keys you have already unlocked. |",
    "| 🍖 Food      | Used to feed your military while they train in their building.|",
    "| 🪖 Military  | Your only defense against the raiders.                        |",
    "| 🧠 Knowledge | Used to unlock more keys on the keyboard; also gained by      |",
    "|              | defeating raiders.                                            |",
    "+--------------+---------------------------------------------------------------+",
    "",
    "You gain resources by activating their respective buildings and writing a short text.",
    "Each mistake you make removes a part of the resources you gain, so type wisely!",
    "",
    "",
    "To continue to the main game type:",
]
CONFIRM_MESSAGE = "Continue"


def draw(screen, game_manager: GameManager):
    """
    Complete unified draw function
    """
    screen.erase()
    screen.bkgd(' ', Colors.TEXT.pair)
    max_h, max_w = screen.getmaxyx()
    # renderer graphics
    draw_border(game_manager, screen, max_h, max_w, game_manager.phases.current_phase)
    screen.addstr(0, 0, game_manager.log_message, Colors.TEXT.pair)
    if game_manager.mode == gm.MODE_INITIAL:
        draw_initial_screen(screen, game_manager, max_w)
    else:
        draw_ui(screen, game_manager, max_h, max_w)
        draw_keyboard(screen, game_manager, max_h, max_w)
    draw_message(game_manager, screen, max_w)
    screen.refresh()


def draw_border(game_manager, screen, max_h, max_w, curr_phase):
    """
    Draw a colored border around the entire window based on phase
    """
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


def draw_initial_screen(screen, game_manager: GameManager, max_w: int):
    try:
        height_modifier = 12
        start_x = 0
        for string in LOGO:
            start_x = max(start_x, len(string))
        start_x = (max_w - start_x) // 2
        for index_y, line in enumerate(LOGO):
            screen.addstr(height_modifier + index_y - 7, start_x, line, Colors.NOON.pair)

        game_manager.current_text = CONFIRM_MESSAGE
        for index_y, line in enumerate(INITIAL_MESSAGE):
            if index_y == len(INITIAL_MESSAGE) - 1:
                screen.addstr(height_modifier + index_y, (max_w - len(line)) // 2, line, Colors.NOON.pair)
            else:
                screen.addstr(height_modifier + index_y, (max_w - len(line)) // 2, line, Colors.TEXT.pair | curses.A_DIM)

        start_x = (max_w - len(CONFIRM_MESSAGE)) // 2
        if start_x < 0:
            start_x = 0

        for i, char in enumerate(CONFIRM_MESSAGE):
            color = Colors.TEXT.pair
            # Check if the character is correctly typed
            if i < len(game_manager.current_input):
                color = Colors.SUCCESS.pair if game_manager.current_input[i] == char else Colors.ERROR.pair
            screen.addch(len(INITIAL_MESSAGE) + height_modifier + 2, start_x + i, char, color | curses.A_BOLD)

        cursor_idx = len(game_manager.current_input)
        if cursor_idx <= len(CONFIRM_MESSAGE):
            screen.addch(len(INITIAL_MESSAGE) + height_modifier + 3, start_x + cursor_idx, '^', Colors.TEXT.pair)
    except curses.error:
        game_manager.log("DrawInitialScreen failed")


def draw_keyboard(screen, game_manager, max_h, max_w):
    """
    Draws the keyboard in the lower middle of the screen
    """
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
                except curses.error:
                    game_manager.log("DrawKeyboard failed at filling interior")

            # Character (bottom center)
            try:
                char_x = draw_x + (key_width // 2)
                screen.addstr(draw_y + key_height - 2, char_x, char.upper(), bg_color | curses.A_BOLD)
            except curses.error:
                game_manager.log("DrawKeyboard failed at characters")

            # Content (center)
            if slot:
                if slot.locked:
                    try:
                        cost_str = f"{slot.unlock_cost}{game_manager.resources.knowledge.symbol}"
                        screen.addstr(draw_y + 2, draw_x + (key_width - len(cost_str)) // 2, cost_str, bg_color)
                    except curses.error:
                        game_manager.log("DrawKeyboard failed at unlock cost")
                elif slot.building is not None:
                    try:
                        screen.addstr(draw_y + 2, draw_x + (key_width - 2) // 2, slot.building.symbol, bg_color)
                    except curses.error:
                        game_manager.log("DrawKeyboard failed at emojis")


def draw_rounded_key_box(game_manager, screen, y, x, h, w, color, shadow=True):
    """
    Draw a rounded box for keyboard keys, optionally with a drop shadow.
    """
    if shadow:
        shadow_color = Colors.SHADOW.pair | curses.A_REVERSE

        try:
            for i in range(h):  # Side shadow
                screen.addch(y + i + 1, x + w, '▌', shadow_color)

            for i in range(w - 1):  # Bottom shadow
                screen.addch(y + h, x + i + 1, '▀', shadow_color)

            screen.addch(y + h, x + w, '▘', shadow_color)  # Bottom-right corner shadow

        except curses.error:
            game_manager.log("DrawKeyBox failed at shadow")

    try:
        # Top border
        screen.addstr(y, x, "╭", color)
        screen.addstr(y, x + 1, "─" * (w - 2), color)
        screen.addstr(y, x + w - 1, "╮", color)

        # Middle rows (filled)
        for i in range(1, h - 1):
            screen.addstr(y + i, x, "│", color)
            screen.addstr(y + i, x + 1, " " * (w - 2), color)
            screen.addstr(y + i, x + w - 1, "│", color)

        # Bottom border
        screen.addstr(y + h - 1, x, "╰", color)
        screen.addstr(y + h - 1, x + 1, "─" * (w - 2), color)
        screen.addstr(y + h - 1, x + w - 1, "╯", color)
    except curses.error:
        game_manager.log("DrawKeyBox failed at border")


def draw_message(game_manager, screen, max_w):
    global MESSAGE_TIME
    if game_manager.mode == gm.MODE_GAME_OVER:
        MESSAGE_TIME = 1000.0
    if game_manager.message and time() - game_manager.message_time <= MESSAGE_TIME:
        try:
            for dy, (message, message_color) in enumerate(game_manager.message):
                c_x = (max_w - len(message)) // 2
                screen.addstr(3 + dy, c_x, message, message_color | curses.A_BOLD)
        except curses.error:
            game_manager.log("DrawMessage failed")
    else:
        game_manager.reset(True, False)


def draw_ui(screen, game_manager: GameManager, max_h: int, max_w: int):
    """
    Draws all UI elements, like:
    Phase info, threat, resources, typehints
    Messages
    Night
    Also handles when to write typing_interface, building_interface or idle
    """
    res_str = str(game_manager.resources)

    try:
        # Idle
        lines = [
            "Keyboard Kingdoms",
            "Morning/Afternoon/Evening: Build & Produce",
            "Night: Defend your city with your Military",
            "",
            f"Survive the nightly attacks for {gm.DAYS_TO_SURVIVE} days!"
        ]
        for i, line in enumerate(lines):
            try:
                if i == 0:
                    screen.addstr(2 + i, 3, line, Colors.TEXT.pair)
                else:
                    screen.addstr(3 + i, 3, line, Colors.TEXT.pair | curses.A_DIM)
            except curses.error:
                game_manager.log("DrawUI failed at top-left typehints")

        # Resources (center-right)
        screen.addstr(1, max_w // 2 - len(res_str) // 2, res_str, Colors.TEXT.pair)

        # Type hint (right side)
        hints = ["[TAB: Next Phase]",
                 "[ESC: Exit]"]
        for i, hint in enumerate(hints):
            screen.addstr(1 + i, max_w - len(hint) - 3, hint, Colors.TEXT.pair | curses.A_DIM)
    except curses.error:
        game_manager.log("DrawUI failed at phase/resources/hint")

    center_y = max_h // 4

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
        except curses.error:
            game_manager.log("DrawUI failed at night")

    elif game_manager.mode == gm.MODE_TYPING:
        msg = f"ACTIVATING: {game_manager.current_key.building.name.upper()}"
        draw_typing_interface(game_manager, screen, msg, center_y, max_w)

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
        except curses.error:
            game_manager.log("DrawUI Failed on BUILDING_SELECT")

    elif game_manager.mode == gm.MODE_IDLE:
        # Phase info (left side)
        try:
            phase_str = f"PHASE: {game_manager.phases.current_phase.name} | Day {game_manager.phases.day}"
            threat_str = f"Required Military: {game_manager.threat}"

            screen.addstr(6, (max_w - len(phase_str)) // 2, phase_str, Colors.TEXT.pair | curses.A_BOLD)
            screen.addstr(8, (max_w - len(threat_str)) // 2, threat_str, Colors.TEXT.pair | curses.A_BOLD)
        except curses.error:
            game_manager.log("DrawUI failed on IDLE")


def draw_typing_interface(game_manager: GameManager, screen, title: str, start_y: int, max_w: int):
    """
    Draws the typing interface including colored text for correct/mistakes
    """
    try:
        screen.addstr(start_y - 2, (max_w - len(title)) // 2, title, Colors.TEXT.pair | curses.A_DIM)
        wpm_message = f"Your WPM is: {game_manager.wpm:.02f}"
        screen.addstr(start_y - 1, (max_w - len(wpm_message)) // 2 + len(title), wpm_message,
                      Colors.TEXT.pair | curses.A_DIM)
        mistakes_message = f"Your accuracy is: {game_manager.mistake_ratio:.2%}"
        screen.addstr(start_y - 1, (max_w - len(mistakes_message)) // 2 - len(title), mistakes_message,
                      Colors.TEXT.pair | curses.A_DIM)

        start_x = (max_w - len(game_manager.current_text)) // 2
        if start_x < 0:
            start_x = 0

        for i, char in enumerate(game_manager.current_text):
            color = Colors.TEXT.pair
            # Check if the character is correctly typed
            if i < len(game_manager.current_input):
                if game_manager.current_input[i] == char:
                    color = Colors.SUCCESS.pair  # Correct
                elif char == ' ' and game_manager.current_input[i] != ' ':
                    color = Colors.ERROR.pair  # Incorrect (space)
                    screen.addch(start_y + 1, start_x + i, '¯', color)  # Red overline ASCII char for wrong space
                else:
                    color = Colors.ERROR.pair  # Incorrect
            screen.addch(start_y, start_x + i, char, color | curses.A_BOLD)

        cursor_idx = len(game_manager.current_input)
        if cursor_idx <= len(game_manager.current_text):
            screen.addch(start_y + 1, start_x + cursor_idx, '^', Colors.TEXT.pair)
    except curses.error:
        game_manager.log("DrawTypingInterface failed")


def main(screen):
    """
    Main function that sets all curses requirements and handles the main game loop
    """
    curses.curs_set(0)
    curses.raw()
    curses.start_color()
    Colors.init()
    screen.nodelay(True)
    game_manager = gm.GameManager(KEYBOARD_LAYOUT)
    try:
        curses.set_escdelay(1)
    except AttributeError:
        os.environ.setdefault('ESCDELAY', '1')
    while True:
        draw(screen, game_manager)
        try:
            key = screen.getch()
        except curses.error:
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
