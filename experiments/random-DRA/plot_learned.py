#!/usr/bin/env python3
"""
Plot statistics from learned-DRA with averages and variance.
Creates 4 separate figures: EQ, MQ, MM, and Time vs size.
"""

import os
import re
import glob
import numpy as np
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
    # Enable LaTeX-style text rendering
    plt.rcParams['text.usetex'] = False
    plt.rcParams['mathtext.default'] = 'regular'
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Error: matplotlib is not installed.")
    print("Please install it using: pip install matplotlib")

def extract_seed_from_log_filename(filename):
    """Extract seed number from filename like 'seed12345_learned.log' -> '12345'"""
    match = re.search(r'seed(\d+)_learned\.log', filename)
    if match:
        return match.group(1)
    return None

def parse_learned_log(log_file_path):
    """Parse a learned log file to extract query counts and automaton stats."""
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
    """Parse timing.log file to extract timing information."""
    timing_data = {}
    try:
        with open(timing_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try tab-separated format first
            parts = line.split('\t')
            if len(parts) >= 3 and parts[0].isdigit():
                filename = parts[1].strip()
                time_str = parts[2].strip()
                
                seed_match = re.search(r'seed(\d+)', filename)
                if seed_match:
                    seed = seed_match.group(1)
                    if time_str.startswith('TIMEOUT') or time_str.startswith('ERROR'):
                        time_match = re.search(r'\(([\d.]+)s\)', time_str)
                        if time_match:
                            timing_data[seed] = float(time_match.group(1))
                    else:
                        try:
                            timing_data[seed] = float(time_str)
                        except ValueError:
                            pass
            else:
                # Try console output format
                match = re.search(r'Learning seed(\d+)_learned\.txt.*?[✓✗].*?\(([\d.]+)s\)', line)
                if match:
                    seed = match.group(1)
                    time_val = float(match.group(2))
                    timing_data[seed] = time_val
    except Exception as e:
        pass
    
    return timing_data

def collect_data(learned_dir="learned-DRA"):
    """Collect all data from log files."""
    if not os.path.exists(learned_dir):
        print(f"Error: Directory '{learned_dir}' does not exist.")
        return None
    
    # Find all size subdirectories
    size_dirs = sorted(glob.glob(os.path.join(learned_dir, "size*")))
    
    if not size_dirs:
        print(f"No size subdirectories found in '{learned_dir}'")
        return None
    
    # Data structure: size -> list of stats dicts
    size_data = defaultdict(list)
    
    # Parse root-level timing.log first
    root_timing_log = os.path.join(learned_dir, "timing.log")
    all_timing_data = {}
    if os.path.exists(root_timing_log):
        all_timing_data = parse_timing_log(root_timing_log)
    
    # Process all log files
    for size_dir in size_dirs:
        size_name = os.path.basename(size_dir)
        size_num = int(size_name.replace("size", ""))
        
        log_pattern = os.path.join(size_dir, "seed*_learned.log")
        log_files = sorted(glob.glob(log_pattern))
        
        for log_file in log_files:
            seed = extract_seed_from_log_filename(log_file)
            if seed is None:
                continue
            
            stats = parse_learned_log(log_file)
            if stats is None:
                continue
            
            # Add timing if available
            if seed in all_timing_data and all_timing_data[seed] is not None:
                stats['time'] = all_timing_data[seed]
            else:
                stats['time'] = None
            
            size_data[size_num].append(stats)
    
    return size_data

def plot_statistics(learned_dir="learned-DRA", output_dir=None):
    """Plot 4 separate figures for EQ, MQ, MM, and Time."""
    if not HAS_MATPLOTLIB:
        print("Cannot plot: matplotlib is not installed.")
        return
    
    if output_dir is None:
        output_dir = learned_dir
    
    # Collect data
    size_data = collect_data(learned_dir)
    if size_data is None:
        return
    
    # Prepare data for plotting
    sizes = sorted(size_data.keys())
    
    # Calculate statistics for each metric
    eq_means = []
    eq_stds = []
    mq_means = []
    mq_stds = []
    mm_means = []
    mm_stds = []
    time_means = []
    time_stds = []
    
    for size in sizes:
        data_list = size_data[size]
        if not data_list:
            continue
        
        # Extract values
        eq_values = [d['eq'] for d in data_list]
        mq_values = [d['mq'] for d in data_list]
        mm_values = [d['mm'] for d in data_list]
        time_values = [d['time'] for d in data_list if d['time'] is not None]
        
        # Calculate mean and std
        eq_means.append(np.mean(eq_values))
        eq_stds.append(np.std(eq_values))
        mq_means.append(np.mean(mq_values))
        mq_stds.append(np.std(mq_values))
        mm_means.append(np.mean(mm_values))
        mm_stds.append(np.std(mm_values))
        
        if time_values:
            time_means.append(np.mean(time_values))
            time_stds.append(np.std(time_values))
        else:
            time_means.append(0)
            time_stds.append(0)
    
    # Create 4 separate figures
    figsize = (12, 8)
    
    # Figure 1: Average EQ
    plt.figure(figsize=figsize)
    plt.plot(sizes, eq_means, marker='o', linewidth=3, markersize=10, label='Average EQ')
    plt.xlabel('Size', fontsize=24, fontweight='bold')
    plt.ylabel('Number of Equivalence Queries', fontsize=24, fontweight='bold')
    plt.title(r'Average Equivalence Queries vs Size', 
              fontsize=26, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.xticks(sizes, fontsize=20)
    plt.yticks(fontsize=20)
    ax = plt.gca()
    ax.yaxis.get_offset_text().set_fontsize(20)
    ax.yaxis.get_offset_text().set_fontweight('bold')
    plt.tight_layout()
    output_file1 = os.path.join(output_dir, "avg_eq_vs_size.png")
    plt.savefig(output_file1, dpi=300, bbox_inches='tight')
    print(f"Figure 1 saved to {output_file1}")
    
    # Figure 2: Average MQ
    plt.figure(figsize=figsize)
    plt.plot(sizes, mq_means, marker='s', linewidth=3, markersize=10, label='Average MQ', color='green')
    plt.xlabel('Size', fontsize=24, fontweight='bold')
    plt.ylabel('Number of Membership Queries', fontsize=24, fontweight='bold')
    plt.title(r'Average Membership Queries vs Size', 
              fontsize=26, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.xticks(sizes, fontsize=20)
    plt.yticks(fontsize=20)
    ax = plt.gca()
    ax.yaxis.get_offset_text().set_fontsize(20)
    ax.yaxis.get_offset_text().set_fontweight('bold')
    plt.tight_layout()
    output_file2 = os.path.join(output_dir, "avg_mq_vs_size.png")
    plt.savefig(output_file2, dpi=300, bbox_inches='tight')
    print(f"Figure 2 saved to {output_file2}")
    
    # Figure 3: Average MM
    plt.figure(figsize=figsize)
    plt.plot(sizes, mm_means, marker='^', linewidth=3, markersize=10, label='Average MM', color='orange')
    plt.xlabel('Size', fontsize=24, fontweight='bold')
    plt.ylabel('Number of Memorability Queries', fontsize=24, fontweight='bold')
    plt.title(r'Average Memorability Queries vs Size', 
              fontsize=26, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.xticks(sizes, fontsize=20)
    plt.yticks(fontsize=20)
    ax = plt.gca()
    ax.yaxis.get_offset_text().set_fontsize(20)
    ax.yaxis.get_offset_text().set_fontweight('bold')
    plt.tight_layout()
    output_file3 = os.path.join(output_dir, "avg_mm_vs_size.png")
    plt.savefig(output_file3, dpi=300, bbox_inches='tight')
    print(f"Figure 3 saved to {output_file3}")
    
    # Figure 4: Average Time
    plt.figure(figsize=figsize)
    plt.plot(sizes, time_means, marker='d', linewidth=3, markersize=10, label='Average Time', color='red')
    plt.xlabel('Size', fontsize=24, fontweight='bold')
    plt.ylabel('Time (seconds)', fontsize=24, fontweight='bold')
    plt.title(r'Average Learning Time vs Size', 
              fontsize=26, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.xticks(sizes, fontsize=20)
    plt.yticks(fontsize=20)
    ax = plt.gca()
    ax.yaxis.get_offset_text().set_fontsize(20)
    ax.yaxis.get_offset_text().set_fontweight('bold')
    plt.tight_layout()
    output_file4 = os.path.join(output_dir, "avg_time_vs_size.png")
    plt.savefig(output_file4, dpi=300, bbox_inches='tight')
    print(f"Figure 4 saved to {output_file4}")
    
    plt.show()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Plot learned automata statistics with variance"
    )
    parser.add_argument(
        '--dir',
        type=str,
        default='learned-DRA',
        help='Directory containing learned automata (default: learned-DRA)'
    )
    parser.add_argument(
        '--out-dir',
        type=str,
        default=None,
        help='Output directory for figures (default: same as input directory)'
    )
    
    args = parser.parse_args()
    
    plot_statistics(args.dir, args.out_dir)

