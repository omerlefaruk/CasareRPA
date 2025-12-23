# PyInstaller hook for urllib3 brotli fix
# Forces urllib3 to use brotli instead of brotlicffi


hiddenimports = ["brotli"]
excludedimports = ["brotlicffi"]
