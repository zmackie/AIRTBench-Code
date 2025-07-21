"""Command-line interface for AIRTBench SmolagAgents implementation."""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional
import click

from .config import AIRTBenchConfig
from .executor import ChallengeExecutor


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """AIRTBench using SmolagAgents framework.
    
    An autonomous AI red teaming agent for solving AI/ML security challenges.
    """
    pass


@cli.command()
@click.option(
    "--model", 
    required=True, 
    help="Model ID to use (e.g., 'gpt-4', 'meta-llama/Llama-2-70b-chat-hf')"
)
@click.option(
    "--platform-api-key", 
    help="Platform API key (or set PLATFORM_API_KEY env var)"
)
@click.option(
    "--challenges", 
    multiple=True, 
    help="Specific challenges to run (can be used multiple times)"
)
@click.option(
    "--llm-challenges-only", 
    is_flag=True, 
    help="Run only challenges flagged as LLM challenges"
)
@click.option(
    "--executor-type", 
    type=click.Choice(["docker", "e2b", "local"]), 
    default="docker",
    help="Code execution environment"
)
@click.option(
    "--max-steps", 
    type=int, 
    default=100, 
    help="Maximum reasoning steps per challenge"
)
@click.option(
    "--concurrency", 
    type=int, 
    default=3, 
    help="Number of challenges to run concurrently"
)
@click.option(
    "--memory-limit", 
    default="2g", 
    help="Memory limit for execution environment"
)
@click.option(
    "--timeout", 
    type=int, 
    default=240, 
    help="Inference timeout in seconds"
)
@click.option(
    "--verbose", 
    is_flag=True, 
    help="Enable verbose output"
)
def run(
    model: str,
    platform_api_key: Optional[str],
    challenges: tuple,
    llm_challenges_only: bool,
    executor_type: str,
    max_steps: int,
    concurrency: int,
    memory_limit: str,
    timeout: int,
    verbose: bool
):
    """Run AIRTBench challenges using SmolagAgents."""
    
    try:
        # Create configuration
        config = AIRTBenchConfig.from_env(
            model=model,
            platform_api_key=platform_api_key,
            challenges=list(challenges) if challenges else None,
            llm_challenges_only=llm_challenges_only,
            executor_type=executor_type,
            max_steps=max_steps,
            concurrency=concurrency,
            memory_limit=memory_limit,
            inference_timeout=timeout,
        )
        
        # Validate configuration
        config.validate()
        
        if verbose:
            print("🔧 Configuration:")
            for key, value in config.to_dict().items():
                if "api_key" in key.lower():
                    value = "***" + str(value)[-4:] if value else None
                print(f"  {key}: {value}")
            print()
        
        # Create and run executor
        executor = ChallengeExecutor(config)
        
        # For now, run a simple test
        print("🎯 SmolagAgents AIRTBench is ready!")
        print("Note: Full orchestration coming soon. Use individual challenge execution for now.")
        
        sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n❌ Execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option(
    "--model", 
    required=True, 
    help="Model ID to use"
)
@click.option(
    "--platform-api-key", 
    help="Platform API key (or set PLATFORM_API_KEY env var)"
)
@click.option(
    "--executor-type", 
    type=click.Choice(["docker", "e2b", "local"]), 
    default="docker",
    help="Code execution environment"
)
@click.argument("challenge_id")
def single(
    model: str,
    platform_api_key: Optional[str],
    executor_type: str,
    challenge_id: str
):
    """Run a single challenge for testing/debugging."""
    
    try:
        config = AIRTBenchConfig.from_env(
            model=model,
            platform_api_key=platform_api_key,
            executor_type=executor_type,
            concurrency=1,
        )
        
        config.validate()
        
        executor = ChallengeExecutor(config)
        
        async def run_single():
            result = await executor.execute_challenge(challenge_id)
            return result
        
        result = asyncio.run(run_single())
        
        sys.exit(0 if result.success else 1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--model", 
    required=True, 
    help="Model ID to test"
)
@click.option(
    "--platform-api-key", 
    help="Platform API key (or set PLATFORM_API_KEY env var)"
)
@click.option(
    "--executor-type", 
    type=click.Choice(["docker", "e2b", "local"]), 
    default="local",
    help="Code execution environment to test"
)
def test(model: str, platform_api_key: Optional[str], executor_type: str):
    """Test the setup with a simple task."""
    
    try:
        from .agent import AIRTBenchAgent
        
        print(f"🧪 Testing setup with model: {model}")
        print(f"🔧 Executor type: {executor_type}")
        
        # Create agent
        agent = AIRTBenchAgent(
            model_id=model,
            platform_api_key=platform_api_key or "dummy",
            executor_type=executor_type,
            max_steps=5,
        )
        
        # Simple test task
        test_prompt = "Calculate the sum of numbers from 1 to 10 using Python."
        
        async def run_test():
            with agent:
                result = await agent.run(test_prompt)
                return result
        
        result = asyncio.run(run_test())
        
        print("✅ Test completed successfully!")
        print(f"📋 Result: {result}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()