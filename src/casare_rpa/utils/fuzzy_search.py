"""
Fuzzy search utilities for node search functionality.

Provides simple but effective fuzzy matching for node names.
"""

from typing import List, Tuple, Optional


def fuzzy_match(query: str, target: str) -> Tuple[bool, int, List[int]]:
    """
    Check if query matches target using fuzzy logic.
    
    Matches if all query characters appear in target in order (case-insensitive).
    Returns match status, score (lower is better), and matched character positions.
    
    Examples:
        "b l" matches "Browser Launch" (positions [0, 8])
        "c e" matches "Click Element" (positions [0, 6])
        "g v" matches "Get Variable" (positions [0, 4])
    
    Args:
        query: Search query string
        target: Target string to match against
        
    Returns:
        Tuple of (matched: bool, score: int, positions: List[int])
        - matched: True if all query chars found in order
        - score: Lower is better (based on gaps and position)
        - positions: Indices of matched characters in target
    """
    query = query.lower().strip()
    target_lower = target.lower()
    
    if not query:
        return True, 0, []
    
    # If exact substring match, prioritize it highest
    if query in target_lower:
        start_pos = target_lower.index(query)
        positions = list(range(start_pos, start_pos + len(query)))
        # Give best possible score to exact substring matches
        score = -200 + start_pos  # Favor exact matches at start of string
        return True, score, positions
    
    # Strategy 1: Try matching query parts to word initials (e.g., "b l" -> "Browser Launch")
    # Extract word initials from target
    words = target_lower.split()
    word_initials = [word[0] for word in words if word]
    query_parts = [q for q in query.split() if q]
    
    # Check if query parts match word initials (in any order or as subsequence)
    if len(query_parts) <= len(word_initials):
        # Try to match query parts as a subsequence of word initials
        # e.g., "b l" should match ['l', 'b'] in "Launch Browser" by matching b->browser, l->launch
        matched_positions = []
        used_words = set()
        
        for part in query_parts:
            # Find a word initial that starts with this part
            found = False
            for word_idx, initial in enumerate(word_initials):
                if word_idx not in used_words and initial == part[0]:
                    matched_positions.append(word_idx)
                    used_words.add(word_idx)
                    found = True
                    break
            
            if not found:
                # No matching word initial found for this part
                matched_positions = []
                break
        
        if len(matched_positions) == len(query_parts):
            # All query parts matched to word initials!
            # Find character positions in target
            positions = []
            word_count = 0
            for j, char in enumerate(target_lower):
                if j == 0 or target_lower[j-1] == ' ':
                    if word_count in matched_positions:
                        positions.append(j)
                    word_count += 1
            
            # Score: prioritize word initial matches with very low (best) score
            # Use negative score to ensure word boundary matches always win
            score = -100 + len(query_parts) + sum(matched_positions)  # Favor earlier words
            return True, score, positions
    
    # Strategy 2: Sequential character matching (fallback)
    positions = []
    target_idx = 0
    word_boundary_bonus = 0
    
    for char in query:
        if char == ' ':  # Skip spaces in query
            continue
            
        # Find next occurrence of character
        found = False
        while target_idx < len(target_lower):
            if target_lower[target_idx] == char:
                positions.append(target_idx)
                
                # Check if this is at a word boundary (after space or at start)
                if target_idx == 0 or target_lower[target_idx - 1] in ' -_':
                    word_boundary_bonus -= 50  # Big bonus for word start
                
                target_idx += 1
                found = True
                break
            target_idx += 1
        
        if not found:
            return False, 999999, []
    
    # Calculate score based on:
    # 1. Total character span (positions[-1] - positions[0])
    # 2. First character position (earlier is better)
    # 3. Number of gaps between matched characters
    # 4. Word boundary bonus (negative = better)
    if positions:
        span = positions[-1] - positions[0]
        first_pos = positions[0]
        gaps = sum(positions[i+1] - positions[i] - 1 for i in range(len(positions)-1))
        score = first_pos * 10 + span + gaps + word_boundary_bonus
    else:
        score = 0
    
    return True, score, positions


def fuzzy_search(query: str, items: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str, int, List[int]]]:
    """
    Search items using fuzzy matching.
    
    Args:
        query: Search query string
        items: List of (category, name, description) tuples
        
    Returns:
        List of (category, name, description, score, positions) tuples, sorted by score
    """
    results = []
    
    for category, name, description in items:
        # Try matching against name first
        matched, score, positions = fuzzy_match(query, name)
        
        if matched:
            results.append((category, name, description, score, positions))
        else:
            # Try matching against description
            matched, score, positions = fuzzy_match(query, description)
            if matched:
                # Penalize description matches slightly
                results.append((category, name, description, score + 100, positions))
    
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
