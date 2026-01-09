from typing import (
    Tuple, Set, Callable, Optional, Iterable, Any, TypeVar
)
from collections import deque

import alphabet
from alphabet import Letter, LetterSeq
from dra import RegisterAutomaton

# -------------------------------------------------
# Types
# -------------------------------------------------

Key_Type = Tuple[
    int,                 # location 1
    Tuple[Letter, ...],  # registers 1
    int,                 # location 2
    Tuple[Letter, ...],  # registers 2
]

# product configuration
Config = Tuple[int, LetterSeq, int, LetterSeq]

Transition = Any

P = TypeVar("P")
R = TypeVar("R")

# -------------------------------------------------
# Subsumption (unifies can_add_to_queue + has_similar_configurations)
# -------------------------------------------------

AbstractionRelation = Callable[
    [Tuple[LetterSeq, LetterSeq], Tuple[LetterSeq, LetterSeq]], bool
]


def subsumed(
    target: RegisterAutomaton,
    queued: Set[Key_Type],
    key: Key_Type,
    abstraction_relation: AbstractionRelation,
) -> bool:
    if key in queued:
        return True

    l1_k, r1_k, l2_k, r2_k = key
    r1_k_seq = target.alphabet.form_sequence(list(r1_k))
    r2_k_seq = target.alphabet.form_sequence(list(r2_k))

    for l1_e, r1_e, l2_e, r2_e in queued:
        if l1_e != l1_k or l2_e != l2_k:
            continue

        r1_e_seq = target.alphabet.form_sequence(list(r1_e))
        r2_e_seq = target.alphabet.form_sequence(list(r2_e))

        if abstraction_relation((r1_e_seq, r2_e_seq), (r1_k_seq, r2_k_seq)):
            return True

    return False


def join_type_relation(target: RegisterAutomaton) -> AbstractionRelation:
    def rel(old: Tuple[LetterSeq, LetterSeq], new: Tuple[LetterSeq, LetterSeq]) -> bool:
        r1_e, r2_e = old
        r1_k, r2_k = new
        return target.alphabet.test_type(r1_e.concat(r2_e), r1_k.concat(r2_k))
    return rel


def pairwise_type_relation(target: RegisterAutomaton) -> AbstractionRelation:
    def rel(old: Tuple[LetterSeq, LetterSeq], new: Tuple[LetterSeq, LetterSeq]) -> bool:
        r1_e, r2_e = old
        r1_k, r2_k = new
        return (
            target.alphabet.test_type(r1_e, r2_e)
            and
            target.alphabet.test_type(r1_k, r2_k)
        )
    return rel

# -------------------------------------------------
# Shared BFS engine
# -------------------------------------------------

NextSteps = Callable[[int, LetterSeq, int, LetterSeq, P], Iterable[Tuple[Letter, Transition, Letter, Transition]]]
Compatible = Callable[[P, Letter, Letter, LetterSeq, LetterSeq], Optional[P]]
OnDifference = Callable[[P], R]


def bfs_distinguish(
    A: RegisterAutomaton,
    B: RegisterAutomaton,
    start_conf: Config,
    sink_locs_A: Set[int],
    sink_locs_B: Set[int],
    init_payload: P,
    next_steps: NextSteps,
    compatible: Compatible,
    abstraction_relation: AbstractionRelation,
    on_difference: OnDifference,
) -> Optional[R]:
    visited: Set[Key_Type] = set()
    queue = deque([(start_conf, init_payload)])

    l1, r1, l2, r2 = start_conf
    visited.add((l1, tuple(r1.letters), l2, tuple(r2.letters)))

    while queue:
        (l1, r1, l2, r2), payload = queue.popleft()

        for a1, t1, a2, t2 in next_steps(l1, r1, l2, r2, payload):
            in1 = r1.append(a1)
            in2 = r2.append(a2)

            if not A.alphabet.test_type(in1, t1.tau):
                continue
            if not B.alphabet.test_type(in2, t2.tau):
                continue

            new_r1 = in1.remove_by_indices(t1.indices_to_remove)
            new_r2 = in2.remove_by_indices(t2.indices_to_remove)

            new_payload = compatible(payload, a1, a2, new_r1, new_r2)
            if new_payload is None:
                continue

            if A.locations[t1.target].accepting != B.locations[t2.target].accepting:
                return on_difference(new_payload)

            key: Key_Type = (
                t1.target, tuple(new_r1.letters),
                t2.target, tuple(new_r2.letters),
            )

            if (
                (t1.target not in sink_locs_A or t2.target not in sink_locs_B)
                and not subsumed(A, visited, key, abstraction_relation)
            ):
                visited.add(key)
                queue.append(((t1.target, new_r1, t2.target, new_r2), new_payload))

    return None

# -------------------------------------------------
# find_difference
# -------------------------------------------------

def find_difference(
    A: RegisterAutomaton, u: LetterSeq,
    B: RegisterAutomaton, v: LetterSeq,
    replace_map: Optional[Callable[[Letter], Letter]] = None,
) -> Optional[LetterSeq]:

    if A.alphabet.letter_type != B.alphabet.letter_type:
        raise Exception("Two automata letter_type mismatch")

    sink_A = A.get_sink_rejecting_locations()
    sink_B = B.get_sink_rejecting_locations()

    (l1, r1, _), (l2, r2, _) = A.run(u)[-1], B.run(v)[-1]

    if A.locations[l1].accepting != B.locations[l2].accepting:
        return A.alphabet.empty_sequence()

    def next_steps(l1, r1, l2, r2, w: list):
        letters = r1.concat(r2).get_letter_extension(A.alphabet.comparator).letters
        for a in set(letters):
            for t1 in A.locations[l1].transitions:
                for t2 in B.locations[l2].transitions:
                    yield a, t1, a, t2

    def compatible(w: list, a1: Letter, _a2: Letter, new_r1: LetterSeq, new_r2: LetterSeq) -> Optional[list]:
        return w + [a1]

    def on_diff(w: list) -> LetterSeq:
        return A.alphabet.form_sequence(w)

    return bfs_distinguish(
        A, B,
        (l1, r1, l2, r2),
        sink_A, sink_B,
        init_payload=[],
        next_steps=next_steps,
        compatible=compatible,
        abstraction_relation=join_type_relation(A),
        on_difference=on_diff,
    )

# -------------------------------------------------
# find_distinguishing_words
# -------------------------------------------------

def find_distinguishing_words(
    A: RegisterAutomaton, u: LetterSeq,
    B: RegisterAutomaton, v: LetterSeq,
    is_memorable: bool,
) -> Optional[Tuple[LetterSeq, LetterSeq]]:

    if A.alphabet.letter_type != B.alphabet.letter_type:
        raise Exception("Two automata letter_type mismatch")

    sink_A = A.get_sink_rejecting_locations()
    sink_B = B.get_sink_rejecting_locations()

    (l1, r1, _), (l2, r2, _) = A.run(u)[-1], B.run(v)[-1]

    if A.locations[l1].accepting != B.locations[l2].accepting:
        eps = A.alphabet.empty_sequence()
        return eps, eps

    def next_steps(l1, r1, l2, r2, payload: Tuple[list, list]):
        w1, w2 = payload
        s1 = A.alphabet.form_sequence(w1)
        s2 = B.alphabet.form_sequence(w2)

        if not is_memorable:
            L1 = r1.concat(s1)
            L2 = r2.concat(s2)
            letters1 = set(L1.get_letter_extension(A.alphabet.comparator).letters)
            letters2 = set(L2.get_letter_extension(A.alphabet.comparator).letters)
        else:
            letters1 = letters2 = set(
                r1.concat(r2).get_letter_extension(A.alphabet.comparator).letters
            )

        for a1 in letters1:
            for a2 in letters2:
                for t1 in A.locations[l1].transitions:
                    for t2 in B.locations[l2].transitions:
                        yield a1, t1, a2, t2

    def compatible(payload: Tuple[list, list], a1: Letter, a2: Letter, new_r1: LetterSeq, new_r2: LetterSeq) -> Optional[Tuple[list, list]]:
        w1, w2 = payload
        nw1, nw2 = w1 + [a1], w2 + [a2]

        s1 = A.alphabet.form_sequence(nw1)
        s2 = B.alphabet.form_sequence(nw2)

        if is_memorable:
            if not A.alphabet.test_type(s1, s2):
                return None
        else:
            if not A.alphabet.test_type(r1.concat(s1), r2.concat(s2)):
                return None

        return nw1, nw2

    def on_diff(payload: Tuple[list, list]) -> Tuple[LetterSeq, LetterSeq]:
        w1, w2 = payload
        return A.alphabet.form_sequence(w1), B.alphabet.form_sequence(w2)

    return bfs_distinguish(
        A, B,
        (l1, r1, l2, r2),
        sink_A, sink_B,
        init_payload=([], []),
        next_steps=next_steps,
        compatible=compatible,
        abstraction_relation=pairwise_type_relation(A),
        on_difference=on_diff,
    )

# -------------------------------------------------
# Preserved helpers from original diff.py (memorable witnesses)
# -------------------------------------------------

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
    suffix = find_difference(target, u, target, uprime, None)
    return (suffix, b, uprime)

def get_sorted_seq(u : LetterSeq):
    return sorted(set(u.letters), key=lambda x: x.value)

def get_memorable_seq(target: RegisterAutomaton, u: LetterSeq):
    u_sorted = get_sorted_seq(u)
    memorables = set()

    for a in u.letters:
        if a in memorables:
            continue
        suffix, _ , _ = get_memorable_witness(target, u, u_sorted, a)
        if suffix:
            memorables.add(a)

    mem_map = {}
    for idx, a in enumerate(u.letters):
        if a in memorables:
            mem_map[a] = idx

    result = target.alphabet.empty_sequence()
    for idx, a in enumerate(u.letters):
        if idx in mem_map.values():
            result = result.append(a)

    return result