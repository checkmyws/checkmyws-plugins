#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check my Website plugin.

Usage:
  check_mywebsite.py [(-v | --verbose)] [-f] <check_id>
  check_mywebsite.py (-h | --help)
  check_mywebsite.py --version

Options:
  -f             Display perfdata.
  -h --help      Show this screen.
  -V --version   Show version.
  -v --verbose   Verbose.
"""

import sys

import logging
logging.basicConfig(format='%(levelname)s %(message)s',)
logger = logging.getLogger("plugin")

try:
    from docopt import docopt

except ImportError:
    print("Please install 'docopt' module ('pip install docopt')")
    sys.exit(3)

try:
    from checkmyws import CheckmywsClient

except ImportError:
    print("Please install 'checkmyws-python' module ('pip install checkmyws-python')")
    sys.exit(3)

# Parse command line arguments
arguments = docopt(__doc__)
check_id = arguments["<check_id>"]

if arguments['--verbose'] is True:
    logger.setLevel(logging.DEBUG)

logger.debug("Command line arguments:\n%s", arguments)

# Get status from API
client = CheckmywsClient()

try:
    status = client.status(check_id)
    
except Exception as err:
    print(err)
    sys.exit(3)

logger.debug("Raw:\n%s\n", status)

# Grab state
state = status.get('state', 3)
state_str = status.get("state_str", state)

logger.debug("State: %s (%s)", state, state_str)

# Build Perfdata string
metrics = status.get('lastvalues', {})
perfdata = metrics.get('httptime', {})
values = []
perfdata_str = []
mean = None

logger.debug("Perfdata: %s", perfdata)

for location in perfdata:
    value = perfdata[location]
    metric = "{0}={1}ms;;;;".format(
        location,
        value
    )
    values.append(value)
    perfdata_str.append(metric)

perfdata_str = " ".join(perfdata_str)

logger.debug("Perfdata string: %s", perfdata_str)

if len(values):
    mean = sum(values)/len(values)

# Build Output
output = status.get("code_str", state_str)

if mean is not None:
    output = "{0}, Mean response time: {1}ms".format(
        output,
        mean
    )

if arguments['-f'] is True and perfdata_str:
    output = "{0} | {1}".format(
        output,
        perfdata_str
    )

# Invalid state
if state < 0:
    state = 3

# Print result
print(output)
sys.exit(state)
