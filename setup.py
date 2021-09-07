"""
This file is part of lascar

lascar is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.


Copyright 2018 Manuel San Pedro, Victor Servant, Charles Guillemet, Ledger SAS - manuel.sanpedro@ledger.fr, victor.servant@ledger.fr, charles@ledger.fr

"""

from setuptools import setup, find_packages
import sys

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="lascar",
    version="1.1",
    description="Ledger's Advanced Side-Channel Analysis Repository - Toolsuite for side-channel acquisition, container and analysis by Ledger.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ledger-Donjon/lascar",
    author="Charles Guillemet, Manuel San Pedro, Victor Servant",
    author_email="charles@ledger.fr, manuel.sanpedro@ledger.fr, victor.servant@ledger.fr",
    install_requires=[
        "click",
        "numpy>=1.17,<1.21",
        "h5py",
        "matplotlib",
        "vispy",
        "sklearn",
        "scipy",
        "keras",
        "progressbar2",
        "pytest",
        "numba",
    ],  ## PyQt5 is here as a backend for vispy, this might change in the future
    packages=find_packages(),
    python_requires='>=3.0',
    setup_requires=["pytest-runner",],
    tests_require=["pytest"],
    entry_points={"console_scripts": ["lascarctl=scripts.lascarctl:main"],},
)
