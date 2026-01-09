
import sys
from dra import RegisterAutomaton, LetterSeq, Letter
from collections import deque
from typing import Optional, Callable, Set, Tuple
import alphabet
from enum import Enum, auto

# equivalence checking between two configurations of two RAs
def find_difference(
    A: RegisterAutomaton, u: LetterSeq, B: RegisterAutomaton, v: LetterSeq
    , replace_map: Optional[Callable[[Letter], Letter]] = None
) -> Optional[LetterSeq]:
    """
    Decide whether there exists a word w such that A accepts uw but B rejects vw.
    u and v must be of the same type (same comparison pattern).
    """
    if A.alphabet.letter_type != B.alphabet.letter_type:
        raise Exception("Two automata letter_type mismatch")

    # ---- Step 0: Preprocessing, check whether a state is sink rejecting
    print("============== Finding difference between u:", u, " and v:", v)
    sink_locs_A = A.get_sink_rejecting_locations()
    sink_locs_B = B.get_sink_rejecting_locations()
    # ---- Step 1: Compute resulting configurations of u and v ----
    conf_u = A.run(u)[-1]  # (loc_u, reg_u, _)
    conf_v = B.run(v)[-1]  # (loc_v, reg_v, _)
    loc_u, reg_u, _ = conf_u
    loc_v, reg_v, _ = conf_v
    
    # if two states have different acceptance status, return empty word
    if A.locations[loc_u].accepting != B.locations[loc_v].accepting:
        return A.alphabet.empty_sequence()

    # ---- Step 2: BFS over configuration pairs ----
    # Each element in the queue is ((loc1, reg1), (loc2, reg2), w_prefix)
    queue = deque([((loc_u, reg_u), (loc_v, reg_v), [])])
    already_queued = set()
    already_queued.add((loc_u, tuple(reg_u.letters), loc_v, tuple(reg_v.letters)))

    while queue:
        (l1, r1), (l2, r2), w_prefix = queue.popleft()
        # Avoid revisiting
        key = (l1, tuple(r1.letters), l2, tuple(r2.letters))

        # ---- Step 3: Explore all possible next-letter transitions ----
        # For correctness, we symbolically explore all combinations of next transitions
        all_letters = r1.concat(r2)
        next_letters = set(
            all_letters.get_letter_extension(A.alphabet.comparator).letters
        )
        # print("r1 ", r1)
        # print("r2 ", r2)
        print("first configuration: "  + str((l1, r1)))
        print("second configuration: " + str((l2, r2)))
        # print("next_letters ", next_letters)
        for next_letter in next_letters:
            for t1 in A.locations[l1].transitions:
                input_tau1 = r1.append(next_letter)
                if not A.alphabet.test_type(input_tau1, t1.tau):
                    continue
                for t2 in B.locations[l2].transitions:
                    input_tau2 = r2.append(next_letter)
                    if not A.alphabet.test_type(input_tau2, t2.tau):
                        continue
                    print("current configs: ", (l1, r1), (l2, r2))
                    print("chosen letter ", next_letter)
                    new_r1 = input_tau1.remove_by_indices(t1.indices_to_remove)
                    new_r2 = input_tau2.remove_by_indices(t2.indices_to_remove)
                    new_w = w_prefix + [next_letter]
                    # If one configuration is accepting and the other is not → found distinguishing w
                    if (
                        A.locations[t1.target].accepting
                        != B.locations[t2.target].accepting
                    ):
                        print("Distinguishing word found: " + str(new_w))
                        return A.alphabet.form_sequence(new_w)
                    # if replace_map is not None:
                    #     w = A.alphabet.form_sequence(new_w)
                    #     mapped_w = A.alphabet.apply_map(w, replace_map)
                    #     u_w = u.concat(w)
                    #     v_mapped_w = v.concat(mapped_w)
                    #     if not A.alphabet.test_type(u_w, v_mapped_w):
                    #         continue
                    if (
                        t1.target not in sink_locs_A or t2.target not in sink_locs_B
                    ) and can_add_to_queue(
                        A,
                        already_queued,
                        (
                            t1.target,
                            tuple(new_r1.letters),
                            t2.target,
                            tuple(new_r2.letters),
                        ),
                    ):
                        print("current queue:", queue)
                        print("letters: " + str(next_letter))
                        print("adding to queue: " + str((t1.target, new_r1, t2.target, new_r2, new_w)))
                        queue.append(
                            ((t1.target, new_r1), (t2.target, new_r2), new_w)
                        )
                        already_queued.add((
                            t1.target,
                            tuple(new_r1.letters),
                            t2.target,
                            tuple(new_r2.letters),
                        ))

    # No distinguishing word found
    return None


Key_Type = Tuple[
    int,  # l1
    Tuple[Letter, ...],  # tuple(r1.letters)
    int,  # l2
    Tuple[Letter, ...],  # tuple(r2.letters)
]


def can_add_to_queue(
    target: RegisterAutomaton, queue: deque[Key_Type], key: Key_Type
) -> bool:
    if key in queue:
        return False
    for existing_key in queue:
        l1_e, r1_e, l2_e, r2_e = existing_key
        l1_k, r1_k, l2_k, r2_k = key
        r1_seq_e = target.alphabet.form_sequence(list(r1_e))
        r1_seq_k = target.alphabet.form_sequence(list(r1_k))
        r2_seq_e = target.alphabet.form_sequence(list(r2_e))
        r2_seq_k = target.alphabet.form_sequence(list(r2_k))
        join_e_seq = r1_seq_e.concat(r2_seq_e)
        join_k_seq = r1_seq_k.concat(r2_seq_k)
        if l1_e == l1_k and l2_e == l2_k:
            if target.alphabet.test_type(join_e_seq, join_k_seq):
                print(  "Skipping adding to queue due to visited: " + str(key))
                return False
    return True

def get_memorable_witness(target: RegisterAutomaton
                          , u: LetterSeq
                          , u_sorted: LetterSeq
                          , a: Letter):
    index = u_sorted.index(a)
    b = None
    if index == 0:
        b = target.alphabet.make_letter(a.value - 0.5)
    elif index == len(u_sorted) - 1:
        b = target.alphabet.make_letter(a.value + 0.5)
    else:
        b = target.alphabet.make_letter((a.value + u_sorted[index + 1].value) / 2.0)

    # we try to replace b with a, and check whether map(u) and u can be distinguished by some v
    def replace_a_with_b(c: Letter) -> Letter:
        if c == a:
            return b
        else:
            return c

    uprime = target.alphabet.apply_map(u, replace_a_with_b)
    # 1. find distinguished word
    print("find distinguisging word: u ", u, "up ", uprime)
    suffix = find_difference(target, u, target, uprime, replace_map=replace_a_with_b)
    # find_distinguishing_seq(target, u, uprime, a, replace_a_with_b)
    return (suffix, b, uprime)

def get_memorable_seq(target: RegisterAutomaton, u: LetterSeq):
    # bs = u.get_letter_extension(target.alphabet.comparator)
    u_sorted = sorted(set(u.letters), key=lambda x: x.value)
    memorables = set()

    for a in u.letters:
        if a in memorables:
            continue
        # print("check ", a, " memorable ", u)
        # compute a letter b such that a != b, yet, u sim_R u'
        suffix, _ , _ = get_memorable_witness(target, u, u_sorted, a)
        # find_distinguishing_seq(target, u, uprime, a, replace_a_with_b)
        if suffix:
            # print("================= distinguished ==================")
            # print("u", u)
            # print("m(u)", uprime)
            # print("w", suffix)
            memorables.add(a)

    # only keep largest index of a memorable letter
    mem_map = {}
    for idx, a in enumerate(u.letters):
        if a in memorables:
            mem_map[a] = idx

    # obtain the corresponding memorable sequence
    result = target.alphabet.empty_sequence()
    for idx, a in enumerate(u.letters):
        if idx in mem_map.values():
            result = result.append(a)

    return result


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
    w = find_difference(dra, u, dra, v, None)
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
    print(find_difference(dra, dra.alphabet.empty_sequence(), hypothesis, dra.alphabet.empty_sequence(), None))
        
        
# test_difference()
# test_cs_and_rpni()


# sys.exit(0)

file_name = "./canos/exam10.txt"
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
print("Learned RA from examples/:")
print(orig.to_text())
print(find_difference(dra, dra.alphabet.empty_sequence(), orig, orig.alphabet.empty_sequence(), None))


# small smoke test (requires example.get_example_ra_* implementations)
try:
    import example

    target = example.get_example_ra_1()
    # teacher = Teacher(target, alphabet.comp_lt, example.solve_memorability_query_1)

    # create small real-valued alphabet sample
    a = Letter(1.0, alphabet.LetterType.REAL)
    b = Letter(2.0, alphabet.LetterType.REAL)
    c = Letter(1.5, alphabet.LetterType.REAL)
    d = Letter(4.0, alphabet.LetterType.REAL)
    seq = [a, b, c, d]
    print(seq)

    seq1 = [a, c, d]
    print(seq1)
    res = get_memorable_seq(target, LetterSeq(seq))
    print("sequence:", seq, "mem_seq:", res)
    res1 = get_memorable_seq(target, LetterSeq(seq1))
    print("sequence:", seq1, "mem_seq:", res1)

    print("-=================")
    target = example.get_example_ra_2()
    seq = [0, 1, 0, 1]
    res = get_memorable_seq(target, target.alphabet.make_sequence(seq))
    print("sequence:", seq, "mem_seq:", res)
    seq = [0, 1, 0]
    res = get_memorable_seq(target, target.alphabet.make_sequence(seq))
    print("sequence:", seq, "mem_seq:", res)
    seq = [0, 1]
    res = get_memorable_seq(target, target.alphabet.make_sequence(seq))
    print("sequence:", seq, "mem_seq:", res)
    seq = [0]
    res = get_memorable_seq(target, target.alphabet.make_sequence(seq))
    print("sequence:", seq, "mem_seq:", res)

    seq = [0, 0]
    res = get_memorable_seq(target, target.alphabet.make_sequence(seq))
    print("sequence:", seq, "mem_seq:", res)

    print("-================= example 4 =================")
    target = example.get_example_ra_4()
    seq = [0, 1]
    res = get_memorable_seq(target, target.alphabet.make_sequence(seq))
    print("sequence:", seq, "mem_seq:", res)
    seq = [0, 1, 0]
    res = get_memorable_seq(target, target.alphabet.make_sequence(seq))
    print("sequence:", seq, "mem_seq:", res)
    seq = [0, 1, 1, 1]
    res = get_memorable_seq(target, target.alphabet.make_sequence(seq))
    print("sequence:", seq, "mem_seq:", res)
    seq = [0, 1, 1, 2]
    res = get_memorable_seq(target, target.alphabet.make_sequence(seq))
    print("sequence:", seq, "mem_seq:", res)

except Exception:
    # keep __main__ minimal and not failing in CI if example/RA missing
    pass