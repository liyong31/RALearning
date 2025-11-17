#!/usr/bin/env python3
import argparse
from dra import RegisterAutomaton
from alphabet import Alphabet, LetterType
from learner import RegisterAutomatonLearner
from teacher import Teacher
import sys
import re
import example

# ---------------------------
# Robust from_text parser
# ---------------------------

def parse_ra_file(filename: str) -> RegisterAutomaton:
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()
        ra = RegisterAutomaton.from_text(text)
        # first normalise the automaton
        # print(ra.to_text())
        print("Normalising the input RA...")
        normalised_ra = ra.get_normalised_dra()
        return normalised_ra

# ---------------------------
# Command line parser
# ---------------------------

def main():
    # target = example.get_example_ra_5()
    # print(target.to_text())
    parser = argparse.ArgumentParser(description=
                                     "RALT: Read a Register Automaton and learn its minimal canonical form\n"
                                     "using an active learning approach.")
    parser.add_argument('--inp', metavar='path', required=True,
                        help='path to input DRA file')
    parser.add_argument('--out', metavar='path', required=True,
                        help='path to output DRA')
    args = parser.parse_args()

    # Parse input RA
    target = parse_ra_file(args.inp)
    print("Target DRA:\n", target.to_text())

    teacher = Teacher(target)
    learner = RegisterAutomatonLearner(teacher, target.alphabet)
    print(f"Initialisation ==============================================")
    learner.start_learning()
    learner.observation_table.pretty_print()

    hypothesis = None
    num_iterations = 1
    while True:
        hypothesis = learner.get_hypothesis()
        print(f"Iteration {num_iterations} ==============================================")
        print("Current observation table:\n")
        learner.observation_table.pretty_print()
        print("\nCurrent Hypothesis:\n", hypothesis.to_dot())

        equivalent, counterexample = teacher.equivalence_query(
            hypothesis)

        if equivalent :
            break
        print("Counterexample found:", counterexample)
        learner.refine_hypothesis(counterexample)
        num_iterations += 1

    print(f"Learning completed ==============================================")
    print("Final Hypothesis:\n")
    print(hypothesis.to_dot())
    print("Statistics:")
    print("#MQ", teacher.num_membership_queries)
    print("#EQ", teacher.num_equivalence_queries)
    print("#MM", teacher.num_memorability_queries)
    
    # Write output RA
    if hypothesis is not None:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(hypothesis.to_text())
    else:
        print("No hypothesis generated.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
