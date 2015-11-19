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


def influxdb_write(influxdb, metric):
    logger.debug("InfluxDB Write: %s", metric)

    try:
        influxdb.write(metric, params={'db': influxdb._database})

    except Exception as err:
        logger.error("InfluxDB Impossible to write data %s: %s", metric, err)

def worker_to_tags(location, worker):
    return {
        'location': location,
        'city': worker['city'],
        'bandwidth': worker['bandwidth'],
        'isp': worker['isp'],
        'country': worker['country']
    }

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
    timestamp = int(timestamp * 1000000000)

    # Extract tags from tags list
    static_tags = raw.get("tags", None)

    if isinstance(static_tags, list):
        static_tags = [t.split(':') for t in static_tags if ':' in t]
        static_tags = dict(static_tags)

    else:
        static_tags = {}

    # Merge tags
    static_tags.update({
        "_id": check_id,
        "url": url_raw,
        "hostname": hostname,
        "path": path
    })

    if raw.get("name", None):
        static_tags['name'] = raw["name"]

    logger.debug("Timestamp:   %s", timestamp)
    logger.debug("Static_tags: %s", static_tags)

    points = []

    # Metrics
    for metric in ("httptime", "dnstime"):
        values = raw["lastvalues"].get(metric, None)

        if values is None:
            continue

        for (location, value) in values.items():
            if asfloat:
                value = float(asfloat)

            worker = raw["workers"][location]

            points.append({
                "tags": worker_to_tags(location, worker),
                "measurement": metric,
                "fields": {"value": value},
                "time": timestamp
            })

    # States by location
    for (location, value) in raw["states"].items():
        if asfloat:
            value = float(asfloat)

        worker = raw["workers"][location]

        points.append({
            "tags": worker_to_tags(location, worker),
            "measurement": "state",
            "fields": {"value": value},
            "time": timestamp
        })

    # Metas
    whitelist = (
        "base64Size",
        "code",
        "contentLength",
        "cssSize",
        "htmlSize",
        "imageSize",
        "jsErrors",
        "jsSize",
        "notFound",
        "otherSize",
        "redirects",
        "requests",
        "webfontSize",
        "yslow_page_load_time",
        "yslow_score"
    )

    for (label, value) in raw["metas"].items():
        if label not in whitelist:
            continue

        if asfloat:
            value = float(asfloat)

        points.append({
            "measurement": label,
            "fields": {"value": value},
            "time": timestamp
        })

    logger.debug("Points: %s", len(points))

    return {"tags": static_tags, "points": points}

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
        metrics.append(
            get_data_from_cmws(check_id, asfloat)
        )

    influxdb = InfluxDBClient.from_DSN(influxdb_dsn, timeout=1)

    for metric in metrics:
        influxdb_write(influxdb, metric)
