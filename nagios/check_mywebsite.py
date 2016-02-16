#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Check my Website plugin.

Usage:
  check_mywebsite.py [(-v | --verbose)] [--proxy=<proxy>] [--url=<url>] [-e] [-f | -g] <check_id>
  check_mywebsite.py (-h | --help)
  check_mywebsite.py (-V | --version)

Options:
  -f               Display Nagios perfdata.
  -g               Display Graphite perfdata.

  -e               Display extra output (Nagios like only).

  --proxy=<proxy>  Proxy URL.
  --url=<url>      API URL.

  -h --help        Show this screen.
  -V --version     Show version.
  -v --verbose     Verbose.
"""

import sys
import time

import logging

__version__ = "0.1.0"

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

try:
    from urllib.parse import urlparse
except:
    # Python 2
    from urlparse import urlparse

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
# Nagios output
###################


def output_nagios(name, timestamp, metrics, arguments, check_id, state_code_str):

    output = state_code_str

    if arguments['-e'] is True:
        status_url = "http://{0}.status.checkmy.ws".format(
            check_id
        )

        console_url = "https://console.checkmy.ws/#/dashboard?_id={0}".format(
            check_id
        )

        output = "{0} [<a href='{1}'>status page</a>] [<a href='{2}'>console</a>]".format(
            output,
            status_url,
            console_url
        )

    if not arguments['-f'] or not metrics:
        return output

    perfdata = []

    means = {}
    sums = {}

    for (metric, values) in metrics.items():
        for (location, value) in values.items():

            #  Data for the availabilty rate of the website ( Ok: 100 Warning: 50 Critical: 0 )
            if metric in ('state'):
                perfdata.append(
                    perfdata2string(metric, value, '%', min=0, max=100)
                )

            elif metric in ('webtesttime'):
                perfdata.append(
                    perfdata2string(metric, value, 'ms', min=0)
                )

            elif metric in ('httptime', 'dnstime'):
                means[metric] = means.get(metric, 0) + value
                sums[metric] = sums.get(metric, 0) + 1

                perfdata.append(
                    perfdata2string(location, value, 'ms', min=0)
                )

            elif metric in ('yslow_page_load_time'):
                perfdata.append(
                    perfdata2string(metric, value, 'ms', min=0)
                )

            elif metric in ('yslow_score'):
                perfdata.append(
                    perfdata2string(metric, value, min=0,  max=100)
                )

            else:
                perfdata.append(
                    perfdata2string(metric, value)
                )

    # Add means
    for metric, value in means.items():
        mean = value / sums[metric]
        perfdata.append(
            perfdata2string("%s_mean" % metric, mean, 'ms', min=0)
        )

    # Build Perfdata
    logger.debug("Perfdata: %s", perfdata)

    perfdata = [m for m in perfdata if len(m)]
    perfdata = " ".join(perfdata)

    output = "{0} | {1}".format(
        output,
        perfdata
    )

    return output

###################
# Graphite output
###################


def output_graphite(name, timestamp, metrics_states, metrics_httptime, metrics_metas):
    output = ""

    # Httptime by location
    for (location, value) in metrics_httptime.items():
        location = location.replace(":", ".").lower()

        metric = "cmws.{0}.httptime.{1} {2} {3}\n".format(
            name,
            location,
            value,
            timestamp
        )

        output += metric

    # States by location
    for (location, value) in metrics_states.items():
        location = location.replace(":", ".").lower()

        metric = "cmws.{0}.states.{1} {2} {3}\n".format(
            name,
            location,
            value,
            timestamp
        )

        output += metric

    # Metas
    for (label, value) in metrics_metas.items():
        metric = "cmws.{0}.metas.{1} {2} {3}\n".format(
            name,
            label,
            value,
            timestamp
        )

        output += metric

    # Remove last \n
    if len(output):
        output = output[:-1]

    return output

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
    proxy = arguments.get("--proxy", None)

    if arguments['--verbose'] is True:
        logger.setLevel(logging.DEBUG)

    logger.debug("Command line arguments:\n%s", arguments)

    logger.debug("Proxy: %s", proxy)

    url = arguments.get("--url", None)
    logger.debug("URL: %s", url)

    # Get status from API
    client = CheckmywsClient(proxy=proxy, url=url)

    try:
        status = client.status(check_id)

    except Exception as err:
        print(err)
        sys.exit(3)

    logger.debug("Raw:\n%s\n", status)

    # Grab informations
    metas = status.get('metas', {})
    timestamp = metas.get("lastcheck", int(time.time()))
    url = urlparse(status["url"])
    name = url.netloc.replace(":", ".")

    logger.debug("URL: %s", url)
    logger.debug("Name: %s", name)

    # Grab state
    state = status.get('state', 3)
    state_str = status.get("state_str", state)
    state_code_str = status.get("state_code_str", state_str)

    # Invalid state
    if state < 0:
        state = 3

    logger.debug("State: %s (%s)", state, state_str)

    # Extract metrics_states
    metrics_states = status.get('states', {})
    logger.debug("Metrics_states: %s", metrics_states)

    # Extract Perfdata
    lastvalues = status.get('lastvalues', {})

    # Convert metas to metric
    #for label in ('yslow_page_load_time'):
    #    value = metas.get(label, None)
    #    if value is not None:
    #        lastvalues[label]['backend'] = value

    # Build output
    if arguments['-g']:
        output = output_graphite(
            name, timestamp, lastvalues
        )

    else:
        output = output_nagios(
            name, timestamp, lastvalues,
            arguments, check_id, state_code_str
        )

    # Display and quit
    print(output)
    sys.exit(state)


if __name__ == '__main__':
    main()
