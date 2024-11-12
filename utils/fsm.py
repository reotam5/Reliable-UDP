from enum import Enum


class FSM:
    class STATE(Enum):
        START = "START"
        EXIT = "EXIT"

    def __init__(self, transitions, initial_state, verbose = False):
        self.transitions = transitions
        self.curret_state = initial_state
        self.prev_state = FSM.STATE.START
        self.verbose = verbose


    def run(self):
        while self.curret_state != FSM.STATE.EXIT:
            next_transition = next((item for item in self.transitions if (item['source'] == self.prev_state and item['dest'] == self.curret_state)), None)
            temp_prev = self.prev_state
            temp_current = self.curret_state

            if next_transition:
                self.prev_state = self.curret_state
                if "action" in next_transition and next_transition["action"]:
                    self.curret_state = next_transition["action"]()
                else:
                    self.curret_state = None

                if self.verbose:
                    print("{val1} -> {val2} -> {val3}".format(val1=temp_prev, val2=temp_current, val3=self.curret_state))

            else:
                raise Exception("transition from {val1} to {val2} is not defined".format(val1=self.prev_state, val2=self.curret_state))
