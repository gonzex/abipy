"""
This module installs a hook for the built-in open so that one can detect if there are 
files that have not been closed. To install the hook, import the module in the script
and call install. Example

import open_hook

# Install the hook
open_hook.install()

# Show open files.
open_hook.print_open_files()

# Remove the hook
open_hook.remove()

Initial version taken from
http://stackoverflow.com/questions/2023608/check-what-files-are-open-in-python
"""
from __future__ import print_function, division, unicode_literals

import sys
try:
    import __builtin__
except ImportError:
    # Py3k
    import builtins as __builtin__

# Save the builtin version (do not change!)
_builtin_file = __builtin__.file
_builtin_open = __builtin__.open

# Global variables used to control the logging volume and the log file.
_VERBOSE = 1
_LOGFILE = sys.stdout


def set_options(**kwargs):
    """Set the value of verbose and logfile."""
    verbose = kwargs.get("verbose", None)
    if verbose is not None:
        _VERBOSE = verbose

    logfile = kwargs.get("logfile", None)
    if logfile is not None:
        _LOGFILE = logfile


# Set of files that have been opened in the python code.
_openfiles = set()


def print_open_files(file=sys.stdout):
    """Print the list of the files that are still open."""
    print("### %d OPEN FILES: [%s]" % (len(_openfiles), ", ".join(f._x for f in _openfiles)), file=file)


def num_openfiles():
    """Number of files in use."""
    return len(_openfiles)


def clear_openfiles():
    """Reinitialize the set of open files."""
    _openfiles = set()


class _newfile(_builtin_file):
    def __init__(self, *args, **kwargs):
        self._x = args[0]

        if _VERBOSE: 
            print("### OPENING %s ###" % str(self._x), file=_LOGFILE)

        _builtin_file.__init__(self, *args, **kwargs)
        _openfiles.add(self)

    def close(self):
        if _VERBOSE:
            print("### CLOSING %s ###" % str(self._x), file=_LOGFILE)

        _builtin_file.close(self)
        try:
            _openfiles.remove(self)
        except KeyError:
            print("File %s is not in openfiles set" % self)


def _newopen(*args, **kwargs):
    """Replacement for python open."""
    return _newfile(*args, **kwargs)


def install():
    """Install the hook."""
    __builtin__.file = _newfile
    __builtin__.open = _newopen


def remove():
    """Remove the hook."""
    __builtin__.file = _builtin_file = __builtin__.file
    __builtin__.open = _builtin_open = __builtin__.open


def test_open_hook():
    """Unit tests for open_hook"""
    import unittest
    import tempfile

    py3k = False
    try:
        import __builtin__
    except ImportError:
        py3k = True
        import builtins as __builtin__


    @unittest.skipIf(py3k, "OpenHook not compatible with py3k")
    class OpenHookTest(unittest.TestCase):
        """Test open_hook module."""
        def setUp(self):
            from abipy.tools import open_hook
            self.open_hook = open_hook
            self.open_hook.install()

        def test_open(self):
            """Test if open_hook detects open files."""
            self.assertEqual(self.open_hook.num_openfiles(), 0)

            _, fname = tempfile.mkstemp()
            fh = open(fname)

            self.open_hook.print_open_files()
            self.assertEqual(self.open_hook.num_openfiles(), 1)

        def tearDown(self):
            self.open_hook.remove()
            # Here we should have the __builtin__ version

            self.assertTrue(file is __builtin__.file)
            self.assertTrue(open is __builtin__.open)


if __name__ == "__main__":
    import unittest
    unittest.main()
