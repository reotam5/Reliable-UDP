import curses
import time
from typing import List


class CLI:
    def __init__(self, titles: List[str], values, step=10):
        self.titles = titles
        self.values = values
        self.step = step
        self.running = False

    def display(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(1)
        selection = 0

        stdscr.clear()
        for i, title in enumerate(self.titles):
            stdscr.addstr(i, 0, title)
        stdscr.refresh()

        while self.running:
            for i, item in enumerate(self.values):
                if i == selection:
                    attr = curses.A_NORMAL
                    cursor = ">"
                else:
                    attr = curses.A_NORMAL
                    cursor = " "

                value_str = "{cursor} {name}: {value}{suffix}\n".format(
                    cursor=cursor,
                    name=item["name"],
                    value=item["get_value"](),
                    suffix=item["suffix"],
                )
                stdscr.addstr(i + 3, 0, value_str, attr)

            key = stdscr.getch()
            if key == curses.KEY_UP:
                selection = (selection - 1) % len(self.values)
            elif key == curses.KEY_DOWN:
                selection = (selection + 1) % len(self.values)
            elif key == curses.KEY_LEFT:
                newValue = (
                    self.values[selection]["get_value"]()
                    - self.values[selection]["step"]
                )
                if "min" in self.values[selection]:
                    newValue = max(self.values[selection]["min"], newValue)
                self.values[selection]["set_value"](newValue)
            elif key == curses.KEY_RIGHT:
                newValue = (
                    self.values[selection]["get_value"]()
                    + self.values[selection]["step"]
                )
                if "max" in self.values[selection]:
                    newValue = min(self.values[selection]["max"], newValue)
                self.values[selection]["set_value"](newValue)

            stdscr.refresh()
            time.sleep(0.01)

    def start(self):
        self.running = True
        curses.wrapper(self.display)

    def stop(self):
        self.running = False
