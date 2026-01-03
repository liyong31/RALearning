from abc import ABC, abstractmethod
from typing import Optional, Callable, Set, Tuple
from collections import deque, defaultdict
from typing import Dict, FrozenSet, Tuple, List, Optional, Set

from alphabet import Letter, LetterSeq
from dra import RegisterAutomaton
import teacher
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

    @abstractmethod
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
        w = teacher.find_difference(self.dra, u_mapped, self.dra, v, None)
        assert w is not None, f" {w} should not be none"
        # D(u)w in L </-> vw in L
        # uD^{-1}(w) in L </-> v w in L
        w_inverse = self.dra.alphabet.apply_map(w, v2u_map)
        return (u.concat(w_inverse), v.concat(w))

    @abstractmethod
    def get_memorable_witness(
        self,
        u: "LetterSeq",
        a: "Letter",
    ) -> Optional[Tuple["LetterSeq", "LetterSeq"]]:
        u_sorted = teacher.get_sorted_seq(u)  
        w, b, up = teacher.get_memorable_witness(self.dra, u, u_sorted, a)
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

# -------------------------------------------------------------
# Backward Search Witness Finder
# -------------------------------------------------------------
# first backward search to find all distinguishable pairs
class BackwardSearchWitnessFinder(WitnessFinder):

    def __init__(self,log_printer : LogPrinter, dra: "RegisterAutomaton"):
        super().__init__(log_printer, dra)
        self.state_reg, self.witnesses = self.backward_search_distinguishing_words()
    
    def get_distinguish_witness(
        self,
        u: "LetterSeq",
        v: "LetterSeq",
    ) -> Optional[Tuple["LetterSeq", "LetterSeq"]]:
        # Implement equivalence checking logic here
        u_state, u_reg, _ = self.dra.run(u)[-1]
        v_state, v_reg, _ = self.dra.run(v)[-1]
        assert (u_state, v_state) in self.witnesses, f"No witness found for ({u_state}, {v_state})"
        if u_state == v_state:
            return None
        # no need to find the distinguishing word if the types are different
        if not self.dra.alphabet.test_type(u_reg, v_reg):
            return None
        u_cano_reg = self.state_reg[u_state]
        v_cano_reg = self.state_reg[v_state]
        sigma_u = u_cano_reg.get_bijective_map(u_reg)
        sigma_v = v_cano_reg.get_bijective_map(v_reg)
        # map the witness back to original registers
        w1, w2 = self.witnesses[(u_state, v_state)]
        w1_mapped = self.dra.alphabet.apply_map(w1, sigma_u)
        w2_mapped = self.dra.alphabet.apply_map(w2, sigma_v)
        return (u.concat(w1_mapped), v.concat(w2_mapped))

    def get_memorable_witness(
        self,
        u: "LetterSeq",
        a: "Letter",
    ) -> "LetterSeq":
        # u and u_sorted are assumed to reach the same state
        u_sorted = teacher.get_sorted_seq(u)  
        b, v = teacher.get_near_seq(self.dra, u, u_sorted, a)
        self.log_printer.debug("b ", b, " v ", v)
        # u and uprime will reach the same state
        u_state, u_reg, _ = self.dra.run(u)[-1]
        v_state, v_reg, _ = self.dra.run(v)[-1]
        # uprime_state, uprime_reg, _ = self.dra.run(u)[-1]
        assert u_state == v_state, f"states not equal {u_state}, {v_state}"
        assert (u_state, u_state) in self.witnesses, f"No witness found for ({u_state}, {u_state})"
        u_cano_reg = self.state_reg[u_state]
        # one is accept and the other is reject
        w1, w2 = self.witnesses[(u_state, u_state)]
        self.log_printer.debug("u_cano ", u_cano_reg, " w1 ", w1, " w2 ", w2)
        # that is, u_cano w1 and u_cano w2 not agree on membership
        assert self.dra.alphabet.test_type(u_cano_reg, u_reg), f"word type not equal, {u_cano_reg}, {u_reg}"
        sigma_u = u_cano_reg.get_bijective_map(u_reg)
        sigma_v = u_cano_reg.get_bijective_map(v_reg)
        w1_mapped = self.dra.alphabet.apply_map(w1, sigma_u)
        w2_mapped = self.dra.alphabet.apply_map(w2, sigma_v)
        # v w2_mapped and u w1_mapped are not agree on membership
        # replace b with a will make v to u
        def replace_b_with_a(c: Letter) -> Letter:
            if c == b:
                return a
            else:
                return c
        w2_mapped = self.dra.alphabet.apply_map(w2_mapped, replace_b_with_a)
        return (u.concat(w1_mapped), u.concat(w2_mapped))

    # only the pair for sink rejecting states will be None
    # the relation is symmetric 
    def backward_search_distinguishing_words(
        self,
    ) -> Dict[Tuple[int, LetterSeq], Tuple[LetterSeq, LetterSeq]]:
        """
        Compute all distinguishable state pairs (p,q) and store
        a witness word for each such pair.

        Returns:
            in_queue: set of distinguishable (p,q)
            witnesses: map (p,q) -> witness words
        """
        # we already assume the input DRA is normalised
        # dra = dra.get_normalised_dra()

        Q = list(self.dra.locations.keys())

        is_accepting = {
            q: self.dra.locations[q].accepting
            for q in Q
        }
        # ---------------------------------------------------------
        # Step 1: reverse delta
        # ---------------------------------------------------------
        rev_trans: Dict[int, Set[Tuple[int, LetterSeq, FrozenSet[int]]]] = {
            q: set() for q in Q
        }
        # make sure all state types on outgoing transitions are the same
        # one such type is enough
        state_reg: Dict[int, LetterSeq] = {
            q: None for q in Q
        }

        for p in Q:
            for t in self.dra.locations[p].transitions:
                rev_trans[t.target].add((p, t.tau, frozenset(t.indices_to_remove)))
                state_reg[p] = t.tau.get_prefix(len(t.tau) - 1)

        # ---------------------------------------------------------
        # Step 4: backward BFS on product states
        # ---------------------------------------------------------
        in_queue: Set[Tuple[int, int]] = set()

        queue = deque()
        result: Dict[Tuple[int, int], Tuple[LetterSeq, LetterSeq]] = {}

        alphabet = self.dra.alphabet
        # Base cases: acceptance mismatch
        for p in Q:
            for q in Q:
                if is_accepting[p] != is_accepting[q]:
                    in_queue.add((p, q))
                    queue.append((p, q))
                    result[(p, q)] = (alphabet.empty_sequence(), alphabet.empty_sequence())
                    # in_queue.add((q, p))
                    # queue.append((q, p))
                    # result[(q, p)] = (alphabet.empty_sequence(), alphabet.empty_sequence())


        self.log_printer.debug(f"Initial distinguishable pairs: {result}")
        self.log_printer.debug(f"Start backward search...")

        # Backward propagation
        # must matinain the order of letters with repect to current states
        while queue:
            q1, q2 = queue.popleft()
            # Explore predecessors
            w1, w2 = result[(q1, q2)]
            self.log_printer.debug(f"Exploring predecessors of ({q1}, {q2}) with result {w1} vs {w2}")
            # q1 is the predecessor of q1 via some (p1, tau1, E1)
            for (p1, tau1, E1) in rev_trans[q1]:
                a1 = tau1.letters[-1]
                q1_reg = state_reg[q1]
                next_reg1 = tau1.remove_by_indices(E1)
                # INVAIRIANT: q1_reg ~ next_reg1
                self.log_printer.debug("q1reg:", q1_reg , "next_reg:", next_reg1)
                sigma1 = q1_reg.get_bijective_map(next_reg1)
                w1_mapped = alphabet.apply_map(w1, sigma1)
                a1w1 = w1_mapped.preappend(a1) # we fix this letter
                self.log_printer.debug("a1w1:", a1w1)
                for (p2, tau2, E2) in rev_trans[q2]:
                    # Find common letters in canonical sets
                    self.log_printer.debug("Considering", (p1, p2))
                    self.log_printer.debug("tau1:", tau1 , "tau2:", tau2)
                    q2_reg = state_reg[q2]
                    next_reg2 = tau2.remove_by_indices(E2)
                    # INVAIRIANT: q1_reg ~ next_reg2
                    sigma2 = q2_reg.get_bijective_map(next_reg2)
                    w2_mapped = alphabet.apply_map(w2, sigma2)
                    self.log_printer.debug("w2_mapped:", w2_mapped)
                    # get all possible letters to try
                    all_letters = tau2.concat(w2_mapped).get_letter_extension(alphabet.comparator)
                    self.log_printer.debug("All letters to try:", all_letters.letters)
                    # try out each letter
                    for a2 in all_letters.letters:
                        self.log_printer.debug("Trying letter:", a2)
                        tau2_reg = tau2.get_prefix(len(tau2) - 1)
                        self.log_printer.debug("tau2_reg:", tau2_reg)
                        a2w2_reg = tau2_reg.append(a2)
                        self.log_printer.debug("tau2:", tau2, "a2w2_reg:", a2w2_reg)
                        if not alphabet.test_type(tau2, a2w2_reg):
                            continue
                        a2w2 = w2_mapped.preappend(a2)
                        self.log_printer.debug("Comparing", a1w1, "vs", a2w2)
                        # if the same type, 
                        if alphabet.test_type(a1w1, a2w2) :
                            if (p1, p2) not in in_queue:
                                pair = (p1, p2)
                                in_queue.add(pair)
                                self.log_printer.debug("adding", a1w1, "vs", a2w2)
                                result[pair] = (a1w1, a2w2)
                                queue.append(pair)
                                # in_queue.add((p2, p1))
                                result[(p2, p1)] = (a2w2, a1w1)
                                # queue.append((p2, p1))
        for p1, p2 in [(i, j) for i in range(self.dra.get_num_states()) for j in range(self.dra.get_num_states())]:
            if (p1, p2) in result:
                w1, w2 = result[(p1, p2)]
                self.log_printer.debug(f"({p1}, {p2}) : {w1} vs {w2}")
            else:
                self.log_printer.debug(f"({p1}, {p2}) : None")
        return state_reg, result
    
def one_step_configs(
        dra : RegisterAutomaton,
        source_loc: int,
        source_reg: LetterSeq,  # current register values
    ) -> List[Tuple[int, LetterSeq, Letter]]:
        next_cfgs = []
        for trans in dra.locations[source_loc].transitions:
            type_len = len(trans.tau) - 1
            st_type = trans.tau.get_prefix(type_len)
            letter = trans.tau.get_letter(type_len)
            if not dra.alphabet.test_type(source_reg, st_type):
                    raise RuntimeError(f"words not the same type {source_reg}, {st_type}")
            # the last letter of tau will be the "input" we need
            sigma = st_type.get_bijective_map(source_reg)
            new_letter = sigma(letter)

            extended_seq = source_reg.append(new_letter)
            # remove indices
            new_reg_seq = extended_seq.remove_by_indices(trans.indices_to_remove)
            next_cfg = (trans.target, new_reg_seq, new_letter)
            next_cfgs.append(next_cfg)
        # print(next_cfgs)
        return next_cfgs
    

with open("canos/exam9.txt", "r") as f:
    text = f.read()
    dra = RegisterAutomaton.from_text(text)
    logger = SimpleLogger(level=LogLevel.DEBUG)
    log_printer = LogPrinter(logger.raw)

    witness_finder = BackwardSearchWitnessFinder(log_printer, dra)
    eq_finder = BackwardSearchWitnessFinder(log_printer, dra)
    print("=======================")
    # for k, v in res.items():
    #     print(f"{k}: {v[0]} vs {v[1]}")
            # config: state, representative, reg
    start = (dra.get_initial()
            , dra.alphabet.empty_sequence()
            , dra.alphabet.empty_sequence())
    queue = deque([start])
    in_queue = set([dra.get_initial()])
    result = [ tuple() for i in range(dra.get_num_states())]
    # BFS over configurations
    while queue:
        loc_id, loc_repr, reg_seq = queue.popleft()
        result[loc_id] = (loc_id
                        , loc_repr
                        , reg_seq)
        # iterate over outgoing transitions
        next_cfgs = one_step_configs(dra, loc_id, reg_seq)
        print(len(next_cfgs))
        for (dest_id, new_reg_seq, letter) in next_cfgs:
            next_config = (dest_id
                        , loc_repr.append(letter)
                        , new_reg_seq)
            if dest_id not in in_queue:
                queue.append(next_config)
                in_queue.add(dest_id)
        
# no path found
print("====================")
print(result)
for i in range(dra.get_num_states()):
    if result[i] is None:
        continue
    _, repr, reg = result[i]
    for a in reg.letters:
        print("======================= ")
        print("u: ", repr, " a: ", a)
        left, right = witness_finder.get_memorable_witness(repr, a)
        print("w: ", left, " w': ", right)
        left, right = eq_finder.get_memorable_witness(repr, a)
        print("w: ", left, " w': ", right)