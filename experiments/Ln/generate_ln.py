#!/usr/bin/env python3
"""
Generate Register Automaton for Ln where n is any positive integer.
Ln recognizes words that are strictly increasing or decreasing and have length n.
"""

import sys
import os

# Add root directory to path to import modules
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, root_dir)

from alphabet import Alphabet, LetterType, comp_lt
from dra import RegisterAutomaton

def generate_ln_automaton(n: int) -> RegisterAutomaton:
    """
    Generate a Register Automaton for Ln.
    Ln recognizes words that are strictly increasing or decreasing and have length n.
    
    Args:
        n: Positive integer, the length of words to recognize
        
    Returns:
        RegisterAutomaton recognizing Ln
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")
    
    alphabet = Alphabet(LetterType.REAL, comp_lt)
    ra = RegisterAutomaton(alphabet)
    
    # State numbering:
    # 0: initial state (empty register [])
    # 1 to n: increasing path (state n is accepting)
    # n+1 to 2n-2: decreasing path (states n+1 to 2n-2)
    # 2n-1: sink state
    
    # Add initial state with empty register
    ra.add_location(0, "[]", accepting=False)
    ra.set_initial(0)
    
    # Add increasing path states (1 to n)
    # State i has label [last_value] where last_value = (i-1).0
    # State n (accepting) has empty register []
    for i in range(1, n + 1):
        accepting = (i == n)  # Only state n is accepting
        if accepting:
            # Accepting state has empty register
            label = "[]"
        elif n == 1 and i == 1:
            # Special case for n=1: state 1 is accepting with empty register
            label = "[]"
        else:
            # Label is just the last value in the register: [(i-1).0]
            last_val = float(i - 1)
            label = f"[{last_val:.1f}]"
        ra.add_location(i, label, accepting=accepting)
    
    # Add decreasing path states (n+1 to 2n-2)
    # State i has label [last_value] where last_value = -(i-n).0
    for i in range(n + 1, 2 * n - 1):
        # Label is just the last value in the register: [-(i-n).0]
        last_val = float(-(i - n))
        label = f"[{last_val:.1f}]"
        ra.add_location(i, label, accepting=False)
    
    # Add sink state
    # For n=1, sink is state 2 (since state 1 is accepting)
    # For n>1, sink is state 2n-1
    if n == 1:
        sink_state = 2
    else:
        sink_state = 2 * n - 1
    ra.add_location(sink_state, "sink", accepting=False)
    
    # Transitions from initial state (0)
    tau_initial_inc = alphabet.make_sequence([0.0])
    if n == 1:
        # Special case: n=1, transition to accepting state with E={0} to store the value
        ra.add_transition(0, tau_initial_inc, {0}, 1)
    else:
        # Normal case: 0 -> 1 with tau=[0.0], E={}
        ra.add_transition(0, tau_initial_inc, set(), 1)
    
    # Transitions in increasing path (1 to n-1)
    # For n=1, this loop is empty (range(1, 1) is empty)
    for i in range(1, n):
        # State i has label [(i-1).0]
        # For transitions, we use the last value in the register
        last_val = float(i - 1)
        next_val = float(i)
        
        # Valid: continue increasing: i -> i+1
        tau_inc = alphabet.make_sequence([last_val, next_val])
        if i + 1 == n:
            # Transition to accepting state: E contains all positions {0,1}
            ra.add_transition(i, tau_inc, {0, 1}, i + 1)
        else:
            # Intermediate transition: E={0}
            ra.add_transition(i, tau_inc, {0}, i + 1)
        
        # Invalid: equal values go to sink: tau=[last_val, last_val], E={0,1}
        tau_eq = alphabet.make_sequence([last_val, last_val])
        ra.add_transition(i, tau_eq, {0, 1}, sink_state)
        
        # Invalid: decreasing goes to sink: tau=[last_val, last_val-1], E={0,1}
        if i > 1:
            tau_dec = alphabet.make_sequence([last_val, last_val - 1.0])
            ra.add_transition(i, tau_dec, {0, 1}, sink_state)
    
    # From state 1, can also start decreasing path (only for n > 1)
    if n > 1:
        tau_start_dec = alphabet.make_sequence([0.0, -1.0])
        if n == 2:
            # Special case: n=2 has no decreasing path states, go directly to accepting state
            # tau=[0.0,-1.0] with E={0,1} clears both values to get empty register
            ra.add_transition(1, tau_start_dec, {0, 1}, n)
        else:
            # Normal case: go to first decreasing path state n+1 with E={0}
            ra.add_transition(1, tau_start_dec, {0}, n + 1)
        
        # Invalid from state 1: equal values go to sink
        tau_1_eq = alphabet.make_sequence([0.0, 0.0])
        ra.add_transition(1, tau_1_eq, {0, 1}, sink_state)
    
    # Transitions from accepting increasing state (n)
    # For n=1, state 1 is accepting and any further input goes to sink
    # For n>1, state n has empty register [] and any further input goes to sink
    tau_any = alphabet.make_sequence([0.0])
    ra.add_transition(n, tau_any, {0}, sink_state)
    
    # Transitions in decreasing path (n+1 to 2n-3, excluding last state 2n-2)
    for i in range(n + 1, 2 * n - 2):
        # State i has register [0.0, -1.0, ..., -(i-n).0]
        # Last value in register is -(i-n).0
        last_val = float(-(i - n))
        next_val = float(-(i - n + 1))  # Next smaller value
        
        # Valid: continue decreasing: i -> i+1 with tau=[last_val, next_val], E={0}
        tau_dec = alphabet.make_sequence([last_val, next_val])
        ra.add_transition(i, tau_dec, {0}, i + 1)
        
        # Invalid: equal values go to sink: tau=[last_val, last_val], E={0,1}
        tau_eq = alphabet.make_sequence([last_val, last_val])
        ra.add_transition(i, tau_eq, {0, 1}, sink_state)
        
        # Invalid: increasing goes to sink: tau=[last_val, last_val+1], E={0,1}
        tau_inc = alphabet.make_sequence([last_val, last_val + 1.0])
        ra.add_transition(i, tau_inc, {0, 1}, sink_state)
    
    # Transitions from last decreasing state (2n-2) 
    # State 2n-2 has register [0.0, -1.0, ..., -(n-2).0]
    # Last value is -(n-2).0, next is -(n-1).0
    # Only add if there are decreasing path states (n > 2, since for n=2, range(n+1, 2n-1) is empty)
    if n > 2:
        last_decreasing_state = 2 * n - 2
        last_val = float(-(n - 2))
        next_val = float(-(n - 1))
        
        # Valid: continue decreasing to accepting state: tau=[last_val, next_val], E={0,1}
        tau_to_accepting = alphabet.make_sequence([last_val, next_val])
        ra.add_transition(last_decreasing_state, tau_to_accepting, {0, 1}, n)
        
        # Invalid transitions from last decreasing state to sink
        tau_eq = alphabet.make_sequence([last_val, last_val])
        ra.add_transition(last_decreasing_state, tau_eq, {0, 1}, sink_state)
        tau_inc = alphabet.make_sequence([last_val, last_val + 1.0])
        ra.add_transition(last_decreasing_state, tau_inc, {0, 1}, sink_state)
    
    # Sink state: all inputs loop back to sink
    tau_sink = alphabet.make_sequence([0.0])
    ra.add_transition(sink_state, tau_sink, {0}, sink_state)
    
    return ra

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate Register Automaton for Ln (strictly increasing or decreasing words of length n)"
    )
    parser.add_argument(
        'n',
        type=int,
        help='Length of words to recognize (positive integer)'
    )
    parser.add_argument(
        '--out', '-o',
        type=str,
        default=None,
        help='Output file path (default: examples/Ln/L{n}.txt)'
    )
    
    args = parser.parse_args()
    
    if args.n <= 0:
        print("Error: n must be a positive integer")
        sys.exit(1)
    
    # Generate automaton
    ra = generate_ln_automaton(args.n)
    
    # Determine output file
    if args.out:
        output_file = args.out
    else:
        # Create Ln directory if it doesn't exist
        ln_dir = "examples/Ln"
        os.makedirs(ln_dir, exist_ok=True)
        output_file = os.path.join(ln_dir, f"L{args.n}.txt")
    
    # Write to file
    text_repr = ra.to_text()
    with open(output_file, 'w') as f:
        f.write(text_repr)
    
    print(f"Generated L{args.n} automaton:")
    print(f"  States: {ra.get_num_states()}")
    print(f"  Transitions: {ra.get_num_trans()}")
    print(f"  Output: {output_file}")

if __name__ == "__main__":
    main()

