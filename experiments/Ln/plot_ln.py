#!/usr/bin/env python3
"""
Plot query statistics from Ln learning logs.
Creates a figure showing EQ, MQ, and MM query counts vs n.
"""

import os
import re
import matplotlib.pyplot as plt
from pathlib import Path
import glob

def parse_log_file(log_file_path):
    """
    Parse a log file to extract query counts.
    Returns (mq, eq, mm) or None if parsing fails.
    """
    try:
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
        
        # Look for Query Statistics section
        in_stats_section = False
        mq = None
        eq = None
        mm = None
        
        for line in lines:
            line = line.strip()
            if line == "Query Statistics:":
                in_stats_section = True
                continue
            
            if in_stats_section:
                if line.startswith("#MQ:"):
                    mq = int(line.split(":")[1].strip())
                elif line.startswith("#EQ:"):
                    eq = int(line.split(":")[1].strip())
                elif line.startswith("#MM:"):
                    mm = int(line.split(":")[1].strip())
                elif line == "" and (mq is not None or eq is not None or mm is not None):
                    # End of stats section
                    break
        
        if mq is not None and eq is not None and mm is not None:
            return (mq, eq, mm)
        else:
            print(f"Warning: Could not parse {log_file_path} (found MQ={mq}, EQ={eq}, MM={mm})")
            return None
    except Exception as e:
        print(f"Error reading {log_file_path}: {e}")
        return None

def extract_n_from_filename(filename):
    """Extract n value from filename like 'L5.log' -> 5"""
    match = re.search(r'L(\d+)\.log', filename)
    if match:
        return int(match.group(1))
    return None

def plot_ln_queries(log_dir="learned-DRA", max_n=25):
    """
    Plot query statistics from Ln learning logs.
    
    Args:
        log_dir: Directory containing the log files
        max_n: Maximum n value to plot (default 25)
    """
    # Find all log files
    pattern = os.path.join(log_dir, "L*.log")
    log_files = sorted(glob.glob(pattern))
    
    if not log_files:
        print(f"No log files found in {log_dir}/")
        return
    
    # Collect data
    n_values = []
    mq_values = []
    eq_values = []
    mm_values = []
    
    for log_file in log_files:
        n = extract_n_from_filename(log_file)
        if n is None or n > max_n:
            continue
        
        query_counts = parse_log_file(log_file)
        if query_counts is not None:
            mq, eq, mm = query_counts
            n_values.append(n)
            mq_values.append(mq)
            eq_values.append(eq)
            mm_values.append(mm)
    
    if not n_values:
        print("No valid data found to plot")
        return
    
    # Sort by n
    sorted_data = sorted(zip(n_values, mq_values, eq_values, mm_values))
    n_values, mq_values, eq_values, mm_values = zip(*sorted_data)
    
    # Create first figure: MMs and EQs
    plt.figure(figsize=(14, 10))
    
    plt.plot(n_values, eq_values, marker='o', label='Equivalence Queries (EQ)', linewidth=5, markersize=14)
    plt.plot(n_values, mm_values, marker='^', label='Memorability Queries (MM)', linewidth=5, markersize=14)
    
    plt.xlabel('n (Length of words)', fontsize=24, fontweight='bold')
    # plt.ylabel('Number of Queries', fontsize=20, fontweight='bold')
    plt.title(r'Equivalence and Memorability Queries for Learning $L_n$', fontsize=26, fontweight='bold')
    plt.legend(fontsize=22)
    plt.grid(True, alpha=0.3)
    plt.xlim(0, max(n_values) + 1)
    
    # Set x-axis ticks to show all n values with larger font
    plt.xticks(n_values, rotation=45, ha='right', fontsize=22)
    plt.yticks(fontsize=22)
    
    # Increase font size for y-axis exponent (scientific notation)
    ax = plt.gca()
    ax.yaxis.get_offset_text().set_fontsize(22)
    ax.yaxis.get_offset_text().set_fontweight('bold')
    
    plt.tight_layout()
    
    # Save the first figure
    output_file1 = os.path.join(log_dir, "query_statistics_eq_mm.png")
    plt.savefig(output_file1, dpi=300, bbox_inches='tight')
    print(f"Figure 1 saved to {output_file1}")
    
    # Create second figure: MQs
    plt.figure(figsize=(14, 10))
    
    plt.plot(n_values, mq_values, marker='s', label='Membership Queries (MQ)', linewidth=5, markersize=14, color='green')
    
    plt.xlabel('n (Length of words)', fontsize=24, fontweight='bold')
    # plt.ylabel('Number of Queries', fontsize=20, fontweight='bold')
    plt.title(r'Membership Queries for Learning $L_n$', fontsize=26, fontweight='bold')
    plt.legend(fontsize=22)
    plt.grid(True, alpha=0.3)
    plt.xlim(0, max(n_values) + 1)
    
    # Set x-axis ticks to show all n values with larger font
    plt.xticks(n_values, rotation=45, ha='right', fontsize=22)
    plt.yticks(fontsize=22)
    
    # Increase font size for y-axis exponent (scientific notation)
    ax = plt.gca()
    ax.yaxis.get_offset_text().set_fontsize(22)
    ax.yaxis.get_offset_text().set_fontweight('bold')
    
    plt.tight_layout()
    
    # Save the second figure
    output_file2 = os.path.join(log_dir, "query_statistics_mq.png")
    plt.savefig(output_file2, dpi=300, bbox_inches='tight')
    print(f"Figure 2 saved to {output_file2}")
    
    # Also show the plots
    plt.show()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Plot query statistics from Ln learning logs"
    )
    parser.add_argument(
        '--log-dir',
        type=str,
        default='learned-DRA',
        help='Directory containing log files (default: learned-DRA)'
    )
    parser.add_argument(
        '--max-n',
        type=int,
        default=25,
        help='Maximum n value to plot (default: 25)'
    )
    
    args = parser.parse_args()
    
    plot_ln_queries(args.log_dir, args.max_n)

if __name__ == "__main__":
    main()

