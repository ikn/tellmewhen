"""tellmewhen timing thread.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version."""

import time
import queue

from .log import log
from .option import option_defns


class Timer:
    """wrapping a trigger with timing information specific to a worker

next_time: unixtime at which this trigger will occur
e: event.Event containing the trigger
trigger: event.Trigger
"""

    def __init__ (self, next_time, e, trigger):
        self.next_time = next_time
        self.event = e
        self.trigger = trigger


def error (msg):
    """log an error message"""
    log('worker:', msg)


def timer_next_time (e, trigger, last):
    """determine when a timer should run

e: event.Event
trigger: event.Trigger
last: unixtime when the timer last ran
"""
    return last + e.sep_time + trigger.time


def init_timer (options, e, trigger):
    """create a new timer

options: option.Options
e: event.Event
trigger: event.Trigger
"""
    # the timer 'last ran' according to the configured start delay
    last = time.time() - options[option_defns.start_delay]
    t = timer_next_time(e, trigger, last)
    return Timer(t, e, trigger)


def start_event (options, name, timers, events):
    """handle a 'start' event

options: option.Options
name: event name
timers: `Timer` lookup by `event.Trigger`
events: `event.Event` lookup by name
"""
    if name not in events:
        error('tried to start unknown event: {}'.format(repr(name)))
    else:
        # reset timer if already exists
        for trigger in events[name].triggers:
            timers[trigger] = init_timer(options, events[name], trigger)


def cancel_event (name, timers, events):
    """handle a 'cancel' event

name: event name
timers: `Timer` lookup by `event.Trigger`
events: `event.Event` lookup by name
"""
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
    """determine when timers should occur, in order, respecting min separation

options: option.Options
timers: `Timer` lookup by `event.Trigger`

Returns an iterator of `(t, timer)` tuples, sorted earliest `t` first, where:

t: unixtime at which `timer` should occur
timer: `Timer`
"""
    subsequent_t = None
    by_t = reversed(sorted(timers.values(), key=lambda timer: timer.next_time))

    for timer in by_t:
        real_t = t = timer.next_time
        if subsequent_t is not None:
            latest_t = subsequent_t - options[option_defns.min_cmd_separation]
            # move this timer earlier if the next one is too near
            if latest_t < t:
                log('adjust event: {} ({:+.3f})'.format(
                    timer.event, latest_t - t))
                real_t = latest_t

        subsequent_t = real_t
        yield (real_t, timer)


def next_timer_time (options, timers):
    """determine when next timer will occur

options: option.Options
timers: `Timer` lookup by `event.Trigger`

Returns unixtime or `None`.
"""
    times = reversed(list(timer_times(options, timers)))
    try:
        return next(times)[0] - time.time()
    except StopIteration:
        return None


def process_timers (options, timers):
    """run triggers according to timers and reset triggered timers

options: option.Options
timers: `Timer` lookup by `event.Trigger`
"""
    now = time.time()

    for real_t, timer in timer_times(options, timers):
        e = timer.event
        trigger = timer.trigger
        if real_t <= now:
            log('trigger event: {} ({:+.3f})'.format(e, -trigger.time))
            try:
                e.trigger()
            except Exception as err:
                log('failed to run command:', err)
            new_t = timer_next_time(e, trigger, timer.next_time - trigger.time)
            # replace with an updated timer
            timers[trigger] = Timer(new_t, e, trigger)


def run (events, options, cmd_queue):
    """start a command processing loop

events: list of `event.Event` giving supported events
options: `option.Options`
cmd_queue: `threading.Queue` used for receiving commands
"""
    # `event.Event` lookup by name
    events = {e.name: e for e in events}
    # `Timer` lookup by `event.Trigger`
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
