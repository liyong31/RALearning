from collections import deque, defaultdict
from typing import List, Set, Dict, Tuple, Optional


from dra import RegisterAutomaton
from alphabet import LetterSeq, Letter, Alphabet
import teacher
import rpni
from log import LogPrinter # type: ignore


Config = Tuple[int, LetterSeq, Letter]

# ---------- Data structure for characteristic sample ----------
# generate samples for RPNI learning
class CharacteristicSample:
    def __init__(self, log_printer: LogPrinter, dra: RegisterAutomaton):
        self.log_printer = log_printer
        self.dra = dra
        self.positives = []
        self.negatives = []

    # ASSUMPTION: the input dra must be well-typed and complete
    def one_step_configs(
        self,
        source_loc: int,
        source_reg: LetterSeq,  # current register values
    ) -> List[Config]:
        next_cfgs = []
        for trans in self.dra.locations[source_loc].transitions:
            type_len = len(trans.tau) - 1
            st_type = trans.tau.get_prefix(type_len)
            letter = trans.tau.get_letter(type_len)
            if not self.dra.alphabet.test_type(source_reg, st_type):
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
        
    def get_state_representatives(
        self,
    ) -> list[Tuple[int, LetterSeq, LetterSeq]]:
        """
            Compute a shortest concrete word that leads to target_loc in a deterministic RA.
        """
        # config: state, representative, reg
        start = (self.dra.get_initial()
                , self.dra.alphabet.empty_sequence()
                , self.dra.alphabet.empty_sequence())
        queue = deque([start])
        in_queue = set([self.dra.get_initial()])
        result = [ tuple() for i in range(self.dra.get_num_states())]
        # BFS over configurations
        while queue:
            loc_id, loc_repr, reg_seq = queue.popleft()
            result[loc_id] = (loc_id
                            , loc_repr
                            , reg_seq)
            # iterate over outgoing transitions
            next_cfgs = self.one_step_configs(loc_id, reg_seq)
            # print(len(next_cfgs))
            for (dest_id, new_reg_seq, letter) in next_cfgs:
                next_config = (dest_id
                            , loc_repr.append(letter)
                            , new_reg_seq)
                if dest_id not in in_queue:
                    queue.append(next_config)
                    in_queue.add(dest_id)
        # no path found
        return result
        
    # ---------- Characteristic sample construction ----------
    def compute_characteristic_sample(self) -> None:
        """
        Compute (St, Tr, Mem, D) (as sets of words) for the given (assumed minimal) DRA.
        - witness_alphabet_size: number of distinct data symbols to use (default = k+2)
        - max_search_len: search bound for suffixes/distinguishers (practical bound; paper proves poly-size exists)
        Returns: dict with keys 'St','Tr','Mem','D' each mapping to set of words (tuples)
        """

        # Build St: choose for each ≡_L-class (we approximate by distinct configs)
        # The paper's St is over equivalence classes; practical approach: take one rep per reachable state/config
        st = set()
        state_reprs = self.get_state_representatives()
        for _, repr, _ in state_reprs:
            st.add(repr)
        self.log_printer.debug("===================== st")
        self.log_printer.debug(st)
        # 2) Build Tr: for each w in St and each a in mem(w) and first non-mem minimal a,
        #    include wa and wd as described in Definition 15.
        tr = set()
        # tr_info = set()
        for _, u, reg in state_reprs:
            bs = reg.get_letter_extension(self.dra.alphabet.comparator)
            for b in bs.letters:
                ub = u.append(b)
                tr.add(ub)
                # tr_info.add((ub, u, reg))
        self.log_printer.debug("===================== tr")
        self.log_printer.debug(tr)            

        # 3) Build Mem: for all w in Tr, for all a in mem(w) we must find b and suffix u
        #    such that wu ≃ (wu)[a/b], they differ in acceptance w.r.t. replacing a by b, and both in Mem.
        # Practical heuristic: search for small u and b such that acceptance differs when we replace at positions of 'a' in suffix.
        mem = set()
        for u in tr:
            # first, obtain the memorable sequence
            configs = self.dra.run(u)
            _, reg, _ = configs[-1]
            u_sorted = sorted(set(u.letters), key=lambda x: x.value)        
            
            for a in reg.letters:
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
                mem.add(u.concat(w))
                b2a_map = up.get_bijective_map(u)
                mem.add(u.concat(self.dra.alphabet.apply_map(w, b2a_map)))
                self.log_printer.debug("===================== memorable u,w,a,b")
                self.log_printer.debug(u, w, a, b)
                # print(mem)
        self.log_printer.debug("===================== mem")
        self.log_printer.debug(mem)
        # 4) Build D: distinguishers for non-equivalent states with same mem size
        #    For each pair of representatives u in St and z in Tr with same mem size and not ≡_L,
        #    find suffixes ww' and zz' showing difference and record them in D.
        D = set()
        for u in st:
            u_configs = self.dra.run(u)
            u_id, u_reg, _ = u_configs[-1]
            for v in tr:
                # we now need to check whether this two reach the same state
                v_configs = self.dra.run(v)
                v_id, v_reg, _ = v_configs[-1]
                if u_id == v_id:
                    # equivalent, no need to distinguish
                    continue
                # memorable words not the same type, u and v already in samples
                if not self.dra.alphabet.test_type(u_reg, v_reg):
                    continue
                # now, find difference
                self.log_printer.debug(f"find difference between ({u}, {u_reg}) and ({v}, {v_reg})")
                # since they have the same type, make a map
                u2v_map = u_reg.get_bijective_map(v_reg)
                v2u_map = v_reg.get_bijective_map(u_reg)
                u_mapped = self.dra.alphabet.apply_map(u, u2v_map)
                w = teacher.find_difference(self.dra, u_mapped, self.dra, v, None)
                assert w is not None, f" {w} should not be none"
                # D(u)w in L </-> vw in L
                # uD^{-1}(w) in L </-> v w in L
                w_inverse = self.dra.alphabet.apply_map(w, v2u_map)
                D.add(u.concat(w_inverse))
                D.add(v.concat(w))
                self.log_printer.debug("===========================")
                self.log_printer.debug(f"distinguish {u} and {v} : {w}")
                self.log_printer.debug(f"distinguish uw^{-1}: {u} {w_inverse}")
                self.log_printer.debug(f"distinguish vw: {u} {w_inverse}")
        self.log_printer.debug("===================== D")
        self.log_printer.debug(D)
        # 5) Build final positive/negative samples
        # Finally, intersect with positive/negative sets is the learner's job; we just return these sets
        all_samples = st.union(tr)
        all_samples = all_samples.union(mem)
        all_samples = all_samples.union(D)
        for w in all_samples:
            if self.dra.is_accepted(w):
                self.positives.append([ l.value for l in w.letters])
            else:
                self.negatives.append([ l.value for l in w.letters])
