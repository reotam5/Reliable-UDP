import time
import curses
from typing import List

class CLI():
    def __init__(self, titles: List[str], values, step = 10):
        self.titles = titles
        self.values = values
        self.step = step


    def display(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(1)
        selection = 0 

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Proxy parameters")
            stdscr.addstr(1, 0, "UP/DOWN arrows to select value, LEFT/RIGHT to adjust")

            for i, item in enumerate(self.values):
                if i == selection:
                    attr = curses.A_NORMAL
                    cursor = ">"
                else:
                    attr = curses.A_NORMAL
                    cursor = " "

                value_str = "{cursor} {name}: {value}{suffix}".format(cursor=cursor, name=item["name"], value=item["get_value"](), suffix=item["suffix"])
                stdscr.addstr(i + 3, 0, value_str, attr)

            key = stdscr.getch()
            if key == curses.KEY_UP:
                selection = (selection - 1) % len(self.values)
            elif key == curses.KEY_DOWN:
                selection = (selection + 1) % len(self.values)
            elif key == curses.KEY_LEFT:
                newValue = self.values[selection]['get_value']() - self.values[selection]['step']
                if "min" in self.values[selection]:
                    newValue = max(self.values[selection]['min'], newValue)
                self.values[selection]['set_value'](newValue)
            elif key == curses.KEY_RIGHT:
                newValue = self.values[selection]['get_value']() + self.values[selection]['step']
                if "max" in self.values[selection]:
                    newValue = min(self.values[selection]['max'], newValue)
                self.values[selection]['set_value'](newValue)
        
            stdscr.refresh()
            time.sleep(0.01)

    def start(self):
        curses.wrapper(self.display)


