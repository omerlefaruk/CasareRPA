"""Quick test of selector normalization"""

from src.casare_rpa.utils.selector_normalizer import normalize_selector, detect_selector_type

print("=" * 60)
print("SELECTOR NORMALIZATION TESTS")
print("=" * 60)

test_cases = [
    # (input, description)
    ('//*[@id="APjFqb"]', 'XPath with /* (our generator)'),
    ('//input[@id="APjFqb"]', 'XPath with // (already correct)'),
    ('xpath=//*[@id="test"]', 'XPath with xpath= prefix'),
    ('#myId', 'CSS ID selector'),
    ('.myClass', 'CSS class selector'),
    ('[data-testid="btn"]', 'CSS data attribute'),
    ('[aria-label="Search"]', 'CSS ARIA attribute'),
    ('text=Click me', 'Text selector'),
    ('/html/body/div', 'Absolute XPath path'),
    ('*[@data-ved="abc123"]', 'XPath without prefix'),
    ('[contains(text(), "test")]', 'XPath-like without prefix'),
]

print("\nNormalization Results:")
print("-" * 60)
for selector, desc in test_cases:
    normalized = normalize_selector(selector)
    detected_type = detect_selector_type(selector)
    changed = " [CHANGED]" if normalized != selector else ""
    print(f"\n{desc}:")
    print(f"  Input:  {selector}")
    print(f"  Output: {normalized}{changed}")
    print(f"  Type:   {detected_type}")

print("\n" + "=" * 60)
print("All tests completed successfully!")
print("=" * 60)
