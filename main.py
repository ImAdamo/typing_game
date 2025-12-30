import curses
import time
import math
from dataclasses import dataclass
from colors import Colors
from resources import Resources
from day_phases import Phases
from buildings import Buildings

NIGHT = "Night"

PRESSED_KEY = 'a'
BUILDINGS = Buildings()


class GameManager:
    def __init__(self):
        self.phases = Phases()
        self.day = 1
        self.resources = Resources()
        self.log_message = "..."

    def log(self, message):
        self.log_message = str(message)


def draw_border(screen, max_h, max_w, curr_phase):
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
        screen.addstr(max_h - 1, max_w - 1, "╝", border_color)

        # Add phase indicator in corners for extra visibility
        screen.addstr(0, 2, f" {curr_phase.name} ", border_color | curses.A_REVERSE)

    except curses.error:
        pass


# TODO: fully rewrite this
# def draw_keyboard(screen, state, max_h, max_w):
#     key_height = 5
#     key_width = 9
#     gap_x = 2
#     gap_y = 1
#
#     total_keyboard_height = len(KEYBOARD_LAYOUT) * (key_height + gap_y)
#     start_y = max_h - total_keyboard_height - 4
#     if start_y < max_h // 2:
#         start_y = max_h // 2
#
#     for row_idx, row_str in enumerate(KEYBOARD_LAYOUT):
#         row_len_px = len(row_str) * (key_width + gap_x)
#         start_x = (max_w - row_len_px) // 2
#
#         # Stagger
#         match row_idx:
#             case 0:
#                 start_x += 0
#             case 1:
#                 start_x += 1
#             case 2:
#                 start_x += 1
#             case 3:
#                 start_x += 2
#
#         current_y = start_y + (row_idx * (key_height + gap_y))
#
#         for i, char in enumerate(row_str):
#             current_x = start_x + (i * (key_width + gap_x))
#             slot = state.keys.get(char)
#
#             # --- Colors ---
#             bg_color = curses.color_pair(2)  # Default Grey
#             is_active = (state.active_key == char)
#
#             # --- Key Press Offset Logic ---
#             draw_y = current_y
#             draw_x = current_x
#             draw_shadow = True
#
#             if is_active:
#                 bg_color = curses.color_pair(3)  # Green Press
#                 draw_y += 1  # Offset down
#                 draw_x += 1  # Offset right
#                 draw_shadow = False  # No shadow when pressed
#
#             elif slot:
#                 if slot.locked:
#                     bg_color = curses.color_pair(7)  # Red Locked
#                 elif slot.activated:
#                     bg_color = curses.color_pair(6)  # Yellow Activated (Wait next phase)
#
#             # Draw the key box (with press offset and shadow logic)
#             draw_rounded_key_box(screen, draw_y, draw_x, key_height, key_width, bg_color, shadow=draw_shadow)
#
#             # Fill the interior
#             for row in range(1, key_height - 1):
#                 try:
#                     screen.addstr(draw_y + row, draw_x + 1, " " * (key_width - 2), bg_color)
#                 except:
#                     pass
#
#             # Character (bottom center)
#             try:
#                 char_x = draw_x + (key_width // 2)
#                 screen.addstr(draw_y + key_height - 2, char_x, char.upper(), bg_color | curses.A_BOLD)
#             except:
#                 pass
#
#             # Content (center)
#             if slot:
#                 if slot.locked:
#                     try:
#                         cost_str = f"${slot.unlock_cost}"
#                         c_x = draw_x + (key_width - len(cost_str)) // 2
#                         screen.addstr(draw_y + 2, c_x, cost_str, bg_color)
#                     except:
#                         pass
#                 elif slot.building:
#                     try:
#                         emoji_x = draw_x + (key_width - 2) // 2
#                         screen.addstr(draw_y + 2, emoji_x, slot.building.emoji, bg_color)
#                     except:
#                         pass


def draw_ui(screen, game_manager, max_h, max_w):
    phase_str = f" PHASE: {game_manager.phases.current_phase.name} | Day {game_manager.day} "
    res_str = str(game_manager.resources)

    try:
        # Phase info (left side)
        screen.addstr(1, 3, phase_str, Colors.TEXT.pair | curses.A_BOLD)

        # Resources (center-right)
        screen.addstr(1, max_w // 2 - len(res_str) // 2, res_str, Colors.TEXT.pair)

        # Help hint (right side)
        hint = "[TAB/ENTER: Next Phase]"
        screen.addstr(1, max_w - len(hint) - 3, hint, Colors.TEXT.pair | curses.A_DIM)
    except curses.error:
        pass

    # TODO: Finish this once I support messages
    # # Message Area
    # if state.message:
    #     try:
    #         c_x = (max_w - len(state.message)) // 2
    #         screen.addstr(3, c_x, state.message, curses.color_pair(state.message_color) | curses.A_BOLD)
    #     except:
    #         pass

    center_y = max_h // 4

    # --- Mode UI ---
    if game_manager.phases.current_phase.name == NIGHT:
        # TODO: figure out if this is correct (seems wrong to have "Night" here)
        # Night Battle Interface
        title = "--- NIGHT PHASE ---"
        try:
            screen.addstr(center_y - 2, (max_w - len(title)) // 2, title,
                          Colors.ERROR.pair | curses.A_BOLD)
            if game_manager.battle_report:  # TODO: finish up battle report and then check this for mistakes
                for i, line in enumerate(game_manager.battle_report):
                    screen.addstr(center_y + i, (max_w - len(line)) // 2, line, Colors.TEXT.pair)
            else:
                msg = "The city sleeps... but something is out there."
                screen.addstr(center_y, (max_w - len(msg)) // 2, msg, Colors.TEXT.pair)
        except:
            pass

    # elif game_manager.mode == 'TYPING_JOB':  # TODO: clean this up when I get to mode
    #     msg = f"ACTIVATING: {game_manager.keys[game_manager.target_key_char].building.name.upper()}"  # TODO: is this correct?
    #     draw_typing_interface(screen, msg, game_manager.target_text, game_manager.current_input, center_y, max_w)
    #
    # elif game_manager.mode == 'TYPING_BUILD':  # TODO: clean this up when I get to mode
    #     if game_manager.pending_building is None:
    #         # Build Menu Table
    #         title = "SELECT BUILDING TO CONSTRUCT"
    #         try:
    #             screen.addstr(center_y - 3, (max_w - len(title)) // 2, title,
    #                           Colors.TEXT.pair | curses.A_BOLD)
    #
    #             # Show typed input
    #             curr_input_str = "".join(game_manager.current_input)
    #             input_lbl = f"CURRENTLY TYPING: {curr_input_str}_"
    #             screen.addstr(center_y - 1, (max_w - len(input_lbl)) // 2, input_lbl, Colors.WARNING.pair)
    #
    #             # Table Header
    #             header = f"{'NAME':<10} {'ICON':<4} {'COST':<6} {'OUTPUT':<15} {'INPUT':<10}"  # TODO: figure out why there are random numbers
    #             table_w = len(header)
    #             start_x = (max_w - table_w) // 2
    #             screen.addstr(center_y + 1, start_x, header, Colors.TEXT.pair | curses.A_UNDERLINE)
    #
    #             # Rows
    #             row_offset = 2
    #             for b in BUILDINGS.get_all_buildings():  # TODO: optimalize
    #                 # Formatting
    #                 output_str = f"+{b.output_amount} {b.output_resource.symbol}"
    #                 input_str = f"-{b.input_amount} {b.input_resource.symbol}" if b.input_resource else "-"
    #                 row_str = f"{b.name:<10} {b.emoji:<4} ${b.cost_money:<5} {output_str:<15} {input_str:<10}"
    #
    #                 # Highlight match  # TODO: WHAT IS ATTR
    #                 attr = Colors.SUCCESS.pair if (
    #                         game_manager.resources['Money'] >= b.cost_money) else Colors.ERROR.pair
    #                 if b.name.lower().startswith(curr_input_str.lower()) and len(curr_input_str) > 0:
    #                     attr = attr | curses.A_REVERSE
    #
    #                 screen.addstr(center_y + row_offset, start_x, row_str, attr)
    #                 row_offset += 1
    #         except:
    #             pass

    else:
        # Idle # TODO: rewrite this beginning sentence to be more senseful
        lines = [
            "CITY MANAGEMENT",
            "Morning/Noon/Evening: Build & Produce",
            "Night: Defend against threats",
            "",
            "Press [Key] to Select",
            "TAB or ENTER to Next Phase"
        ]
        for i, line in enumerate(lines):
            try:
                screen.addstr(center_y + i, (max_w - len(line)) // 2, line, Colors.TEXT.pair)
            except:
                pass


def draw_typing_interface(screen, title, target, current_input, start_y, max_w):
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

        cursor_idx = len(current_input)  # TODO: why cursor_idx? why the x?
        if cursor_idx < len(target):
            screen.addch(start_y + 1, start_x + cursor_idx, '^', Colors.TEXT.pair)
    except:
        pass


def main(screen):
    global PRESSED_KEY
    curses.curs_set(0)
    curses.raw()
    curses.start_color()
    Colors.init()
    screen.nodelay(True)
    gm = GameManager()
    while True:
        screen.erase()
        screen.bkgd(' ', curses.color_pair(1))  # Set background to black
        max_h, max_w = screen.getmaxyx()
        # renderer graphics
        draw_border(screen, max_h, max_w, gm.phases.current_phase)
        # screen.border("║", "║", "═", "═", "╔", "╗", "╚", "╝")
        screen.addstr(0, 0, gm.log_message, Colors.TEXT.pair)

        draw_ui(screen, gm, max_h, max_w)
        # draw_keyboard(screen, gm, max_h, max_w)
        screen.addch(10, 10, PRESSED_KEY, Colors.TEXT.pair)
        screen.refresh()
        try:
            key = screen.getch()
        except:
            key = -1

        if key != -1:  # might not work
            gm.log(key)
            if 32 <= key <= 126:
                PRESSED_KEY = chr(key).lower()
                curses.beep()
                curses.flash()
            # handle input
            if key == 27:  # escape = exit
                break
            pass
        time.sleep(0.01)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
