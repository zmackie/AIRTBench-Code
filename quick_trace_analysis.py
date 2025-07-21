#!/usr/bin/env python3
"""
Quick analysis script for AI red-teaming traces
"""

import json
import sys
from collections import defaultdict, Counter

def analyze_traces(jsonl_path, max_lines=100):
    """Analyze first N lines of traces file"""
    print(f"Analyzing first {max_lines} lines of {jsonl_path}")
    
    conversations = []
    challenges = defaultdict(int)
    success_patterns = []
    token_usage = []
    
    with open(jsonl_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line_num > max_lines:
                break
                
            if line.strip():
                try:
                    trace = json.loads(line)
                    
                    # Extract conversations and challenges
                    if 'resourceSpans' in trace:
                        for resource_span in trace['resourceSpans']:
                            if 'scopeSpans' in resource_span:
                                for scope_span in resource_span['scopeSpans']:
                                    if 'spans' in scope_span:
                                        for span in scope_span['spans']:
                                            if 'attributes' in span:
                                                for attr in span['attributes']:
                                                    # Extract chat data
                                                    if attr.get('key') == 'chats':
                                                        try:
                                                            chat_data = json.loads(attr['value']['stringValue'])
                                                            conversations.extend(chat_data)
                                                        except:
                                                            continue
                                                    
                                                    # Extract challenge info
                                                    elif attr.get('key') == 'dreadnode.params':
                                                        try:
                                                            params = json.loads(attr['value']['stringValue'])
                                                            challenge_name = params.get('challenge')
                                                            if challenge_name:
                                                                challenges[challenge_name] += 1
                                                        except:
                                                            continue
                                                            
                except json.JSONDecodeError:
                    continue
    
    print(f"Found {len(conversations)} conversations")
    print(f"Found {len(challenges)} unique challenges")
    
    # Analyze conversations
    success_indicators = ["correct", "Congrats!", "gAAAAA", "flag was correct", "submit_flag"]
    message_lengths = []
    role_counts = Counter()
    
    for conv in conversations:
        if conv and 'messages' in conv:
            for msg in conv['messages']:
                if msg:
                    role_counts[msg.get('role', 'unknown')] += 1
                    
                    if 'content' in msg and msg['content']:
                        for content in msg['content']:
                            if content and content.get('type') == 'text':
                                text = content.get('text', '')
                                message_lengths.append(len(text))
                                
                                # Check for success indicators
                                for indicator in success_indicators:
                                    if indicator.lower() in text.lower():
                                        success_patterns.append({
                                            'conversation_id': conv.get('uuid'),
                                            'role': msg.get('role'),
                                            'indicator': indicator,
                                            'preview': text[:200]
                                        })
        
        # Extract token usage
        if conv and 'usage' in conv:
            usage = conv['usage']
            token_usage.append({
                'input_tokens': usage.get('input_tokens', 0),
                'output_tokens': usage.get('output_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            })
    
    # Print results
    print("\n=== ANALYSIS RESULTS ===")
    print(f"Total conversations: {len(conversations)}")
    print(f"Success patterns found: {len(success_patterns)}")
    print(f"Token usage records: {len(token_usage)}")
    
    print("\nChallenges:")
    for challenge, count in challenges.items():
        print(f"  {challenge}: {count}")
    
    print("\nRole distribution:")
    for role, count in role_counts.items():
        print(f"  {role}: {count}")
    
    if message_lengths:
        print(f"\nMessage length stats:")
        print(f"  Min: {min(message_lengths)}")
        print(f"  Max: {max(message_lengths)}")
        print(f"  Avg: {sum(message_lengths) / len(message_lengths):.1f}")
    
    if token_usage:
        input_tokens = [u['input_tokens'] for u in token_usage]
        output_tokens = [u['output_tokens'] for u in token_usage]
        total_tokens = [u['total_tokens'] for u in token_usage]
        
        print(f"\nToken usage stats:")
        print(f"  Input tokens - Min: {min(input_tokens)}, Max: {max(input_tokens)}, Avg: {sum(input_tokens) / len(input_tokens):.1f}")
        print(f"  Output tokens - Min: {min(output_tokens)}, Max: {max(output_tokens)}, Avg: {sum(output_tokens) / len(output_tokens):.1f}")
        print(f"  Total tokens - Min: {min(total_tokens)}, Max: {max(total_tokens)}, Avg: {sum(total_tokens) / len(total_tokens):.1f}")
    
    print(f"\nSuccess patterns (first 5):")
    for i, pattern in enumerate(success_patterns[:5]):
        print(f"  {i+1}. {pattern['role']}: {pattern['indicator']} - {pattern['preview']}")
    
    # Example conversation structure
    print(f"\nExample conversation structure:")
    for i, conv in enumerate(conversations[:2]):
        print(f"  Conversation {i+1}:")
        if conv and 'messages' in conv:
            for j, msg in enumerate(conv['messages'][:3]):
                if msg:
                    role = msg.get('role', 'unknown')
                    if 'content' in msg and msg['content']:
                        for content in msg['content']:
                            if content and content.get('type') == 'text':
                                text = content.get('text', '')
                                print(f"    {j+1}. {role}: {text[:100]}...")
                                break

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_trace_analysis.py <path_to_jsonl_file>")
        sys.exit(1)
    
    jsonl_path = sys.argv[1]
    analyze_traces(jsonl_path)