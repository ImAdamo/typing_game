import curses
from time import sleep, time
import math
from random import randint
from dataclasses import dataclass
from colors import Colors
from resources import Resources
from day_phases import Phases
from buildings import Buildings, BuildingType
from key import Keyboard, Key

# Constants
MODE_IDLE = 'IDLE'
MODE_TYPING = 'TYPING_JOB'
MODE_BUILDING_SELECT = 'TYPING_BUILD'

# Params
KEY_DELAY = 0.1
KEYBOARD_LAYOUT = [
    "`1234567890-=",
    "qwertyuiop[]",
    "asdfghjkl;'",
    "zxcvbnm,./"
]

# Helpers
PRESSED_KEY = 'a'


class GameManager:
    def __init__(self):
        self.phases: Phases = Phases()
        self.resources: Resources = Resources()
        self.buildings = Buildings()
        self.keyboard = Keyboard(KEYBOARD_LAYOUT, self.buildings)
        self.log_message: str = "..."

        self.message: str = ""
        self.message_color: int = Colors.TEXT.pair
        self.battle_report: list[str] | None

        self.mode: str = MODE_IDLE

        self.active_key: Key | None = None
        self.key_press_time: float = 0

        self.current_text: str | None = None
        self.current_input: list[str] = list()

        self.pending_building: BuildingType | None = None

    def resolve_night_battle(self) -> list[str] | None:
        """
        Resolves the night battle based on current military and money resources and day count.
        If it's Night returns a list of strings with victory/loss information or None if it's not Night.
        """
        if self.phases.is_night():
            threat = self.phases.day * 5 + randint(0, self.resources.money.amount // 50)  # TODO: balance ts out
            defense = self.resources.military.amount

            result_str = f"THREAT LEVEL: {threat} | DEFENSE: {defense}"

            if defense >= threat:
                reward = threat * 2
                self.resources.knowledge.add(reward)  # TODO: balance ts out
                return [
                    "VICTORY!",
                    result_str,
                    "The city is safe.",
                    f"Gained {reward} Knowledge from combat experience."
                ]
            else:
                loss = threat - defense
                lost_food = loss * 2
                lost_money = loss * 5  # TODO: balance ts out
                self.resources.food.subtract(lost_food)
                self.resources.money.subtract(lost_money)

                return [
                    "DEFEAT...",
                    result_str,
                    "Raiders breached the defenses!",
                    f"Lost {lost_food} Food and ${lost_money}."
                ]
        else:
            return None

    def interact_key(self, char):
        key = self.keyboard.get(char)
        if self.mode == MODE_IDLE:
            if key.locked:
                if self.resources.money.amount >= key.unlock_cost:
                    key.locked = False
                    self.resources.money.subtract(key.unlock_cost)
                    self.message = f"Key '{key.char.upper()}' unlocked!"
                    self.message_color = Colors.SUCCESS
                else:
                    self.message = f"You need {key.unlock_cost} to unlock '{key.char.upper()}'!"
                    self.message_color = Colors.ERROR
            elif key.building is BuildingType:  # TODO: check if this works
                self.current_text = key.building.name
                self.mode = MODE_TYPING
            elif key.building is None:  # already checks for key locked in earlier if
                self.mode = MODE_BUILDING_SELECT

    def log(self, message):
        self.log_message = str(message)


def draw(screen, game_manager):
    screen.erase()
    screen.bkgd(' ', Colors.TEXT.pair)
    max_h, max_w = screen.getmaxyx()
    # renderer graphics
    draw_border(screen, max_h, max_w, game_manager.phases.current_phase)
    # screen.border("║", "║", "═", "═", "╔", "╗", "╚", "╝")
    screen.addstr(0, 0, game_manager.log_message, Colors.TEXT.pair)
    draw_ui(screen, game_manager, max_h, max_w)
    draw_keyboard(screen, game_manager, max_h, max_w)
    screen.addch(10, 10, PRESSED_KEY, Colors.TEXT.pair)
    screen.refresh()


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
            slot = game_manager.keyboard.get(char)

            # --- Colors ---
            bg_color = Colors.GREY_KEY.pair  # Default Grey
            is_active = (game_manager.active_key == char)

            # --- Key Press Offset Logic ---
            draw_y = current_y
            draw_x = current_x
            draw_shadow = True

            if is_active:
                bg_color = curses.color_pair(3)  # Green Press
                draw_y += 1  # Offset down
                draw_x += 1  # Offset right
                draw_shadow = False  # No shadow when pressed

            elif slot:  # TODO: figure out why we're asking "if slot"
                if slot.locked:
                    bg_color = Colors.WARNING.pair  # Red Locked
                elif slot.activated:
                    bg_color = Colors.ERROR.pair  # Yellow Activated (Wait next phase)

            # Draw the key box (with press offset and shadow logic)
            draw_rounded_key_box(screen, draw_y, draw_x, key_height, key_width, bg_color, shadow=draw_shadow)

            # Fill the interior
            for row in range(1, key_height - 1):
                try:
                    screen.addstr(draw_y + row, draw_x + 1, " " * (key_width - 2), bg_color)
                except:
                    pass

            # Character (bottom center)
            try:
                char_x = draw_x + (key_width // 2)
                screen.addstr(draw_y + key_height - 2, char_x, char.upper(), bg_color | curses.A_BOLD)
            except:
                pass

            # Content (center)
            if slot:  # TODO: figure out why we're asking "if slot"
                if slot.locked:
                    try:
                        cost_str = f"${slot.unlock_cost}"
                        screen.addstr(draw_y + 2, draw_x + (key_width - len(cost_str)) // 2, cost_str, bg_color)
                    except:
                        pass
                elif slot.building is not None:
                    try:
                        screen.addstr(draw_y + 2, draw_x + (key_width - 2) // 2, slot.building.emoji, bg_color)
                    except:
                        pass


def draw_rounded_key_box(stdscr, y, x, h, w, color, shadow=True):
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
            pass

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
        pass


def draw_ui(screen, game_manager, max_h, max_w):
    phase_str = f" PHASE: {game_manager.phases.current_phase.name} | Day {game_manager.phases.day} "
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
    if game_manager.message:
        try:
            c_x = (max_w - len(game_manager.message)) // 2
            screen.addstr(3, c_x, game_manager.message, game_manager.message_color | curses.A_BOLD)
        except:
            pass

    center_y = max_h // 4

    # --- Mode UI ---
    if game_manager.phases.is_night():
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

    # TODO: make this work (target_key_char, key building, target_text,...)
    elif game_manager.mode == MODE_TYPING:  # TODO: clean this up when I get to mode
        msg = f"ACTIVATING: {game_manager.keyboard.keys[game_manager.target_key_char].building.name.upper()}"  # TODO: is this correct?
        draw_typing_interface(screen, msg, game_manager.target_text, game_manager.current_input, center_y, max_w)

    elif game_manager.mode == MODE_BUILDING_SELECT:  # TODO: clean this up when I get to mode
        if game_manager.pending_building is None:
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
                header = f"{'NAME':<10} {'ICON':<4} {'COST':<6} {'OUTPUT':<15} {'INPUT':<10}"  # TODO: clean up this whole drawing with a repr in the Resources dataclass
                table_w = len(header)
                start_x = (max_w - table_w) // 2
                screen.addstr(center_y + 1, start_x, header, Colors.TEXT.pair | curses.A_UNDERLINE)

                # Rows
                row_offset = 2
                for b in game_manager.buildings:
                    # Formatting
                    output_str = f"+{b.output_amount} {b.output_resource.symbol}"
                    input_str = f"-{b.input_amount} {b.input_resource.symbol}" if b.input_resource else "-"
                    row_str = f"{b.name:<10} {b.emoji:<4} ${b.cost_money:<5} {output_str:<15} {input_str:<10}"

                    # Highlight match
                    attr = Colors.SUCCESS.pair if (
                            game_manager.resources['Money'] >= b.cost_money) else Colors.ERROR.pair
                    if b.name.lower().startswith(curr_input_str.lower()) and len(curr_input_str) > 0:
                        attr = attr | curses.A_REVERSE

                    screen.addstr(center_y + row_offset, start_x, row_str, attr)
                    row_offset += 1
            except:
                pass

    elif game_manager.mode == MODE_IDLE:
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

        cursor_idx = len(current_input)  # TODO: why cursor_idx? why the x? why id?
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
        draw(screen, gm)
        try:
            key = screen.getch()
        except:
            key = -1

        if gm.active_key and (time() - gm.key_press_time > KEY_DELAY):
            gm.active_key = None

        key_char = None
        if key != -1:  # might not work
            gm.key_press_time = time()
            gm.log(key)
            if key == 9 or key == 10:
                gm.phases.next_phase()
                gm.battle_report = gm.resolve_night_battle()
            if 32 <= key <= 126:
                key_char = chr(key).lower()
                PRESSED_KEY = key_char
                gm.active_key = key_char
                gm.interact_key(key_char)
                if gm.mode == MODE_BUILDING_SELECT:
                    gm.current_input.append(key_char)
            if key == 27:  # escape = exit
                break
            if key == 263:
                if gm.mode in (MODE_BUILDING_SELECT, MODE_TYPING) and gm.current_input:
                    gm.current_input.pop()
            pass

        # TODO: finish up the logic router into a function in gm

        sleep(0.01)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
