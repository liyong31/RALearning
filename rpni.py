# Sketch: passive learning of a deterministic register automaton (DRA)
# following the high-level structure of Algorithm 2 / SET_TRANSITION
# from Balachander, Filiot, Gentilini (CONCUR 2024)
# We modified the algorithm a bit to make it more practical and fix the s-completability check.
# Yong Li, 2025

from collections import defaultdict, deque
from dra import RegisterAutomaton, Transition
from alphabet import Alphabet, LetterType, LetterSeq, Letter, comp_id, comp_lt
from log import LogPrinter, LogLevel, SimpleLogger # type: ignore
import sys

# length-lexicographic comparison
def ll_compare(u, v):
    """
    Returns:
        -1 if u < v (length-lexicographic)
         0 if u == v
         1 if u > v
    """
    # Compare by length
    if len(u) < len(v):
        return -1
    if len(u) > len(v):
        return 1

    # Lengths equal → lexicographic comparison
    if u < v:
        return -1
    if u > v:
        return 1
    return 0


# ---------- Sample representation ----------
class Sample:
    def __init__(self, positives, negatives):
        # positives/negatives: sets/lists of data-words (tuples or lists)
        self.pos = set(tuple(w) for w in positives)
        self.neg = set(tuple(w) for w in negatives)

    def prefs(self):
        """Return all non-empty prefixes of all samples (both pos and neg)."""
        P = set()
        for w in list(self.pos) + list(self.neg):
            for i in range(1, len(w) + 1):
                P.add(tuple(w[:i]))
        return P


# ---------- RPNI learning algorithm ----------
class RegisterAutomatonRPNILearner:
    def __init__(self, log_printer: LogPrinter, sample: Sample, alphabet: Alphabet):
        self.log_printer = log_printer
        self.sample = sample
        self.alphabet = alphabet
        # add mutable samples for optimization in s-completability check
        self.mutable_pairs = set([(p, n) for p in sample.pos for n in sample.neg])
        self.mutable_neg = set(sample.neg)
        self.is_sample_mutable = False

    def test_consistency(self, dra: RegisterAutomaton):
        for w in self.sample.pos:
            w_seq = dra.alphabet.make_sequence([l for l in list(w)])
            if not dra.is_accepted(w_seq):
                print(f"pos {w} should be accepted")
                return False
        for w in self.sample.neg:
            w_seq = dra.alphabet.make_sequence([l for l in list(w)])
            if dra.is_accepted(w_seq):
                print(f"neg {w} should be rejected")
                return False
        return True

    # ---------- Learning algorithm (high-level sketch) ----------
    def learn(self) -> RegisterAutomaton:
        # Initialize partial DRA A (one state, maybe accepting empty word)
        initial = 0
        reg_size_map: dict[int, int] = {}
        A = RegisterAutomaton(self.alphabet)
        # first add one state and it is initial
        A.add_location(initial, "ε", False)
        A.set_initial(initial)
        reg_size_map[initial] = 0

        # check whether initial is accepting
        if tuple() in self.sample.pos:
            A.set_final(initial)
        # to_read: prefixes excluding empty
        to_read = sorted(
            self.sample.prefs(), key=lambda w: (len(w), list(w))
        )  # length-lexicographic
        to_read = deque([w for w in to_read if w != tuple()])

        # maintain set of seen prefixes that are readable
        readable = set()
        readable.add(tuple())  # empty word readable
        self.num_iters = 0
        while to_read:
            self.log_printer.debug(
                f"====================== iteration {self.num_iters} ======================"
            )
            self.log_printer.debug("Hypothesis:\n", A.to_dot())
            ua = to_read.popleft()
            # find u and a such that ua = u + (a,)
            u = ua[:-1]
            a = ua[-1]
            self.log_printer.debug("u", u)
            self.log_printer.debug("a", a)
            # ensure A can read u (paper guarantees S-completability ensures this)
            u_seq = self.alphabet.make_sequence(list(u))
            # u is guaranteed with a run
            u_configs = A.run(u_seq)
            # get the last configuration
            st, reg, _ = u_configs[-1]
            if st is None:
                # If we cannot read u yet, postpone ua (in real algorithm to_read is always arranged so u is readable)
                raise RuntimeError("u cannot be processed", u)

            # compute and add transition (st, a) using SET_TRANSITION
            a_letter = self.alphabet.make_letter(a)
            # GUARANTEE 2: A is S-completable
            t = self.set_transition(A, self.sample, reg_size_map, st, reg, a_letter)
            ua_seq = self.alphabet.make_sequence(list(ua))
            if t.target >= A.get_num_states():
                assert (
                    t.target == A.get_num_states()
                ), f"New state {t.target} larger than #states {A.get_num_states()}"
                A.add_location(t.target, str(ua_seq), False)
                reg_size_map[t.target] = reg_size_map[st] + 1 - len(t.indices_to_remove)

            A.add_transition(t.source, t.tau, t.indices_to_remove, t.target)
            self.log_printer.debug("added transition: ", t)
            # update readable and to_read: remove prefixes that are now readable; mark final states for pos words
            # first, check whether ua is accepting
            if self.search(self.alphabet, ua_seq, self.sample):
                readable.add(ua)
                A.set_final(t.target)
            # now, check all words in to_read whether they are now readable
            new_to_keep = []
            for w in list(to_read):
                w_seq = self.alphabet.make_sequence(list(w))
                succesful, state = A.has_run(w_seq)
                self.log_printer.debug(f" {w} has arun: ", succesful, state)
                if succesful:
                    # GUARANTEE 3: A is (Pos\to_read, Neg)-consistent
                    if self.search(self.alphabet, w_seq, self.sample):
                        A.set_final(state)
                else:
                    # GUARANTEE 1: a word w in to_read does not have proper run in A
                    new_to_keep.append(w)
            to_read = deque(new_to_keep)
            self.num_iters += 1
            #OPTIMIZATION: optionally update mutable samples for set_transition
            # samples that have run in A have been proved to be completable already
            if self.is_sample_mutable:
                # update mutable samples
                pos_neg_to_remove = set()
                neg_to_remove = set()
                for (w, z) in self.mutable_pairs:
                    w_seq = self.alphabet.make_sequence(list(w))
                    z_seq = self.alphabet.make_sequence(list(z))
                    neg_removed = A.has_run(z_seq)[0]
                    if neg_removed:
                        neg_to_remove.add(z)
                    if neg_removed and A.has_run( w_seq)[0]:
                        pos_neg_to_remove.add((w, z))
                self.mutable_neg -= neg_to_remove
                self.mutable_pairs -= pos_neg_to_remove
        # print(f"Learning finished in {self.num_iters} iterations.")
        # print(f"====================== iteration {self.num_iters} ======================")
        return A

    # ---------- SET_TRANSITION  ----------
    def set_transition(
        self,
        A: RegisterAutomaton,
        sample: Sample,
        reg_size_map: dict[int, int],
        q: int,
        reg: LetterSeq,
        a: Letter,
    ):
        """
        Try to erase as many registers as possible, then try to reuse an existing
        state as target while preserving S-completability (conservative check).
        Returns a Transition-like object with fields (src, tau, indices_to_remove, tgt).
        """
        # print(f"Trying to find the transition: ({q}, {reg}) over {a}")
        to_erase = set()  # default: erase nothing
        i = reg_size_map[q]
        # all possible indices to retain
        to_retain = set(range(i + 1))
        # print("to_retain", to_retain)
        # check whether a is already in reg
        j = reg.index(a)
        # new transition label
        tau = reg.append(a)
        # remove duplicate occurrence
        if j >= 0:
            to_erase.add(j)
            to_retain.remove(j)
        # attempt: try erase all combinations (for sketch: try erasing prefixes of memory)
        try_erase = list(to_retain)
        while len(try_erase) > 0:
            h = try_erase.pop()
            # copy current automaton
            Aprime = A.clone()
            f = Aprime.get_num_states()
            # by default it is not accepting?
            Aprime.add_location(f, str(f), False)
            to_erase.add(h)
            # try to erase the index h
            Aprime.add_transition(q, tau, to_erase, f)
            # test its completable ability
            # if cannot be removed, remove h
            if not self.s_completable(Aprime, sample):
                to_erase.remove(h)

        # Try to reuse existing states as target (prefer reuse), else create fresh
        for p in range(A.get_num_states()):
            new_reg_size = i + 1 - len(to_erase)
            # the next state must have same length for the register size
            if reg_size_map[p] != new_reg_size:
                continue
            Aprime = A.clone()
            self.log_printer.debug(f"Trying to set transition ({q}, {tau}, {to_erase}, {p})")
            Aprime.add_transition(q, tau, to_erase, p)
            if self.s_completable(Aprime, sample):
                return Transition(q, tau, to_erase, p)

        # no existing target works -> create fresh state
        new_p = A.get_num_states()
        return Transition(q, tau, to_erase, new_p)

    def search(self, alphabet: Alphabet, w_seq: LetterSeq, sample: Sample):
        for wp in sample.pos:
            wp_seq = alphabet.make_sequence(list(wp))
            if alphabet.test_type(w_seq, wp_seq):
                return True
        return False

    # ---------- S-completability conservative check (sketch) ----------
    #TODO: if a sample has a run with A, ignore it in future checks
    # update it in learn()
    def s_completable(self, A: RegisterAutomaton, sample: Sample):
        """
        Conservative check: add the candidate transition to a shallow copy of A,
        treat undefined transitions as going to a rejecting sink, and verify no
        negative sample becomes accepted and positives remain accepted (if previously readable).
        This is not the full S-completability routine of the paper, but a practical
        check you can replace with the paper's exact procedure.
        """
        # print(A.to_dot())
        # 1. check whether it overlaps with negatives
        for w in self.mutable_neg:
            w_seq = A.alphabet.make_sequence(list(w))
            if A.is_accepted(w_seq):
                return False

        # 2. check whether there exists w=w1w2 in Pos and z=z1z2 in Neg
        # s.t. (q0, ε) -> w1 -> (q, s) and (q0, ε) -> z1 -> (q, s') with sw2 \sim_R s'z2
        # TODO q has a fixed length of register values, so |w2| = |z2|
        for (w, z) in self.mutable_pairs: 
            self.log_printer.debug(f"compare {w} and {z}")
            w_seq = A.alphabet.make_sequence(list(w))
            # now we fix a state and a suffix for w
            w_state = A.get_initial()
            w_reg = A.alphabet.empty_sequence()
            w_suffix = w_seq
            while True:
                z_seq = A.alphabet.make_sequence(list(z))
                assert not A.alphabet.test_type(
                    w_seq, z_seq
                ), f"Error, should not be the same type {w_seq} {z_seq}"
                # now we test on z_seq
                z_state = A.get_initial()
                z_reg = A.alphabet.empty_sequence()
                z_suffix = z_seq

                # first, w_suffix and z_suffix cannot be same type at the beginning
                for j in range(-1, len(z_seq)):
                    # if both are do not reading anything, skip
                    self.log_printer.debug(f"z_state: {z_state}, z_reg: {z_reg}")
                    if j == -1 and len(w_suffix) == len(w_seq):
                        # j == -1 means no letter is read yet for
                        continue
                    if j == -1:
                        z_config = (z_state, z_reg, None)
                    else:
                        z_config = A.step((z_state, z_reg, None), z_seq.letters[j])
                    z_suffix = z_seq.get_suffix(j + 1)
                    # when z_config is None, means cannot reach next state
                    # hence, 
                    self.log_printer.debug(f"z_config: {z_config}")
                    # not possible to reach next state, abort
                    if z_config is None:
                        break
                    z_state, z_reg, _ = z_config
                    # now compare w and z at current state
                    if w_state != z_state:
                        continue
                    # NOTE newly added test by us, without this condition
                    # the definition is not sufficient
                    if not A.alphabet.test_type(w_reg, z_reg):
                        # two reg do not have the same type
                        return False

                    # reach the same state from q0
                    w_type = w_reg.concat(w_suffix)
                    z_type = z_reg.concat(z_suffix)
                    self.log_printer.debug(f"w_reg: {w_reg}")
                    self.log_printer.debug(f"w_suffix: {w_suffix}")
                    self.log_printer.debug(f"z_reg: {z_reg}")
                    self.log_printer.debug(f"z_suffix: {z_suffix}")
                    self.log_printer.debug(f"w_type: {w_type}")
                    self.log_printer.debug(f"z_type: {z_type}")
                    if A.alphabet.test_type(w_type, z_type):
                        return False
                # proceed to next z
                # proceed to next letter in w
                if len(w_suffix) <= 0:
                    break
                # len(w_suffix) > 0
                w_config = A.step((w_state, w_reg, None), w_suffix.letters[0])
                if w_config is None:
                    break
                w_state, w_reg, _ = w_config
                w_suffix = w_suffix.get_suffix(1)

        return True


# positives = [[], [0, 0], [1, 1]]
# positives = [[], [10, 10], [11, 11]]
# negatives = [[0], [0, 1, 1], [0, 1]]

# positives = [[0, 1], [0, -1]]
# negatives = [[], [0,0], [0], [0,0,1], [0, 1, 0, 1], [0, -1, 0, 1], [0,0,0,1]]

# sample = Sample(positives, negatives)
# prefs = list(sample.prefs())
# ordered_prefs = sorted(prefs, key=lambda w: (len(w), w))
# print(prefs)
# print(ordered_prefs)

# sigma = Alphabet(LetterType.REAL, comp_lt)
# A = dra_passive_learn(sample, sigma)

# print(A.to_dot())
# print(A.to_text())
