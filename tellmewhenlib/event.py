import subprocess


class Trigger:
    def __init__ (self, time):
        self.time = time


class Event:
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
