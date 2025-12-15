
import sys
from dra import RegisterAutomaton
import teacher

def test_difference():
    """
        Test the difference finding procedure between two register automata
    """
    # build two RAs
    file_name = "./canos/exam9.txt"
    dra = None
    with open(file_name, 'r') as f:
        text = f.read()
        dra = RegisterAutomaton.from_text(text)
    print(dra.to_dot())
    # compare all pairs of representatives
    u = dra.alphabet.make_sequence([0, 0, 1, 2])
    v = dra.alphabet.make_sequence([0, 0, 1])
    w = teacher.find_difference(dra, u, dra, v, None)
    print(f"Difference between {u} and {v}")
    if w is not None:
        print(f"Found difference: {w}")
    else:
        print("No difference found")
        
def test_cs_and_rpni():
    """
        Test the characteristic sample generation and RPNI learner
    """
    from charc import CharacteristicSample
    from rpni import Sample, RegisterAutomatonRPNILearner
    # build RA
    file_name = "./canos/exam9.txt"
    dra = None
    with open(file_name, 'r') as f:
        text = f.read()
        dra = RegisterAutomaton.from_text(text)
    print("Original RA:")
    print(dra.to_text())
    # generate characteristic sample
    cs = CharacteristicSample(dra)
    cs.compute_characteristic_sample()
    print("Characteristic Sample:")
    # print("Positives:")
    # for pos in cs.positives:
    #     print(pos)
    # print("Negatives:")
    # for neg in cs.negatives:
    #     print(neg)
    # learn from sample
    from log import LogPrinter, LogLevel, SimpleLogger # type: ignore
    logger = SimpleLogger(
        name="RALT",
        level=LogLevel.DEBUG,
        logfile=None,
        stream=sys.stdout
    )
    log_printer = LogPrinter(logger.raw)
    
    sample = Sample(cs.positives, cs.negatives)
    learner = RegisterAutomatonRPNILearner(log_printer, sample, dra.alphabet)
    learner.is_sample_mutable = False
    # should distinguish 0 0, and 0 1 0 0.5 with 0.5
    hypothesis = learner.learn()
    print("Learned RA from Characteristic Sample:")
    print(hypothesis.to_dot())
    print(teacher.find_difference(dra, dra.alphabet.empty_sequence(), hypothesis, dra.alphabet.empty_sequence(), None))
        
        
# test_difference()
# test_cs_and_rpni()


# sys.exit(0)

file_name = "./canos/exam9.txt"
dra = None
with open(file_name, 'r') as f:
        text = f.read()
        dra = RegisterAutomaton.from_text(text)
print("Original RA:")
print(dra.to_text())
file_name = "./ra.txt"
orig = None
with open(file_name, 'r') as f:
        text = f.read()
        orig = RegisterAutomaton.from_text(text)
print("Original RA from examples/:")
print(orig.to_text())
print(teacher.find_difference(dra, dra.alphabet.empty_sequence(), orig, orig.alphabet.empty_sequence(), None))