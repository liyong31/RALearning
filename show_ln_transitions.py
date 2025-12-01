#!/usr/bin/env python3
"""
Show number of transitions for each Ln automaton in examples/Ln.
"""

import os
import re
import glob
from dra import RegisterAutomaton

def extract_n_from_filename(filename):
    """Extract n value from filename like 'L5.txt' -> 5"""
    match = re.search(r'L(\d+)\.txt', filename)
    if match:
        return int(match.group(1))
    return None

def get_num_transitions_from_file(filepath):
    """Parse automaton file and return number of transitions."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        ra = RegisterAutomaton.from_text(text)
        return ra.get_num_trans()
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None

def show_ln_transitions(ln_dir="examples/Ln"):
    """Show number of transitions for each Ln automaton."""
    # Find all L*.txt files
    pattern = os.path.join(ln_dir, "L*.txt")
    ln_files = sorted(glob.glob(pattern))
    
    if not ln_files:
        print(f"No L*.txt files found in {ln_dir}/")
        return
    
    # Collect data
    data = []
    for ln_file in ln_files:
        n = extract_n_from_filename(ln_file)
        if n is None:
            continue
        
        num_trans = get_num_transitions_from_file(ln_file)
        if num_trans is not None:
            data.append((n, num_trans))
    
    if not data:
        print("No valid data found")
        return
    
    # Sort by n
    data.sort(key=lambda x: x[0])
    
    # Display results
    print("Number of transitions for Ln automata:")
    print("=" * 40)
    print(f"{'n':<10} {'#Transitions':<15}")
    print("-" * 40)
    for n, num_trans in data:
        print(f"{n:<10} {num_trans:<15}")
    print("=" * 40)
    print(f"Total: {len(data)} automata")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Show number of transitions for each Ln automaton"
    )
    parser.add_argument(
        '--dir',
        type=str,
        default='examples/Ln',
        help='Directory containing Ln automata (default: examples/Ln)'
    )
    
    args = parser.parse_args()
    
    show_ln_transitions(args.dir)

