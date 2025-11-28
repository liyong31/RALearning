from email import parser
import random
from alphabet import Alphabet, LetterType, Letter, LetterSeq, comp_lt
from dra import RegisterAutomaton
import sys
import random
from alphabet import Alphabet, Letter, LetterSeq
from dra import RegisterAutomaton

class StructuredRandomRAGenerator:
    """
    Random generator for deterministic RAs with:
    1. Location labels u
    2. tau = u + [l] for outgoing transitions
    3. Target v = tau after removing indices E
    4. l comes from u.get_letter_extension(alphabet.comparator)
    5. Max number of states and max number of registers controlled
    """

    def __init__(self, alphabet: Alphabet, seed: int = 0):
        random.seed(seed)
        self.alphabet = alphabet

    def generate(self,
                 num_states: int = 5,
                #  num_registers: int = 3,
                 accepting_prob: float = 0.3) -> RegisterAutomaton:

        ra = RegisterAutomaton(self.alphabet)

        # --- Initial state ---
        initial_u = self.alphabet.empty_sequence()
        ra.add_location(0, initial_u, accepting=random.random() < accepting_prob)
        ra.set_initial(0)

        sequences = [initial_u]             # existing state labels
        location_map = {str(initial_u): 0}  # map u -> location id
        next_loc_id = 1
        dest_locs = set()
        dest_locs.add(0)

        added_transitions = set()

        while len(sequences) < num_states:
            # pick source
            src_idx = random.randrange(len(sequences))
            u = sequences[src_idx]
            src = location_map[str(u)]
            
            if len(u) == 1:
                dest_locs.add(src)

            # skip if current state already at max registers
            # if len(u.letters) >= num_registers:
            #     continue

            # get possible letter extensions
            extensions = u.get_letter_extension(self.alphabet.comparator)
            if not extensions:
                continue

            # pick random letter l from extensions
            l = random.choice(extensions.letters)
            tau = u.append(l)

            # enforce determinism
            key = (src, str(tau))
            if key in added_transitions:
                continue

            # randomly choose indices to remove
            #remove_count = random.randint(0, len(tau.letters))
            keep_count = random.randint(0, len(tau.letters))
            indices_to_keep = set(random.sample(range(len(tau.letters)), keep_count)) if keep_count > 0 else set()
            # indices_to_remove = set(random.sample(range(len(tau.letters)), remove_count)) if remove_count > 0 else set()
            # letters_to_remove = set([letter for i, letter in enumerate(tau.letters) if i in indices_to_remove])
            keep_letters = [ l for i, l in enumerate(tau.letters) if i in indices_to_keep]  
            # for i, letter in enumerate(tau.letters):
            #     if letter in letters_to_remove:
            #         indices_to_remove.add(i)
            # compute target label
            v = self.alphabet.form_sequence(
                self.keep_last_occurrences(keep_letters))
            # tau.remove_by_indices(indices_to_remove)

            # add target location if new and limit num_states
            v_str = str(v)
            if v_str in location_map:
                tgt = location_map[v_str]
            elif len(location_map) < num_states:
                tgt = next_loc_id
                next_loc_id += 1
                ra.add_location(tgt, v, accepting=random.random() < accepting_prob)
                sequences.append(v)
                location_map[v_str] = tgt
            else:
                # cannot add new state, skip
                continue
            # compute the indices_to_remove
            indices_keep_map = {l:0 for l in keep_letters}
            for i, l in enumerate(tau.letters):
                if l in keep_letters:
                    indices_keep_map[l] = max(i, indices_keep_map[l])
            
            indices_to_remove = set(range(len(tau.letters))) - set(indices_keep_map.values())
            # add transition
            ra.add_transition(src, tau, indices_to_remove, tgt)
            added_transitions.add(key)
        
        # now make sure each location has at least one transition
        for loc_id, loc in ra.locations.items():
            if len(loc.transitions) > 0:
                continue
                # get possible letter extensions
            u = sequences[loc_id]
            extensions = u.get_letter_extension(self.alphabet.comparator)
            if not extensions:
                continue
            # pick random letter l from extensions
            l = random.choice(extensions.letters)
            tau = u.append(l)
            # either go to the initial or one-letter state
            dest = random.choice(list(dest_locs))
            indices_to_remove = set()
            if dest != 0:
                indices_to_remove = set(range(len(tau)-1))
            else:
                indices_to_remove = set(range(len(tau)))
            ra.add_transition(loc_id, tau, indices_to_remove, dest)
                
        
        return ra.get_normalised_dra()

    def keep_last_occurrences(self, seq):
        """
        Return a list where for each letter in seq,
        only its last occurrence is kept.
        Order of surviving letters is preserved.
        """
        seen = set()
        out = []
        # iterate backwards, collect first time we see a letter (from the end)
        for x in reversed(seq):
            if x not in seen:
                seen.add(x)
                out.append(x)
        # reverse again to restore forward order
        return list(reversed(out))
    
if __name__ == "__main__":
    # Example usage
    import argparse
    parser = argparse.ArgumentParser(description="Generate a random Register Automaton (RA) and output its text representation.")
    parser.add_argument('--num', type=int, default=6,
                        help='number of states in the generated RA')
    parser.add_argument('--seed', type=int, default=0,
                        help='random seed for RA generation')
    parser.add_argument('--out', type=str, default='ra.txt',
                        help='output file to save the RA text representation')
    args = parser.parse_args()
    alphabet = Alphabet(LetterType.REAL, comp_lt)
    generator = StructuredRandomRAGenerator(alphabet, seed=int(args.seed))
    ra = generator.generate(num_states=int(args.num), accepting_prob=0.3)

    print("Generated Random Register Automaton:")
    print(ra)     
    print(ra.to_text())
    
    text_repr = ra.to_text()
    with open(args.out, "w") as f:
        f.write(text_repr)
    
    print("#States:", ra.get_num_states())
    print("#Trans:", ra.get_num_trans())

    # # Load back
    # with open(args.out) as f:
    #     text_data = f.read()
    # print("===============================")
    # ra2 = RegisterAutomaton.from_text(text_data)
    # print(ra2.to_text())
    
    # # make complete sure they are the same
    # assert ra.to_text() == ra2.to_text()
    # print("===============================")
    # print("Making complete:")
    # ra2.make_complete()
    # print(ra2.to_text())
# --- LetterSeq methods ---