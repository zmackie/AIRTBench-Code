"""
Configuration management for AIRTBench SmolagAgents implementation.

This replicates the behavior of the original AIRTBench configuration system.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class AIRTBenchConfig:
    """Configuration for AIRTBench agent and orchestrator."""
    
    # Core required parameters
    model: str
    platform_api_key: Optional[str] = None
    
    # Execution configuration
    include_thoughts: bool = False
    enable_cache: bool = False
    kernel_timeout: int = 120
    inference_timeout: int = 240
    truncate_output_length: int = 5000
    max_executions_per_step: int = 1
    concurrency: int = 3
    challenges: Optional[List[str]] = None
    max_steps: int = 100
    give_up: bool = False
    memory_limit: str = "2g"
    llm_challenges_only: bool = False
    
    # Additional configuration
    executor_type: str = "docker"
    challenge_dir: Optional[Path] = None
    additional_authorized_imports: List[str] = field(default_factory=list)
    
    @classmethod
    def from_env(cls, **overrides) -> "AIRTBenchConfig":
        """Create configuration from environment variables and overrides."""
        
        # Get API key from environment
        api_key = (
            overrides.get("platform_api_key") or
            os.environ.get("PLATFORM_API_KEY") or 
            os.environ.get("DREADNODE_API_TOKEN")
        )
        
        if not api_key:
            raise ValueError(
                "Platform API key is required. Set via --platform-api-key argument "
                "or PLATFORM_API_KEY/DREADNODE_API_TOKEN environment variable."
            )
        
        # Set default model if not provided
        model_id = overrides.get("model") or "meta-llama/Llama-2-70b-chat-hf"
        
        config = cls(
            model=model_id,
            platform_api_key=api_key,
        )
        
        # Apply overrides
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return config
    
    def validate(self) -> None:
        """Validate configuration parameters."""
        if not self.platform_api_key:
            raise ValueError("Platform API key is required")
        
        if not self.model:
            raise ValueError("Model ID is required")
        
        if self.executor_type not in ["docker", "e2b", "local"]:
            raise ValueError(f"Invalid executor_type: {self.executor_type}")
        
        if self.concurrency < 1:
            raise ValueError("Concurrency must be >= 1")
        
        if self.max_steps < 1:
            raise ValueError("Max steps must be >= 1")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            field.name: getattr(self, field.name) 
            for field in self.__dataclass_fields__.values()
        }