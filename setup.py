# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    import pypandoc
    # for PyPI: Removing images with relative paths and their descriptions:
    import re
    LDESC = open('README.md', 'r').read()
    matches = re.findall(r'\n\n(.*(\n.+)*:\n\n!\[.*\]\((.*\))(\n\n)?)', LDESC)
    for match in matches:
        text, _, link, _ = match
        if text.startswith('http://'): continue
        LDESC = LDESC.replace(text, '')
    # Converting to rst
    LDESC = pypandoc.convert(LDESC, 'rst', format='md')
except (ImportError, IOError, RuntimeError) as e:
    print("Could not create long description:")
    print(str(e))
    LDESC = ''

setup(name='ds1054z',
      version = '0.3.8',
      description = 'Python package and software for the Rigol DS1054Z oscilloscope.',
      long_description = LDESC,
      author = 'Philipp Klaus',
      author_email = 'philipp.l.klaus@web.de',
      url = 'https://github.com/pklaus/ds1054z',
      license = 'GPL',
      packages = ['ds1054z'],
      entry_points = {
          'console_scripts': [
              'ds1054z = ds1054z.cli:main',
          ],
      },
      include_package_data = True,
      zip_safe = True,
      platforms = 'any',
      install_requires = ['python_vxi11'],
      extras_require = {
          'savescreen':  ["Pillow",],
          'discovery':   ["zeroconf",],
      },
      package_data = {
          '': ['resources/*.png'],
      },
      keywords = 'Rigol Oscilloscope DS1054Z',
      classifiers = [
          'Development Status :: 4 - Beta',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Topic :: Scientific/Engineering :: Visualization',
          'Topic :: Scientific/Engineering',
          'Topic :: System :: Hardware :: Hardware Drivers',
          'Intended Audience :: Science/Research',
      ]
)


