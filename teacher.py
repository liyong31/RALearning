from typing import List, Tuple, Callable, Optional, Iterable
import itertools

import word
from word import Letter, LetterSequence, Numeric
from ra import RegisterAutomaton

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
                 , comp: Callable[[object, object], bool] = word.comp_id
                 , mem_query_resolver: Optional[Callable[[RegisterAutomaton, LetterSequence], LetterSequence]] = None):
        self.target = target
        self.comp = comp
        self.mem_query_resolver = mem_query_resolver

    def membership_query(self, seq: LetterSequence) -> bool:
        """Return whether the target RA accepts seq under comparator comp."""
        return self.target.is_accepted(seq, self.comp)

    def _generate_sequences(self, alphabet: Iterable[Letter], max_len: int = 10) -> Iterable[LetterSequence]:
        """Yield all LetterSequence over alphabet up to length max_len (includes empty)."""
        # yield empty
        yield LetterSequence([])
        alphabet_list = list(alphabet)
        for L in range(1, max_len + 1):
            for prod in itertools.product(alphabet_list, repeat=L):
                yield LetterSequence(list(prod))

    def equivalence_query(
        self,
        hypothesis: RegisterAutomaton,
        alphabet: Iterable[Letter],
        max_len: int = 4
    ) -> Tuple[bool, Optional[LetterSequence]]:
        """
        Heuristic equivalence check: compare hypothesis against target on all sequences
        generated from `alphabet` up to length `max_len`. Returns (True, None) if no
        counterexample found, otherwise (False, counterexample).
        """
        for seq in self._generate_sequences(alphabet, max_len):
            t_ans = self.target.is_accepted(seq, self.comp)
            h_ans = hypothesis.is_accepted(seq, self.comp)
            if t_ans != h_ans:
                return False, seq
        return True, None

    def memorability_query(
        self,
        u: LetterSequence
    ) -> LetterSequence:
        """
        Heuristic memorability check (placeholder): currently returns the input sequence unchanged.
        A proper implementation should, for each letter a in u, determine whether there exists
        a different letter b such that the bijective renaming D that maps a to b makes u and D(u)
        reach the same state in the target RegisterAutomaton.
        """
        seq = self.mem_query_resolver(self.target, u)
        seq.letter_type = self.target.letter_type
        return seq
        # print(self.target)
        # mem_positions : dict[Letter, int] = {}
        # reached_loc, _, _ = self.target.run(u, self.comp)[-1]
        # print("reached loc:", reached_loc)
        # u_extensions = u.get_letter_extension(self.comp)
        # print("u extensions:", u_extensions)
        # for i in range(len(u.letters)):
        #     a = u.letters[i]
        #     print(mem_positions)
        #     print("curr letter:", u.letters[i] )
        #     if u.letters[i] in mem_positions:
        #         mem_positions[u.letters[i]] = i
        #         continue
        #     # else, we need to check whether it is memorable
        #     a_seq = LetterSequence([u.letters[i]])
        #     print("reached here", a, )
        #     b_seq = [b for b in u_extensions.letters if a != b]
        #     print("extensions:", b_seq)
            
        #     for b in b_seq:
        #         # sigma = b_seq.get_bijective_mapping_dense(LetterSequence([a]))
        #         def sigma(c: Letter) -> Letter:
        #             if c == a: return b
        #             else: return c
        #         proj_u = LetterSequence([sigma(l) for l in u.letters])
        #         print("projected u: ", proj_u)
        #         proj_reached_loc, _, _ = self.target.run(proj_u, self.comp)[-1]
        #         print("reached loc: ", proj_reached_loc)
        #         if reached_loc != proj_reached_loc:
        #             mem_positions[u.letters[i]] = i
        #             break
        # # now return the memorable sequence
        # mem_seq = []
        # for i in range(len(u.letters)):
        #     if u.letters[i] in mem_positions.keys():
        #         mem_seq.append(u.letters[i])
        
        # return LetterSequence(mem_seq)

if __name__ == "__main__":
    # small smoke test (requires example.get_example_ra_* implementations)
    try:
        import example
        target = example.get_example_ra_1()
        teacher = Teacher(target, word.comp_lt, example.solve_memorability_query_1)

        # create small real-valued alphabet sample
        a = Letter(1.0, word.LetterType.REAL)
        b = Letter(2.0, word.LetterType.REAL)
        c = Letter(1.5, word.LetterType.REAL)
        d = Letter(4.0, word.LetterType.REAL)
        seq = [a, b, c, d]
        print(seq)
        
        seq1 = [a, b, d, d]

        res = teacher.memorability_query(LetterSequence(seq))
        print("sequence:", seq, "mem_seq:", res)
        res1 = teacher.memorability_query(LetterSequence(seq1))
        print("sequence:", seq1, "mem_seq:", res1)
        

    except Exception:
        # keep __main__ minimal and not failing in CI if example/RA missing
        pass