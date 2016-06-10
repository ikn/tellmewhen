"""tellmewhen command-line interface.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version."""

import argparse
import json

from . import event, option
all_option_defns = list(option.option_defns.__dict__.values())

VERSION = '0.1.0-next'


def check (valid):
    if not valid:
        raise ValueError('invalid config')


def validate_config_triggers (triggers):
    check(isinstance(triggers, list))
    for t in triggers:
        check(isinstance(t, dict))
        check(set(t.keys()) == set(['offset_time']))

        check(isinstance(t['offset_time'], (int, float)))


def validate_config_events (events):
    check(isinstance(events, list))
    for e in events:
        check(isinstance(e, dict))
        check((set(e.keys()) ==
                set(['name', 'command', 'separation_time', 'triggers'])))

        check(isinstance(e['name'], str))
        check((isinstance(e['command'], list) and len(e['command']) > 0 and
                all(isinstance(w, str) for w in e['command'])))
        check((isinstance(e['separation_time'], (int, float)) and
                e['separation_time'] > 0))
        validate_config_triggers(e['triggers'])

    assert(len(set(e['name'] for e in events)) == len(events))


def read_config (file_obj):
    config = json.load(file_obj)
    file_obj.close()
    check(isinstance(config, dict))
    check(set(config.keys()) == set(['events']))
    return config


def opt_var_name (o):
    return 'option_' + o.name


def add_opt (p, o, *args, **kwargs):
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

    config_events = sum([read_config(config_file_obj)['events']
                         for config_file_obj in args.config], [])
    validate_config_events(config_events)
    event_defns = [
        event.Event(e['name'], e['command'], e['separation_time'],
                    [event.Trigger(t['offset_time']) for t in e['triggers']])
        for e in config_events
    ]

    raw_options = {}
    for o in all_option_defns:
        raw_options[o.name] = getattr(args, opt_var_name(o))
    options = option.Options(raw_options)

    return (event_defns, options)
