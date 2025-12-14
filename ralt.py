#!/usr/bin/env python3
import argparse
from enum import Enum, auto
from dra import Fraction, RegisterAutomaton
from alphabet import Alphabet, LetterType, comp_lt, comp_id
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

class Mode(Enum):
    ACTIVE = auto()
    PASSIVE = auto()
    CHAR = auto()
    
# ---------------------------
# Learner execution
# ---------------------------

def execute_characteristic_sample_generation(log_printer: LogPrinter, inp_name:str, out_name:str) -> None:
    # Parse input RA
    target = parse_ra_file(log_printer, inp_name)
    log_printer.info("Input file:", inp_name)
    log_printer.info("Target DRA-text:\n", target.to_text())
    log_printer.debug("Target DRA-dot:\n", target.to_dot())

    from charc import CharacteristicSample
    alphabet = target.alphabet
    cs = CharacteristicSample(target)
    log_printer.info("Computing characteristic sample...")
    cs.compute_characteristic_sample()
    
    # Write output sample
    with open(out_name, "w", encoding="utf-8") as f:
        f.write("# Characteristic Sample generated from DRA\n")
        f.write("# Positive samples:\n")
        f.write("# Format: pos: v1 v2 v3 ... vn\n")
        f.write("# Negative samples:\n")
        f.write("# Format: neg: v1 v2 v3 ... vn\n")
        compare_type = "<" if alphabet.comparator == comp_lt else "="
        f.write("alphabet:" + " " + str(alphabet.letter_type) + ", " + compare_type + "\n")
        for pos in cs.positives:
            f.write("pos: " + " ".join(str(v) for v in pos) + "\n")
        for neg in cs.negatives:
            f.write("neg: " + " ".join(str(v) for v in neg) + "\n")
    log_printer.info(f"Characteristic sample written to {out_name}.")
    
def execute_passive_learner(log_printer: LogPrinter, inp_name:str, out_name:str) -> None:
    # Parse input sample
    from rpni import Sample, RegisterAutomatonRPNILearner
    positives = []
    negatives = []
    alphabet = None
    
    convert = lambda x: float(x) if alphabet.letter_type == LetterType.REAL else Fraction(x)
    with open(inp_name, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("alphabet: "):
                alphabet_info = line[10:].strip().split(", ")
                compare_type = comp_lt if alphabet_info[1] == "<" else comp_id
                alphabet = Alphabet(alphabet_info[0], compare_type)
            elif line.startswith("pos:"):
                values = [convert(v) for v in line[4:].strip().split()]
                positives.append(values)
            elif line.startswith("neg:"):
                values = [convert(v) for v in line[4:].strip().split()]
                negatives.append(values)
    sample = Sample(positives, negatives)
    log_printer.info(f"Input sample read from {inp_name}:")
    log_printer.info(f"#Positive samples: {len(positives)}")
    log_printer.info(f"#Negative samples: {len(negatives)}")
    
    # Learn RA from sample
    learner = RegisterAutomatonRPNILearner(sample, alphabet)
    learner.is_sample_mutable = True
    log_printer.info("Learning RA from sample...")
    hypothesis = learner.learn()
    
    # Write output RA
    with open(out_name, "w", encoding="utf-8") as f:
        f.write(hypothesis.to_text())
    log_printer.info(f"Hypothesis RA written to {out_name}.")   
    
def execute_active_learner(log_printer: LogPrinter, mode: Mode, inp_name:str, out_name:str) -> None:
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

def execute_learner(log_printer: LogPrinter, mode: Mode, inp_name:str, out_name:str) -> None:
    if mode == Mode.ACTIVE:
        execute_active_learner(log_printer, inp_name, out_name)
    elif mode == Mode.PASSIVE:
        execute_passive_learner(log_printer, inp_name, out_name)
    elif mode == Mode.CHAR:
        execute_characteristic_sample_generation(log_printer, inp_name, out_name)
    else:
        log_printer.error("Unknown mode.")
        sys.exit(1) 
# ---------------------------
# Command line parser
# ---------------------------
def parse_args():
    parser = argparse.ArgumentParser(description=
                                     "RALT: Read an input and learn its minimal canonical form\n"
                                     "using an active/passive learning approach.")
    # Input/output
    parser.add_argument('--inp', metavar='path', required=True,
                        help='path to input DRA/Sample file')
    parser.add_argument('--out', metavar='path', required=True,
                        help='path to output DRA')
    
    # Verbosity / logging
    parser.add_argument('--verbose', type=int, choices=[0, 1, 2], default=1,
                        help='verbose level: 0 silent, 1 normal, 2 debug')
    parser.add_argument('--log', metavar='path', default='-', 
                        help='path to log file (default: stdout)')
    
    # Mutually exclusive modes
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--rpni', action='store_true',
                       help='Use passive learning for the samples in the input file')
    group.add_argument('--char', action='store_true',
                       help='Generate characteristic sample file from input DRA')
    args = parser.parse_args()
    return args



def main():
    # target = example.get_example_ra_5()
    # print(target.to_text())
    args = parse_args()
    
    # get execution mode
    if args.rpni:
        mode = Mode.PASSIVE
    elif args.char:
        mode = Mode.CHAR
    else:
        mode = Mode.ACTIVE
        
    # Set logging level
    logger = SimpleLogger(
        name="RALT",
        level=LogLevel(args.verbose),
        logfile=args.log if args.log != '-' else None,
        stream=sys.stdout if args.log == '-' else None
    )
    log_printer = LogPrinter(logger.raw)
    
    # Execute learner
    execute_learner(log_printer, mode, args.inp, args.out)

if __name__ == "__main__":
    main()
