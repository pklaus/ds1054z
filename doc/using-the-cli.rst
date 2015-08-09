Using the Command Line Tool
===========================

This package installs a versatile command line (CLI) tool called ``ds1054z``.
You can use it to save the screen of your scope, for example::

    ds1054z \
      --save-screen 'default' --overlay 0.3 \
      192.168.0.23

As a result, a file like this will be saved to your current working directory:

.. image:: images/ds1054z-scope-display.png


The signature of the command line tool is as follows::

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

