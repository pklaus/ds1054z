
ds1054z
=======

This package allows you to connect to your Rigol DS1054Z
oscilloscope via Ethernet. It comes with a class to use
in your own scripts as well as with a command line tool.

Installation
------------

Installing it is dead simple:

    pip install ds1054z

ds1054z depends on [python-vxi11](https://github.com/python-ivi/python-vxi11)
which should automatically get installed along with itself.

To `--save-screen` shots with the CLI tool, it also needs Pillow,
and to be able to automatically discover the IP address of the scope
on your local network, which needs zeroconf, those requirements will
be installed alongside if you specify those extras when installing:

    pip install ds1054z[savescreen,discovery]

Usage
-----

The command line tool this package comes with is called `ds1054z`:

    philipp@lion$ ds1054z --help
    
    usage: ds1054z [-h] [--discover] [--save-screen IMG_FILENAME]
                   [--overlay RATIO] [--properties PROPERTIES]
                   [--operate {run,stop,single,tforce}] [--shell] [--verbose]
                   [--debug]
                   [device]
    
    CLI for the DS1054Z scope by Rigol
    
    positional arguments:
      device                The device string. Typically the IP address of the
                            oscilloscope. Will try to discover a single (!) scope
                            on the network if you leave it out.
    
    optional arguments:
      -h, --help            show this help message and exit
      --discover, -d        Discover and list scopes in your network and exit
      --save-screen IMG_FILENAME, -i IMG_FILENAME
                            Save an image of the screen
      --overlay RATIO, -o RATIO
                            Dim on-screen controls in --save-screen with a mask
                            (default ratio: 0.5)
      --properties PROPERTIES, -p PROPERTIES
                            Query properties of the DS1054Z instance (separated by
                            a comma)
      --operate {run,stop,single,tforce}
                            Operate essential oscilloscope functions
      --shell, -s           Start an interactive shell to control your scope.
      --verbose, -v         More verbose output
      --debug               Enable debugging output

Or use the DS1054Z class in your own code:

    from ds1054z import DS1054Z
    
    scope = DS1054Z('192.168.0.23')
    print("Connected to: ", scope.idn)
    
    print("displayed channels: ", str(scope.displayed_channels))


Author
------

* Philipp Klaus

Resources
---------

* This Python package was inspired by [DS1054Z_screen_capture](https://github.com/RoGeorge/DS1054Z_screen_capture).
* There is a Qt4 based GUI interface for the scope called [DSRemote](http://www.teuniz.net/DSRemote/).

