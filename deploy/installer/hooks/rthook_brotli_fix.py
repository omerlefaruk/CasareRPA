# Runtime hook to fix brotlicffi import issue in urllib3
# This runs before any other imports

import sys


# Create a fake brotlicffi module that points to brotli
class FakeBrotlicffi:
    """Fake brotlicffi module that wraps brotli."""

    def __getattr__(self, name):
        import brotli

        return getattr(brotli, name)


# Install fake module before anything imports it
sys.modules["brotlicffi"] = FakeBrotlicffi()
