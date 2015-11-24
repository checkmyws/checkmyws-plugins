
## Requirements

    pip install docopt influxdb checkmyws-python

Check if public access on your `check` is enable, see [Nagios example]([https://github.com/checkmyws/checkmyws-plugins/tree/master/nagios).

## Usage

```
Check my Website to InfluxDB

Usage:
  cmws2influxdb.py [-v] [-f] [--api=<api>] [--influxdb=<influxdb>] <check_id>...

Options:
  -h --help              Show this screen
  -v                     Verbose
  -f                     Force plugin to send values as float
  <check_id>             Check id
  --api=<api>            API URL            [default: https://api.checkmy.ws/api]
  --influxdb=<influxdb>  influxdb DSN       [default: influxdb://<user>:<password>@localhost:8086/<database>]
```

## Example

    python cmws2influxdb.py --influxdb=influxdb://root:rootinfluxdb:8086/cmws c03a4b55-5d14-4701-a27b-774e6a678124
