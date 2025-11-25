"""
Test fuzzy search functionality.
"""

from casare_rpa.utils.fuzzy_search import fuzzy_match, fuzzy_search, highlight_matches, SearchIndex


def test_fuzzy_match():
    """Test basic fuzzy matching."""
    print("Testing fuzzy_match...")
    
    # Test: "b l" should match "Browser Launch"
    matched, score, positions = fuzzy_match("b l", "Browser Launch")
    print(f"  'b l' matches 'Browser Launch': {matched} (score: {score}, positions: {positions})")
    assert matched == True
    
    # Test: "c e" should match "Click Element"
    matched, score, positions = fuzzy_match("c e", "Click Element")
    print(f"  'c e' matches 'Click Element': {matched} (score: {score}, positions: {positions})")
    assert matched == True
    
    # Test: "g v" should match "Get Variable"
    matched, score, positions = fuzzy_match("g v", "Get Variable")
    print(f"  'g v' matches 'Get Variable': {matched} (score: {score}, positions: {positions})")
    assert matched == True
    
    # Test: "typ" should match "Type Text"
    matched, score, positions = fuzzy_match("typ", "Type Text")
    print(f"  'typ' matches 'Type Text': {matched} (score: {score}, positions: {positions})")
    assert matched == True
    
    # Test: "xyz" should NOT match "Browser Launch"
    matched, score, positions = fuzzy_match("xyz", "Browser Launch")
    print(f"  'xyz' matches 'Browser Launch': {matched}")
    assert matched == False
    
    print("✓ All fuzzy_match tests passed!\n")


def test_fuzzy_search():
    """Test fuzzy search with multiple items."""
    print("Testing fuzzy_search...")
    
    items = [
        ("Browser", "Launch Browser", "Open a new browser instance"),
        ("Browser", "Close Browser", "Close the browser"),
        ("Interaction", "Click Element", "Click on an element"),
        ("Interaction", "Type Text", "Type text into an input"),
        ("Variable", "Get Variable", "Retrieve a variable value"),
        ("Variable", "Set Variable", "Set a variable value"),
        ("Navigation", "Go To URL", "Navigate to a URL"),
    ]
    
    # Test: "b l" should prioritize "Browser Launch"
    results = fuzzy_search("b l", items)
    print(f"  Search 'b l':")
    for cat, name, desc, score, pos in results[:3]:
        print(f"    - {name} (score: {score})")
    assert len(results) > 0
    assert results[0][1] == "Launch Browser"  # Should be first result
    
    # Test: "c e" should prioritize "Click Element"
    results = fuzzy_search("c e", items)
    print(f"  Search 'c e':")
    for cat, name, desc, score, pos in results[:3]:
        print(f"    - {name} (score: {score})")
    assert results[0][1] == "Click Element"
    
    # Test: "typ" should find "Type Text"
    results = fuzzy_search("typ", items)
    print(f"  Search 'typ':")
    for cat, name, desc, score, pos in results[:3]:
        print(f"    - {name} (score: {score})")
    assert results[0][1] == "Type Text"
    
    print("✓ All fuzzy_search tests passed!\n")


def test_highlight_matches():
    """Test match highlighting."""
    print("Testing highlight_matches...")

    # Test highlighting
    html = highlight_matches("Browser Launch", [0, 8])
    print(f"  Highlighted 'Browser Launch' at [0, 8]: {html}")
    assert "<b" in html
    assert "B" in html and "L" in html

    print("✓ All highlight_matches tests passed!\n")


def test_search_index():
    """Test SearchIndex optimized search."""
    print("Testing SearchIndex...")

    items = [
        ("Browser", "Launch Browser", "Open a new browser instance"),
        ("Browser", "Close Browser", "Close the browser"),
        ("Interaction", "Click Element", "Click on an element"),
        ("Interaction", "Type Text", "Type text into an input"),
        ("Variable", "Get Variable", "Retrieve a variable value"),
        ("Variable", "Set Variable", "Set a variable value"),
        ("Navigation", "Go To URL", "Navigate to a URL"),
    ]

    # Create index
    index = SearchIndex(items)

    # Test: "b l" should prioritize "Launch Browser"
    results = index.search("b l")
    print(f"  Search 'b l':")
    for cat, name, desc, score, pos in results[:3]:
        print(f"    - {name} (score: {score})")
    assert len(results) > 0
    assert results[0][1] == "Launch Browser"

    # Test: "c e" should find "Click Element"
    results = index.search("c e")
    print(f"  Search 'c e':")
    for cat, name, desc, score, pos in results[:3]:
        print(f"    - {name} (score: {score})")
    assert results[0][1] == "Click Element"

    # Test: max_results limit
    results = index.search("", max_results=3)
    print(f"  Search '' with max_results=3: {len(results)} results")
    assert len(results) == 3

    # Test: empty query returns items up to max_results
    results = index.search("", max_results=10)
    assert len(results) == 7  # Only 7 items in total

    print("✓ All SearchIndex tests passed!\n")


def test_search_index_consistency():
    """Test that SearchIndex returns same results as fuzzy_search."""
    print("Testing SearchIndex consistency with fuzzy_search...")

    items = [
        ("Browser", "Launch Browser", "Open a new browser"),
        ("Browser", "Close Browser", "Close the browser"),
        ("Interaction", "Click Element", "Click on element"),
    ]

    index = SearchIndex(items)

    queries = ["browser", "click", "la"]

    for query in queries:
        index_results = index.search(query, max_results=10)
        fuzzy_results = fuzzy_search(query, items)

        # Compare top results (order might differ slightly due to early termination)
        index_names = [r[1] for r in index_results]
        fuzzy_names = [r[1] for r in fuzzy_results]

        print(f"  Query '{query}':")
        print(f"    Index: {index_names}")
        print(f"    Fuzzy: {fuzzy_names}")

        # At least the top result should match
        if index_names and fuzzy_names:
            # Both should find the same items (possibly different order)
            assert set(index_names) == set(fuzzy_names), f"Mismatch for query '{query}'"

    print("✓ SearchIndex consistency tests passed!\n")


if __name__ == "__main__":
    test_fuzzy_match()
    test_fuzzy_search()
    test_highlight_matches()
    test_search_index()
    test_search_index_consistency()
    print("=" * 60)
    print("All fuzzy search tests passed! ✓")
    print("=" * 60)
