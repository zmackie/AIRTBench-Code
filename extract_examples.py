#!/usr/bin/env python3
"""
Extract specific examples of successful AI red-teaming interactions
"""

import json
import sys
import re

def extract_examples(jsonl_path, max_lines=200):
    """Extract examples from traces file"""
    print(f"Extracting examples from {jsonl_path}")
    
    successful_interactions = []
    challenge_approaches = {}
    code_execution_patterns = []
    
    with open(jsonl_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line_num > max_lines:
                break
                
            if line.strip():
                try:
                    trace = json.loads(line)
                    
                    # Extract conversations
                    if 'resourceSpans' in trace:
                        for resource_span in trace['resourceSpans']:
                            if 'scopeSpans' in resource_span:
                                for scope_span in resource_span['scopeSpans']:
                                    if 'spans' in scope_span:
                                        for span in scope_span['spans']:
                                            if 'attributes' in span:
                                                for attr in span['attributes']:
                                                    if attr.get('key') == 'chats':
                                                        try:
                                                            chat_data = json.loads(attr['value']['stringValue'])
                                                            analyze_conversations(chat_data, successful_interactions, challenge_approaches, code_execution_patterns)
                                                        except:
                                                            continue
                                                            
                except json.JSONDecodeError:
                    continue
    
    print_results(successful_interactions, challenge_approaches, code_execution_patterns)

def analyze_conversations(conversations, successful_interactions, challenge_approaches, code_execution_patterns):
    """Analyze individual conversations for patterns"""
    
    for conv in conversations:
        if conv and 'messages' in conv:
            conversation_data = {
                'uuid': conv.get('uuid'),
                'messages': [],
                'success_indicators': [],
                'code_blocks': [],
                'challenge_type': None
            }
            
            for msg in conv['messages']:
                if msg and 'content' in msg and msg['content']:
                    for content in msg['content']:
                        if content and content.get('type') == 'text':
                            text = content.get('text', '')
                            
                            # Store message
                            conversation_data['messages'].append({
                                'role': msg.get('role'),
                                'text': text,
                                'length': len(text)
                            })
                            
                            # Check for success indicators
                            success_indicators = [
                                "The flag was correct",
                                "Congrats!",
                                "gAAAAA",
                                "submit_flag",
                                "flag was correct"
                            ]
                            
                            for indicator in success_indicators:
                                if indicator in text:
                                    conversation_data['success_indicators'].append(indicator)
                            
                            # Extract code blocks
                            code_blocks = re.findall(r'<execute-code>(.*?)</execute-code>', text, re.DOTALL)
                            conversation_data['code_blocks'].extend(code_blocks)
                            
                            # Identify challenge type
                            if 'probe' in text.lower():
                                conversation_data['challenge_type'] = 'probe'
                            elif 'puppeteer' in text.lower():
                                conversation_data['challenge_type'] = 'puppeteer'
                            elif 'extractor' in text.lower():
                                conversation_data['challenge_type'] = 'extractor'
            
            # Store if successful or interesting
            if conversation_data['success_indicators'] or conversation_data['code_blocks']:
                successful_interactions.append(conversation_data)
                
                # Store challenge approach
                if conversation_data['challenge_type']:
                    if conversation_data['challenge_type'] not in challenge_approaches:
                        challenge_approaches[conversation_data['challenge_type']] = []
                    challenge_approaches[conversation_data['challenge_type']].append(conversation_data)
                
                # Store code execution patterns
                if conversation_data['code_blocks']:
                    code_execution_patterns.extend(conversation_data['code_blocks'])

def print_results(successful_interactions, challenge_approaches, code_execution_patterns):
    """Print analysis results"""
    
    print(f"\n=== EXAMPLES ANALYSIS ===")
    print(f"Successful interactions found: {len(successful_interactions)}")
    print(f"Challenge types identified: {len(challenge_approaches)}")
    print(f"Code execution patterns: {len(code_execution_patterns)}")
    
    # Challenge type breakdown
    print(f"\nChallenge Type Breakdown:")
    for challenge_type, interactions in challenge_approaches.items():
        print(f"  {challenge_type}: {len(interactions)} interactions")
    
    # Example successful interaction
    print(f"\n=== EXAMPLE SUCCESSFUL INTERACTION ===")
    if successful_interactions:
        example = successful_interactions[0]
        print(f"Conversation UUID: {example['uuid']}")
        print(f"Challenge Type: {example['challenge_type']}")
        print(f"Success Indicators: {example['success_indicators']}")
        print(f"Number of messages: {len(example['messages'])}")
        print(f"Number of code blocks: {len(example['code_blocks'])}")
        
        print(f"\nMessage Flow:")
        for i, msg in enumerate(example['messages'][:5]):  # First 5 messages
            print(f"  {i+1}. [{msg['role']}] ({msg['length']} chars): {msg['text'][:150]}...")
        
        if example['code_blocks']:
            print(f"\nCode Execution Examples:")
            for i, code in enumerate(example['code_blocks'][:3]):  # First 3 code blocks
                print(f"  Code Block {i+1}:")
                print(f"    {code.strip()[:200]}...")
    
    # Challenge-specific approaches
    print(f"\n=== CHALLENGE-SPECIFIC APPROACHES ===")
    for challenge_type, interactions in challenge_approaches.items():
        print(f"\n{challenge_type.upper()} Challenge:")
        
        # Common patterns
        common_patterns = []
        for interaction in interactions:
            for msg in interaction['messages']:
                if msg['role'] == 'assistant' and 'execute-code' in msg['text']:
                    common_patterns.append(msg['text'])
        
        print(f"  - {len(interactions)} successful interactions")
        print(f"  - Common assistant patterns found: {len(common_patterns)}")
        
        # Extract key strategies
        strategies = set()
        for interaction in interactions:
            for msg in interaction['messages']:
                if msg['role'] == 'assistant':
                    text = msg['text'].lower()
                    if 'prompt' in text and 'inject' in text:
                        strategies.add('prompt_injection')
                    if 'system' in text and 'leak' in text:
                        strategies.add('system_leak')
                    if 'flag' in text and 'extract' in text:
                        strategies.add('flag_extraction')
                    if 'bypass' in text or 'circumvent' in text:
                        strategies.add('bypass_techniques')
        
        print(f"  - Strategies used: {', '.join(strategies)}")
    
    # Token efficiency analysis
    print(f"\n=== TOKEN EFFICIENCY ANALYSIS ===")
    if successful_interactions:
        message_lengths = []
        for interaction in successful_interactions:
            total_length = sum(msg['length'] for msg in interaction['messages'])
            message_lengths.append(total_length)
        
        print(f"  Average conversation length: {sum(message_lengths) / len(message_lengths):.1f} chars")
        print(f"  Shortest successful conversation: {min(message_lengths)} chars")
        print(f"  Longest successful conversation: {max(message_lengths)} chars")
        
        # Find most efficient examples
        efficient_examples = [
            interaction for interaction in successful_interactions
            if sum(msg['length'] for msg in interaction['messages']) < 5000
        ]
        
        print(f"  Efficient examples (< 5000 chars): {len(efficient_examples)}")
        
        if efficient_examples:
            print(f"\n  Most efficient example:")
            efficient = min(efficient_examples, key=lambda x: sum(msg['length'] for msg in x['messages']))
            print(f"    UUID: {efficient['uuid']}")
            print(f"    Total length: {sum(msg['length'] for msg in efficient['messages'])} chars")
            print(f"    Messages: {len(efficient['messages'])}")
            print(f"    Success indicators: {efficient['success_indicators']}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_examples.py <path_to_jsonl_file>")
        sys.exit(1)
    
    jsonl_path = sys.argv[1]
    extract_examples(jsonl_path)