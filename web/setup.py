import pathlib, os, sys
import setuptools
from setuptools import Command, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

# This call to setup() does all the work
setup(
    name="coreMS-app",
    version="3.0.1",
    description="Data processing, and annotation for small molecular analysis by mass spec",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.pnnl.gov/mass-spectrometry/corems-app",
    author="Corilo, Yuri",
    author_email="corilo@pnnl.gov",
    license="BSD",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],

    install_requires=required,

)
