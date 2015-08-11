Installation
============

Installing :py:mod:`ds1054z` is dead simple if you can use
pip to install Python packages::

    pip install ds1054z[savescreen,discovery]
 
The package depends on `python-vxi11`_ for the communication
with the scope. It should automatically get installed along with ds1054z.
 
By specifying ``savescreen`` and ``discovery`` in square brackets
after the package name, you're asking pip to install
the requirements for those extras as well:

- ``savescreen`` makes it possible to use the `save-screen` action with the CLI tool. (Pillow will get installed)
- ``discovery``: To be able to automatically discover the IP address of the scope
  on your local network, this extra will install ``zeroconf``.

If you don't have access to ``pip`` , the installation might be a bit more tricky.
Please let me know how this can be done on your favorite platform
and I will add this information here.

.. _python-vxi11: https://github.com/python-ivi/python-vxi11
