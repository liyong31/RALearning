#!/usr/bin/env python3
import argparse
from dra import RegisterAutomaton
from alphabet import Alphabet, LetterType
from learner import RegisterAutomatonLearner
from teacher import Teacher
import sys
import re

# ---------------------------
# Robust from_text parser
# ---------------------------

def parse_ra_file(filename: str) -> RegisterAutomaton:
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()
        ra = RegisterAutomaton.from_text(text)
        return ra

# ---------------------------
# Command line parser
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Read a Register Automaton and learn its minimal canonical form")
    parser.add_argument("i", help="Input RA text file")
    parser.add_argument("o", help="Output RA text file")
    args = parser.parse_args()

    # Parse input RA
    target = parse_ra_file(args.i)
    teacher = Teacher(target)
    learner = RegisterAutomatonLearner(teacher, target.alphabet)
    learner.start_learning()

    num_iterations = 0
    hypothesis = None
    while True:
        hypothesis = learner.get_hypothesis()
        print("Current Hypothesis:\n", hypothesis.to_dot())

        equivalent, counterexample = teacher.equivalence_query(
            hypothesis)

        if equivalent :
            print("Final hypothesis:\n", hypothesis)
            print(hypothesis.to_dot())
            break

        learner.refine_hypothesis(counterexample)
        num_iterations += 1

    print("#MQ", teacher.num_membership_queries)
    print("#EQ", teacher.num_equivalence_queries)
    print("#MM", teacher.num_memorability_queries)
    print("Learning completed.")
    
    # Write output RA
    if hypothesis is not None:
        with open(args.o, "w", encoding="utf-8") as f:
            f.write(hypothesis.to_text())
    else:
        print("No hypothesis generated.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
