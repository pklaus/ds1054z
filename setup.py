# -*- coding: utf-8 -*-

from distutils.core import setup

setup(name='ds1054z',
      version = '0.2.0',
      description = '',
      long_description = '',
      author = 'Philipp Klaus',
      author_email = 'philipp.l.klaus@web.de',
      url = '',
      license = 'GPL',
      packages = ['ds1054z'],
      scripts = ['scripts/ds1054z'],
      include_package_data = True,
      zip_safe = True,
      platforms = 'any',
      requires = ['python_vxi11'],
      keywords = 'usbtmc Rigol Oscilloscope',
      classifiers = [
          'Development Status :: 4 - Beta',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: GPL License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Monitoring',
          'Topic :: System :: Logging',
      ]
)


