Using the DS1054Z Class
=======================

The Class :py:class:`ds1054z.DS1054Z` is a very easy and convenient way to
interact with your oscilloscope programmatically.

First, import the class from the :py:mod:`ds1054z` module:

>>> from ds1054z import DS1054Z

Now you're able to instantiate the class providing the host you want to connect to.
This can be an IP address or a VISA resources string:

>>> scope = DS1054Z('192.168.0.21')
>>> # or
>>> scope = DS1054Z('TCPIP::192.168.1.104::INSTR')

More information on the resources string can be found in the `README`_ of the
:py:mod:`vxi11` package which :py:class:`ds1054z.DS1054Z` uses to connect to the scope.

.. _README: https://github.com/python-ivi/python-vxi11/blob/master/README.md#python-vxi-11-readme

You can then check the identification of the device by accessing its :py:attr:`idn` property::

>>> print(scope.idn)

which will print something like ``RIGOL TECHNOLOGIES,DS1054Z,DS1ZA116171318,00.04.03``.

To send a command to the oscilloscope, use the :py:meth`ds1054z.DS1054Z.write` method.
Here we start the scope:

>>> scope.write(":RUN")

Note that for those very basic functions there might already be a convenience function
present. In this case it's called :py:meth:`ds1054z.DS1054Z.run`::

>>> scope.run()

If you want to read back values from the scope, use the :py:meth:`ds1054z.DS1054Z.query` method:

>>> scope.query(":ACQuire:SRATe?")
u'5.000000e+08'

Please note that the answer is given as a (unicode) string here.
You still need to convert the value to a float yourself.

>>> float(scope.query(":ACQuire:SRATe?"))
1000000000.0


