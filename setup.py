import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
desc = "Prometheus Test Data Generator"

with open(os.path.join(here, 'README.md'), 'r') as fh:
    long_desc = fh.read()

requires = []

setup(name='ptdg',
      author='CJ Niemira',
      author_email='siege@siege.org',
      version='0.1',
      description=desc,
      long_description=long_desc,
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Intended Audience :: System Administrators",
          "License :: Public Domain",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3 :: Only",
          "Topic :: Software Development :: Testing"
      ],
      url='http://github.com/cniemira/ptdg',
      keywords='',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      # setup_requires=['pytest-runner'],
      # tests_require=['pytest'],
      install_requires=requires,
      entry_points="""\
      [console_scripts]
      ptdg = ptdg:main
      """,
      )
