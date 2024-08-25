import sys
from collections import abc

# Patch the pathlib module
import pathlib
if not hasattr(pathlib, 'Sequence'):
    setattr(pathlib, 'Sequence', abc.Sequence)

# Patch the collections module
import collections
if not hasattr(collections, 'Sequence'):
    setattr(collections, 'Sequence', abc.Sequence)

# Patch zipfile module
import zipfile
if not hasattr(zipfile, 'Sequence'):
    setattr(zipfile, 'Sequence', abc.Sequence)

# Patch pkg_resources module
import pkg_resources
if not hasattr(pkg_resources, 'Sequence'):
    setattr(pkg_resources, 'Sequence', abc.Sequence)