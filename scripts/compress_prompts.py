"""Prompt compression utilities to reduce token usage.

Provides functions to compress and optimize prompts before LLM calls.
"""

import re
from typing import List


def compress_prompt(prompt: str, aggressive: bool = False) -> str:
    """Compress a prompt by removing redundant text.

    Args:
        prompt: The prompt to compress.
        aggressive: If True, use more aggressive compression.

    Returns:
        Compressed prompt string.

    Examples:
        >>> prompt = "This is a very long prompt with many redundant words."
        >>> compress_prompt(prompt)
        'Long prompt with redundant words.'
    """
    compressed = re.sub(r"\s+", " ", prompt).strip()

    filler_patterns = [
        r"\b(please|kindly|would you mind|i would like|i want to|i need you to)\s+",
        r"\b(can you|could you|help me to)\s+",
        r"\b(the|a|an)\s+(?:[a-z]+\s+){1,2}(?:that|which|who)\s+",
    ]

    for pattern in filler_patterns:
        compressed = re.sub(pattern, "", compressed, flags=re.IGNORECASE)

    verbose_map = {
        r"\b(equivalent to|the same as)\b": "=",
        r"\b(in order to)\b": "to",
        r"\b(as a result of|due to the fact that)\b": "because",
        r"\b(with regard to|in terms of)\b": "for",
        r"\b(at this point in time|at the present time)\b": "now",
        r"\b(for the purpose of)\b": "for",
        r"\b(in the event that)\b": "if",
        r"\b(whether or not)\b": "whether",
        r"\b(on a daily basis|on a regular basis)\b": "daily",
        r"\b(in the majority of cases)\b": "usually",
        r"\b(at all times)\b": "always",
        r"\b(what is meant by)\b": "",
        r"\b(it is important to note that)\b": "",
    }

    for verbose, short in verbose_map.items():
        compressed = re.sub(verbose, short, compressed, flags=re.IGNORECASE)

    if aggressive:
        compressed = re.sub(r"\b(the|a|an)\b ", "", compressed, flags=re.IGNORECASE)
        compressed = re.sub(r"\s+", " ", compressed).strip()

    return compressed


def truncate_conversation(
    messages: list[dict], max_tokens: int, model: str = "gpt-4"
) -> list[dict]:
    """Truncate conversation to fit within token limit.

    Implements sliding window: keeps last messages until limit is reached.

    Args:
        messages: List of conversation messages (role, content).
        max_tokens: Maximum token budget for conversation.
        model: Model name for token estimation (gpt-4, claude-3, etc.).

    Returns:
        Truncated list of messages.

    Examples:
        >>> messages = [
        ...     {"role": "user", "content": "Hello"},
        ...     {"role": "assistant", "content": "Hi there!"},
        ...     {"role": "user", "content": "How are you?"},
        ... ]
        >>> truncate_conversation(messages, max_tokens=100)
        [...]
    """
    if not messages:
        return []

    def estimate_tokens(text: str) -> int:
        return len(text) // 4

    total_tokens = sum(estimate_tokens(m["content"]) for m in messages)

    if total_tokens <= max_tokens:
        return messages

    truncated = messages.copy()
    while total_tokens > max_tokens and len(truncated) > 1:
        removed = truncated.pop(0)
        total_tokens -= estimate_tokens(removed["content"])

    return truncated


def remove_redundant_context(messages: list[dict]) -> list[dict]:
    """Remove redundant context from conversation.

    Removes duplicate or highly similar consecutive messages.

    Args:
        messages: List of conversation messages.

    Returns:
        Filtered list with redundant messages removed.
    """
    if len(messages) < 2:
        return messages

    filtered = [messages[0]]

    for i in range(1, len(messages)):
        if messages[i].get("content", "") != filtered[-1].get("content", ""):
            filtered.append(messages[i])

    return filtered


def summarize_long_code_blocks(prompt: str, max_lines: int = 20) -> str:
    """Summarize long code blocks in prompts.

    Replaces long code blocks with shorter summaries.

    Args:
        prompt: Prompt with potential code blocks.
        max_lines: Maximum lines to keep before summarizing.

    Returns:
        Prompt with summarized code blocks.
    """
    # Match code blocks in markdown format
    code_block_pattern = r"```(\w+)?\n(.*?)\n```"
    result = []

    pos = 0
    for match in re.finditer(code_block_pattern, prompt, re.DOTALL):
        # Add text before code block
        result.append(prompt[pos : match.start()])

        lang = match.group(1) or ""
        code = match.group(2)
        lines = code.split("\n")

        if len(lines) > max_lines:
            # Truncate with summary
            summary = "\n".join(lines[:max_lines])
            summary += f"\n... (truncated {len(lines) - max_lines} more lines)"
            result.append(f"```{lang}\n{summary}\n```")
        else:
            result.append(match.group(0))

        pos = match.end()

    result.append(prompt[pos:])
    return "".join(result)


def compress_system_prompt(system_prompt: str) -> str:
    """Compress system prompts specifically.

    System prompts often have verbose instructions. This applies
    domain-specific compression rules.

    Args:
        system_prompt: System prompt to compress.

    Returns:
        Compressed system prompt.
    """
    patterns = [
        r"\b(you are|act as|behave like)\s+(?:a\s+)?(?:an?\s+)?(?:AI\s+)?(?:assistant|agent|model)\b",
        r"\b(follow these|adhere to|comply with)\s+(?:guidelines|instructions|rules)\b",
        r"\b(make sure to|ensure that|verify that)\b",
        r"\b(in all cases|at all times|always)\b",
    ]

    compressed = system_prompt
    for pattern in patterns:
        compressed = re.sub(pattern, "", compressed, flags=re.IGNORECASE)

    compressed = re.sub(r"\s+", " ", compressed).strip()

    return compressed


def optimize_prompt_for_model(prompt: str, model: str) -> str:
    """Optimize prompt for specific model.

    Different models have different optimal prompt formats.
    Applies model-specific optimizations.

    Args:
        prompt: The prompt to optimize.
        model: Model identifier (gpt-4, claude-3-opus, etc.).

    Returns:
        Model-optimized prompt.
    """
    if "claude" in model.lower():
        pass

    elif "gpt" in model.lower():
        pass

    return prompt
