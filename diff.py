from typing import List, Set, Tuple, Callable, Optional, Iterable
import itertools

import alphabet
from alphabet import Letter, LetterSeq
from dra import RegisterAutomaton

import bisect
from sortset import SortedSet

from collections import deque
from typing import Optional, List, Tuple

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
    already_queued = set()
    queue = deque([((loc_u, reg_u), (loc_v, reg_v), [])])
    already_queued.add((loc_u, tuple(reg_u.letters), loc_v, tuple(reg_v.letters)))

    while queue:
        (l1, r1), (l2, r2), w_prefix = queue.popleft()
        # already_queued makes sure we do not revisit
        # key = (l1, tuple(r1.letters), l2, tuple(r2.letters))

        # ---- Step 3: Explore all possible next-letter transitions ----
        # For correctness, we symbolically explore all combinations of next transitions
        all_letters = r1.concat(r2)
        next_letters = SortedSet(
            all_letters.get_letter_extension(A.alphabet.comparator).letters
        )
        # print("r1 ", r1)
        # print("r2 ", r2)
        # print("next_letters ", next_letters)
        for next_letter in next_letters:
            for t1 in A.locations[l1].transitions:
                input_tau1 = r1.append(next_letter)
                # skip if letter does not satisfy transition guard
                if not A.alphabet.test_type(input_tau1, t1.tau):
                    continue
                for t2 in B.locations[l2].transitions:
                    # print("chosen letter ", next_letter)
                    input_tau2 = r2.append(next_letter)
                    if not A.alphabet.test_type(input_tau2, t2.tau):
                        continue
                    new_r1 = input_tau1.remove_by_indices(t1.indices_to_remove)
                    new_r2 = input_tau2.remove_by_indices(t2.indices_to_remove)
                    new_w = w_prefix + [next_letter]
                    # If one configuration is accepting and the other is not → found distinguishing w
                    if (
                        A.locations[t1.target].accepting
                        != B.locations[t2.target].accepting
                    ):
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
                        queue.append(
                            ((t1.target, new_r1), (t2.target, new_r2), new_w)
                        )
                        already_queued.add((
                            t1.target,
                            tuple(new_r1.letters),
                            t2.target,
                            tuple(new_r2.letters)
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
    target: RegisterAutomaton, queued: Set[Key_Type], key: Key_Type
) -> bool:
    if key in queued:
        return False
    for existing_key in queued:
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
                return False
    return True

def get_near_b_letter(target: RegisterAutomaton, u_sorted: LetterSeq, a: Letter) -> Letter:
    index = u_sorted.index(a)
    b = None
    if index == 0:
        b = target.alphabet.make_letter(a.value - 0.5)
    elif index == len(u_sorted) - 1:
        b = target.alphabet.make_letter(a.value + 0.5)
    else:
        b = target.alphabet.make_letter((a.value + u_sorted[index + 1].value) / 2.0)
    return b

def get_near_seq(target: RegisterAutomaton
                 , u: LetterSeq
                 , u_sorted: LetterSeq
                 , a: Letter) -> Tuple[Letter, LetterSeq]:
    b = get_near_b_letter(target, u_sorted, a)
    # we try to replace b with a, and check whether map(u) and u can be distinguished by some v
    def replace_a_with_b(c: Letter) -> Letter:
        if c == a:
            return b
        else:
            return c
    uprime = target.alphabet.apply_map(u, replace_a_with_b)
    return (b, uprime)

def get_memorable_witness(target: RegisterAutomaton
                          , u: LetterSeq
                          , u_sorted: LetterSeq
                          , a: Letter):
    
    b, uprime = get_near_seq(target, u, u_sorted, a)
    # 1. find distinguished word
    # print("u ", u, "up ", uprime)
    suffix = find_difference(target, u, target, uprime, None)
    # find_distinguishing_seq(target, u, uprime, a, replace_a_with_b)
    return (suffix, b, uprime)

def get_sorted_seq(u : LetterSeq):
    return sorted(set(u.letters), key=lambda x: x.value)

def get_memorable_seq(target: RegisterAutomaton, u: LetterSeq):
    # bs = u.get_letter_extension(target.alphabet.comparator)
    u_sorted = get_sorted_seq(u)
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

def has_similar_configurations(
    target: RegisterAutomaton, queued: Set[Key_Type], key: Key_Type
 )-> bool:
    if key in queued:
        return False
    for existing_key in queued:
        l1_e, r1_e, l2_e, r2_e = existing_key
        l1_k, r1_k, l2_k, r2_k = key
        r1_seq_e = target.alphabet.form_sequence(list(r1_e))
        r1_seq_k = target.alphabet.form_sequence(list(r1_k))
        r2_seq_e = target.alphabet.form_sequence(list(r2_e))
        r2_seq_k = target.alphabet.form_sequence(list(r2_k))
        if l1_e == l1_k and l2_e == l2_k:
            if target.alphabet.test_type(r1_seq_e, r2_seq_e) and target.alphabet.test_type(r1_seq_k, r2_seq_k):
                return False
    return True
    

# find two words that distinguish two configurations of a RA
# TODO proof of the algorithm
def find_distinguishing_words(
    A: RegisterAutomaton, u: LetterSeq, B: RegisterAutomaton, v: LetterSeq
    , is_memorable : bool
) -> Optional[Tuple[LetterSeq, LetterSeq]]:
    """
    Decide whether there exists a word w such that A accepts uw but B rejects vw.
    u and v must be of the same type (same comparison pattern).
    """
    if A.alphabet.letter_type != B.alphabet.letter_type:
        raise Exception("Two automata letter_type mismatch")
    # print(A.to_dot())
    # ---- Step 0: Preprocessing, check whether a state is sink rejecting

    sink_locs_A = A.get_sink_rejecting_locations()
    sink_locs_B = B.get_sink_rejecting_locations()
    # ---- Step 1: Compute resulting configurations of u and v ----
    conf_u = A.run(u)[-1]  # (loc_u, reg_u, _)
    conf_v = B.run(v)[-1]  # (loc_v, reg_v, _)
    loc_u, reg_u, _ = conf_u
    loc_v, reg_v, _ = conf_v
    # print("loc_u ", loc_u, " loc_v ", loc_v)
    # print("reg_u ", reg_u, " reg_v ", reg_v)

    pre_u = reg_u
    pre_v = reg_v
    a = None
    b = None

    if is_memorable:
        # only need to ignore the part that differs in u and v
        # except two letters, u and v should be the same
        r = A.alphabet.empty_sequence()
        for i in range(len(u)):
            # print(f"reg_u[{i}]=", u.get_letter(i))
            # print(f"reg_v[{i}]=", v.get_letter(i))
            # print(f"u[i] == v[i]", u.get_letter(i) == v.get_letter(i))
            if u.get_letter(i) == v.get_letter(i):
                r = r.append(u.get_letter(i))
            else:
                a = u.get_letter(i)
                b = v.get_letter(i)
        pre_u = pre_v = r            
    
    # if two states have different acceptance status, return empty word
    if A.locations[loc_u].accepting != B.locations[loc_v].accepting:
        return A.alphabet.empty_sequence(), A.alphabet.empty_sequence()

    # ---- Step 2: BFS over configuration pairs ----
    # Each element in the queue is ((loc1, reg1), (loc2, reg2), w_prefix)
    already_queued = set()
    queue = deque([((loc_u, reg_u), (loc_v, reg_v), [], [])])
    already_queued.add((loc_u, tuple(reg_u.letters), loc_v, tuple(reg_v.letters)))

    while queue:
        (l1, r1), (l2, r2), w1_prefix, w2_prefix = queue.popleft()
        # already_queued makes sure we do not revisit
        # key = (l1, tuple(r1.letters), l2, tuple(r2.letters))

        # ---- Step 3: Explore all possible next-letter transitions ----
        # For correctness, we symbolically explore all combinations of next transitions
        w1_seq = A.alphabet.form_sequence(w1_prefix)
        w2_seq = A.alphabet.form_sequence(w2_prefix)
        
        w1_next_letters = SortedSet(
                pre_u.concat(r1).concat(w1_seq).get_letter_extension(A.alphabet.comparator).letters
            )
        
        w2_next_letters = SortedSet(
                pre_v.concat(r2).concat(w2_seq).get_letter_extension(A.alphabet.comparator).letters
            )
        
        if a is not None and b is not None:
            w1_next_letters.add(a)
            w2_next_letters.add(b)
        
        # print("r1 ", r1)
        # print("r2 ", r2)
        for a1 in w1_next_letters:
            for t1 in A.locations[l1].transitions:
                input_tau1 = r1.append(a1)
                # print(f" tau1 {t1.tau} input1 {input_tau1}")
                # skip if letter does not satisfy transition guard
                if not A.alphabet.test_type(input_tau1, t1.tau):
                    continue
                for a2 in w2_next_letters:
                    for t2 in B.locations[l2].transitions:
                        # print("chosen letter ", next_letter)
                        input_tau2 = r2.append(a2)
                        # print(f" tau2 {t2.tau} input2 {input_tau2}")
                        if not B.alphabet.test_type(input_tau2, t2.tau):
                            continue
                        new_r1 = input_tau1.remove_by_indices(t1.indices_to_remove)
                        new_r2 = input_tau2.remove_by_indices(t2.indices_to_remove)
                        new_w1 = w1_prefix + [a1]
                        new_w2 = w2_prefix + [a2]
                        
                        new_w1_seq = A.alphabet.form_sequence(new_w1)
                        new_w2_seq = A.alphabet.form_sequence(new_w2)
                        # print(f"next pair ({t1.target}, {t2.target})")
                        # print(f"new_w1 {new_w1_seq}, new_w2 {new_w2_seq}")
                        # must be the same type
                        if not A.alphabet.test_type(pre_u.concat(new_w1_seq), pre_v.concat(new_w2_seq)):
                            continue
                        # if is_memorable and not A.alphabet.test_type(new_w1_seq, new_w2_seq):
                        # #     continue
                        # If one configuration is accepting and the other is not → found distinguishing w
                        if (
                            A.locations[t1.target].accepting
                            != B.locations[t2.target].accepting
                        ):
                            # if is_memorable and not A.alphabet.test_type(reg_u.concat(new_w1_seq), reg_v.concat(new_w2_seq)):
                            #     # we need to make sure that aw1 and bw2 not equal
                            #     return new_w1_seq, new_w2_seq
                            # elif not is_memorable:
                            return new_w1_seq, new_w2_seq
                        if (
                            t1.target not in sink_locs_A or t2.target not in sink_locs_B
                        ) and has_similar_configurations(
                            A,
                            already_queued,
                            (
                                t1.target,
                                tuple(new_r1.letters),
                                t2.target,
                                tuple(new_r2.letters),
                            ),
                        ):
                            queue.append(
                                ((t1.target, new_r1), (t2.target, new_r2), new_w1, new_w2)
                            )
                            already_queued.add((
                                t1.target,
                                tuple(new_r1.letters),
                                t2.target,
                                tuple(new_r2.letters)
                            ))

    # No distinguishing word found
    return None