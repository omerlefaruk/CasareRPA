# Geist Fonts

This directory will contain the Geist Sans and Geist Mono font files for Epic 1.2.

## Font Files (to be added)

- `Geist-Regular.ttf`
- `Geist-Medium.ttf`
- `Geist-SemiBold.ttf`
- `GeistMono-Regular.ttf`
- `GeistMono-Medium.ttf`
- `GeistMono-SemiBold.ttf`

## Source

Geist fonts are available at: https://vercel.com/font/geist

## License

Geist is licensed under the SIL Open Font License 1.1.

## PyInstaller Integration

These fonts will be bundled in the PyInstaller build via the datas configuration in:
`deploy/installer/casarerpa.spec`

Add to DATAS:
```python
(str(SRC_DIR / "casare_rpa" / "resources" / "fonts"), "fonts"),
```

## Usage

Fonts are automatically registered at app startup by:
`src/casare_rpa/presentation/canvas/theme/font_loader.py`

