#!/usr/bin/env python3
import argparse
from dra import RegisterAutomaton
from alphabet import Alphabet, LetterType
from learner import RegisterAutomatonLearner
from teacher import Teacher
import sys
import re
import example
from log import LogPrinter, LogLevel, SimpleLogger # type: ignore

# ---------------------------
# Robust from_text parser
# ---------------------------

def parse_ra_file(log_printer: LogPrinter, filename: str) -> RegisterAutomaton:
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()
        ra = RegisterAutomaton.from_text(text)
        # first normalise the automaton
        # print(ra.to_text())
        log_printer.info("Normalising the input RA...")
        normalised_ra = ra.get_normalised_dra()
        return normalised_ra
    
def execute_learner(log_printer: LogPrinter, inp_name:str, out_name:str) -> None:
    # Parse input RA
    target = parse_ra_file(log_printer, inp_name)
    log_printer.info("Input file:", inp_name)
    log_printer.info("Target DRA-text:\n", target.to_text())
    log_printer.debug("Target DRA-dot:\n", target.to_dot())

    teacher = Teacher(target)
    learner = RegisterAutomatonLearner(teacher, target.alphabet)
    log_printer.info(f"Initialisation ==============================================")
    learner.start_learning()
    learner.observation_table.pretty_print(log_printer.info)

    hypothesis = None
    num_iterations = 1
    while True:
        hypothesis = learner.get_hypothesis()
        log_printer.info(f"Iteration {num_iterations} ==============================================")
        log_printer.info("Current observation table:")
        learner.observation_table.pretty_print(log_printer.info)
        log_printer.debug("Current Hypothesis:\n", hypothesis.to_dot())

        equivalent, counterexample = teacher.equivalence_query(
            hypothesis)

        if equivalent :
            break
        log_printer.info("Counterexample found:", counterexample)
        learner.refine_hypothesis(counterexample)
        num_iterations += 1

    log_printer.info(f"Learning completed ==============================================")
    log_printer.debug("Final Hypothesis:\n", hypothesis.to_dot())
    log_printer.force("Query Statistics:")
    log_printer.force(f"#MQ: {teacher.num_membership_queries}")
    log_printer.force(f"#EQ: {teacher.num_equivalence_queries}")
    log_printer.force(f"#MM: {teacher.num_memorability_queries}")
    # log_printer.force()
    log_printer.force("Target Automaton:")
    log_printer.force(f"#States: {target.get_num_states()}")
    log_printer.force(f"#Trans: {target.get_num_trans()}")
    # log_printer.force()
    log_printer.force("Hypothesis Automaton:")
    log_printer.force(f"#States: {hypothesis.get_num_states()}")
    log_printer.force(f"#Trans: {hypothesis.get_num_trans()}")
    
    # Write output RA
    if hypothesis is not None:
        with open(out_name, "w", encoding="utf-8") as f:
            f.write(hypothesis.to_text())
    else:
        log_printer.error("No hypothesis generated.", file=sys.stderr)
        sys.exit(1)

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
    parser.add_argument('--verbose', type=int, choices=[0, 1, 2], default=1,
                        help='verbose level: 0 silent, 1 normal, 2 debug')
    parser.add_argument('--log', metavar='path', default='-', 
                        help='path to log file (default: stdout)')
    args = parser.parse_args()
    
    # Set logging level
    logger = SimpleLogger(
        name="RALT",
        level=LogLevel(args.verbose),
        logfile=args.log if args.log != '-' else None,
        stream=sys.stdout if args.log == '-' else None
    )
    log_printer = LogPrinter(logger.raw)
    # Parse input RA
    execute_learner(log_printer, args.inp, args.out)

if __name__ == "__main__":
    main()
