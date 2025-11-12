from typing import List, Tuple, Callable, Optional, Iterable
import itertools

import alphabet
from alphabet import Letter, LetterSeq
from dra import RegisterAutomaton

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
        seq = self.mem_query_resolver(self.target, u)
        return seq

if __name__ == "__main__":
    # small smoke test (requires example.get_example_ra_* implementations)
    try:
        import example
        target = example.get_example_ra_1()
        teacher = Teacher(target, alphabet.comp_lt, example.solve_memorability_query_1)

        # create small real-valued alphabet sample
        a = Letter(1.0, alphabet.LetterType.REAL)
        b = Letter(2.0, alphabet.LetterType.REAL)
        c = Letter(1.5, alphabet.LetterType.REAL)
        d = Letter(4.0, alphabet.LetterType.REAL)
        seq = [a, b, c, d]
        print(seq)
        
        seq1 = [a, b, d, d]

        res = teacher.memorability_query(LetterSeq(seq))
        print("sequence:", seq, "mem_seq:", res)
        res1 = teacher.memorability_query(LetterSeq(seq1))
        print("sequence:", seq1, "mem_seq:", res1)
        

    except Exception:
        # keep __main__ minimal and not failing in CI if example/RA missing
        pass