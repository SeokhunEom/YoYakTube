"""
AI model management CLI module

Command-line interface for managing and testing AI models.
"""

import click
import sys
import os
import time
import json
from typing import Optional, List

# Add parent directory to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from yoyaktube.llm import get_or_create_llm, ChatMessage


# Available models for each provider
AVAILABLE_MODELS = {
    'openai': [
        'gpt-5',
        'gpt-5-mini',
        'gpt-5-nano'
    ]
}


def get_api_key() -> str:
    """Get OpenAI API key from environment."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        click.echo("Error: OPENAI_API_KEY environment variable is required", err=True)
        sys.exit(1)
    return api_key


def list_models_command(provider: Optional[str]):
    """List available models."""
    if provider:
        if provider in AVAILABLE_MODELS:
            click.echo(f"Available {provider} models:")
            for model in AVAILABLE_MODELS[provider]:
                click.echo(f"  - {model}")
        else:
            click.echo(f"Error: Unknown provider '{provider}'", err=True)
            sys.exit(1)
    else:
        click.echo("Available models by provider:")
        for prov, models in AVAILABLE_MODELS.items():
            click.echo(f"\n{prov}:")
            for model in models:
                click.echo(f"  - {model}")


def test_model_command(provider: str, model: str, prompt: str):
    """Test model connection."""
    click.echo(f"Testing {provider}/{model}...")
    
    # Get API key
    api_key = get_api_key()
    
    try:
        # Create LLM client
        llm = get_or_create_llm(provider, model, api_key)
        
        # Test with simple prompt
        messages = [ChatMessage(role="user", content=prompt)]
        
        start_time = time.time()
        response = llm.chat(messages, temperature=0.2)
        end_time = time.time()
        
        # Display results
        click.echo(f"✅ Connection successful!")
        click.echo(f"Response time: {end_time - start_time:.2f} seconds")
        click.echo(f"Response: {response.content}")
        
        if response.usage:
            click.echo(f"Token usage: {response.usage}")
        
    except Exception as e:
        click.echo(f"❌ Connection failed: {e}", err=True)
        sys.exit(1)


def direct_chat_command(provider: str, model: str):
    """Direct chat with AI model."""
    click.echo(f"=== Direct Chat with {provider}/{model} ===")
    click.echo("Type your messages. Use 'quit' or 'exit' to end the conversation.")
    click.echo()
    
    # Get API key
    api_key = get_api_key()
    
    try:
        # Create LLM client
        llm = get_or_create_llm(provider, model, api_key)
    except Exception as e:
        click.echo(f"Error creating LLM client: {e}", err=True)
        sys.exit(1)
    
    # Chat loop
    conversation: List[ChatMessage] = []
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit']:
                click.echo("Ending conversation.")
                break
            
            if not user_input:
                continue
            
            # Add user message
            conversation.append(ChatMessage(role="user", content=user_input))
            
            # Get AI response
            response = llm.chat(conversation, temperature=0.7)
            assistant_response = response.content
            
            # Add assistant response
            conversation.append(ChatMessage(role="assistant", content=assistant_response))
            
            # Display response
            click.echo(f"AI: {assistant_response}")
            click.echo()
            
        except KeyboardInterrupt:
            click.echo("\nEnding conversation.")
            break
        except Exception as e:
            click.echo(f"Error: {e}")
            click.echo()


def benchmark_command(models: Optional[str], prompt: str, output: Optional[str]):
    """Benchmark model performance."""
    if not models:
        # Default models to benchmark
        models_to_test = ['gpt-5-mini', 'gpt-5']
    else:
        models_to_test = [m.strip() for m in models.split(',')]
    
    click.echo("Running model benchmark...")
    click.echo(f"Test prompt: {prompt}")
    click.echo()
    
    # Get API key
    api_key = get_api_key()
    
    results = []
    
    for model in models_to_test:
        click.echo(f"Testing {model}...")
        
        try:
            # Create LLM client
            llm = get_or_create_llm('openai', model, api_key)
            
            # Test with prompt
            messages = [ChatMessage(role="user", content=prompt)]
            
            start_time = time.time()
            response = llm.chat(messages, temperature=0.2)
            end_time = time.time()
            
            result = {
                'model': model,
                'response_time': end_time - start_time,
                'response': response.content,
                'usage': response.usage,
                'success': True
            }
            
            click.echo(f"  ✅ Success in {result['response_time']:.2f}s")
            
        except Exception as e:
            result = {
                'model': model,
                'error': str(e),
                'success': False
            }
            click.echo(f"  ❌ Failed: {e}")
        
        results.append(result)
        click.echo()
    
    # Display summary
    click.echo("=== Benchmark Results ===")
    successful_models = [r for r in results if r['success']]
    
    if successful_models:
        fastest = min(successful_models, key=lambda x: x['response_time'])
        click.echo(f"Fastest model: {fastest['model']} ({fastest['response_time']:.2f}s)")
        
        # Show all results
        for result in results:
            if result['success']:
                usage_info = ""
                if result['usage']:
                    usage_info = f" | Tokens: {result['usage'].get('total_tokens', 'N/A')}"
                click.echo(f"{result['model']}: {result['response_time']:.2f}s{usage_info}")
            else:
                click.echo(f"{result['model']}: FAILED - {result['error']}")
    
    # Save results if requested
    if output:
        try:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            click.echo(f"\nResults saved to {output}")
        except Exception as e:
            click.echo(f"Error saving results: {e}", err=True)


@click.group()
def cli():
    """AI model management"""
    pass


@cli.command('list')
@click.option('--provider', help='Show models for specific provider')
def list_models(provider):
    """List available models"""
    list_models_command(provider)


@cli.command('test')
@click.argument('provider')
@click.argument('model')
@click.option('--prompt', default='Hello, please respond with a simple greeting.', help='Test prompt')
def test_model(provider, model, prompt):
    """Test model connection"""
    test_model_command(provider, model, prompt)


@cli.command('chat')
@click.option('--provider', default='openai', help='AI provider')
@click.option('--model', default='gpt-5-mini', help='Model name')
def chat(provider, model):
    """Direct chat with AI model"""
    direct_chat_command(provider, model)


@cli.command('benchmark')
@click.option('--models', help='Comma-separated list of models to benchmark')
@click.option('--prompt', default='Summarize the concept of machine learning in 2 sentences.', help='Benchmark prompt')
@click.option('--output', help='Save results to file')
def benchmark(models, prompt, output):
    """Benchmark model performance"""
    benchmark_command(models, prompt, output)


if __name__ == '__main__':
    cli()