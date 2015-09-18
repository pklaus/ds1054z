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
        info         Print information about your oscilloscope
        cmd          Send an SCPI command to the oscilloscope
        save-screen  Save an image of the screen
        save-data    Save the waveform data to a file
        properties   Query properties of the DS1054Z instance
        run          Start the oscilloscope data acquisition
        stop         Stop the oscilloscope data acquisition
        single       Set the oscilloscope to the single trigger mode.
        tforce       Generate a trigger signal forcefully.
        shell        Start an interactive shell to control your scope.
    
    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  More verbose output

Global Options
--------------

You can increase the verbosity of the tool
by stating ``--verbose`` before the action argument

If you want to know what's going on behind the scenes,
and for tracing errors in this software, you might also enable
the debugging output by using the undocumented ``--debug``
parameter. Also put it in front of your action argument.

Saving Screenshots
------------------

You can use the tool to save the screen of your scope, for example::

    ds1054z save-screen --overlay 0.6

As a result, a file like this will be saved to your current working directory:

.. image:: images/ds1054z-scope-display.png

Zeroconf Device Discovery
-------------------------

Note that no oscilloscope IP address was specified in the last command.
This works because the tool performs discovery of DS1000Z devices
on the local network. If it finds a single one, it picks that as your device.

If you have multiple oscilloscopes in your network, or want the cli tool
to perform your action faster (discovery takes about 1 second upfront),
or discovery doesn't work for you (please `file a bug report`_ in that case),
then you can just as well specify the scope by its IP address or hostname
as a positional parameter to most of the actions::

    ds1054z save-screen --overlay 0.6 192.168.0.23

Exporting Data
--------------

You can save the waveform data to a file with the ``save-data`` command::

    ds1054z save-data --filename samples_{ts}.txt

.. _file a bug report: https://github.com/pklaus/ds1054z/issues
