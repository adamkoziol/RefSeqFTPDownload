#!/usr/bin/env python
from setuptools import setup, find_packages
__author__ = 'adamkoziol'

setup(
    name="RefseqDownloader",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    license='MIT',
    author='Adam Koziol',
    author_email='adam.koziol@inspection.gc.ca',
    description='Script to download refseq release or refseq assemblies in a slightly parallel fashion',
    url='https://github.com/adamkoziol/RefSeqFTPDownload',
    long_description=open('README.md').read(),
    install_requires=['pycurl',
                      'biopython >= 1.65'],
)
