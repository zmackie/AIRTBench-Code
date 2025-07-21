"""
Challenge execution engine for AIRTBench SmolagAgents implementation.

This provides challenge execution functionality that replicates the behavior
of the original AIRTBench system.
"""

import asyncio
import time
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from .agent import AIRTBenchAgent, extract_flag_from_output
from .config import AIRTBenchConfig


@dataclass
class ExecutionResult:
    """Result of executing a challenge."""
    
    challenge_id: str
    success: bool
    flag_found: Optional[str] = None
    steps_taken: int = 0
    execution_time: float = 0.0
    error_message: Optional[str] = None
    agent_output: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "challenge_id": self.challenge_id,
            "success": self.success,
            "flag_found": self.flag_found,
            "steps_taken": self.steps_taken,
            "execution_time": self.execution_time,
            "error_message": self.error_message,
            "agent_output": self.agent_output,
            "metadata": self.metadata or {}
        }


class ChallengeExecutor:
    """Executes individual challenges using SmolagAgents."""
    
    def __init__(self, config: AIRTBenchConfig):
        """Initialize the challenge executor.
        
        Args:
            config: AIRTBench configuration
        """
        self.config = config
        self.agent = None
    
    async def execute_challenge(self, challenge_id: str) -> ExecutionResult:
        """Execute a single challenge.
        
        Args:
            challenge_id: The ID of the challenge to execute
            
        Returns:
            ExecutionResult containing the outcome
        """
        start_time = time.time()
        
        try:
            # Create agent if not exists
            if self.agent is None:
                self.agent = self._create_agent()
            
            print(f"🚀 Starting challenge: {challenge_id}")
            
            # Execute the challenge
            result = await self._run_challenge(challenge_id)
            
            execution_time = time.time() - start_time
            
            # Check if flag was found in result
            flag_found = extract_flag_from_output(result)
            success = flag_found is not None
            
            print(f"{'✅' if success else '❌'} Challenge {challenge_id} {'completed' if success else 'failed'}")
            if flag_found:
                print(f"🏁 Flag found: {flag_found[:10]}...")
            
            return ExecutionResult(
                challenge_id=challenge_id,
                success=success,
                flag_found=flag_found,
                execution_time=execution_time,
                agent_output=str(result),
                metadata={
                    "model_id": self.config.model,
                    "executor_type": self.config.executor_type,
                    "max_steps": self.config.max_steps
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error executing challenge {challenge_id}: {str(e)}"
            print(f"❌ {error_msg}")
            
            return ExecutionResult(
                challenge_id=challenge_id,
                success=False,
                execution_time=execution_time,
                error_message=error_msg,
                metadata={
                    "model_id": self.config.model,
                    "executor_type": self.config.executor_type,
                }
            )
    
    def _create_agent(self) -> AIRTBenchAgent:
        """Create the AIRTBench agent instance."""
        return AIRTBenchAgent(
            model_id=self.config.model,
            platform_api_key=self.config.platform_api_key,
            executor_type=self.config.executor_type,
            max_steps=self.config.max_steps,
            memory_limit=self.config.memory_limit,
            additional_authorized_imports=self.config.additional_authorized_imports,
        )
    
    async def _run_challenge(self, challenge_id: str) -> str:
        """Run the challenge solving process.
        
        Args:
            challenge_id: The challenge to solve
            
        Returns:
            Agent's output/result
        """
        # Use agent's solve_challenge method
        with self.agent:
            result_dict = await self.agent.solve_challenge(challenge_id)
            return result_dict.get("result", "")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.agent:
            self.agent.cleanup()
            self.agent = None