#!/usr/bin/env python3
"""
Batch learner for Ln automata.
Learns all Lx.txt files in examples/Ln and saves results to examples/Ln_learned/
"""

import subprocess
import sys
import os
from pathlib import Path
import glob
import time

def learn_ln_batch(min_n=None, max_n=None):
    """
    Learn all Ln automata from examples/Ln/
    
    Args:
        min_n: Minimum value of n to process (e.g., 10 means only learn L10, L15, ..., L50).
               If None, no lower bound is applied.
        max_n: Maximum value of n to process (e.g., 50 means only learn L5, L10, ..., L50).
               If None, no upper bound is applied.
    """
    # Input directory
    input_dir = "target-DRA"
    
    # Output directory
    output_dir = "learned-DRA"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create timing log file
    timing_log_file = os.path.join(output_dir, "timing.log")
    with open(timing_log_file, 'w') as f:
        f.write("Filename\tTime (seconds)\n")
    
    # Find all Lx.txt files
    pattern = os.path.join(input_dir, "L*.txt")
    input_files = sorted(glob.glob(pattern))
    
    if not input_files:
        print(f"No L*.txt files found in {input_dir}/")
        return
    
    # Filter by min_n and/or max_n if specified
    if min_n is not None or max_n is not None:
        filtered_files = []
        for input_file in input_files:
            base_name = Path(input_file).stem  # Gets "L5" from "L5.txt"
            # Extract n from "Ln" format
            if base_name.startswith("L") and base_name[1:].isdigit():
                n = int(base_name[1:])
                # Check bounds
                if min_n is not None and n < min_n:
                    continue
                if max_n is not None and n > max_n:
                    continue
                filtered_files.append(input_file)
        input_files = filtered_files
    
    if not input_files:
        bounds_str = []
        if min_n is not None:
            bounds_str.append(f"n >= {min_n}")
        if max_n is not None:
            bounds_str.append(f"n <= {max_n}")
        bounds_msg = " with " + " and ".join(bounds_str) if bounds_str else ""
        print(f"No L*.txt files found{bounds_msg}")
        return
    
    print(f"Found {len(input_files)} automata to learn")
    print(f"Input directory: {input_dir}/")
    print(f"Output directory: {output_dir}/")
    if min_n is not None:
        print(f"Min n: {min_n}")
    if max_n is not None:
        print(f"Max n: {max_n}")
    print()
    
    success_count = 0
    fail_count = 0
    total_start_time = time.time()
    
    for input_file in input_files:
        # Extract the base name (e.g., "L5" from "examples/Ln/L5.txt")
        base_name = Path(input_file).stem  # Gets "L5" from "L5.txt"
        
        # Output files
        log_file = os.path.join(output_dir, f"{base_name}.log")
        learned_file = os.path.join(output_dir, f"{base_name}_learned.txt")
        
        print(f"Learning {base_name}...", end=" ", flush=True)
        
        # Start timing
        start_time = time.time()
        
        # Get script directory and root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(script_dir))
        
        # Call ralt_quiet.py from root directory
        ralt_quiet_path = os.path.join(root_dir, "ralt_quiet.py")
        cmd = [
            sys.executable,
            ralt_quiet_path,
            "--inp", input_file,
            "--out", learned_file
        ]
        
        try:
            with open(log_file, 'w') as log_f:
                result = subprocess.run(
                    cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=True,
                    timeout=3600  # 1 hour timeout per automaton
                )
            elapsed_time = time.time() - start_time
            print(f"✓ ({elapsed_time:.2f}s)")
            success_count += 1
            
            # Record timing
            with open(timing_log_file, 'a') as f:
                f.write(f"{base_name}.txt\t{elapsed_time:.2f}\n")
        except subprocess.TimeoutExpired:
            elapsed_time = time.time() - start_time
            print(f"✗ TIMEOUT ({elapsed_time:.2f}s)")
            fail_count += 1
            # Record timeout in timing log
            with open(timing_log_file, 'a') as f:
                f.write(f"{base_name}.txt\tTIMEOUT ({elapsed_time:.2f}s)\n")
            # Clean up partial files
            if os.path.exists(learned_file):
                os.remove(learned_file)
        except subprocess.CalledProcessError as e:
            elapsed_time = time.time() - start_time
            print(f"✗ ERROR ({elapsed_time:.2f}s)")
            fail_count += 1
            # Record error in timing log
            with open(timing_log_file, 'a') as f:
                f.write(f"{base_name}.txt\tERROR ({elapsed_time:.2f}s)\n")
            # Clean up partial files
            if os.path.exists(learned_file):
                os.remove(learned_file)
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"✗ ERROR: {str(e)[:50]} ({elapsed_time:.2f}s)")
            fail_count += 1
            # Record error in timing log
            with open(timing_log_file, 'a') as f:
                f.write(f"{base_name}.txt\tERROR ({elapsed_time:.2f}s)\n")
            # Clean up partial files
            if os.path.exists(learned_file):
                os.remove(learned_file)
    
    total_elapsed_time = time.time() - total_start_time
    
    print()
    print("=" * 60)
    print(f"Summary: {success_count} succeeded, {fail_count} failed")
    print(f"Total time: {total_elapsed_time:.2f}s ({total_elapsed_time/60:.2f} minutes)")
    print(f"Output directory: {output_dir}/")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Learn all Ln automata from examples/Ln/"
    )
    parser.add_argument(
        '--min-n',
        type=int,
        default=None,
        help='Minimum value of n to process (e.g., 10 means only learn L10, L15, ..., L50). If not specified, no lower bound is applied.'
    )
    parser.add_argument(
        '--max-n',
        type=int,
        default=None,
        help='Maximum value of n to process (e.g., 50 means only learn L5, L10, ..., L50). If not specified, no upper bound is applied.'
    )
    
    args = parser.parse_args()
    
    learn_ln_batch(min_n=args.min_n, max_n=args.max_n)

