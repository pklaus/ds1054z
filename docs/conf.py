#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ds1054z documentation build configuration file

import sys
import os
import shlex

# General information about the project.
project = 'ds1054z'
copyright = '2015, Philipp Klaus'
author = 'Philipp Klaus'
version = 'v0.3.dev'
release = 'v0.3.dev'

extensions = ['sphinx.ext.autodoc',]
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
language = 'en'
exclude_patterns = ['_build']
add_module_names = True
pygments_style = 'sphinx'
#keep_warnings = True
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if not on_rtd:
    # https://docs.readthedocs.org/en/latest/theme.html
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}
html_domain_indices = False
html_use_index = False
html_show_sourcelink = False
html_show_sphinx = False
htmlhelp_basename = 'ds1054z_doc'

# -- Options for LaTeX output ---------------------------------------------
latex_documents = [
  (master_doc, 'ds1054z.tex', 'ds1054z Documentation',
   'Philipp Klaus', 'manual'),
]
