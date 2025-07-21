#!/usr/bin/env python3
"""
Analysis script for AI red-teaming traces from frontier-models-traces.jsonl
"""

import json
import re
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional
import sys

class TraceAnalyzer:
    def __init__(self, jsonl_path: str):
        self.jsonl_path = jsonl_path
        self.traces = []
        self.conversations = []
        self.challenges = defaultdict(list)
        self.success_patterns = []
        self.token_usage = []
        
    def load_traces(self):
        """Load and parse the JSONL file"""
        print("Loading traces...")
        with open(self.jsonl_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        trace = json.loads(line)
                        self.traces.append(trace)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line {line_num}: {e}")
                        continue
        print(f"Loaded {len(self.traces)} traces")
    
    def extract_conversations(self):
        """Extract chat conversations from telemetry traces"""
        print("Extracting conversations...")
        
        for trace in self.traces:
            if 'resourceSpans' in trace:
                for resource_span in trace['resourceSpans']:
                    if 'scopeSpans' in resource_span:
                        for scope_span in resource_span['scopeSpans']:
                            if 'spans' in scope_span:
                                for span in scope_span['spans']:
                                    # Look for chat data in span attributes
                                    if 'attributes' in span:
                                        for attr in span['attributes']:
                                            if attr.get('key') == 'chats':
                                                try:
                                                    chat_data = json.loads(attr['value']['stringValue'])
                                                    self.conversations.extend(chat_data)
                                                except (json.JSONDecodeError, KeyError):
                                                    continue
                                            
                                            # Extract challenge information
                                            elif attr.get('key') == 'dreadnode.params':
                                                try:
                                                    params = json.loads(attr['value']['stringValue'])
                                                    challenge_name = params.get('challenge')
                                                    if challenge_name:
                                                        self.challenges[challenge_name].append({
                                                            'params': params,
                                                            'span': span
                                                        })
                                                except (json.JSONDecodeError, KeyError):
                                                    continue
        
        print(f"Extracted {len(self.conversations)} conversations")
        print(f"Found {len(self.challenges)} unique challenges")
    
    def analyze_success_patterns(self):
        """Analyze successful interactions and flag submissions"""
        print("Analyzing success patterns...")
        
        success_indicators = [
            "correct",
            "Congrats!",
            "gAAAAA",
            "flag was correct",
            "submit_flag",
            "successfully"
        ]
        
        for conv in self.conversations:
            if conv and 'messages' in conv and conv['messages']:
                for msg in conv['messages']:
                    if msg and 'content' in msg and msg['content']:
                        for content in msg['content']:
                            if content and content.get('type') == 'text':
                                text = content.get('text', '')
                                
                                # Check for success indicators
                                for indicator in success_indicators:
                                    if indicator.lower() in text.lower():
                                        self.success_patterns.append({
                                            'conversation_id': conv.get('uuid'),
                                            'message_role': msg.get('role'),
                                            'success_indicator': indicator,
                                            'text_snippet': text[:500],  # First 500 chars
                                            'full_text': text
                                        })
                                        break
    
    def analyze_token_usage(self):
        """Analyze token usage patterns"""
        print("Analyzing token usage...")
        
        for conv in self.conversations:
            if conv and 'usage' in conv and conv['usage']:
                usage = conv['usage']
                self.token_usage.append({
                    'conversation_id': conv.get('uuid'),
                    'input_tokens': usage.get('input_tokens', 0),
                    'output_tokens': usage.get('output_tokens', 0),
                    'total_tokens': usage.get('total_tokens', 0)
                })
    
    def extract_challenge_examples(self):
        """Extract examples of different challenge types and approaches"""
        print("Extracting challenge examples...")
        
        challenge_examples = {}
        
        for challenge_name, challenge_data in self.challenges.items():
            examples = []
            
            # Find conversations for this challenge
            for conv in self.conversations:
                if 'messages' in conv:
                    for msg in conv['messages']:
                        if 'content' in msg and msg['content']:
                            for content in msg['content']:
                                if content.get('type') == 'text':
                                    text = content.get('text', '')
                                    if challenge_name in text.lower():
                                        examples.append({
                                            'role': msg.get('role'),
                                            'text': text,
                                            'conversation_id': conv.get('uuid')
                                        })
            
            if examples:
                challenge_examples[challenge_name] = examples
        
        return challenge_examples
    
    def generate_report(self):
        """Generate structured analysis report"""
        print("Generating analysis report...")
        
        report = {
            'summary': {
                'total_traces': len(self.traces),
                'total_conversations': len(self.conversations),
                'unique_challenges': len(self.challenges),
                'success_patterns_found': len(self.success_patterns),
                'token_usage_records': len(self.token_usage)
            },
            'challenges': {},
            'success_patterns': self.success_patterns,
            'token_analysis': self.analyze_token_stats(),
            'conversation_structure': self.analyze_conversation_structure(),
            'recommendations': self.generate_recommendations()
        }
        
        # Add challenge-specific analysis
        for challenge_name, challenge_data in self.challenges.items():
            report['challenges'][challenge_name] = {
                'occurrences': len(challenge_data),
                'examples': self.extract_challenge_examples().get(challenge_name, [])[:3]  # First 3 examples
            }
        
        return report
    
    def analyze_token_stats(self):
        """Analyze token usage statistics"""
        if not self.token_usage:
            return {}
        
        input_tokens = [u['input_tokens'] for u in self.token_usage]
        output_tokens = [u['output_tokens'] for u in self.token_usage]
        total_tokens = [u['total_tokens'] for u in self.token_usage]
        
        return {
            'input_tokens': {
                'min': min(input_tokens),
                'max': max(input_tokens),
                'avg': sum(input_tokens) / len(input_tokens)
            },
            'output_tokens': {
                'min': min(output_tokens),
                'max': max(output_tokens),
                'avg': sum(output_tokens) / len(output_tokens)
            },
            'total_tokens': {
                'min': min(total_tokens),
                'max': max(total_tokens),
                'avg': sum(total_tokens) / len(total_tokens)
            }
        }
    
    def analyze_conversation_structure(self):
        """Analyze conversation structure patterns"""
        role_counts = Counter()
        message_lengths = []
        
        for conv in self.conversations:
            if conv and 'messages' in conv and conv['messages']:
                for msg in conv['messages']:
                    if msg:
                        role_counts[msg.get('role', 'unknown')] += 1
                        
                        if 'content' in msg and msg['content']:
                            for content in msg['content']:
                                if content and content.get('type') == 'text':
                                    text = content.get('text', '')
                                    message_lengths.append(len(text))
        
        return {
            'role_distribution': dict(role_counts),
            'message_length_stats': {
                'min': min(message_lengths) if message_lengths else 0,
                'max': max(message_lengths) if message_lengths else 0,
                'avg': sum(message_lengths) / len(message_lengths) if message_lengths else 0
            }
        }
    
    def generate_recommendations(self):
        """Generate recommendations for token-efficient examples"""
        recommendations = []
        
        # Analyze message lengths for optimization opportunities
        long_messages = []
        for conv in self.conversations:
            if conv and 'messages' in conv and conv['messages']:
                for msg in conv['messages']:
                    if msg and 'content' in msg and msg['content']:
                        for content in msg['content']:
                            if content and content.get('type') == 'text':
                                text = content.get('text', '')
                                if len(text) > 2000:  # Long messages
                                    long_messages.append({
                                        'role': msg.get('role'),
                                        'length': len(text),
                                        'conversation_id': conv.get('uuid'),
                                        'preview': text[:200] + '...'
                                    })
        
        if long_messages:
            recommendations.append({
                'category': 'Message Length Optimization',
                'description': f'Found {len(long_messages)} messages longer than 2000 characters',
                'suggestion': 'Consider breaking down long instructions into smaller, focused steps'
            })
        
        # Analyze repetitive patterns
        if self.success_patterns:
            recommendations.append({
                'category': 'Success Pattern Analysis',
                'description': f'Found {len(self.success_patterns)} success indicators',
                'suggestion': 'Use these patterns to create more focused examples'
            })
        
        return recommendations

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_traces.py <path_to_jsonl_file>")
        sys.exit(1)
    
    jsonl_path = sys.argv[1]
    analyzer = TraceAnalyzer(jsonl_path)
    
    try:
        analyzer.load_traces()
        analyzer.extract_conversations()
        analyzer.analyze_success_patterns()
        analyzer.analyze_token_usage()
        
        report = analyzer.generate_report()
        
        # Save report to file
        with open('trace_analysis_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\nAnalysis complete!")
        print(f"Report saved to: trace_analysis_report.json")
        
        # Print summary
        print("\nSummary:")
        print(f"- Total traces: {report['summary']['total_traces']}")
        print(f"- Total conversations: {report['summary']['total_conversations']}")
        print(f"- Unique challenges: {report['summary']['unique_challenges']}")
        print(f"- Success patterns found: {report['summary']['success_patterns_found']}")
        print(f"- Token usage records: {report['summary']['token_usage_records']}")
        
        if report['challenges']:
            print(f"\nChallenges found:")
            for challenge_name, data in report['challenges'].items():
                print(f"  - {challenge_name}: {data['occurrences']} occurrences")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()