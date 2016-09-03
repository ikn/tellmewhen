"""tellmewhen program options.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version."""


class OptionDefns:
    """used to store all options"""
    pass


class Option:
    """defines an option accepted by the program

name: identifying name
parse: function taking a string and returning a valid value for the option; may
       raise `ValueError`
default: default value for the option
desc: description string
"""

    def __init__ (self, name, parse, default, desc):
        self.name = name
        self.default = default
        self._parse = parse
        self.desc = desc

    def __str__ (self):
        return '<Option {}>'.format(repr(self.name))

    __repr__ = __str__

    def parse (self, value):
        """parse a string and returns a valid value for the option

Raises `ValueError`.
"""
        return self._parse(value)


"""store of available options"""
option_defns = OptionDefns()

option_defns.socket_host = Option('socket_host', str, 'localhost',
    'hostname to listen for commands on')
option_defns.socket_port = Option('socket_port', int, 58732,
    'port to listen for commands on')
option_defns.start_delay = Option('start_delay', float, 1,
    'a `start\' command indicates an event occurred this many seconds ago')
option_defns.min_cmd_separation = Option('min_cmd_separation', float, 2,
    'minimum allowed number of seconds between triggering different events')


class Options:
    """store of values for options provided to the program

values: dict providing a lookup of `Option.name` to option value; raises
        `KeyError` if any names are not in `option_defns`

Supports dict-style item lookup by `Option`.  All options in `option_defns` are
available.
"""

    def __init__ (self, values):
        self._values = {}
        unknown = set(values) - set(option_defns.__dict__)
        if unknown:
            first_unknown = next(iter(unknown))
            raise KeyError('unknown option: {}'.format(repr(first_unknown)))

        for name, defn in option_defns.__dict__.items():
            self._values[defn] = (
                defn.parse(values[name]) if name in values
                else defn.default
            )

    def __getitem__(self, k):
        return self._values[k]
