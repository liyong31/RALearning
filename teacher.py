from typing import List, Set, Tuple, Callable, Optional, Iterable
import itertools

import alphabet
from alphabet import Letter, LetterSeq
from dra import RegisterAutomaton

import bisect

from collections import deque
from typing import Optional, List, Tuple


# equivalence checking between two configurations of two RAs
def find_difference(
    A: RegisterAutomaton, u: LetterSeq, B: RegisterAutomaton, v: LetterSeq
) -> Optional[LetterSeq]:
    """
    Decide whether there exists a word w such that A accepts uw but B rejects vw.
    u and v must be of the same type (same comparison pattern).
    """
    if A.alphabet.letter_type != B.alphabet.letter_type:
        raise Exception("Two automata letter_type mismatch")

    # ---- Step 0: Preprocessing, check whether a state is sink rejecting
    def is_sink_rejecting(loc_id: int, automaton: RegisterAutomaton) -> bool:
        loc = automaton.locations[loc_id]
        if loc.accepting:
            return False
        for transition in loc.transitions:
            if transition.target != loc_id:
                return False
        return True

    def get_sink_rejecting_locs(automaton: RegisterAutomaton) -> Set[int]:
        sink_locs = set()
        for loc_id, loc in automaton.locations.items():
            if is_sink_rejecting(loc_id, automaton):
                sink_locs.add(loc_id)
        return sink_locs

    sink_locs_A = get_sink_rejecting_locs(A)
    sink_locs_B = get_sink_rejecting_locs(B)

    # ---- Step 1: Compute resulting configurations of u and v ----
    conf_u = A.run(u)[-1]  # (loc_u, reg_u, _)
    conf_v = B.run(v)[-1]  # (loc_v, reg_v, _)
    loc_u, reg_u, _ = conf_u
    loc_v, reg_v, _ = conf_v

    # ---- Step 2: BFS over configuration pairs ----
    # Each element in the queue is ((loc1, reg1), (loc2, reg2), w_prefix)
    queue = deque([((loc_u, reg_u), (loc_v, reg_v), [])])
    visited = set()

    while queue:
        (l1, r1), (l2, r2), w_prefix = queue.popleft()
        # Avoid revisiting
        key = (l1, tuple(r1.letters), l2, tuple(r2.letters))
        if key in visited:
            continue
        visited.add(key)

        # ---- Step 3: Explore all possible next-letter transitions ----
        # For correctness, we symbolically explore all combinations of next transitions
        all_letters = r1.concat(r2)
        next_letters = set(
            all_letters.get_letter_extension(A.alphabet.comparator).letters
        )
        # print("r1 ", r1)
        # print("r2 ", r2)
        # print("next_letters ", next_letters)
        for next_letter in next_letters:
            for t1 in A.locations[l1].transitions:
                for t2 in B.locations[l2].transitions:
                    # print("chosen letter ", next_letter)
                    input_tau1 = r1.append(next_letter)
                    input_tau2 = r2.append(next_letter)
                    if A.alphabet.test_type(
                        input_tau1, t1.tau
                    ) and A.alphabet.test_type(input_tau2, t2.tau):
                        new_r1 = input_tau1.remove_by_indices(t1.indices_to_remove)
                        new_r2 = input_tau2.remove_by_indices(t2.indices_to_remove)
                        new_w = w_prefix + [next_letter]
                        # If one configuration is accepting and the other is not → found distinguishing w
                        if (
                            A.locations[t1.target].accepting
                            != B.locations[t2.target].accepting
                        ):
                            return A.alphabet.form_sequence(new_w)
                        if (
                            t1.target not in sink_locs_A or t2.target not in sink_locs_B
                        ) and can_add_to_queue(
                            A,
                            visited,
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

    # No distinguishing word found
    return None


Key_Type = Tuple[
    int,  # l1
    Tuple[Letter, ...],  # tuple(r1.letters)
    int,  # l2
    Tuple[Letter, ...],  # tuple(r2.letters)
]


def can_add_to_queue(
    target: RegisterAutomaton, visited: Set[Key_Type], key: Key_Type
) -> bool:
    if key in visited:
        return False
    for existing_key in visited:
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


def get_memorable_seq(target: RegisterAutomaton, u: LetterSeq):
    # bs = u.get_letter_extension(target.alphabet.comparator)
    u_sorted = sorted(set(u.letters), key=lambda x: x.value)
    memorables = set()

    # create a find method
    def find(u: List[Letter], x: Letter) -> int:
        for i, v in enumerate(u):
            if v == x:
                return i
        return -1

    for a in u.letters:
        if a in memorables:
            continue
        # print("check ", a, " memorable ", u)
        # compute a letter b such that a != b, yet, u sim_R u'
        index = find(u_sorted, a)
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
        # print("u ", u, "up ", uprime)
        suffix = find_difference(target, u, target, uprime)
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


class Teacher:
    """
    Teacher that holds a target RegisterAutomaton and answers:
      - membership_query(seq) -> bool
      - equivalence_query(hypothesis, alphabet, comp, max_len) -> (is_equivalent, counterexample)
      - memorability_query(u) -> bool

    Equivalence is checked by exhaustive testing over the provided alphabet up to max_len.
    For infinite or large alphabets provide a representative alphabet or a custom generator.
    """

    def __init__(self, target: RegisterAutomaton):
        self.target = target
        # self.mem_query_resolver = mem_query_resolver
        self.num_membership_queries = 0
        self.num_equivalence_queries = 0
        self.num_memorability_queries = 0

    def membership_query(self, seq: LetterSeq) -> bool:
        """Return whether the target RA accepts seq under comparator comp."""
        self.num_membership_queries = self.num_membership_queries + 1
        return self.target.is_accepted(seq)

    def _generate_sequences(
        self, alphabet: Iterable[Letter], max_len: int = 10
    ) -> Iterable[LetterSeq]:
        """Yield all LetterSeq over alphabet up to length max_len (includes empty)."""
        # yield empty
        yield self.target.alphabet.empty_sequence()
        alphabet_list = list(alphabet)
        for L in range(1, max_len + 1):
            for prod in itertools.product(alphabet_list, repeat=L):
                yield self.target.alphabet.form_sequence(list(prod))

    def equivalence_query(
        self,
        hypothesis: RegisterAutomaton,
        alphabet: Iterable[Letter],
        max_len: int = 4,
    ) -> Tuple[bool, Optional[LetterSeq]]:
        """
        Heuristic equivalence check: compare hypothesis against target on all sequences
        generated from `alphabet` up to length `max_len`. Returns (True, None) if no
        counterexample found, otherwise (False, counterexample).
        """
        # for seq in self._generate_sequences(alphabet, max_len):
        #     t_ans = self.target.is_accepted(seq)
        #     h_ans = hypothesis.is_accepted(seq)
        #     if t_ans != h_ans:
        #         return False, seq
        self.num_equivalence_queries = self.num_equivalence_queries + 1
        seq = find_difference(
            self.target,
            self.target.alphabet.empty_sequence(),
            hypothesis,
            hypothesis.alphabet.empty_sequence(),
        )

        if seq is not None:
            return False, seq
        return True, None

    def memorability_query(self, u: LetterSeq) -> LetterSeq:
        """
        Heuristic memorability check (placeholder): currently returns the input sequence unchanged.
        A proper implementation should, for each letter a in u, determine whether there exists
        a different letter b such that the bijective renaming D that maps a to b makes u and D(u)
        reach the same state in the target RegisterAutomaton.
        """
        self.num_memorability_queries = self.num_memorability_queries + 1
        seq = get_memorable_seq(self.target, u)
        # seq = self.mem_query_resolver(self.target, u)
        return seq


if __name__ == "__main__":
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
