#!/usr/bin/env python
# -*- coding: utf8 -*-

"""Check my Website to InfluxDB

Usage:
  cmws2influxdb.py [-v] <check_id>... [--influxdb=<influxdb>]

Options:
  -h --help              Show this screen
  -v                     Verbose
  <check_id>             Check id
  --influxdb=<influxdb>  influxdb DSN       [default: influxdb://<user>:<password>@localhost:8086/<database>]
"""

from docopt import docopt
import sys

from influxdb import InfluxDBClient

import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    level=logging.INFO
)

logger = logging.getLogger("plugin")

logging.getLogger("requests").setLevel(logging.WARNING)

try:
    from urllib.parse import urlparse
except:
    # Python 2
    from urlparse import urlparse

try:
    from checkmyws import CheckmywsClient
except:
    logger.error("Error: please install Check my Website client 'pip install checkmyws-python'")
    sys.exit(1)


def influxdb_format(measurement, tags, value, timestamp):
    return {
        "tags": tags,
        "points": [{
            "measurement": measurement,
            "fields": {"value": value},
            "time": timestamp * 1000000000
        }]
    }


def influxdb_write(influxdb, metric):
    logger.debug("InfluxDB Write: %s", metric)

    try:
        influxdb.write(metric, params={'db': influxdb._database})

    except Exception as err:
        logger.error("InfluxDB Impossible to write data %s: %s", metric, err)


def get_data_from_cmws(check_id):
    # Get data from Check my Website
    cmws = CheckmywsClient()
    raw = cmws.status(check_id)

    metrics = []

    # Format data
    url_raw = raw["url"]
    url = urlparse(url_raw)
    hostname = url.netloc.replace(":", ".")
    path = url.path

    if not path:
        path = "/"

    timestamp = raw["metas"]["lastcheck"]

    # Httptime by location
    for (location, value) in raw["lastvalues"]["httptime"].items():
        tags = {
            '_id': check_id,
            'url': url_raw,
            'hostname': hostname,
            'location': location,
            'path': path
        }

        metric = influxdb_format(
            "httptime",
            tags,
            value,
            timestamp
        )

        metrics.append(metric)

    # States by location
    for (location, value) in raw["states"].items():
        tags = {
            '_id': check_id,
            'url': url_raw,
            'hostname': hostname,
            'location': location,
            'path': path
        }

        metric = influxdb_format(
            "state",
            tags,
            value,
            timestamp
        )

        metrics.append(metric)

    # Metas
    blacklist = ('title', 'lastcheck', 'laststatechange_bin', 'laststatechange')
    for (label, value) in raw["metas"].items():
        if label in blacklist:
            continue

        tags = {
            '_id': check_id,
            'url': url_raw,
            'hostname': hostname,
            'path': path
        }

        metric = influxdb_format(
            label,
            tags,
            value,
            timestamp
        )

        metrics.append(metric)

    return metrics

if __name__ == '__main__':
    arguments = docopt(__doc__)

    influxdb_dsn = arguments['--influxdb']
    verbose = arguments['-v']

    if arguments['<check_id>'] is not None:
        check_ids = arguments['<check_id>']

    if verbose:
        logger.setLevel(logging.DEBUG)

    check_ids = set(check_ids)

    logger.debug("influxdb_dsn: %s", influxdb_dsn)
    logger.debug("check_ids: %s", check_ids)

    metrics = []

    for check_id in check_ids:
        metrics += get_data_from_cmws(check_id)

    influxdb = InfluxDBClient.from_DSN(influxdb_dsn, timeout=1)

    for metric in metrics:
        influxdb_write(influxdb, metric)
