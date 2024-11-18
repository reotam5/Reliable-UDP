from enum import Enum
from typing import Any


class FSM:
    class STATE(Enum):
        START = "START"
        EXIT = "EXIT"

    def __init__(self, transitions, initial_state, verbose = False):
        self.transitions = transitions
        self.curret_state = initial_state
        self.prev_state = FSM.STATE.START
        self.verbose = verbose


    def run(self, *args):
        next_args: Any = args
        while self.prev_state != FSM.STATE.EXIT:
            next_transition = next((item for item in self.transitions if (item['source'] == self.prev_state and item['dest'] == self.curret_state)), None)
            temp_prev = self.prev_state
            temp_current = self.curret_state

            if next_transition:
                self.prev_state = self.curret_state
                if "action" in next_transition and next_transition["action"]:
                    result = next_transition["action"](*next_args)
                    if type(result) is tuple:
                        self.curret_state, *next_args = result
                    else:
                        if self.prev_state == FSM.STATE.EXIT:
                            next_args = (result,)
                        else:
                            self.curret_state = result
                            next_args = ()
                else:
                    self.curret_state = None

                if self.verbose:
                    print("{val1} -> {val2} -> {val3}".format(val1=temp_prev, val2=temp_current, val3=self.curret_state))

            else:
                raise Exception("transition from {val1} to {val2} is not defined".format(val1=self.prev_state, val2=self.curret_state))
        return next_args[0] if len(next_args) > 0 else None
