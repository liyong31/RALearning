from collections import deque, defaultdict
from typing import List, Set, Dict, Tuple, Optional


from dra import RegisterAutomaton
from alphabet import LetterSeq, Letter, Alphabet
import witness
import rpni
from log import LogPrinter # type: ignore
from sortset import SortedSet


Config = Tuple[int, LetterSeq, Letter]

# ---------- Data structure for characteristic sample ----------
# generate samples for RPNI learning
class CharacteristicSample:
    def __init__(self, log_printer: LogPrinter, dra: RegisterAutomaton):
        self.log_printer = log_printer
        self.dra = dra
        self.positives = []
        self.negatives = []
        self.max_length = 0
        self.avg_length = 0.0
        self.witness_finder = None
        
    def set_witness_finder(self, use_backward_finder: witness.WitnessFinder):
        if use_backward_finder:
            self.witness_finder = witness.DistinguishCheckWitnessFinder(self.log_printer, self.dra)
        else:
            self.witness_finder = witness.EqCheckWitnessFinder(self.log_printer, self.dra)

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
        self.log_printer.debug("DRA:\n", self.dra.to_dot())
        # Build St: choose for each ≡_L-class (we approximate by distinct configs)
        # The paper's St is over equivalence classes; practical approach: take one rep per reachable state/config
        st = SortedSet()
        state_reprs = self.get_state_representatives()
        self.log_printer.debug("===================== repr")
        self.log_printer.debug(state_reprs)
        
        for _, repr, _ in state_reprs:
            st.add(repr)
        self.log_printer.debug(f"===================== st, , {len(st)}")
        self.log_printer.debug(st)
        # 2) Build Tr: for each w in St and each a in mem(w) and first non-mem minimal a,
        #    include wa and wd as described in Definition 15.
        tr = SortedSet()
        # tr_info = set()
        for _, u, reg in state_reprs:
            bs = reg.get_letter_extension(self.dra.alphabet.comparator)
            for b in bs.letters:
                ub = u.append(b)
                tr.add(ub)
                # tr_info.add((ub, u, reg))
        self.log_printer.debug(f"===================== tr, {len(tr)}")
        self.log_printer.debug(tr)            

        # 3) Build Mem: for all w in Tr, for all a in mem(w) we must find b and suffix u
        #    such that wu ≃ (wu)[a/b], they differ in acceptance w.r.t. replacing a by b, and both in Mem.
        # Practical heuristic: search for small u and b such that acceptance differs when we replace at positions of 'a' in suffix.
        mem = SortedSet()
        for u in tr:
            # first, obtain the memorable sequence
            configs = self.dra.run(u)
            _, reg, _ = configs[-1]            
            for a in reg.letters:
                (uw1, uw2) = self.witness_finder.get_memorable_witness(u, a)
                mem.add(uw1)
                mem.add(uw2)
                # print(mem)
        self.log_printer.debug(f"===================== mem, {len(mem)}")
        self.log_printer.debug(mem)
        # 4) Build D: distinguishers for non-equivalent states with same mem size
        #    For each pair of representatives u in St and z in Tr with same mem size and not ≡_L,
        #    find suffixes ww' and zz' showing difference and record them in D.
        D = SortedSet()
        for u in st:
            for v in tr:
                res = self.witness_finder.get_distinguish_witness(u, v)
                if res is not None:
                    D.add(res[0])
                    D.add(res[1])

        self.log_printer.debug(f"===================== D, {len(D)}")
        self.log_printer.debug(D)
        self.log_printer.info("total samples generated ", len(st) + len(tr) + len(mem) + len(D))
        # 5) Build final positive/negative samples
        # Finally, intersect with positive/negative sets is the learner's job; we just return these sets
        all_samples = st.union(tr)
        all_samples = all_samples.union(mem)
        all_samples = all_samples.union(D)
        ttl_length = 0
        for w in all_samples:
            ttl_length += len(w.letters)
            self.max_length = max(self.max_length, len(w.letters))
            if self.dra.is_accepted(w):
                self.positives.append([ l.value for l in w.letters])
            else:
                self.negatives.append([ l.value for l in w.letters])
        self.avg_length = ttl_length / len(all_samples) if len(all_samples) > 0 else 0.0
