"""tellmewhen logging.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version."""

import sys
import time


def log (*args):
    t = time.time()
    formatted_time = '[{}.{:03}]'.format(
        time.strftime('%H:%M:%S', time.gmtime(t)),
        int((t % 1) * 1000))
    print(formatted_time, *args, file=sys.stderr)
