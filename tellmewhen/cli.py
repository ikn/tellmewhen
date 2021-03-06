"""tellmewhen command-line interface.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version."""

import argparse
import json

from . import event, option
all_option_defns = list(option.option_defns.__dict__.values())

VERSION = '1.0.0-next'


class ConfigError (ValueError):
    """indicates that a config file is invalid

msg: reason the config file is invalid
"""

    def __init__ (self, *msg):
        self.msg = msg
        ValueError.__init__(self, ' '.join(map(str, msg)))


def check (valid, source, *msg):
    """assertion method for config validation

valid: bool - fail if False
source: string representing the source of the configuration at this level
msg: message used on failure

Raises `ConfigError`.
"""
    if not valid:
        raise ConfigError(
            'invalid config: {}: {}'.format(source, ' '.join(map(str, msg))))


def check_obj (obj, source, names):
    """check that an item is a dict (JSON object) with the correct properties

source: string representing the source of the configuration at this level
names: expected property names

Raises `ConfigError`.
"""
    check(isinstance(obj, dict), source, 'expected an object')
    check(
        set(obj.keys()) == set(names), source,
        'expected exactly properties: ' +
            ', '.join('`{}`'.format(name) for name in names))


def validate_config_triggers (triggers, source):
    """validate the triggers for an event retrieved from a config file

triggers: unvalidated 'triggers' property
source: string representing the source of the configuration at this level

Raises `ConfigError`.
"""
    check(isinstance(triggers, list), source, 'expected a list')
    for i, t in enumerate(triggers):
        t_source = '{}[{}]'.format(source, i)
        check_obj(t, t_source, ['offset_time'])

        check(isinstance(t['offset_time'], (int, float)),
              t_source + '.offset_time',
              'expected a number')


def validate_config_events (events, source):
    """validate the events retrieved from a config file

events: list of dicts with the correct properties
source: string representing the source of the configuration at this level

Raises `ConfigError`.
"""
    check(isinstance(events, list), source, 'expected a list')
    for i, e in enumerate(events):
        e_source = '{}[{}]'.format(source, i)
        check_obj(e, e_source,
                  ['name', 'command', 'separation_time', 'triggers'])

        check(isinstance(e['name'], str),
              e_source + '.name',
              'expected a string')
        check((isinstance(e['command'], list) and len(e['command']) > 0 and
                all(isinstance(w, str) for w in e['command'])),
              e_source + '.command',
              'expected a non-empty list of strings')
        check((isinstance(e['separation_time'], (int, float)) and
                e['separation_time'] > 0),
              e_source + '.separation_time',
              'expected a number')
        validate_config_triggers(e['triggers'], e_source + '.triggers')

    check(len(set(e['name'] for e in events)) == len(events),
          source,
          'expected unique event names')


def read_config (file_obj, source):
    """read a config file into a list of events

file_obj: open readable file object
source: string representing the source of the configuration at this level

Returns the list retrieved from the file, checking only that each item is a dict
(JSON object) with the correct properties.

Raises `ConfigError`.
"""
    try:
        config = json.load(file_obj)
    except json.JSONDecodeError as e:
        check(False, source, 'invalid JSON:', e)
    file_obj.close()
    check_obj(config, source, ['events'])
    return config


def opt_var_name (o):
    """retrieve the metavar name for a command-line option

o: `option.Option`
"""
    return 'option_' + o.name


def add_opt (p, o, *args, **kwargs):
    """add an option to a command-line argument parser

p: `argparse.ArgumentParser`
o: `option.Option`
args, kwargs: extra arguments for `p.add_argument`; we already set `dest`,
              `type`, `default` and `help`
"""
    # do it like this because of a weird cx_Freeze bug
    opts = {
        'dest': opt_var_name(o),
        'type': o.parse,
        'default': o.default,
        'help': o.desc
    }
    opts.update(kwargs)
    p.add_argument(*args, **opts)


def parse_args ():
    p = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='''
Start the timing server.  Use `tellmewhenc' to run commands - see the README
file for general usage details.
        ''')
    p.add_argument('config', type=argparse.FileType('r'), nargs='+', help='''
path to a configuration file in JSON format describing timers to set up - see
the README file for details on the structure of this file
                   ''')
    p.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

    od = option.option_defns
    add_opt(p, od.socket_host, '-H', '--host', metavar='HOST')
    add_opt(p, od.socket_port, '-p', '--port', metavar='PORT')
    add_opt(p, od.start_delay, '-d', '--start-delay', metavar='SECONDS')
    add_opt(p, od.min_cmd_separation, '--min-event-separation',
            metavar='SECONDS')

    args = p.parse_args()

    # parse the config file into `event.Event` instances
    event_defns = []
    try:
        for config_file_obj in args.config:
            path = config_file_obj.name
            # raises ConfigError
            config_events = read_config(config_file_obj, path)['events']
            # raises ConfigError
            validate_config_events(config_events, path + ': events')
            for e in config_events:
                event_defns.append(event.Event(
                    e['name'], e['command'], e['separation_time'],
                    [event.Trigger(t['offset_time']) for t in e['triggers']]))
    except ConfigError as e:
        p.error(*e.msg)

    else:
        raw_options = {}
        for o in all_option_defns:
            raw_options[o.name] = getattr(args, opt_var_name(o))
        options = option.Options(raw_options)

        return (event_defns, options)
