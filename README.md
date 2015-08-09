
# ds1054z

This package allows you to connect to your Rigol DS1054Z
oscilloscope via Ethernet. It comes with a command line tool
as well as with a class to control the scope with your own script.

## Installation

The installation is dead simple:

    pip install ds1054z[savescreen,discovery]

ds1054z depends on [python-vxi11](https://github.com/python-ivi/python-vxi11)
which should automatically get installed along with itself.


For more information on the installation, please consult the [installation section][] of the [package documentation][].

## Features

* Discovering your scope via mDNS / DNS-SD
* Saving Screenshots (incl. adjustable dimming of on-screen controls)
* Running / stopping the scope
* Acquiring waveforms
* ... more to come!

## Usage


### Command Line Tool

This package installs a versatile command line (CLI) tool called `ds1054z`. You can use it to save the screen of your scope, for example:

```bash
ds1054z \
  --save-screen 'default' --overlay 0.6 \
  192.168.0.23
```

As a result, a file like this will be saved to your current working directory:

![oscilloscope screenshot](doc/images/ds1054z-scope-display.png)

Find out more ways to use the CLI tool with `ds1054z --help`

### Developers

If you're into Python programming, use [the DS1054Z class][]
in your own code:

```python
from ds1054z import DS1054Z

scope = DS1054Z('192.168.0.23')
print("Connected to: ", scope.idn)

print("Currently displayed channels: ", str(scope.displayed_channels))
```

Author
------

* Philipp Klaus  
  <philipp.l.klaus@web.de>

Resources
---------

* This Python package was inspired by [DS1054Z_screen_capture](https://github.com/RoGeorge/DS1054Z_screen_capture).
* The device discovery built into this software is largely based on [this code](https://gist.github.com/MerseyViking/c67b7d6ebdda55929fbd) by [MerseyViking / GeoSpark](https://github.com/MerseyViking).
* There is a Qt4 based GUI interface for the scope called [DSRemote](http://www.teuniz.net/DSRemote/).

[installation section]: https://ds1054z.readthedocs.org/en/stable/installation.html
[package documentation]: https://ds1054z.readthedocs.org/en/stable/index.html
[the DS1054Z class]: https://ds1054z.readthedocs.org/en/stable/api/ds1054z.html
