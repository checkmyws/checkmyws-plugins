# Nagios plugin

## Dependencies

    pip install checkmyws-python docopt
    
## Usage

```
$ ./check_mywebsite.py -h
Check my Website plugin.

Usage:
  check_mywebsite.py [(-v | --verbose)] [-f] <check_id>
  check_mywebsite.py (-h | --help)
  check_mywebsite.py --version

Options:
  -f             Display perfdata.
  -h --help      Show this screen.
  -V --version   Show version.
  -v --verbose   Verbose.
```

For the script to work you must enable [status page](http://wooster.checkmy.ws/2014/05/checkmyws-status-page/).
You can found `check_id` in URL of [console](https://console.checkmy.ws)

Ex:
    $ ./check_mywebsite.py -f 95c81e64-48af-4190-acb7-48bd659ea903
    200 Ok, Mean response time: 123ms | DE:FRA:OVH:DC=167ms;;;; FR:PAR:OVH:DC=79ms;;;;
