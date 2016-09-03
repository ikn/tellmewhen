"""tellmewhen event representations.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version."""

import subprocess


class Trigger:
    """time relative to an event occurrence at which to trigger its effects

time: trigger time relative to event occurrence, in seconds
"""

    def __init__ (self, time):
        self.time = time


class Event:
    """a timer that occurs on a fixed period, with effects

name: identifying name
cmd: command to execute when the event's effects are triggered, as taken by
     `subprocess.Popen`
sep_time: time between occurrences
triggers: list of `Trigger`
"""
    def __init__ (self, name, cmd, sep_time, triggers):
        self.name = name
        self.cmd = cmd
        self.sep_time = sep_time
        self.triggers = triggers

    def __str__ (self):
        return '<Event {}>'.format(repr(self.name))

    __repr__ = __str__

    def trigger (self):
        subprocess.Popen(self.cmd)
