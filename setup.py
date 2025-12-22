#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='pycoolc',
    description="COOL Language Compiler in Python 3.",
    long_description="""
PyCOOLC is a feature-complete compiler for the COOL Programming Language,
targeting the MIPS 32-bit Architecture and written entirely in Python 3.

Features:
- Complete lexical, syntax, and semantic analysis
- Type inference with SELF_TYPE support
- Constant propagation and dead code elimination
- MIPS 32-bit code generation
- Comprehensive test suite
""",
    version='1.0.0',
    author='Ahmad Alhour',
    maintainer='Ahmad Alhour',
    author_email='a.z.alhour@gmail.com',
    license="MIT",
    platforms='Cross Platform',
    url='https://github.com/aalhour/pycoolc',
    packages=find_packages(exclude=['tests', 'tests.*']),
    entry_points={
        'console_scripts': [
            'pycoolc = pycoolc.pycoolc:main'
        ],
    },
    python_requires='>=3.12',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Compilers",
        "License :: OSI Approved :: MIT License"
    ],
    install_requires=['ply>=3.9'],
    extras_require={
        'dev': [
            'pytest>=7.0',
            'mypy>=1.0',
            'deadcode>=2.4'
        ],
    },
)
