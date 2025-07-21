"""
API functions for AIRTBench SmolagAgents implementation.

These functions replicate the exact behavior of the original AIRTBench API functions.
"""

import os
import aiohttp
from loguru import logger


async def check_flag_api(challenge_id: str, flag: str, api_key: str) -> bool:
    """Validate flag via the Crucible API.
    
    Args:
        challenge_id: The challenge identifier
        flag: The flag to validate (format: gAAAAA...)
        api_key: Platform API key for authentication
        
    Returns:
        True if flag is correct, False otherwise
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{os.environ.get('CRUCIBLE_URL', 'https://platform.dreadnode.io')}/api/challenges/{challenge_id}/submit-flag"
            headers = {"X-API-Key": api_key}
            payload = {"challenge": challenge_id, "flag": flag}

            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return bool(data.get("correct", False))
                logger.warning(
                    f"API flag validation error: {response.status} - {await response.text()}",
                )
                return False
    except (aiohttp.ClientError, OSError, ValueError) as e:
        logger.error(f"Error during API flag validation: {e}")
        return False


async def validate_api_key(api_key: str) -> bool:
    """Validate API key authorization.

    Args:
        api_key: API key to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not api_key or api_key.strip() == "":
        logger.error("API key is blank or empty")
        return False

    try:
        # Use a bogus flag to test the API key with a standard challenge
        test_challenge_id = "pieceofcake"
        test_flag = "gAAAAAbogus_airtbench_test_flag_for_validation"

        async with aiohttp.ClientSession() as session:
            url = f"{os.environ.get('CRUCIBLE_URL', 'https://platform.dreadnode.io')}/api/challenges/{test_challenge_id}/submit-flag"
            headers = {"X-API-Key": api_key}
            payload = {"challenge": test_challenge_id, "flag": test_flag}

            async with session.post(url, headers=headers, json=payload) as response:
                # 401/403 means invalid key
                if response.status in (401, 403):
                    logger.error(f"API key validation failed with status {response.status}")
                    return False

                # Any other response indicates the key is valid
                logger.info(f"API key validated successfully (status {response.status})")
                return True

    except (aiohttp.ClientError, OSError, ValueError) as e:
        logger.error(f"API key validation error: {e}")
        return False


async def check_challenge_availability(challenge_id: str, api_key: str) -> bool:
    """Check if a specific challenge is available.

    Args:
        challenge_id: Challenge identifier to check
        api_key: Platform API key

    Returns:
        True if the challenge is available, False otherwise
    """
    try:
        async with aiohttp.ClientSession() as session:
            # Test the challenge endpoint with a bogus flag submission
            url = f"{os.environ.get('CRUCIBLE_URL', 'https://platform.dreadnode.io')}/api/challenges/{challenge_id}/submit-flag"
            headers = {"X-API-Key": api_key}
            payload = {"challenge": challenge_id, "flag": "gAAAAA_invalid_test"}

            async with session.post(url, headers=headers, json=payload) as response:
                # 404 means challenge doesn't exist
                if response.status == 404:
                    logger.warning(f"Challenge '{challenge_id}' not available")
                    return False

                # 401/403 indicates API key issue, not challenge availability
                if response.status in (401, 403):
                    logger.error(f"API key unauthorized for challenge {challenge_id}")
                    return False

                # Any other response means the challenge exists
                logger.info(f"Challenge {challenge_id} is available (status {response.status})")
                return True

    except (aiohttp.ClientError, OSError, ValueError) as e:
        logger.error(f"Error checking challenge {challenge_id} availability: {e}")
        return False