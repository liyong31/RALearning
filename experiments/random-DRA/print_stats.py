#!/usr/bin/env python3
"""
Display experimental results from learned-DRA in a table format.
Shows for each size: states, transitions, EQ, MQ, MM, and total learning time.
"""

import os
import re
import glob
from pathlib import Path
from collections import defaultdict

def extract_seed_from_log_filename(filename):
    """Extract seed number from filename like 'seed12345_learned.log' -> '12345'"""
    match = re.search(r'seed(\d+)_learned\.log', filename)
    if match:
        return match.group(1)
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
    Note: The timing.log may contain console output format instead of tab-separated.
    """
    timing_data = {}
    current_size = None
    
    try:
        with open(timing_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check if this line indicates a new size directory
            size_match = re.search(r'Learning automata in size(\d+)/', line_stripped)
            if size_match:
                current_size = int(size_match.group(1))
                continue
            
            # Try tab-separated format first: Size\tFilename\tTime
            parts = line_stripped.split('\t')
            if len(parts) >= 3:
                size_str = parts[0].strip()
                filename = parts[1].strip()
                time_str = parts[2].strip()
                
                try:
                    size = int(size_str)
                except ValueError:
                    continue
                
                if time_str.startswith('TIMEOUT') or time_str.startswith('ERROR'):
                    time_match = re.search(r'\(([\d.]+)s\)', time_str)
                    if time_match:
                        timing_data[(size, filename)] = float(time_match.group(1))
                else:
                    try:
                        timing_data[(size, filename)] = float(time_str)
                    except ValueError:
                        pass
            else:
                # Try console output format: "Learning seed{SEED}_learned.txt... ✓ (time)s"
                match = re.search(r'Learning seed(\d+)_learned\.txt.*?[✓✗].*?\(([\d.]+)s\)', line_stripped)
                if match:
                    seed = match.group(1)
                    time_val = float(match.group(2))
                    filename = f"seed{seed}.txt"
                    # Store with size if we know it, otherwise just filename
                    if current_size is not None:
                        timing_data[(current_size, filename)] = time_val
                    else:
                        timing_data[filename] = time_val
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
    
    # Find all size subdirectories
    size_dirs = sorted(glob.glob(os.path.join(learned_dir, "size*")))
    
    if not size_dirs:
        print(f"No size subdirectories found in {learned_dir}/")
        return
    
    # Collect data grouped by size
    size_results = defaultdict(list)
    
    for size_dir in size_dirs:
        size_name = os.path.basename(size_dir)  # e.g., "size5"
        try:
            size_num = int(size_name.replace("size", ""))
        except ValueError:
            continue
        
        # Find all log files in this size directory
        log_pattern = os.path.join(size_dir, "seed*_learned.log")
        log_files = sorted(glob.glob(log_pattern))
        
        for log_file in log_files:
            seed = extract_seed_from_log_filename(log_file)
            if seed is None:
                continue
            
            stats = parse_log_file(log_file)
            if stats is None:
                continue
            
            # Get timing from timing.log
            # The log file is seed{SEED}_learned.log, but timing.log has the original filename seed{SEED}.txt
            log_basename = os.path.basename(log_file)  # e.g., "seed12345_learned.log"
            filename = log_basename.replace('_learned.log', '.txt')  # e.g., "seed12345.txt"
            
            # Try to get time with size key first
            time_val = timing_data.get((size_num, filename), None)
            
            # If not found, try filename only (for console output format)
            if time_val is None:
                time_val = timing_data.get(filename, None)
            
            size_results[size_num].append({
                'seed': seed,
                'states': stats['states'],
                'trans': stats['trans'],
                'eq': stats['eq'],
                'mq': stats['mq'],
                'mm': stats['mm'],
                'time': time_val
            })
    
    if not size_results:
        print("No valid data found to display")
        return
    
    # Print table
    print("=" * 120)
    print(f"{'Size':<8} {'States':<10} {'Trans':<10} {'EQ':<10} {'MQ':<15} {'MM':<10} {'Time (s)':<15}")
    print("=" * 120)
    
    sorted_sizes = sorted(size_results.keys())
    
    for size in sorted_sizes:
        results = size_results[size]
        
        # Calculate averages for this size
        if results:
            avg_states = sum(r['states'] for r in results) / len(results)
            avg_trans = sum(r['trans'] for r in results) / len(results)
            avg_eq = sum(r['eq'] for r in results) / len(results)
            avg_mq = sum(r['mq'] for r in results) / len(results)
            avg_mm = sum(r['mm'] for r in results) / len(results)
            
            # Calculate average time for this size
            time_values = [r['time'] for r in results if r['time'] is not None]
            if time_values:
                avg_time = sum(time_values) / len(time_values)
                size_time_str = f"{avg_time:.2f}"
            else:
                size_time_str = "NA"
            
            print(f"{size:<8} {avg_states:<10.1f} {avg_trans:<10.1f} {avg_eq:<10.1f} {avg_mq:<15.1f} {avg_mm:<10.1f} {size_time_str:<15}")
    
    print("=" * 120)

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

