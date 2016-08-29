"""tellmewhen timing thread.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version."""

import time
import queue

from .log import log
from .option import option_defns


def error (msg):
    log('worker:', msg)


def timer_next_time (e, trigger, last):
    return last + e.sep_time + trigger.time


def init_timer (options, e, trigger):
    t = timer_next_time(
        e, trigger, time.time() - options[option_defns.start_delay])
    return (t, e, trigger)


def start_event (options, name, timers, events):
    if name not in events:
        error('tried to start unknown event: {}'.format(repr(name)))
    else:
        # reset timer if already exists
        for trigger in events[name].triggers:
            timers[trigger] = init_timer(options, events[name], trigger)


def cancel_event (name, timers, events):
    if name not in events:
        error('tried to cancel unknown event: {}'.format(repr(name)))
    else:
        for trigger in events[name].triggers:
            try:
                del timers[trigger]
            except KeyError:
                error('tried to cancel not running event: {}'.format(repr(name)))
                break


def timer_times (options, timers):
    subsequent_t = None
    by_t = reversed(sorted(timers.values(), key=lambda timer: timer[0]))

    for t, e, trigger in by_t:
        real_t = t
        if subsequent_t is not None:
            latest_t = subsequent_t - options[option_defns.min_cmd_separation]
            # move this timer earlier if the next one is too near
            if latest_t < t:
                log('adjust event: {} ({:+.3f})'.format(e, latest_t - t))
                real_t = latest_t

        subsequent_t = real_t
        yield (real_t, (t, e, trigger))


def next_timer_time (options, timers):
    times = reversed(list(timer_times(options, timers)))
    try:
        return next(times)[0] - time.time()
    except StopIteration:
        return None


def process_timers (options, timers):
    now = time.time()

    for real_t, (t, e, trigger) in timer_times(options, timers):
        if real_t <= now:
            log('trigger event: {} ({:+.3f})'.format(e, -trigger.time))
            e.trigger()
            new_t = timer_next_time(e, trigger, t - trigger.time)
            timers[trigger] = (new_t, e, trigger)


def run (events, options, cmd_queue):
    events = {e.name: e for e in events}
    timers = {}

    while True:
        try:
            cmd = cmd_queue.get(timeout=next_timer_time(options, timers))
        except queue.Empty:
            pass
        else:
            log('received command:', repr(cmd))
            if cmd == 'quit':
                break
            elif cmd == 'cancel':
                timers = {}
            elif cmd.startswith('start'):
                start_event(options, cmd[len('start '):], timers, events)
            elif cmd.startswith('cancel'):
                cancel_event(cmd[len('cancel '):], timers, events)
            else:
                error('received unknown command: {}'.format(repr(cmd)))

        process_timers(options, timers)
