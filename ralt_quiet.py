#!/usr/bin/env python3
"""
RALT (Quiet Version): Minimal logging version that only records query counts
and final automata information.
"""
import argparse
from dra import RegisterAutomaton
from alphabet import Alphabet, LetterType
from learner import RegisterAutomatonLearner
from teacher import Teacher
import sys

# ---------------------------
# Robust from_text parser
# ---------------------------

def parse_ra_file(filename: str) -> RegisterAutomaton:
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()
        ra = RegisterAutomaton.from_text(text)
        # Normalise the automaton
        normalised_ra = ra.get_normalised_dra()
        return normalised_ra
    
def execute_learner(inp_name: str, out_name: str) -> None:
    # Parse input RA
    target = parse_ra_file(inp_name)

    teacher = Teacher(target)
    learner = RegisterAutomatonLearner(teacher, target.alphabet)
    
    # Start learning (no verbose output)
    learner.start_learning()

    hypothesis = None
    num_iterations = 1
    while True:
        hypothesis = learner.get_hypothesis()
        # print("hypothesis:", hypothesis)

        equivalent, counterexample = teacher.equivalence_query(hypothesis)

        if equivalent:
            break
        
        learner.refine_hypothesis(counterexample)
        num_iterations += 1

    # Output only query counts and final statistics
    print("Query Statistics:")
    print(f"#MQ: {teacher.num_membership_queries}")
    print(f"#EQ: {teacher.num_equivalence_queries}")
    print(f"#MM: {teacher.num_memorability_queries}")
    print()
    print("Target Automaton:")
    print(f"#States: {target.get_num_states()}")
    print(f"#Trans: {target.get_num_trans()}")
    print()
    print("Hypothesis Automaton:")
    print(f"#States: {hypothesis.get_num_states()}")
    print(f"#Trans: {hypothesis.get_num_trans()}")
    
    # Write output RA
    if hypothesis is not None:
        with open(out_name, "w", encoding="utf-8") as f:
            f.write(hypothesis.to_text())
    else:
        print("No hypothesis generated.", file=sys.stderr)
        sys.exit(1)

# ---------------------------
# Command line parser
# ---------------------------

def main():
    parser = argparse.ArgumentParser(
        description="RALT (Quiet): Learn Register Automaton with minimal logging"
    )
    parser.add_argument('--inp', metavar='path', required=True,
                        help='path to input DRA file')
    parser.add_argument('--out', metavar='path', required=True,
                        help='path to output DRA')
    args = parser.parse_args()

    # Execute learner
    execute_learner(args.inp, args.out)

if __name__ == "__main__":
    main()

