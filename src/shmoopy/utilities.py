from pathlib import Path
import inspect


# Read the package version file
with open(Path(__file__).parent / 'version.txt', 'r') as fid:
    __version__ = fid.readlines()[0].replace('\n', '')


def find_decorated_methods(cls, attribute_name):
    return [name for name, method in inspect.getmembers(cls, inspect.isfunction)
            if hasattr(method, attribute_name)]