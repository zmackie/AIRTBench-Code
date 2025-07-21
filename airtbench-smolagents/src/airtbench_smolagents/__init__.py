"""AIRTBench implementation using SmolagAgents framework."""

from .agent import AIRTBenchAgent
from .config import AIRTBenchConfig  
from .executor import ChallengeExecutor
from .api import check_flag_api, validate_api_key
from .util import (
    flatten,
    majority_vote,
    all_in,
    any_in,
    not_in,
    enforce_concurrency,
    strip_ansi_codes,
)

__version__ = "0.1.0"
__all__ = [
    # Core classes
    "AIRTBenchAgent",
    "AIRTBenchConfig", 
    "ChallengeExecutor",
    
    # API functions
    "check_flag_api",
    "validate_api_key",
    
    # Utility functions
    "flatten",
    "majority_vote", 
    "all_in",
    "any_in",
    "not_in",
    "enforce_concurrency",
    "strip_ansi_codes",
]
