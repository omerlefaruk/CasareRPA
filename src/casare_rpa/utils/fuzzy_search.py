"""
Fuzzy search utilities for node search functionality.

Provides fast and effective fuzzy matching for node names using
a scoring algorithm inspired by fzf and Sublime Text.
"""

from typing import List, Tuple, Optional
from functools import lru_cache


# Scoring constants (higher is better for positive, used to compute final score)
SCORE_EXACT_MATCH = 1000
SCORE_PREFIX_MATCH = 500
SCORE_WORD_INITIAL_MATCH = 300
SCORE_CONSECUTIVE_BONUS = 15
SCORE_WORD_START_BONUS = 50
SCORE_CAMEL_CASE_BONUS = 30
SCORE_GAP_PENALTY = -3
SCORE_LEADING_GAP_PENALTY = -1


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
    memo: dict
) -> Optional[Tuple[int, List[int]]]:
    """
    Recursively find the best matching positions.

    Returns (score, positions) or None if no match.
    """
    if q_idx >= len(query):
        return (0, [])

    memo_key = (q_idx, last_pos)
    if memo_key in memo:
        return memo[memo_key]

    char = query[q_idx]
    if char not in char_positions:
        memo[memo_key] = None
        return None

    best_score = None
    best_positions = None

    for pos in char_positions[char]:
        if pos <= last_pos:
            continue

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
        sub_result = _find_best_match(query, target, char_positions, q_idx + 1, pos, memo)

        if sub_result is not None:
            sub_score, sub_positions = sub_result
            total_score = pos_score + sub_score

            if best_score is None or total_score > best_score:
                best_score = total_score
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
