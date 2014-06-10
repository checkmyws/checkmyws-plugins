#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Check my Website plugin.

Usage:
  check_mywebsite.py [(-v | --verbose)] [--proxy=<proxy>] [-f] <check_id>
  check_mywebsite.py (-h | --help)
  check_mywebsite.py (-V | --version)

Options:
  -f               Display perfdata.
  --proxy=<proxy>  Proxy URL.

  -h --help        Show this screen.
  -V --version     Show version.
  -v --verbose     Verbose.
"""

__version__ = "0.1.0"

import sys

import logging
logging.basicConfig(format='%(levelname)s %(message)s',)
logger = logging.getLogger("plugin")

###################
# Check dependencies
###################

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

###################
# Functions
###################


def perfdata2string(label, value, unit='', warn='', crit='', min='', max=''):
    if not isinstance(value, (int, float)):
        return ""

    return "'{label}'={value}{unit};{warn};{crit};{min};{max}".format(
            label=label,
            value=value,
            unit=unit,
            warn=warn,
            crit=crit,
            min=min,
            max=max
        )

###################
# Main
###################


def main():
    # Parse command line arguments
    arguments = docopt(__doc__)

    # Display version
    if arguments['--version'] is True:
        print("Version: {0}".format(__version__))
        sys.exit(3)

    check_id = arguments["<check_id>"]
    verbose = arguments['--verbose']
    proxy = arguments.get("--proxy", None)

    if verbose is True:
        logger.setLevel(logging.DEBUG)

    logger.debug("Command line arguments:\n%s", arguments)

    logger.debug("Proxy: %s", proxy)

    # Get status from API
    client = CheckmywsClient(proxy=proxy)

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

    # Extract Perfdata
    metas  = status.get('metas', {})
    metrics = status.get('lastvalues', {})
    metrics = metrics.get('httptime', {})
    perfdata = []

    # Build Perfdata string
    logger.debug("Metrics: %s", metrics)
    values = []

    # Response time by location
    for key in metrics:
        value = metrics[key]
        perfdata.append(
            perfdata2string(key, value, 'ms', min=0)
        )
        values.append(value)

    # Mean time
    if len(values):
        mean_time = sum(values)/len(values)
        perfdata.append(
            perfdata2string('mean_time', mean_time, 'ms', min=0)
        )

    # Yslow load time
    yslow_page_load_time = metas.get('yslow_page_load_time', None)
    perfdata.append(
        perfdata2string('yslow_page_load_time', yslow_page_load_time, 'ms', min=0)
    )

    # Yslow score
    yslow_score = metas.get('yslow_score', None)
    perfdata.append(
        perfdata2string('yslow_score', yslow_score, min=0, max=100)
    )

    # Build Perfdata
    logger.debug("Perfdata: %s", perfdata)
    perfdata = [m for m in perfdata if len(m)]
    perfdata = " ".join(perfdata)

    # Build Output
    output = status.get("state_code_str", state_str)

    if mean_time is not None:
        output = "{0}, Mean response time: {1}ms".format(
            output,
            mean_time
        )

    if arguments['-f'] is True and perfdata:
        output = "{0} | {1}".format(
            output,
            perfdata
        )

    # Invalid state
    if state < 0:
        state = 3

    # Print output
    print(output)
    sys.exit(state)


if __name__ == '__main__':
    main()