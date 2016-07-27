#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='pycoolc',
    description="COOL Language Compiler in Python 3.",
    long_description="PyCOOLC is a feature-complete compiler for the COOL Programming Language, targeting the MIPS 32-bit Architecture and written entirely in Python 3.",
    version='0.0.1',
    author='Ahmad Alhour',
    maintainer='Ahmad Alhour',
    author_email='a.z.alhour@gmail.com',
    license="MIT",
    platforms='Cross Platform',
    url='https://github.com/aalhour/pycoolc',
    packages=[
        'pycoolc',
        'tests'
    ],
    entry_points={
        'console_scripts': [
            'pycoolc = pycoolc.pycoolc:main'
        ],
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Natural Language :: English",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Compilers",
        "License :: OSI Approved :: MIT License"
    ],
    install_requires=['ply']
)

