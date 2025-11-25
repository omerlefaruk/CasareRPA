"""
Blazingly fast fuzzy search for node search functionality.

Optimized for instant responsiveness with:
- O(n) linear matching algorithm (no recursion)
- Prefix caching for incremental typing
- Smart abbreviation matching
- Aggressive early termination
"""

from typing import List, Tuple, Optional, Set, Dict
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class IndexedItem:
    """Pre-computed data for a searchable item."""
    category: str
    name: str
    description: str
    name_lower: str
    name_words: Tuple[str, ...]  # Words in the name
    initials: str  # First char of each word
    all_chars: frozenset  # All unique chars in name_lower


class SearchIndex:
    """
    Pre-computed search index for blazingly fast fuzzy searching.

    Optimizations:
    - Pre-computed lowercase, word lists, and initials
    - Result caching for prefix queries
    - Early termination on good matches
    """

    __slots__ = ('_indexed', '_cache', '_cache_limit')

    def __init__(self, items: List[Tuple[str, str, str]]):
        """
        Create a search index from items.

        Args:
            items: List of (category, name, description) tuples
        """
        self._indexed: List[IndexedItem] = []
        self._cache: Dict[str, List[Tuple[str, str, str, int, List[int]]]] = {}
        self._cache_limit = 100  # Max cached queries
        self._build_index(items)

    def _build_index(self, items: List[Tuple[str, str, str]]):
        """Pre-compute all searchable data."""
        for category, name, description in items:
            name_lower = name.lower()

            # Split into words (by space, dash, underscore, or camelCase)
            words = _split_into_words(name_lower)

            # Build initials from first char of each word
            initials = ''.join(w[0] for w in words if w)

            self._indexed.append(IndexedItem(
                category=category,
                name=name,
                description=description,
                name_lower=name_lower,
                name_words=tuple(words),
                initials=initials,
                all_chars=frozenset(name_lower)
            ))

    def search(self, query: str, max_results: int = 15) -> List[Tuple[str, str, str, int, List[int]]]:
        """
        Search indexed items using optimized fuzzy matching.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of (category, name, description, score, positions) tuples
        """
        query = query.lower().strip()

        if not query:
            # Return first N items when no query
            return [(item.category, item.name, item.description, 0, [])
                    for item in self._indexed[:max_results]]

        # Check cache for exact query or shorter prefix
        cached = self._cache.get(query)
        if cached is not None:
            return cached[:max_results]

        # Remove spaces for matching
        query_chars = query.replace(' ', '')
        if not query_chars:
            return [(item.category, item.name, item.description, 0, [])
                    for item in self._indexed[:max_results]]

        query_set = frozenset(query_chars)
        query_first = query_chars[0]

        results = []

        for item in self._indexed:
            # FAST PRE-FILTER: Skip if first char not in name
            if query_first not in item.all_chars:
                continue

            # Try matching strategies in order of quality
            score, positions = _match_item(query_chars, query_set, item)

            if score < 10000:  # Valid match found
                results.append((item.category, item.name, item.description, score, positions))

        # Sort by score (lower is better)
        results.sort(key=lambda x: x[3])
        results = results[:max_results]

        # Cache result (limit cache size)
        if len(self._cache) >= self._cache_limit:
            # Remove oldest entries
            keys_to_remove = list(self._cache.keys())[:20]
            for k in keys_to_remove:
                del self._cache[k]
        self._cache[query] = results

        return results

    def clear_cache(self):
        """Clear the result cache."""
        self._cache.clear()


def _split_into_words(text: str) -> List[str]:
    """Split text into words by space, dash, underscore, or camelCase."""
    words = []
    current = []

    for i, c in enumerate(text):
        if c in ' -_':
            if current:
                words.append(''.join(current))
                current = []
        elif c.isupper() and current and not current[-1].isupper():
            # camelCase boundary
            words.append(''.join(current))
            current = [c.lower()]
        else:
            current.append(c.lower() if c.isupper() else c)

    if current:
        words.append(''.join(current))

    return words


def _match_item(query: str, query_set: frozenset, item: IndexedItem) -> Tuple[int, List[int]]:
    """
    Match query against item using multiple strategies.
    Returns (score, positions) where lower score is better.
    Score >= 10000 means no match.
    """
    name_lower = item.name_lower

    # Strategy 1: EXACT substring match (best)
    idx = name_lower.find(query)
    if idx != -1:
        is_word_start = idx == 0 or name_lower[idx - 1] in ' -_'
        positions = list(range(idx, idx + len(query)))
        if is_word_start:
            return (idx, positions)  # Score = position (0 is best)
        else:
            return (100 + idx, positions)  # Mid-word match, penalize

    # Strategy 2: INITIALS match (e.g., "lf" -> "List Filter")
    if len(query) <= len(item.initials):
        if item.initials.startswith(query):
            # Perfect initials prefix match
            positions = _get_initial_positions(item.name_words, len(query), item.name_lower)
            return (50 + len(query), positions)
        elif query in item.initials:
            # Initials substring match
            start = item.initials.index(query)
            positions = _get_initial_positions(item.name_words, len(query), item.name_lower, start)
            return (75 + start * 10, positions)

    # Strategy 3: ABBREVIATION match (consecutive chars from word starts)
    abbrev_result = _match_abbreviation(query, item.name_words, item.name_lower)
    if abbrev_result[0] < 10000:
        return abbrev_result

    # Strategy 4: SUBSEQUENCE match (chars in order, anywhere)
    if query_set <= item.all_chars:
        subseq_result = _match_subsequence_fast(query, name_lower)
        if subseq_result[0] < 10000:
            return subseq_result

    return (10000, [])  # No match


def _get_initial_positions(words: Tuple[str, ...], count: int, full_name: str, start: int = 0) -> List[int]:
    """Get positions of first characters of words."""
    positions = []
    pos = 0
    word_idx = 0

    for word in words:
        if word_idx >= start and len(positions) < count:
            positions.append(pos)
        pos += len(word)
        # Account for separator (space, dash, etc.)
        while pos < len(full_name) and full_name[pos] in ' -_':
            pos += 1
        word_idx += 1

    return positions


def _match_abbreviation(query: str, words: Tuple[str, ...], full_name: str) -> Tuple[int, List[int]]:
    """
    Match query as abbreviation of words.

    E.g., "lifl" matches "List Filter" (li from List, fl from Filter)
    """
    if not words:
        return (10000, [])

    positions = []
    query_idx = 0
    name_pos = 0

    for word in words:
        if query_idx >= len(query):
            break

        # Try to match consecutive chars from this word
        word_start = name_pos
        chars_matched = 0

        for i, c in enumerate(word):
            if query_idx < len(query) and query[query_idx] == c:
                positions.append(word_start + i)
                query_idx += 1
                chars_matched += 1
            elif chars_matched > 0:
                # Stop matching from this word once we hit a non-match
                break

        name_pos += len(word)
        # Skip separator
        while name_pos < len(full_name) and full_name[name_pos] in ' -_':
            name_pos += 1

    if query_idx == len(query):
        # All query chars matched
        # Score based on compactness (fewer gaps = better)
        gap_penalty = 0
        for i in range(1, len(positions)):
            gap = positions[i] - positions[i-1] - 1
            if gap > 0:
                gap_penalty += gap * 2
        return (150 + gap_penalty, positions)

    return (10000, [])


def _match_subsequence_fast(query: str, target: str) -> Tuple[int, List[int]]:
    """
    Fast linear subsequence matching.
    Find all query chars in order in target.
    """
    positions = []
    target_idx = 0

    for qchar in query:
        # Find next occurrence of qchar
        found = False
        while target_idx < len(target):
            if target[target_idx] == qchar:
                positions.append(target_idx)
                target_idx += 1
                found = True
                break
            target_idx += 1

        if not found:
            return (10000, [])

    # Score: penalize gaps and late positions
    score = 200  # Base score for subsequence match

    # Bonus for consecutive matches
    consecutive = 0
    for i in range(1, len(positions)):
        if positions[i] == positions[i-1] + 1:
            consecutive += 1
    score -= consecutive * 10

    # Penalty for large gaps
    if positions:
        total_span = positions[-1] - positions[0]
        score += (total_span - len(query)) * 3

        # Penalty for late start
        score += positions[0] * 2

    return (score, positions)


# ============================================================================
# Convenience functions for non-indexed searches
# ============================================================================

def fuzzy_match(query: str, target: str) -> Tuple[bool, int, List[int]]:
    """
    Quick fuzzy match for a single query-target pair.

    Returns:
        Tuple of (matched: bool, score: int, positions: List[int])
    """
    query = query.lower().strip().replace(' ', '')
    if not query:
        return True, 0, []

    target_lower = target.lower()
    words = tuple(_split_into_words(target_lower))
    initials = ''.join(w[0] for w in words if w)

    item = IndexedItem(
        category="",
        name=target,
        description="",
        name_lower=target_lower,
        name_words=words,
        initials=initials,
        all_chars=frozenset(target_lower)
    )

    query_set = frozenset(query)
    score, positions = _match_item(query, query_set, item)

    return (score < 10000, score, positions)


def fuzzy_search(query: str, items: List[Tuple[str, str, str]], max_results: int = 15) -> List[Tuple[str, str, str, int, List[int]]]:
    """
    Search items using fuzzy matching.

    For repeated searches on the same items, use SearchIndex instead
    for better performance.

    Args:
        query: Search query string
        items: List of (category, name, description) tuples
        max_results: Maximum results to return

    Returns:
        List of (category, name, description, score, positions) tuples
    """
    index = SearchIndex(items)
    return index.search(query, max_results)


def highlight_matches(text: str, positions: List[int]) -> str:
    """
    Create HTML string with matched characters highlighted.

    Args:
        text: Original text
        positions: Indices of characters to highlight

    Returns:
        HTML string with <b> tags around matched characters
    """
    if not positions:
        return text

    pos_set = set(positions)
    result = []

    for i, char in enumerate(text):
        if i in pos_set:
            result.append(f"<b style='color: #FFA500;'>{char}</b>")
        else:
            result.append(char)

    return ''.join(result)
