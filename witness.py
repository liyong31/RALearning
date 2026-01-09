from abc import ABC, abstractmethod
from typing import Optional, Callable, Set, Tuple
from collections import deque, defaultdict
from typing import Dict, FrozenSet, Tuple, List, Optional, Set

from alphabet import Letter, LetterSeq
from dra import RegisterAutomaton
import diff
from log import SimpleLogger, LogLevel, LogPrinter # type: ignore


# The input DRA must be well-typed and complete

class WitnessFinder(ABC):
    """Interface for finding distinguishing witnesses between register automata."""

    def __init__(self, log_printer : LogPrinter, dra: "RegisterAutomaton"):
        self.dra = dra
        self.log_printer = log_printer

    @abstractmethod
    def get_distinguish_witness(
        self,
        u: LetterSeq,
        v: LetterSeq,
    ) -> Optional[Tuple["LetterSeq", "LetterSeq"]]:
        """
        Return a word distinguishing (dra, u) from (dra, v), or None if none exists.
        """
        pass
        
    @abstractmethod
    def get_memorable_witness(
        self,
        u: "LetterSeq",
        a: "Letter",
    ) -> Optional[Tuple["LetterSeq", "LetterSeq"]]:
        """
        Return a witness word memorable w.r.t. the target automaton.
        """
        pass
    

class EqCheckWitnessFinder(WitnessFinder):
    """A witness finder that uses equivalence checking to find witnesses."""

    def __init__(self, log_printer : LogPrinter, dra: "RegisterAutomaton"):
        super().__init__(log_printer, dra)

    def get_distinguish_witness(
        self,
        u: "LetterSeq",
        v: "LetterSeq",
    ) -> Optional[Tuple["LetterSeq", "LetterSeq"]]:
        u_state, u_reg, _ = self.dra.run(u)[-1]
        v_state, v_reg, _ = self.dra.run(v)[-1]
        if u_state == v_state:
            return None
        # no need to find the distinguishing word if the types are different
        if not self.dra.alphabet.test_type(u_reg, v_reg):
            return None
        u2v_map = u_reg.get_bijective_map(v_reg)
        v2u_map = v_reg.get_bijective_map(u_reg)
        u_mapped = self.dra.alphabet.apply_map(u, u2v_map)
        w = diff.find_difference(self.dra, u_mapped, self.dra, v, None)
        assert w is not None, f" {w} should not be none"
        # D(u)w in L </-> vw in L
        # uD^{-1}(w) in L </-> v w in L
        w_inverse = self.dra.alphabet.apply_map(w, v2u_map)
        return (u.concat(w_inverse), v.concat(w))

    def get_memorable_witness(
        self,
        u: "LetterSeq",
        a: "Letter",
    ) -> Tuple["LetterSeq", "LetterSeq"]:
        u_sorted = diff.get_sorted_seq(u)  
        w, b, up = diff.get_memorable_witness(self.dra, u, u_sorted, a)
        # print("u ", u)
        # print("b ", b)
        # print("a ", a)
        # print("w ", w)
        # print("reg ", reg)
        assert w is not None, f"{a} is not memorable in {u}"
        # a_idx = w.index(a)
        # w must contain either a or b
        # if a_idx >= 0:
        # uw, u[a/b]w not equal
        b2a_map = up.get_bijective_map(u)
        return (u.concat(w), u.concat(self.dra.alphabet.apply_map(w, b2a_map)))      

class DistinguishCheckWitnessFinder(WitnessFinder):
    """A witness finder that uses equivalence checking to find witnesses."""

    def __init__(self, log_printer : LogPrinter, dra: "RegisterAutomaton"):
        super().__init__(log_printer, dra)

    def get_distinguish_witness(
        self,
        u: "LetterSeq",
        v: "LetterSeq",
    ) -> Optional[Tuple["LetterSeq", "LetterSeq"]]:
        u_state, u_reg, _ = self.dra.run(u)[-1]
        v_state, v_reg, _ = self.dra.run(v)[-1]
        if u_state == v_state:
            return None
        # no need to find the distinguishing word if the types are different
        if not self.dra.alphabet.test_type(u_reg, v_reg):
            return None
        w1, w2 = diff.find_distinguishing_words(self.dra, u, self.dra, v, False)
        assert w1 is not None, f" {w1} should not be none"
        assert w2 is not None, f" {w2} should not be none"
        assert self.dra.alphabet.test_type(u_reg.concat(w1), v_reg.concat(w2)), f"not same type"
        # print(f"============= dist {u}, {v}")
        # print(f"w1 {w1}, w2 {w2}")
        assert(self.dra.is_accepted(u.concat(w1)) != self.dra.is_accepted(v.concat(w2))), f"same accept type"
        return (u.concat(w1), v.concat(w2))

    def get_memorable_witness(
        self,
        u: "LetterSeq",
        a: "Letter",
    ) -> Tuple["LetterSeq", "LetterSeq"]:
        # print(f"identify memorable: {a}, {u}")
        u_sorted = diff.get_sorted_seq(u) 
        b, up = diff.get_near_seq(self.dra, u, u_sorted, a)
        # # w1 must contain a, so we get aw1 and bw2
        w1, w2 = diff.find_distinguishing_words(self.dra, u, self.dra, up, True)
        # w1 = w1.preappend(a)
        # w2 = w2.preappend(a)
        # print(u.concat(w1), up.concat(w2))
        assert(self.dra.is_accepted(u.concat(w1)) != self.dra.is_accepted(up.concat(w2))), f"same accept type"

        # assert w1 is not None, f"{a} is not memorable in {u}"
        # assert w2 is not None, f"{a} is not memorable in {u}"
        # uw1, u'w2 not agree on membership
        # uw, u[a/b]w not equal
        # print(f"============= dist {u}, {up}")
        # print(f"w1 {w1}, w2 {w2}")
        # print("added pair: ", u.concat(w1), up.concat(w2))
        return (u.concat(w1), up.concat(w2))  