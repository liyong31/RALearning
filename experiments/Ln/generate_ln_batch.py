#!/usr/bin/env python3
"""
Batch generator for Ln automata.
Calls generate_ln.py for n = 5, 10, 15, ..., 100
"""

import subprocess
import sys
import os

def generate_ln_batch():
    """Generate Ln automata for n = 5, 10, 15, ..., 100"""
    # Values of n to generate: 5, 10, 15, ..., 100
    n_values = list(range(1, 26, 1))
    
    # Create generated-DRA directory
    generated_dir = "generated-DRA"
    os.makedirs(generated_dir, exist_ok=True)
    
    print(f"Generating Ln automata for n = {n_values}")
    print(f"Total: {len(n_values)} automata")
    print(f"Output directory: {generated_dir}/")
    print()
    
    success_count = 0
    fail_count = 0
    
    for n in n_values:
        print(f"Generating L{n}...", end=" ", flush=True)
        
        # Output file path
        output_file = os.path.join(generated_dir, f"L{n}.txt")
        
        # Call generate_ln.py from same directory
        cmd = [
            sys.executable,
            "generate_ln.py",
            str(n),
            "--out", output_file
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60  # 1 minute timeout per automaton
            )
            print("✓")
            success_count += 1
        except subprocess.TimeoutExpired:
            print("✗ TIMEOUT")
            fail_count += 1
        except subprocess.CalledProcessError as e:
            print(f"✗ ERROR: {e.stderr[:50] if e.stderr else 'Unknown error'}")
            fail_count += 1
        except Exception as e:
            print(f"✗ ERROR: {str(e)[:50]}")
            fail_count += 1
    
    print()
    print("=" * 60)
    print(f"Summary: {success_count} succeeded, {fail_count} failed")
    print(f"Output directory: {generated_dir}/")

if __name__ == "__main__":
    generate_ln_batch()

