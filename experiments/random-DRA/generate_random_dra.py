#!/usr/bin/env python3
"""
Batch generator and learner for register automata.
Procedure:
1. Generate a target automaton of given size
2. If size < 5, discard and regenerate
3. Use ralt.py to learn the target automaton
4. If #States-hypothesis is a multiple of 5, copy learned automaton to corresponding size folder
5. Continue until we have the target number of automata for each size:
   - Size 10: 20 automata
   - Size 15, 20: 30 automata
   - Size 25, 30, 35: 40 automata
   - Size 40, 45, 50: 44 automata
   - Size 5: 20 automata (default)
"""

import subprocess
import sys
import os
import random
import re
import shutil
from pathlib import Path

# Import to verify automaton size
# Add root directory to path to import dra module
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, root_dir)
from dra import RegisterAutomaton

def extract_hypothesis_states(log_file_path):
    """
    Extract #States-hypothesis from the end of a log file.
    Returns the number of states or None if not found.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Search from the end backwards
        for line in reversed(lines):
            line = line.strip()
            match = re.search(r'#States-hypothesis\s*:\s*(\d+)', line)
            if match:
                return int(match.group(1))
        
        return None
    except Exception as e:
        print(f"    Error reading log file {log_file_path}: {e}")
        return None

def generate_and_learn_automata(max_automata_per_size=50, max_size=50):
    """
    Generate target automata, learn them, and organize by hypothesis size.
    Target sizes are randomly selected from target_sizes for each iteration.
    
    Args:
        max_automata_per_size: Maximum number of automata to collect for each hypothesis size (default, used for sizes not in mapping)
        max_size: Maximum hypothesis size to collect (default 50)
    """
    # Sizes we want to collect: 5, 10, 15, ..., max_size
    target_sizes = list(range(5, max_size + 1, 5))
    # Sizes we will consider for generation
    target_sizes2 = list(range(5, max_size + 5, 1))
    # Mapping from hypothesis size to number of automata to collect
    size_to_count = {
        5: 50,   # Default for size 5 (not specified by user)
        10: 50,
        15: 50,
        20: 50,
        25: 50,
        30: 50,
        35: 50,
        40: 50,
        45: 50,
        50: 50,
    }
    
    # Track how many automata we have for each size
    size_counts = {size: 0 for size in target_sizes}
    
    # Get the target count for each size
    size_targets = {size: size_to_count.get(size, max_automata_per_size) for size in target_sizes}
    
    # Get script directory and root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(script_dir))
    
    # Directory for generated automata
    generated_dir = "generated-DRA"
    os.makedirs(generated_dir, exist_ok=True)
    
    # Create subdirectories for each target size in generated-DRA
    for size in target_sizes:
        size_dir = os.path.join(generated_dir, f"size{size}")
        os.makedirs(size_dir, exist_ok=True)
    
    # Output directory for learned automata (if needed)
    output_dir = "generated-DRA"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create subdirectories for each target size
    for size in target_sizes:
        size_dir = os.path.join(output_dir, f"size{size}")
        os.makedirs(size_dir, exist_ok=True)
    
    print(f"Generating target automata from sizes: {target_sizes}")
    print(f"Collecting learned automata with hypothesis sizes: {target_sizes}")
    print(f"Target counts per size: {size_targets}")
    print(f"Generated automata directory: {generated_dir}/")
    print(f"Output directory: {output_dir}/")
    print()
    
    iteration = 0
    max_iterations = 10000  # Safety limit
    
    while iteration < max_iterations:
        # Check if we've collected enough for all sizes
        if all(size_counts[size] >= size_targets[size] for size in target_sizes):
            print("\n✓ Collected enough automata for all sizes!")
            break
        
        iteration += 1
        
        # Randomly select target size from target_sizes
        target_size = random.choice(target_sizes2)
        
        # Generate a random seed
        seed = random.randint(0, 2**31 - 1)
        
        # Temporary files (using unique filenames with seed)
        temp_target_file = f"temp_target_seed{seed}.txt"
        temp_learned_file = f"temp_learned_seed{seed}.txt"
        temp_log_file = f"temp_learned_seed{seed}.log"
        
        # Step 1: Generate target automaton
        print(f"[{iteration}] Generating target (size {target_size}, seed {seed})...", end=" ", flush=True)
        
        max_retries = 100
        retry_count = 0
        actual_seed = seed
        generation_success = False
        
        while retry_count < max_retries and not generation_success:
            if retry_count > 0:
                actual_seed = random.randint(0, 2**31 - 1)
                temp_target_file = f"temp_target_seed{actual_seed}.txt"
                temp_learned_file = f"temp_learned_seed{actual_seed}.txt"
                temp_log_file = f"temp_learned_seed{actual_seed}.log"
            
            # Run genra.py from root directory
            genra_path = os.path.join(root_dir, "genra.py")
            cmd_gen = [
                sys.executable,
                genra_path,
                "--num", str(target_size-1),
                "--seed", str(actual_seed),
                "--out", temp_target_file
            ]
            
            try:
                result = subprocess.run(
                    cmd_gen,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=5
                )
                
                # Verify the generated automaton has size >= 5
                if os.path.exists(temp_target_file):
                    try:
                        with open(temp_target_file, 'r') as f:
                            text_data = f.read()
                        ra = RegisterAutomaton.from_text(text_data)
                        actual_size = ra.get_num_states()
                        
                        if actual_size >= 5:
                            generation_success = True
                        else:
                            os.remove(temp_target_file)
                            retry_count += 1
                    except Exception as e:
                        if os.path.exists(temp_target_file):
                            os.remove(temp_target_file)
                        retry_count += 1
                else:
                    retry_count += 1
                    
            except subprocess.TimeoutExpired:
                if os.path.exists(temp_target_file):
                    os.remove(temp_target_file)
                retry_count += 1
            except subprocess.CalledProcessError:
                if os.path.exists(temp_target_file):
                    os.remove(temp_target_file)
                retry_count += 1
        
        if not generation_success:
            print("✗ Failed to generate valid target")
            continue
        
        print("✓", end=" ", flush=True)
        
        # Step 2: Learn the target automaton
        print("Learning...", end=" ", flush=True)
        
        # Run ralt.py from root directory
        ralt_path = os.path.join(root_dir, "ralt.py")
        cmd_learn = [
            sys.executable,
            ralt_path,
            "--inp", temp_target_file,
            "--out", temp_learned_file
        ]
        
        try:
            with open(temp_log_file, 'w') as log_f:
                result = subprocess.run(
                    cmd_learn,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=True,
                    timeout=120  # 1 hour timeout
                )
        except subprocess.TimeoutExpired:
            print("✗ TIMEOUT")
            # Clean up
            for f in [temp_target_file, temp_learned_file, temp_log_file]:
                if os.path.exists(f):
                    os.remove(f)
            continue
        except subprocess.CalledProcessError:
            print("✗ Learning failed")
            # Clean up
            for f in [temp_target_file, temp_learned_file, temp_log_file]:
                if os.path.exists(f):
                    os.remove(f)
            continue
        
        # Step 3: Extract hypothesis size from log
        hypothesis_size = extract_hypothesis_states(temp_log_file)
        
        if hypothesis_size is None:
            print("✗ Could not extract hypothesis size")
            # Clean up
            for f in [temp_target_file, temp_learned_file, temp_log_file]:
                if os.path.exists(f):
                    os.remove(f)
            continue
        
        print(f"✓ Hypothesis: {hypothesis_size} states", end=" ", flush=True)
        
        # Step 4: Save learned automaton to generated-DRA if size is a multiple of 5 or in target_sizes
        should_save = (hypothesis_size % 5 == 0) or (hypothesis_size in target_sizes)
        
        if should_save and os.path.exists(temp_learned_file):
            # Create directory for hypothesis size if it doesn't exist
            learned_size_dir = os.path.join(generated_dir, f"size{hypothesis_size}")
            os.makedirs(learned_size_dir, exist_ok=True)
            learned_file = os.path.join(learned_size_dir, f"seed{actual_seed}_learned.txt")
            shutil.copy2(temp_learned_file, learned_file)
        
        # Step 5: Check if hypothesis size is a multiple of 5 and within range for counting
        if hypothesis_size % 5 == 0 and hypothesis_size in target_sizes:
            # Get target count for this size
            target_count = size_targets[hypothesis_size]
            # Check if we still need more for this size
            if size_counts[hypothesis_size] < target_count:
                size_counts[hypothesis_size] += 1
                if should_save:
                    print(f"→ Saved to size{hypothesis_size}/ ({size_counts[hypothesis_size]}/{target_count})")
                else:
                    print(f"→ ({size_counts[hypothesis_size]}/{target_count})")
            else:
                if should_save:
                    print(f"→ Saved to size{hypothesis_size}/ (already have enough)")
                else:
                    print(f"→ Already have enough for size{hypothesis_size}")
        elif should_save:
            print(f"→ Saved to size{hypothesis_size}/")
        else:
            print(f"→ Not a multiple of 5 or in target_sizes")
        
        # Clean up temporary files
        for f in [temp_target_file, temp_learned_file, temp_log_file]:
            if os.path.exists(f):
                os.remove(f)
        
        # Print progress summary every 10 iterations
        if iteration % 10 == 0:
            print(f"\nProgress: {dict(size_counts)}")
            print()
    
    # Final summary
    print("\n" + "="*60)
    print("Final Summary:")
    for size in target_sizes:
        count = size_counts[size]
        target_count = size_targets[size]
        status = "✓" if count >= target_count else f"({target_count - count} remaining)"
        print(f"  size{size}: {count}/{target_count} {status}")
    print(f"\nTotal iterations: {iteration}")
    print(f"Output directory: {output_dir}/")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate target automata, learn them, and organize by hypothesis size"
    )
    parser.add_argument(
        '--max-per-size',
        type=int,
        default=50,
        help='Maximum number of automata to collect per hypothesis size (default: 50)'
    )
    parser.add_argument(
        '--max-size',
        type=int,
        default=50,
        help='Maximum hypothesis size to collect (default: 50)'
    )
    
    args = parser.parse_args()
    
    if args.max_size < 5 or args.max_size % 5 != 0:
        print("Error: max-size must be >= 5 and a multiple of 5")
        sys.exit(1)
    
    generate_and_learn_automata(
        max_automata_per_size=args.max_per_size,
        max_size=args.max_size
    )

