#!/usr/bin/env

import os
import versioneer
from setuptools import setup


def recurse_data_files(rootdir, extn=None):
    datfiles = []
    for root, _, files in os.walk(rootdir):
        for ff in files:
            if extn is None or extn in ff:
                datfiles.append(os.path.join('..', root, ff))
    return datfiles


with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

config = dict(
    name='eniius',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author='Duc Le',
    author_email='duc.le@stfc.ac.uk',
    description='A utility for embedding neutron instrument information using (nx)spe files.',
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=['eniius', 'eniius.mccode'],
    install_requires=[
        'numpy',
        'nexusformat>=0.7.8',
        'PyChop @ git+https://github.com/g5t/pychop.git@main',
        'mccode @ git+ssh://git@github.com/g5t/mccode-antlr.git',
    ],
    extras_require = {},
    url="https://github.com/mducle/eniius",
    zip_safe=False,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Physics",
    ]
)

data_files = recurse_data_files(os.path.join(os.path.dirname(__file__), 'eniius', 'instruments'))
config['package_data'] = {'eniius': data_files}
setup(**config)