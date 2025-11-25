"""
Performance benchmarks for fuzzy search functionality.

Tests speed, memory efficiency, and identifies bottlenecks in the tab search implementation.
"""

import time
import sys
import random
import string
from typing import List, Tuple
from functools import wraps
import statistics

# Import the fuzzy search module
from casare_rpa.utils.fuzzy_search import (
    fuzzy_match, fuzzy_search, highlight_matches,
    _match_word_initials, _smart_subsequence_match, _find_best_match,
    SearchIndex  # New optimized class
)


def benchmark(name: str, iterations: int = 100):
    """Decorator to benchmark a function."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            times = []
            result = None
            for _ in range(iterations):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                end = time.perf_counter()
                times.append((end - start) * 1000)  # Convert to ms

            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0

            print(f"\n[{name}]")
            print(f"  Iterations: {iterations}")
            print(f"  Avg time:   {avg_time:.4f} ms")
            print(f"  Min time:   {min_time:.4f} ms")
            print(f"  Max time:   {max_time:.4f} ms")
            print(f"  Std dev:    {std_dev:.4f} ms")

            return result, avg_time
        return wrapper
    return decorator


def generate_random_node_name(word_count: int = 2) -> str:
    """Generate a random node name like 'Click Element' or 'Browser Launch'."""
    words = [
        "Browser", "Launch", "Click", "Element", "Type", "Text", "Navigate",
        "URL", "Wait", "Timeout", "Variable", "Set", "Get", "Loop", "For",
        "While", "If", "Condition", "Then", "Else", "Switch", "Case", "Break",
        "Continue", "Return", "Function", "Call", "Input", "Output", "Log",
        "Debug", "Error", "Warning", "Info", "Screenshot", "Download", "Upload",
        "File", "Read", "Write", "Delete", "Create", "Update", "Search", "Find",
        "Replace", "Extract", "Parse", "Format", "Convert", "Encode", "Decode",
        "Encrypt", "Decrypt", "Hash", "Validate", "Check", "Test", "Assert",
        "Compare", "Match", "Filter", "Sort", "Group", "Count", "Sum", "Average",
        "Maximum", "Minimum", "Random", "Generate", "Send", "Receive", "Connect",
        "Disconnect", "Open", "Close", "Start", "Stop", "Pause", "Resume", "Cancel"
    ]
    return " ".join(random.choices(words, k=word_count))


def generate_node_items(count: int) -> List[Tuple[str, str, str]]:
    """Generate a list of node items for testing."""
    categories = ["Browser", "Interaction", "Variable", "Control Flow", "Data", "File", "Network", "Desktop"]
    items = []

    for i in range(count):
        category = random.choice(categories)
        name = generate_random_node_name(random.randint(2, 4))
        description = f"Description for {name} node - does something useful"
        items.append((category, name, description))

    return items


# ============================================================================
# Individual Component Benchmarks
# ============================================================================

def test_fuzzy_match_single():
    """Benchmark single fuzzy_match calls."""
    print("\n" + "=" * 70)
    print("BENCHMARK: Single fuzzy_match performance")
    print("=" * 70)

    test_cases = [
        ("b l", "Browser Launch"),           # Word initial match
        ("click", "Click Element"),          # Prefix match
        ("typ", "Type Text"),                # Short prefix
        ("gv", "Get Variable"),              # Word initials without space
        ("browser launch", "Browser Launch"), # Full match
        ("xyz", "Browser Launch"),           # No match
        ("ce", "Click Element"),             # Two letter initials
        ("navurl", "Navigate To URL"),       # Longer subsequence
    ]

    for query, target in test_cases:
        @benchmark(f"fuzzy_match('{query}', '{target}')", iterations=1000)
        def run_test():
            return fuzzy_match(query, target)
        run_test()


def test_word_initial_matching():
    """Benchmark word initial matching specifically."""
    print("\n" + "=" * 70)
    print("BENCHMARK: Word initial matching (_match_word_initials)")
    print("=" * 70)

    test_cases = [
        ("b l", "Browser Launch", "browser launch"),
        ("c e", "Click Element", "click element"),
        ("g t u", "Go To URL", "go to url"),
        ("s v", "Set Variable", "set variable"),
    ]

    for query, target, target_lower in test_cases:
        @benchmark(f"_match_word_initials('{query}')", iterations=1000)
        def run_test():
            return _match_word_initials(query, target, target_lower)
        run_test()


def test_smart_subsequence():
    """Benchmark smart subsequence matching."""
    print("\n" + "=" * 70)
    print("BENCHMARK: Smart subsequence matching (_smart_subsequence_match)")
    print("=" * 70)

    test_cases = [
        ("brwsr", "Browser Launch", "browser launch"),      # Missing vowels
        ("lnch", "Browser Launch", "browser launch"),       # Scattered chars
        ("clkelmnt", "Click Element", "click element"),     # Condensed
        ("typetxt", "Type Text Into Field", "type text into field"),  # Longer
    ]

    for query, target, target_lower in test_cases:
        @benchmark(f"_smart_subsequence_match('{query}')", iterations=500)
        def run_test():
            return _smart_subsequence_match(query, target, target_lower)
        run_test()


# ============================================================================
# Bulk Search Benchmarks
# ============================================================================

def test_fuzzy_search_scaling():
    """Benchmark fuzzy_search with different item counts."""
    print("\n" + "=" * 70)
    print("BENCHMARK: fuzzy_search scaling with item count")
    print("=" * 70)

    queries = ["b l", "click", "var", "loop", "xyz"]
    item_counts = [10, 50, 100, 200, 500, 1000]

    results = {}

    for count in item_counts:
        items = generate_node_items(count)

        @benchmark(f"fuzzy_search with {count} items", iterations=50)
        def run_test():
            total_results = 0
            for q in queries:
                total_results += len(fuzzy_search(q, items))
            return total_results

        _, avg_time = run_test()
        results[count] = avg_time

    # Print scaling analysis
    print("\n--- Scaling Analysis ---")
    base_count = item_counts[0]
    base_time = results[base_count]

    for count in item_counts:
        ratio = count / base_count
        time_ratio = results[count] / base_time
        efficiency = ratio / time_ratio if time_ratio > 0 else 0
        print(f"  {count:4d} items: {results[count]:8.4f} ms  (x{ratio:.1f} items, x{time_ratio:.2f} time, efficiency: {efficiency:.2f})")


def test_query_length_impact():
    """Benchmark impact of query length on performance."""
    print("\n" + "=" * 70)
    print("BENCHMARK: Query length impact on performance")
    print("=" * 70)

    items = generate_node_items(200)

    queries = [
        "b",                    # 1 char
        "bl",                   # 2 chars
        "b l",                  # 3 chars (with space)
        "brow",                 # 4 chars
        "browser",              # 7 chars
        "browser la",           # 10 chars
        "browser launch",       # 14 chars
    ]

    for query in queries:
        @benchmark(f"Query '{query}' ({len(query)} chars)", iterations=100)
        def run_test():
            return fuzzy_search(query, items)
        run_test()


# ============================================================================
# Edge Case Benchmarks
# ============================================================================

def test_worst_case_scenarios():
    """Benchmark worst-case scenarios."""
    print("\n" + "=" * 70)
    print("BENCHMARK: Worst-case scenarios")
    print("=" * 70)

    # Items with many similar prefixes
    similar_items = [
        ("Browser", f"Browser Action {i}", "Description") for i in range(100)
    ]

    @benchmark("Search similar items (100 'Browser Action X')", iterations=50)
    def run_similar():
        return fuzzy_search("browser", similar_items)
    run_similar()

    # Long target strings
    long_items = [
        ("Category", f"This Is A Very Long Node Name With Many Words Number {i}", "Long description here")
        for i in range(100)
    ]

    @benchmark("Search long node names", iterations=50)
    def run_long():
        return fuzzy_search("tiv", long_items)
    run_long()

    # Query with many characters
    items = generate_node_items(100)

    @benchmark("Long query (20+ chars)", iterations=50)
    def run_long_query():
        return fuzzy_search("browser launch element click", items)
    run_long_query()


# ============================================================================
# Memory Usage Analysis
# ============================================================================

def test_memory_usage():
    """Analyze memory usage patterns."""
    print("\n" + "=" * 70)
    print("ANALYSIS: Memory usage patterns")
    print("=" * 70)

    import gc

    # Force garbage collection before measurement
    gc.collect()

    items_sizes = [100, 500, 1000]

    for count in items_sizes:
        items = generate_node_items(count)

        # Measure memory of items list
        items_size = sys.getsizeof(items)
        for item in items:
            items_size += sum(sys.getsizeof(s) for s in item)

        print(f"\n  {count} items:")
        print(f"    Items list memory: ~{items_size / 1024:.2f} KB")

        # Measure result memory
        results = fuzzy_search("b", items)
        results_size = sys.getsizeof(results)
        for r in results:
            results_size += sum(sys.getsizeof(x) for x in r)

        print(f"    Results memory:    ~{results_size / 1024:.2f} KB")


# ============================================================================
# Comparison with Simple Approaches
# ============================================================================

def simple_substring_search(query: str, items: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
    """Simple substring search for comparison."""
    query_lower = query.lower()
    return [item for item in items if query_lower in item[1].lower()]


def test_comparison_with_simple():
    """Compare fuzzy search with simple substring search."""
    print("\n" + "=" * 70)
    print("COMPARISON: Fuzzy search vs Simple substring search")
    print("=" * 70)

    items = generate_node_items(500)
    queries = ["browser", "click", "var", "loop"]

    @benchmark("Simple substring search (500 items)", iterations=100)
    def run_simple():
        results = []
        for q in queries:
            results.extend(simple_substring_search(q, items))
        return results

    @benchmark("Fuzzy search (500 items)", iterations=100)
    def run_fuzzy():
        results = []
        for q in queries:
            results.extend(fuzzy_search(q, items))
        return results

    simple_result, simple_time = run_simple()
    fuzzy_result, fuzzy_time = run_fuzzy()

    print(f"\n  Simple search time: {simple_time:.4f} ms")
    print(f"  Fuzzy search time:  {fuzzy_time:.4f} ms")
    print(f"  Overhead factor:    {fuzzy_time / simple_time:.2f}x")


def test_search_index_vs_fuzzy_search():
    """Compare SearchIndex vs fuzzy_search for repeated queries."""
    print("\n" + "=" * 70)
    print("COMPARISON: SearchIndex vs fuzzy_search (repeated queries)")
    print("=" * 70)

    item_counts = [100, 500, 1000]
    queries = ["b l", "click", "var", "loop", "typ", "browser"]

    for count in item_counts:
        items = generate_node_items(count)

        # Build index once (measure separately)
        start = time.perf_counter()
        index = SearchIndex(items)
        index_build_time = (time.perf_counter() - start) * 1000

        print(f"\n--- {count} items (index build: {index_build_time:.2f} ms) ---")

        @benchmark(f"fuzzy_search ({count} items)", iterations=50)
        def run_fuzzy():
            results = []
            for q in queries:
                results.extend(fuzzy_search(q, items))
            return results

        @benchmark(f"SearchIndex.search ({count} items)", iterations=50)
        def run_indexed():
            results = []
            for q in queries:
                results.extend(index.search(q))
            return results

        _, fuzzy_time = run_fuzzy()
        _, indexed_time = run_indexed()

        speedup = fuzzy_time / indexed_time if indexed_time > 0 else 0
        print(f"  Speedup: {speedup:.2f}x faster with SearchIndex")


def test_search_index_scaling():
    """Test how SearchIndex scales with item count."""
    print("\n" + "=" * 70)
    print("BENCHMARK: SearchIndex scaling")
    print("=" * 70)

    queries = ["b l", "click", "var", "loop", "xyz"]
    item_counts = [10, 50, 100, 200, 500, 1000]

    results = {}

    for count in item_counts:
        items = generate_node_items(count)
        index = SearchIndex(items)

        @benchmark(f"SearchIndex.search with {count} items", iterations=50)
        def run_test():
            total_results = 0
            for q in queries:
                total_results += len(index.search(q))
            return total_results

        _, avg_time = run_test()
        results[count] = avg_time

    # Print scaling analysis
    print("\n--- Scaling Analysis (SearchIndex) ---")
    base_count = item_counts[0]
    base_time = results[base_count]

    for count in item_counts:
        ratio = count / base_count
        time_ratio = results[count] / base_time
        efficiency = ratio / time_ratio if time_ratio > 0 else 0
        print(f"  {count:4d} items: {results[count]:8.4f} ms  (x{ratio:.1f} items, x{time_ratio:.2f} time, efficiency: {efficiency:.2f})")


# ============================================================================
# Highlight Performance
# ============================================================================

def test_highlight_performance():
    """Benchmark highlight_matches performance."""
    print("\n" + "=" * 70)
    print("BENCHMARK: highlight_matches performance")
    print("=" * 70)

    texts_and_positions = [
        ("Browser Launch", [0, 8]),
        ("Click Element", [0, 6]),
        ("This Is A Very Long Node Name With Many Words", [0, 5, 10, 15, 20, 25, 30]),
        ("Short", [0]),
    ]

    for text, positions in texts_and_positions:
        @benchmark(f"highlight '{text[:20]}...' ({len(positions)} positions)", iterations=1000)
        def run_highlight():
            return highlight_matches(text, positions)
        run_highlight()


# ============================================================================
# Main Runner
# ============================================================================

def run_all_benchmarks():
    """Run all benchmarks."""
    print("\n" + "=" * 70)
    print("FUZZY SEARCH PERFORMANCE BENCHMARK SUITE")
    print("=" * 70)

    # Individual component tests
    test_fuzzy_match_single()
    test_word_initial_matching()
    test_smart_subsequence()

    # Bulk search tests
    test_fuzzy_search_scaling()
    test_query_length_impact()

    # Edge cases
    test_worst_case_scenarios()

    # Memory analysis
    test_memory_usage()

    # Comparisons
    test_comparison_with_simple()
    test_highlight_performance()

    # NEW: SearchIndex optimizations
    test_search_index_vs_fuzzy_search()
    test_search_index_scaling()

    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_all_benchmarks()
