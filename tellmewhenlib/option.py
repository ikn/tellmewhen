class OptionDefns:
    pass


class Option:
    def __init__ (self, name, parse, default, desc):
        self.name = name
        self.default = default
        self._parse = parse
        self.desc = desc

    def __str__ (self):
        return '<Option {}>'.format(repr(self.name))

    __repr__ = __str__

    def parse (self, value):
        return self._parse(value)


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
