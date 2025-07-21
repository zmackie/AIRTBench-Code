#!/usr/bin/env python3
"""
Detailed analysis of successful AI red-teaming interactions
"""

import json
import sys
import re
from collections import defaultdict

def analyze_detailed(jsonl_path, max_lines=50):
    """Analyze specific successful interactions in detail"""
    print(f"Detailed analysis of {jsonl_path}")
    
    successful_examples = []
    
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
                                                            extract_successful_examples(chat_data, successful_examples)
                                                        except:
                                                            continue
                                                            
                except json.JSONDecodeError:
                    continue
    
    analyze_success_strategies(successful_examples)

def extract_successful_examples(conversations, successful_examples):
    """Extract only the most successful examples"""
    
    for conv in conversations:
        if conv and 'messages' in conv:
            # Look for actual successful flag submissions
            success_found = False
            for msg in conv['messages']:
                if msg and 'content' in msg and msg['content']:
                    for content in msg['content']:
                        if content and content.get('type') == 'text':
                            text = content.get('text', '')
                            if 'The flag was correct' in text and 'Congrats!' in text:
                                success_found = True
                                break
                if success_found:
                    break
            
            if success_found:
                # Extract the full conversation
                full_conversation = []
                for msg in conv['messages']:
                    if msg and 'content' in msg and msg['content']:
                        for content in msg['content']:
                            if content and content.get('type') == 'text':
                                text = content.get('text', '')
                                full_conversation.append({
                                    'role': msg.get('role'),
                                    'text': text
                                })
                
                successful_examples.append({
                    'uuid': conv.get('uuid'),
                    'conversation': full_conversation
                })

def analyze_success_strategies(successful_examples):
    """Analyze strategies used in successful interactions"""
    
    print(f"\n=== DETAILED SUCCESS ANALYSIS ===")
    print(f"Successful examples found: {len(successful_examples)}")
    
    if not successful_examples:
        print("No successful examples found in the sample")
        return
    
    # Analyze each successful example
    for i, example in enumerate(successful_examples[:3]):  # First 3 examples
        print(f"\n--- SUCCESSFUL EXAMPLE {i+1} ---")
        print(f"UUID: {example['uuid']}")
        print(f"Messages: {len(example['conversation'])}")
        
        # Extract challenge type
        challenge_type = "unknown"
        for msg in example['conversation']:
            if 'probe' in msg['text'].lower():
                challenge_type = "probe"
                break
            elif 'puppeteer' in msg['text'].lower():
                challenge_type = "puppeteer"
                break
            elif 'extractor' in msg['text'].lower():
                challenge_type = "extractor"
                break
        
        print(f"Challenge type: {challenge_type}")
        
        # Show conversation flow
        print(f"\nConversation flow:")
        for j, msg in enumerate(example['conversation']):
            role = msg['role']
            text = msg['text']
            print(f"  {j+1}. [{role}] ({len(text)} chars)")
            
            if role == 'system':
                print(f"     System: {text[:100]}...")
            elif role == 'user':
                # Extract key parts of user message
                if '<challenge-info>' in text:
                    challenge_start = text.find('<challenge-info>')
                    challenge_end = text.find('</challenge-info>')
                    if challenge_start != -1 and challenge_end != -1:
                        challenge_info = text[challenge_start:challenge_end+17]
                        print(f"     Challenge: {challenge_info[:200]}...")
                
                if '<execute-code>' in text:
                    code_blocks = re.findall(r'<execute-code>(.*?)</execute-code>', text, re.DOTALL)
                    print(f"     Code blocks: {len(code_blocks)}")
                    for k, code in enumerate(code_blocks):
                        print(f"       Code {k+1}: {code.strip()[:100]}...")
            
            elif role == 'assistant':
                # Extract key assistant strategies
                print(f"     Assistant: {text[:200]}...")
                
                if '<execute-code>' in text:
                    code_blocks = re.findall(r'<execute-code>(.*?)</execute-code>', text, re.DOTALL)
                    print(f"     Assistant code blocks: {len(code_blocks)}")
                    for k, code in enumerate(code_blocks):
                        print(f"       Code {k+1}: {code.strip()[:100]}...")
                
                # Look for strategy keywords
                strategies = []
                text_lower = text.lower()
                if 'prompt injection' in text_lower or 'inject' in text_lower:
                    strategies.append('prompt_injection')
                if 'system prompt' in text_lower or 'leak' in text_lower:
                    strategies.append('system_leak')
                if 'bypass' in text_lower or 'circumvent' in text_lower:
                    strategies.append('bypass')
                if 'flag' in text_lower and 'extract' in text_lower:
                    strategies.append('flag_extraction')
                
                if strategies:
                    print(f"     Strategies detected: {', '.join(strategies)}")
        
        print(f"\n")
    
    # Extract common patterns
    print(f"=== COMMON SUCCESS PATTERNS ===")
    
    # Code execution patterns
    all_code_blocks = []
    for example in successful_examples:
        for msg in example['conversation']:
            if msg['role'] == 'assistant':
                code_blocks = re.findall(r'<execute-code>(.*?)</execute-code>', msg['text'], re.DOTALL)
                all_code_blocks.extend(code_blocks)
    
    print(f"Total code blocks from successful examples: {len(all_code_blocks)}")
    
    # Most common code patterns
    code_patterns = defaultdict(int)
    for code in all_code_blocks:
        code_clean = code.strip()
        if 'import' in code_clean:
            code_patterns['import_statements'] += 1
        if 'requests' in code_clean:
            code_patterns['requests_usage'] += 1
        if 'query(' in code_clean:
            code_patterns['query_function'] += 1
        if 'submit_flag' in code_clean:
            code_patterns['flag_submission'] += 1
        if 'print(' in code_clean:
            code_patterns['print_statements'] += 1
    
    print(f"Common code patterns:")
    for pattern, count in sorted(code_patterns.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pattern}: {count}")
    
    # Extract most efficient successful approach
    print(f"\n=== MOST EFFICIENT APPROACH ===")
    if successful_examples:
        shortest_example = min(successful_examples, 
                              key=lambda x: sum(len(msg['text']) for msg in x['conversation']))
        
        print(f"Shortest successful conversation:")
        print(f"  UUID: {shortest_example['uuid']}")
        print(f"  Total length: {sum(len(msg['text']) for msg in shortest_example['conversation'])} chars")
        print(f"  Messages: {len(shortest_example['conversation'])}")
        
        print(f"\nFull conversation:")
        for i, msg in enumerate(shortest_example['conversation']):
            print(f"  {i+1}. [{msg['role']}]")
            print(f"     {msg['text'][:300]}...")
            print()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python detailed_analysis.py <path_to_jsonl_file>")
        sys.exit(1)
    
    jsonl_path = sys.argv[1]
    analyze_detailed(jsonl_path)