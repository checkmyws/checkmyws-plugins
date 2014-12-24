# checkmyws-plugins

Plugins for [Check my Website](http://www.checkmy.ws)

# prerequisites

A working setup of shinken (1.4 or 2.x). You also need to install the following python modules :

- docopt
- checkmyws

```
pip install docopt checkmyws
```

# Install pack 

## shinken-1.4

clone this repo and copy the content of checkmywsplugins/shinken/pack-checkmyws/pack/* to /etc/shinken/packs/checkmyws

```
mkdir /etc/shinken/
cp checkmywsplugins/shinken/pack-checkmyws/pack/* to /etc/shinken/packs/checkmyws/
```

Also copy the plugin to your plugins folder 

```
cp checkmywsplugins/shinken/check_mywebsite.py /usr/lib64/nagios/plugins/
chmod +x /usr/lib64/nagios/plugins/check_mywebsite.py
```

## shinken-2.x

shinken install check_mywebsite

# Adding your websites from checkmy.ws to shinken

You only need to create a "fake" host with a single macro. This macro define which websites you want to monitor. It is a coma separated list. Each item of the list is of the form websitename$(website ID)$. 

A complete example : 

```
define host{
    use                         checkmywebsite-ex
    contact_groups        admins
    host_name              Websites
    address                   localhost
    _CHECKMYIDS          www.shinken-solutions.com$(dd91a249-bbd5-40e3-a5a0-2575e9804b54)$,www.shinken.io$(05d582d9-dd3f-48cf-a739-1981305c47a2)$,www.shinken-monitoring.org$(064fa551-739f-4a91-9479-2b2d45f306c2)$,www.shinkenlab.io$(b8549512-1032-4ba6-b891-db953deb8797)$
}



