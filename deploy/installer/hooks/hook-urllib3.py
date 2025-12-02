# PyInstaller hook for urllib3 brotli fix
# Forces urllib3 to use brotli instead of brotlicffi

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ["brotli"]
excludedimports = ["brotlicffi"]
