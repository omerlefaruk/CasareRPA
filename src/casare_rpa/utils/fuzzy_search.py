"""
Fuzzy search utilities for node search functionality.

Provides fast and effective fuzzy matching for node names using
a scoring algorithm inspired by fzf and Sublime Text.

Performance optimizations:
- Pre-computed lowercase and character sets for items
- Early termination after finding enough good matches
- Aggressive pre-filtering with character set intersection
- Memoized recursive matching with depth limits
"""

from typing import List, Tuple, Optional, Set, Dict
from functools import lru_cache
from dataclasses import dataclass


# Scoring constants (higher is better for positive, used to compute final score)
SCORE_EXACT_MATCH = 1000
SCORE_PREFIX_MATCH = 500
SCORE_WORD_INITIAL_MATCH = 300
SCORE_CONSECUTIVE_BONUS = 15
SCORE_WORD_START_BONUS = 50
SCORE_CAMEL_CASE_BONUS = 30
SCORE_GAP_PENALTY = -3
SCORE_LEADING_GAP_PENALTY = -1

# Performance tuning constants
MAX_RESULTS_BEFORE_EARLY_EXIT = 20  # Stop searching after finding this many good matches
MAX_RECURSION_DEPTH = 50  # Limit recursion in subsequence matching
GOOD_SCORE_THRESHOLD = -200  # Scores better than this trigger early exit counting


@dataclass(slots=True)
class IndexedItem:
    """Pre-computed data for a searchable item."""
    category: str
    name: str
    description: str
    name_lower: str
    desc_lower: str
    name_chars: Set[str]
    word_starts: List[Tuple[int, str]]  # (position, char) for word initials


class SearchIndex:
    """
    Pre-computed search index for fast fuzzy searching.

    Use this class when searching the same items multiple times
    to avoid repeated preprocessing.
    """

    __slots__ = ('_items', '_indexed')

    def __init__(self, items: List[Tuple[str, str, str]]):
        """
        Create a search index from items.

        Args:
            items: List of (category, name, description) tuples
        """
        self._items = items
        self._indexed: List[IndexedItem] = []
        self._build_index()

    def _build_index(self):
        """Pre-compute all searchable data."""
        for category, name, description in self._items:
            name_lower = name.lower()
            desc_lower = description.lower()

            # Pre-compute character set for quick filtering
            name_chars = set(name_lower)

            # Pre-compute word starts for word initial matching
            word_starts = []
            for i, char in enumerate(name_lower):
                if i == 0 or name_lower[i-1] in ' -_':
                    word_starts.append((i, char))

            self._indexed.append(IndexedItem(
                category=category,
                name=name,
                description=description,
                name_lower=name_lower,
                desc_lower=desc_lower,
                name_chars=name_chars,
                word_starts=word_starts
            ))

    def search(self, query: str, max_results: int = 10) -> List[Tuple[str, str, str, int, List[int]]]:
        """
        Search indexed items using fuzzy matching.

        This is faster than fuzzy_search() for repeated searches on the same items.

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default 10)

        Returns:
            List of (category, name, description, score, positions) tuples
        """
        query = query.lower().strip()
        if not query:
            return [(item.category, item.name, item.description, 0, [])
                    for item in self._indexed[:max_results]]

        query_no_spaces = query.replace(' ', '')
        if not query_no_spaces:
            return [(item.category, item.name, item.description, 0, [])
                    for item in self._indexed[:max_results]]

        query_chars = set(query_no_spaces)
        query_first = query_no_spaces[0]

        results = []
        good_results_count = 0

        for item in self._indexed:
            # Fast pre-filter: check if first char exists
            if query_first not in item.name_chars:
                if query_first not in item.desc_lower:
                    continue

            # More aggressive filter: check if all query chars exist in name
            if query_chars <= item.name_chars:
                # All chars present - try matching name
                matched, score, positions = _fuzzy_match_indexed(
                    query, query_no_spaces, item.name, item.name_lower, item.word_starts
                )
                if matched:
                    results.append((item.category, item.name, item.description, score, positions))
                    if score < GOOD_SCORE_THRESHOLD:
                        good_results_count += 1
                        if good_results_count >= MAX_RESULTS_BEFORE_EARLY_EXIT:
                            break
                    continue

            # Fallback: try description
            matched, score, positions = fuzzy_match(query, item.description)
            if matched:
                results.append((item.category, item.name, item.description, score + 200, positions))

        # Sort by score and limit results
        results.sort(key=lambda x: x[3])
        return results[:max_results]


def _fuzzy_match_indexed(
    query: str,
    query_no_spaces: str,
    target: str,
    target_lower: str,
    word_starts: List[Tuple[int, str]]
) -> Tuple[bool, int, List[int]]:
    """
    Optimized fuzzy match using pre-computed data.

    This is an internal function used by SearchIndex.
    """
    if not query:
        return True, 0, []

    has_spaces = ' ' in query
    mid_match_score = None
    mid_match_positions = None

    # === Strategy 1: Exact substring match at word boundary ===
    if query_no_spaces in target_lower:
        start_pos = target_lower.index(query_no_spaces)
        is_word_start = start_pos == 0 or target_lower[start_pos - 1] in ' -_'

        if is_word_start:
            positions = list(range(start_pos, start_pos + len(query_no_spaces)))
            score = -SCORE_EXACT_MATCH + start_pos
            return True, score, positions
        elif not has_spaces:
            # Store for later comparison with word initials
            mid_match_score = -SCORE_PREFIX_MATCH + start_pos + 50
            mid_match_positions = list(range(start_pos, start_pos + len(query_no_spaces)))

    # === Strategy 2: Word initial matching (using pre-computed word_starts) ===
    initials_result = _match_word_initials_fast(query_no_spaces, word_starts)
    if initials_result[0]:
        return initials_result

    # Return mid-word match if we had one
    if mid_match_score is not None:
        return True, mid_match_score, mid_match_positions

    # === Strategy 3: Smart subsequence matching ===
    return _smart_subsequence_match(query_no_spaces, target, target_lower)


def _match_word_initials_fast(
    query_chars: str,
    word_starts: List[Tuple[int, str]]
) -> Tuple[bool, int, List[int]]:
    """
    Fast word initial matching using pre-computed word starts.
    """
    if not query_chars or not word_starts:
        return False, 999999, []

    positions = []
    used_indices = set()

    for qchar in query_chars:
        found = False
        for idx, (pos, initial) in enumerate(word_starts):
            if idx not in used_indices and initial == qchar:
                positions.append(pos)
                used_indices.add(idx)
                found = True
                break

        if not found:
            return False, 999999, []

    if len(positions) == len(query_chars):
        positions.sort()
        score = -SCORE_WORD_INITIAL_MATCH + sum(positions) // 10
        return True, score, positions

    return False, 999999, []


def fuzzy_match(query: str, target: str) -> Tuple[bool, int, List[int]]:
    """
    Check if query matches target using fuzzy logic.

    Uses a scoring algorithm similar to fzf/Sublime Text:
    - Exact substring matches score highest
    - Prefix matches score very high
    - Word initial matches (e.g., "lb" -> "Launch Browser") score high
    - Consecutive character matches get bonuses
    - Matches at word boundaries get bonuses
    - Gaps between matches incur penalties

    Examples:
        "b l" matches "Browser Launch" (word initials)
        "lb" matches "Launch Browser" (word initials without space)
        "click" matches "Click Element" (prefix)
        "typ" matches "Type Text" (prefix)

    Args:
        query: Search query string
        target: Target string to match against

    Returns:
        Tuple of (matched: bool, score: int, positions: List[int])
        - matched: True if query matches target
        - score: Lower is better (inverted internally for sorting)
        - positions: Indices of matched characters in target
    """
    query = query.lower().strip()
    target_lower = target.lower()

    if not query:
        return True, 0, []

    if not target:
        return False, 999999, []

    # Check if query has spaces (indicating word-level search intent)
    has_spaces = ' ' in query

    # Remove spaces from query for character matching
    query_chars = query.replace(' ', '')

    # === Strategy 1: Exact substring match at word boundary (best) ===
    if query_chars in target_lower:
        start_pos = target_lower.index(query_chars)
        # Check if match starts at word boundary
        is_word_start = start_pos == 0 or target_lower[start_pos - 1] in ' -_'

        if is_word_start:
            # Perfect prefix/word-start match
            positions = list(range(start_pos, start_pos + len(query_chars)))
            score = -SCORE_EXACT_MATCH + start_pos
            return True, score, positions
        elif not has_spaces:
            # Mid-word substring match - lower priority than word initial matches
            positions = list(range(start_pos, start_pos + len(query_chars)))
            # Score it lower than word initial matches
            score = -SCORE_PREFIX_MATCH + start_pos + 50
            # Don't return yet - check if word initials are better
        else:
            # Query has spaces but substring is mid-word - likely not intended
            pass

    # === Strategy 2: Word initial matching ===
    # "lb" or "l b" should match "Launch Browser"
    initials_result = _match_word_initials(query, target, target_lower)
    if initials_result[0]:
        return initials_result

    # If we had a mid-word substring match (no spaces in query), return it now
    if not has_spaces and query_chars in target_lower:
        start_pos = target_lower.index(query_chars)
        is_word_start = start_pos == 0 or target_lower[start_pos - 1] in ' -_'
        if not is_word_start:
            positions = list(range(start_pos, start_pos + len(query_chars)))
            score = -SCORE_PREFIX_MATCH + start_pos + 50
            return True, score, positions

    # === Strategy 3: Smart subsequence matching with scoring ===
    result = _smart_subsequence_match(query_chars, target, target_lower)
    return result


def _match_word_initials(query: str, target: str, target_lower: str) -> Tuple[bool, int, List[int]]:
    """
    Match query against word initials.

    "lb" matches "Launch Browser"
    "b l" matches "Browser Launch"
    "ce" matches "Click Element"
    """
    # Get word start positions and their characters
    word_starts = []  # List of (position, char)
    for i, char in enumerate(target_lower):
        if i == 0 or target_lower[i-1] in ' -_':
            word_starts.append((i, char))

    if not word_starts:
        return False, 999999, []

    # Get query characters (without spaces)
    query_chars = [c for c in query.lower() if c != ' ']

    if not query_chars:
        return False, 999999, []

    # Try to match each query char to a word initial
    # Allow matching in any order for flexibility
    positions = []
    used_words = set()

    for qchar in query_chars:
        found = False
        for idx, (pos, initial) in enumerate(word_starts):
            if idx not in used_words and initial == qchar:
                positions.append(pos)
                used_words.add(idx)
                found = True
                break

        if not found:
            # Try matching to word prefixes (first few chars of each word)
            for idx, (pos, _) in enumerate(word_starts):
                if idx in used_words:
                    continue
                # Check if this word starts with the query char
                if target_lower[pos] == qchar:
                    positions.append(pos)
                    used_words.add(idx)
                    found = True
                    break

        if not found:
            return False, 999999, []

    if len(positions) == len(query_chars):
        # Sort positions for proper highlighting
        positions.sort()
        # Score: prefer matches that use fewer words and earlier positions
        score = -SCORE_WORD_INITIAL_MATCH + sum(positions) // 10
        return True, score, positions

    return False, 999999, []


def _smart_subsequence_match(query: str, target: str, target_lower: str) -> Tuple[bool, int, List[int]]:
    """
    Find the best subsequence match using dynamic programming.

    This finds positions that maximize the score based on:
    - Consecutive matches
    - Word boundary matches
    - Minimal gaps
    """
    if not query:
        return True, 0, []

    n, m = len(query), len(target_lower)

    if n > m:
        return False, 999999, []

    # Find all positions where each query character appears in target
    char_positions = {}
    for i, char in enumerate(target_lower):
        if char not in char_positions:
            char_positions[char] = []
        char_positions[char].append(i)

    # Check if all query characters exist in target
    for char in query:
        if char not in char_positions:
            return False, 999999, []

    # Use recursive search with memoization to find best match
    best_result = _find_best_match(query, target_lower, char_positions, 0, -1, {})

    if best_result is None:
        return False, 999999, []

    score, positions = best_result
    # Invert score (we computed higher=better, but return lower=better)
    return True, -score, positions


def _find_best_match(
    query: str,
    target: str,
    char_positions: dict,
    q_idx: int,
    last_pos: int,
    memo: dict,
    depth: int = 0
) -> Optional[Tuple[int, List[int]]]:
    """
    Recursively find the best matching positions.

    Returns (score, positions) or None if no match.
    Includes depth limiting for performance.
    """
    if q_idx >= len(query):
        return (0, [])

    # Depth limit to prevent exponential blowup on long strings
    if depth > MAX_RECURSION_DEPTH:
        return None

    memo_key = (q_idx, last_pos)
    if memo_key in memo:
        return memo[memo_key]

    char = query[q_idx]
    if char not in char_positions:
        memo[memo_key] = None
        return None

    best_score = None
    best_positions = None
    positions_for_char = char_positions[char]

    # Limit candidates for better performance
    candidates_checked = 0
    max_candidates = 10  # Don't check every occurrence, just the first few

    for pos in positions_for_char:
        if pos <= last_pos:
            continue

        candidates_checked += 1
        if candidates_checked > max_candidates and best_score is not None:
            # We have a good match, skip remaining candidates
            break

        # Calculate score for this position
        pos_score = 0

        # Bonus for consecutive match
        if pos == last_pos + 1:
            pos_score += SCORE_CONSECUTIVE_BONUS
        else:
            # Gap penalty
            gap = pos - last_pos - 1 if last_pos >= 0 else pos
            if last_pos < 0:
                pos_score += gap * SCORE_LEADING_GAP_PENALTY
            else:
                pos_score += gap * SCORE_GAP_PENALTY

        # Bonus for word boundary
        if pos == 0 or target[pos - 1] in ' -_':
            pos_score += SCORE_WORD_START_BONUS
        # Bonus for camelCase boundary
        elif pos > 0 and target[pos].isupper() and target[pos - 1].islower():
            pos_score += SCORE_CAMEL_CASE_BONUS

        # Recurse for remaining query
        sub_result = _find_best_match(query, target, char_positions, q_idx + 1, pos, memo, depth + 1)

        if sub_result is not None:
            sub_score, sub_positions = sub_result
            total_score = pos_score + sub_score

            if best_score is None or total_score > best_score:
                best_score = total_score
                # Build positions list efficiently
                best_positions = [pos] + sub_positions

    if best_score is not None:
        memo[memo_key] = (best_score, best_positions)
        return (best_score, best_positions)

    memo[memo_key] = None
    return None


def fuzzy_search(query: str, items: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str, int, List[int]]]:
    """
    Search items using fuzzy matching.

    Optimized for performance with:
    - Quick prefix check to skip non-matching items
    - Caching of query preprocessing
    - Early exit for exact matches

    Args:
        query: Search query string
        items: List of (category, name, description) tuples

    Returns:
        List of (category, name, description, score, positions) tuples, sorted by score
    """
    query = query.lower().strip()
    if not query:
        return [(cat, name, desc, 0, []) for cat, name, desc in items]

    results = []
    query_chars = set(query.replace(' ', ''))
    query_first = query.replace(' ', '')[0] if query.replace(' ', '') else ''

    for category, name, description in items:
        name_lower = name.lower()

        # Quick check: does target contain first query char?
        if query_first and query_first not in name_lower:
            # Also check description
            desc_lower = description.lower()
            if query_first not in desc_lower:
                continue

        # Try matching against name first
        matched, score, positions = fuzzy_match(query, name)

        if matched:
            results.append((category, name, description, score, positions))
        else:
            # Try matching against description (with penalty)
            matched, score, positions = fuzzy_match(query, description)
            if matched:
                results.append((category, name, description, score + 200, positions))

    # Sort by score (lower is better)
    results.sort(key=lambda x: x[3])

    return results


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
    
    result = []
    pos_set = set(positions)
    
    for i, char in enumerate(text):
        if i in pos_set:
            result.append(f"<b style='color: #FFA500;'>{char}</b>")
        else:
            result.append(char)
    
    return ''.join(result)
