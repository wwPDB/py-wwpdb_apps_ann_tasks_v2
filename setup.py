# File: setup.py
# Date: 6-Oct-2018
#
# Update:
#
import re

from setuptools import find_packages
from setuptools import setup

packages = []
thisPackage = "wwpdb.apps.ann_tasks_v2"

with open("wwpdb/apps/ann_tasks_v2/__init__.py", "r") as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError("Cannot find version information")


setup(
    name=thisPackage,
    version=version,
    description="wwPDB annotation/review/status/validation module backend",
    long_description="See:  README.md",
    author="Ezra Peisach",
    author_email="ezra.peisach@rcsb.org",
    url="https://github.com/rcsb/py-wwpdb_apps_ann_tasks_v2",
    #
    license="Apache 2.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        # 'Development Status :: 5 - Production/Stable',
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    #
    install_requires=[
        "wwpdb.utils.config >= 0.45",
        "wwpdb.apps.wf_engine",
        "wwpdb.io",
        "wwpdb.utils.db >= 0.6",
        "wwpdb.utils.emdb ~= 1.0",
        "wwpdb.utils.wf ~= 0.13",
        "wwpdb.utils.session",
        "mmcif >= 0.25",
        "wwpdb.utils.dp ~= 0.54",
        "wwpdb.utils.detach",
        "wwpdb.utils.nmr >= 0.24",
        "mmcif.utils ~= 0.22",
        "matplotlib",
        "pygal",
    ],
    packages=find_packages(exclude=["wwpdb.apps.tests-ann", "mock-data"]),
    # Enables Manifest to be used
    # include_package_data = True,
    package_data={
        # If any package contains *.md or *.rst ...  files, include them:
        "": ["*.md", "*.rst", "*.txt", "*.cfg"],
    },
    #
    # These basic tests require no database services -
    test_suite="wwpdb.apps.tests-ann",
    tests_require=["tox"],
    #
    # Not configured ...
    extras_require={
        "buster": ["wwpdb.apps.validation ~= 2.3"],
        "dev": ["check-manifest"],
        "test": ["coverage"],
    },
    # Added for
    command_options={"build_sphinx": {"project": ("setup.py", thisPackage), "version": ("setup.py", version), "release": ("setup.py", version)}},
    # This setting for namespace package support -
    zip_safe=False,
)
