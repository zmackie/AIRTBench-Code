"""
Utility functions for AIRTBench SmolagAgents implementation.

These functions replicate the exact behavior of the original AIRTBench util.py module.
"""

import asyncio
import re
import typing as t

T = t.TypeVar("T")


def flatten(list_: t.Sequence[t.Sequence[T]]) -> list[T]:
    """Flatten a nested sequence into a single list.
    
    Args:
        list_: Sequence of sequences to flatten
        
    Returns:
        Single-level list containing all elements in order
    """
    return [item for sublist in list_ for item in sublist]


def majority_vote(list_: list[bool]) -> bool:
    """Return True if more than half of the boolean values are True.
    
    Args:
        list_: List of boolean values
        
    Returns:
        True if strict majority (> 50%) are True, False otherwise
    """
    return sum(list_) > len(list_) // 2


def all_in(str_: str, *checks: str) -> bool:
    """Check if ALL check strings are found in target string (case-insensitive).
    
    Args:
        str_: String to search within
        *checks: Variable number of strings to find
        
    Returns:
        True if all check strings are found, False otherwise
    """
    return all(check in str_.lower() for check in checks)


def any_in(str_: str, *checks: str) -> bool:
    """Check if ANY check string is found in target string (case-insensitive).
    
    Args:
        str_: String to search within
        *checks: Variable number of strings to find
        
    Returns:
        True if any check string is found, False otherwise
    """
    return any(check in str_.lower() for check in checks)


def not_in(str_: str, *checks: str) -> bool:
    """Check if NONE of the check strings are found in target string.
    
    Args:
        str_: String to search within
        *checks: Variable number of strings to check
        
    Returns:
        True if none of the check strings are found, False otherwise
    """
    return not any_in(str_, *checks)


async def enforce_concurrency(coros: t.Sequence[t.Awaitable[T]], limit: int) -> list[T]:
    """Execute coroutines with semaphore-based concurrency limiting.
    
    Args:
        coros: Sequence of awaitable objects
        limit: Maximum number of concurrent executions
        
    Returns:
        List of results in original order
    """
    async def run_coroutine_with_semaphore(semaphore: asyncio.Semaphore, coro: t.Awaitable[T]) -> T:
        async with semaphore:
            return await coro
    
    semaphore = asyncio.Semaphore(limit)
    return await asyncio.gather(*(run_coroutine_with_semaphore(semaphore, coro) for coro in coros))


# ANSI escape sequence pattern (identical to original)
ANSI_ESCAPE_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text.
    
    Args:
        text: Text potentially containing ANSI escape sequences
        
    Returns:
        Text with all ANSI escape sequences removed
    """
    return ANSI_ESCAPE_PATTERN.sub("", text)