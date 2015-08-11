Using the Command Line Tool
===========================

This package installs a versatile command line (CLI) tool called ``ds1054z``.

The signature of the command line tool is as follows::

    philipp@lion$ ds1054z --help
    
    usage: ds1054z [-h] [-v] <action> ...
    
    CLI for the DS1054Z scope by Rigol
    
    This tool can be used in very versatile ways.
    Ask it for --help on the individual actions
    and it will tell you how to use them.
    
    positional arguments:
      <action>       Action to perform on the scope:
        discover     Discover and list scopes on your network and exit
        save-screen  Save an image of the screen
        properties   Query properties of the DS1054Z instance
        run          Start the oscilloscope data acquisition
        stop         Stop the oscilloscope data acquisition
        single       Set the oscilloscope to the single trigger mode.
        tforce       Generate a trigger signal forcefully.
        shell        Start an interactive shell to control your scope.
    
    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  More verbose output

You can use it to save the screen of your scope, for example::

    ds1054z save-screen --overlay 0.6

As a result, a file like this will be saved to your current working directory:

.. image:: images/ds1054z-scope-display.png

Note that no oscilloscope IP address was specified in the last command.
This works because the tool performs discovery of DS1000Z devices
on the local network. If it finds a single one, it picks that as your device.

If you have multiple oscilloscopes in your network, or discovery
doesn't work for you (please `file a bug report`_ in that case),
then you can just as well specify its IP address or hostname as an
positional parameter::

    ds1054z save-screen --overlay 0.6 192.168.0.23

.. _file a bug report: https://github.com/pklaus/ds1054z/issues
