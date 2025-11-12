from typing import List, Tuple, Callable, Optional, Iterable
import itertools

import alphabet
from alphabet import Letter, LetterSeq
from dra import RegisterAutomaton

from collections import deque
from typing import Optional, List, Tuple

def find_difference(A: RegisterAutomaton, u: LetterSeq, B: RegisterAutomaton, v: LetterSeq) -> Optional[LetterSeq]:
    """
    Decide whether there exists a word w such that A accepts uw but B rejects vw.
    u and v must be of the same type (same comparison pattern).
    """
    if A.alphabet.letter_type != B.alphabet.letter_type:
        raise Exception("Two automata letter_type mismatch")
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

        # If one configuration is accepting and the other is not → found distinguishing w
        acc1 = A.locations[l1].accepting
        acc2 = B.locations[l2].accepting
        if acc1 != acc2:
            # print("Found distinguishing word:", w_prefix)
            return w_prefix

        # Avoid revisiting
        key = (l1, tuple(r1.letters), l2, tuple(r2.letters))
        if key in visited:
            continue
        visited.add(key)

        # ---- Step 3: Explore all possible next-letter transitions ----
        # For correctness, we symbolically explore all combinations of next transitions
        next_letters = set(r1.get_letter_extension(target.alphabet.comparator).letters)
        next_letters |= set(r2.get_letter_extension(target.alphabet.comparator).letters)
        for next_letter in next_letters:
            for t1 in A.locations[l1].transitions:
                for t2 in B.locations[l2].transitions:
                    input_tau1 = r1.append(next_letter)
                    input_tau2 = r2.append(next_letter)
                    if A.alphabet.test_type(input_tau1, t1.tau) and A.alphabet.test_type(input_tau2, t2.tau):
                    # Do NOT require same type here.
                        new_r1 = input_tau1.remove_by_indices(t1.indices_to_remove)
                        new_r2 = input_tau2.remove_by_indices(t2.indices_to_remove)
                        new_w = w_prefix + [next_letter]  # symbolic; can track separately if needed
                        queue.append(((t1.target, new_r1), (t2.target, new_r2), new_w))

    # No distinguishing word found
    return None

def find_distinguishing_word(target: RegisterAutomaton, u: LetterSeq, v: LetterSeq) -> bool:
    """
    Decide whether there exists a word w such that A accepts uw but not vw.
    u and v must be of the same type (same comparison pattern).
    """
    return find_difference(target, u, target, v)

def get_memorable_seq(target: RegisterAutomaton, u: LetterSeq):
    print("enter memorable seq")
    bs = u.get_letter_extension(target.alphabet.comparator)
    memorables = set()
    print(bs)
    for a in u.letters:
        if a in memorables:
            continue
        print("checking letter ", a)
        # we try to replace b with a, and check whether map(u) and u can be distinguished by some v
        for b in bs.letters:
            if a == b: continue
            # 1. obtain the map
            print("replaced letter ", b)
            sigma = LetterSeq([a]).get_bijective_map(LetterSeq([b]))
            sigma_u = target.alphabet.apply_map(u, sigma)
            suffix = find_distinguishing_word(target, u, sigma_u)
            if suffix:
                print("================= distinguished ==================")
                print("u", u)
                print("m(u)", sigma_u)
                print("w", suffix)
                memorables.add(a)
                break
    # only keep the memorables
    print("all memorable letters ", memorables)
    mem_map = {}
    for idx, a in enumerate(u.letters):                
        if a in memorables:
            mem_map[a] = idx
    print("map ", mem_map)
    print("map values ", mem_map.values())
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
    def __init__(self, target: RegisterAutomaton
                 , mem_query_resolver: Optional[Callable[[RegisterAutomaton, LetterSeq], LetterSeq]] = None):
        self.target = target
        self.mem_query_resolver = mem_query_resolver
        self.num_membership_queries = 0
        self.num_equivalence_queries = 0
        self.num_memorability_queries = 0

    def membership_query(self, seq: LetterSeq) -> bool:
        """Return whether the target RA accepts seq under comparator comp."""
        self.num_membership_queries = self.num_membership_queries + 1
        return self.target.is_accepted(seq)

    def _generate_sequences(self, alphabet: Iterable[Letter], max_len: int = 10) -> Iterable[LetterSeq]:
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
        max_len: int = 4
    ) -> Tuple[bool, Optional[LetterSeq]]:
        """
        Heuristic equivalence check: compare hypothesis against target on all sequences
        generated from `alphabet` up to length `max_len`. Returns (True, None) if no
        counterexample found, otherwise (False, counterexample).
        """
        for seq in self._generate_sequences(alphabet, max_len):
            t_ans = self.target.is_accepted(seq)
            h_ans = hypothesis.is_accepted(seq)
            if t_ans != h_ans:
                return False, seq
        self.num_equivalence_queries = self.num_equivalence_queries + 1
        return True, None

    def memorability_query(
        self,
        u: LetterSeq
    ) -> LetterSeq:
        """
        Heuristic memorability check (placeholder): currently returns the input sequence unchanged.
        A proper implementation should, for each letter a in u, determine whether there exists
        a different letter b such that the bijective renaming D that maps a to b makes u and D(u)
        reach the same state in the target RegisterAutomaton.
        """
        self.num_memorability_queries = self.num_memorability_queries + 1
        seq = get_memorable_seq(self.target, u)
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
        

    except Exception:
        # keep __main__ minimal and not failing in CI if example/RA missing
        pass