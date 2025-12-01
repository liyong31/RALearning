#!/usr/bin/env python3
"""
Batch learner for register automata using ralt.py
Learns automata from generated_automata/ within a size range and saves logs in learned_automata/
Organizes logs into subfolders by size
"""

import subprocess
import sys
import os
import glob
import argparse
import time
from pathlib import Path

def learn_automata(lowerbound=5, upperbound=50):
    """Learn all automata from target-DRA/ and save logs to learned-DRA/.
    
    Args:
        lowerbound: Minimum automaton size to process (inclusive)
        upperbound: Maximum automaton size to process (inclusive)
    """
    # Get script directory to determine relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(script_dir))
    
    input_dir = "target-DRA"
    output_dir = "learned-DRA"
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create timing log file
    timing_log_file = os.path.join(output_dir, "timing.log")
    with open(timing_log_file, 'w') as f:
        f.write("Size\tFilename\tTime (seconds)\n")
    
    # Find all size subdirectories and filter to size range
    all_size_dirs = sorted(glob.glob(os.path.join(input_dir, "size*")))
    
    # Filter to sizes within [lowerbound, upperbound]
    size_dirs = []
    for size_dir in all_size_dirs:
        size_name = os.path.basename(size_dir)  # e.g., "size5"
        try:
            # Extract size number from directory name (e.g., "size5" -> 5)
            size_num = int(size_name.replace("size", ""))
            if lowerbound <= size_num <= upperbound:
                size_dirs.append(size_dir)
        except ValueError:
            # Skip directories that don't match the pattern
            continue
    
    if not size_dirs:
        print(f"No size subdirectories with size between {lowerbound} and {upperbound} found in '{input_dir}'")
        sys.exit(1)
    
    print(f"Processing automata with sizes between {lowerbound} and {upperbound} (inclusive)")
    
    total_files = 0
    processed = 0
    
    # Count total files first (only in filtered directories, at most 50 per size)
    max_per_size = 50
    for size_dir in size_dirs:
        txt_files = glob.glob(os.path.join(size_dir, "*.txt"))
        total_files += min(len(txt_files), max_per_size)
    
    print(f"Found {total_files} automata files to learn")
    print(f"Output directory: {output_dir}/")
    print()
    
    for size_dir in size_dirs:
        size_name = os.path.basename(size_dir)  # e.g., "size5"
        
        # Create corresponding output subdirectory
        output_size_dir = os.path.join(output_dir, size_name)
        os.makedirs(output_size_dir, exist_ok=True)
        
        # Find all .txt files in this size directory
        txt_files = sorted(glob.glob(os.path.join(size_dir, "*.txt")))
        
        if not txt_files:
            print(f"  No files found in {size_name}/")
            continue
        
        # Limit to at most 50 automata per size
        max_per_size = 50
        original_count = len(txt_files)
        txt_files = txt_files[:max_per_size]
        
        if original_count > max_per_size:
            print(f"Learning automata in {size_name}/ ({len(txt_files)}/{original_count} files, at most {max_per_size})...")
        else:
            print(f"Learning automata in {size_name}/ ({len(txt_files)} files)...")
        
        # Extract size number for timing log
        size_num = int(size_name.replace("size", ""))
        
        for txt_file in txt_files:
            processed += 1
            filename = os.path.basename(txt_file)  # e.g., "seed12345.txt"
            # Log file should match pattern seed{seed}_learned.log
            base_name = filename.replace(".txt", "")  # e.g., "seed12345"
            log_filename = f"{base_name}_learned.log"  # e.g., "seed12345_learned.log"
            log_file = os.path.join(output_size_dir, log_filename)
            # Output file for learned automaton (ralt.py --out)
            learned_file = os.path.join(output_size_dir, filename.replace(".txt", "_learned.txt"))
            
            print(f"  [{processed}/{total_files}] Learning {filename}...", end=" ", flush=True)
            
            # Start timing
            start_time = time.time()
            
            # Run ralt_quiet.py from root directory
            ralt_quiet_path = os.path.join(root_dir, "ralt_quiet.py")
            cmd = [
                sys.executable,
                ralt_quiet_path,
                "--inp", txt_file,
                "--out", learned_file
            ]
            
            try:
                # Capture both stdout and stderr to the log file
                with open(log_file, 'w') as log_f:
                    result = subprocess.run(
                        cmd,
                        stdout=log_f,
                        stderr=subprocess.STDOUT,  # Merge stderr into stdout
                        text=True,
                        check=True,
                        timeout=3600  # 1 hour timeout per learning task
                    )
                elapsed_time = time.time() - start_time
                print(f"✓ ({elapsed_time:.2f}s)")
                
                # Record timing
                with open(timing_log_file, 'a') as f:
                    f.write(f"{size_num}\t{filename}\t{elapsed_time:.2f}\n")
            except subprocess.TimeoutExpired:
                elapsed_time = time.time() - start_time
                print(f"✗ TIMEOUT ({elapsed_time:.2f}s)")
                # Remove incomplete files if they exist
                if os.path.exists(log_file):
                    os.remove(log_file)
                if os.path.exists(learned_file):
                    os.remove(learned_file)
                # Record timeout in timing log
                with open(timing_log_file, 'a') as f:
                    f.write(f"{size_num}\t{filename}\tTIMEOUT ({elapsed_time:.2f}s)\n")
                continue
            except subprocess.CalledProcessError as e:
                elapsed_time = time.time() - start_time
                # Write error to log file
                with open(log_file, 'a') as log_f:
                    log_f.write(f"\n\nERROR: Learning failed with exit code {e.returncode}\n")
                print(f"✗ ERROR ({elapsed_time:.2f}s, see {log_filename})")
                # Record error in timing log
                with open(timing_log_file, 'a') as f:
                    f.write(f"{size_num}\t{filename}\tERROR ({elapsed_time:.2f}s)\n")
                continue
        
        print(f"  Completed {size_name}: {len(txt_files)} automata learned")
        print()
    
    print(f"All done! Learned {processed}/{total_files} automata")
    print(f"Log files saved in '{output_dir}/'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch learner for register automata using ralt.py"
    )
    parser.add_argument(
        '--lowerbound', type=int, default=50,
        help='Minimum automaton size to process (inclusive, default: 5)'
    )
    parser.add_argument(
        '--upperbound', type=int, default=50,
        help='Maximum automaton size to process (inclusive, default: 50)'
    )
    args = parser.parse_args()
    
    if args.lowerbound > args.upperbound:
        print(f"Error: lowerbound ({args.lowerbound}) must be <= upperbound ({args.upperbound})")
        sys.exit(1)
    
    learn_automata(lowerbound=args.lowerbound, upperbound=args.upperbound)

