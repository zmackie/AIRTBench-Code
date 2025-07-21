"""Flag validation tool for AIRTBench."""

import os
import asyncio
import aiohttp
from typing import Optional
from smolagents import tool


@tool
def submit_flag(challenge_id: str, flag: str) -> bool:
    """Submit a flag for validation to the challenge platform.
    
    Use this tool when you discover a flag in format 'gAAAAA...' to check if it's correct.
    The tool will return True if the flag is correct, False otherwise.
    
    Args:
        challenge_id: The ID of the challenge the flag belongs to
        flag: The flag to submit (should start with 'gAAAAA')
        
    Returns:
        True if the flag is correct, False otherwise
    """
    # Get API key from environment
    api_key = os.environ.get("PLATFORM_API_KEY") or os.environ.get("DREADNODE_API_TOKEN")
    
    if not api_key:
        print("❌ No API key found in environment variables")
        return False
    
    # Basic validation
    if not flag.startswith("gAAAAA"):
        print("❌ Invalid flag format - must start with 'gAAAAA'")
        return False
    
    if not challenge_id.strip():
        print("❌ Challenge ID cannot be empty")
        return False
    
    # Run async validation in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(_validate_flag_async(challenge_id, flag, api_key))
    except Exception as e:
        print(f"❌ Flag validation error: {e}")
        return False


async def _validate_flag_async(challenge_id: str, flag: str, api_key: str) -> bool:
    """Async implementation of flag validation.
    
    Args:
        challenge_id: The ID of the challenge
        flag: The flag to validate
        api_key: Platform API key
        
    Returns:
        True if flag is correct, False otherwise
    """
    url = f"{os.environ.get('CRUCIBLE_URL', 'https://platform.dreadnode.io')}/api/challenges/{challenge_id}/submit-flag"
    headers = {"X-API-Key": api_key}
    payload = {"challenge": challenge_id, "flag": flag}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    is_correct = bool(data.get("correct", False))
                    
                    if is_correct:
                        print(f"🎉 Flag correct for challenge '{challenge_id}'!")
                        print("The flag was correct. Congrats!")
                    else:
                        print(f"❌ Flag incorrect for challenge '{challenge_id}'")
                    
                    return is_correct
                
                elif response.status in (401, 403):
                    print(f"❌ Authentication failed for challenge '{challenge_id}' (status {response.status})")
                    return False
                
                elif response.status == 404:
                    print(f"❌ Challenge '{challenge_id}' not found (status {response.status})")
                    return False
                
                else:
                    error_text = await response.text()
                    print(f"❌ API error for challenge '{challenge_id}': {response.status} - {error_text}")
                    return False
                    
    except aiohttp.ClientError as e:
        print(f"❌ Network error during flag validation: {e}")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error during flag validation: {e}")
        return False


class FlagValidatorTool:
    """Tool wrapper for flag validation functionality."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the flag validator.
        
        Args:
            api_key: Platform API key for authentication
        """
        self.api_key = api_key or os.environ.get("PLATFORM_API_KEY") or os.environ.get("DREADNODE_API_TOKEN")
        
        if not self.api_key:
            raise ValueError(
                "API key is required. Provide it during initialization or set "
                "PLATFORM_API_KEY/DREADNODE_API_TOKEN environment variable."
            )
    
    def __call__(self, challenge_id: str, flag: str) -> bool:
        """Submit flag for validation."""
        return submit_flag(challenge_id, flag)