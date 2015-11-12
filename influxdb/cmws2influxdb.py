#!/usr/bin/env python
# -*- coding: utf8 -*-

"""Check my Website to InfluxDB

Usage:
  cmws2influxdb.py [-v] [-f] <check_id>... [--influxdb=<influxdb>]

Options:
  -h --help              Show this screen
  -v                     Verbose
  -f                     Force plugin to send values as float
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
except ImportError as err:
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


def get_data_from_cmws(check_id, asfloat=False):
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

    tags = raw.get("tags", None)

    if isinstance(tags, list):
        tags = [t.split(':') for t in tags if ':' in t]
        tags = dict(tags)

    else:
        tags = {}

    tags["_id"] = check_id
    tags["url"] = url_raw
    tags["hostname"] = hostname
    tags["path"] = path

    if raw.get("name", None):
        tags['name'] = raw["name"]

    # Httptime by location
    for (location, value) in raw["lastvalues"]["httptime"].items():
        t = dict(tags)
        t["location"] = location

        if asfloat:
            value = float(asfloat)

        metric = influxdb_format(
            "httptime",
            t,
            value,
            timestamp
        )

        metrics.append(metric)

    # States by location
    for (location, value) in raw["states"].items():
        t = dict(tags)
        t["location"] = location

        if asfloat:
            value = float(asfloat)

        metric = influxdb_format(
            "state",
            t,
            value,
            timestamp
        )

        metrics.append(metric)

    # Metas
    blacklist = (
        'title', 'lastcheck', 'laststatechange_bin', 'laststatechange',
        'dns_expiration_timestamp', 'ssl_cert_expiration_timestamp'
    )
    for (label, value) in raw["metas"].items():
        if label in blacklist:
            continue

        if asfloat:
            value = float(asfloat)

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
    asfloat = arguments['-f']

    if arguments['<check_id>'] is not None:
        check_ids = arguments['<check_id>']

    if verbose:
        logger.setLevel(logging.DEBUG)

    check_ids = set(check_ids)

    logger.debug("influxdb_dsn: %s", influxdb_dsn)
    logger.debug("check_ids: %s", check_ids)

    metrics = []

    for check_id in check_ids:
        metrics += get_data_from_cmws(check_id, asfloat)

    influxdb = InfluxDBClient.from_DSN(influxdb_dsn, timeout=1)

    for metric in metrics:
        influxdb_write(influxdb, metric)
