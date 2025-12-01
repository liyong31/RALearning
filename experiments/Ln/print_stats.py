#!/usr/bin/env python3
"""
Display experimental results from learned-DRA in a table format.
Shows for each n: states, transitions, EQ, MQ, MM, and total learning time.
"""

import os
import re
import glob
from pathlib import Path

def extract_n_from_filename(filename):
    """Extract n value from filename like 'L5.log' -> 5"""
    match = re.search(r'L(\d+)\.log', filename)
    if match:
        return int(match.group(1))
    return None

def parse_log_file(log_file_path):
    """
    Parse a log file to extract query counts and automaton stats.
    Returns dict with: mq, eq, mm, states, trans
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract query counts
        mq_match = re.search(r'#MQ:\s*(\d+)', content)
        eq_match = re.search(r'#EQ:\s*(\d+)', content)
        mm_match = re.search(r'#MM:\s*(\d+)', content)
        
        # Extract hypothesis automaton stats
        states_match = re.search(r'Hypothesis Automaton:.*?#States:\s*(\d+)', content, re.DOTALL)
        trans_match = re.search(r'Hypothesis Automaton:.*?#Trans:\s*(\d+)', content, re.DOTALL)
        
        if mq_match and eq_match and mm_match and states_match and trans_match:
            return {
                'mq': int(mq_match.group(1)),
                'eq': int(eq_match.group(1)),
                'mm': int(mm_match.group(1)),
                'states': int(states_match.group(1)),
                'trans': int(trans_match.group(1))
            }
        else:
            return None
    except Exception as e:
        return None

def parse_timing_log(timing_log_path):
    """
    Parse timing.log file to extract timing information.
    Returns dict mapping filename -> time in seconds
    """
    timing_data = {}
    try:
        with open(timing_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('Filename'):
                continue  # Skip header and empty lines
            
            # Try tab-separated format
            parts = line.split('\t')
            if len(parts) >= 2:
                filename = parts[0].strip()
                time_str = parts[1].strip()
                
                if time_str.startswith('TIMEOUT') or time_str.startswith('ERROR'):
                    time_match = re.search(r'\(([\d.]+)s\)', time_str)
                    if time_match:
                        timing_data[filename] = float(time_match.group(1))
                else:
                    try:
                        timing_data[filename] = float(time_str)
                    except ValueError:
                        pass
    except Exception as e:
        pass
    
    return timing_data

def show_table(learned_dir="learned-DRA"):
    """
    Display experimental results in a table format.
    """
    if not os.path.exists(learned_dir):
        print(f"Error: Directory '{learned_dir}' does not exist.")
        return
    
    # Parse timing log
    timing_log_path = os.path.join(learned_dir, "timing.log")
    timing_data = {}
    if os.path.exists(timing_log_path):
        timing_data = parse_timing_log(timing_log_path)
    
    # Find all log files
    pattern = os.path.join(learned_dir, "L*.log")
    log_files = sorted(glob.glob(pattern))
    
    if not log_files:
        print(f"No log files found in {learned_dir}/")
        return
    
    # Collect data
    results = []
    for log_file in log_files:
        n = extract_n_from_filename(log_file)
        if n is None:
            continue
        
        stats = parse_log_file(log_file)
        if stats is None:
            continue
        
        # Get timing from timing.log
        filename = os.path.basename(log_file).replace('.log', '.txt')
        time_val = timing_data.get(filename, None)
        
        results.append({
            'n': n,
            'states': stats['states'],
            'trans': stats['trans'],
            'eq': stats['eq'],
            'mq': stats['mq'],
            'mm': stats['mm'],
            'time': time_val
        })
    
    # Sort by n
    results.sort(key=lambda x: x['n'])
    
    if not results:
        print("No valid data found to display")
        return
    
    # Print table
    print("=" * 100)
    print(f"{'n':<6} {'States':<8} {'Trans':<8} {'EQ':<8} {'MQ':<12} {'MM':<8} {'Time (s)':<12}")
    print("=" * 100)
    
    total_time = 0
    for r in results:
        n = r['n']
        states = r['states']
        trans = r['trans']
        eq = r['eq']
        mq = r['mq']
        mm = r['mm']
        time_val = r['time']
        
        time_str = f"{time_val:.2f}" if time_val is not None else "NA"
        if time_val is not None:
            total_time += time_val
        
        print(f"{n:<6} {states:<8} {trans:<8} {eq:<8} {mq:<12} {mm:<8} {time_str:<12}")
    
    print("=" * 100)
    total_time_str = f"{total_time:.2f}"
    print(f"{'Total':<6} {'':<8} {'':<8} {'':<8} {'':<12} {'':<8} {total_time_str:>12}")
    print("=" * 100)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Display experimental results from learned-DRA in a table format"
    )
    parser.add_argument(
        '--dir',
        type=str,
        default='learned-DRA',
        help='Directory containing learned automata (default: learned-DRA)'
    )
    
    args = parser.parse_args()
    
    show_table(args.dir)

