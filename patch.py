import sys
from importlib import abc

def patch_pathlib():
    try:
        import pathlib
    except ImportError:
        return
    
    if hasattr(pathlib, 'Sequence'):
        return
    
    import collections.abc
    sys.modules['collections'].Sequence = collections.abc.Sequence

patch_pathlib()