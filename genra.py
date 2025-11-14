import random
from alphabet import Alphabet, LetterType, Letter, LetterSeq, comp_lt
from dra import RegisterAutomaton

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
                 num_registers: int = 3,
                 max_transitions: int = 10,
                 accepting_prob: float = 0.3) -> RegisterAutomaton:

        ra = RegisterAutomaton(self.alphabet)

        # --- Initial state ---
        initial_u = self.alphabet.empty_sequence()
        ra.add_location(0, initial_u, accepting=random.random() < accepting_prob)
        ra.set_initial(0)

        sequences = [initial_u]             # existing state labels
        location_map = {str(initial_u): 0}  # map u -> location id
        next_loc_id = 1

        added_transitions = set()
        num_added = 0

        while num_added < max_transitions and len(sequences) < num_states:
            # pick source
            src_idx = random.randrange(len(sequences))
            u = sequences[src_idx]
            src = location_map[str(u)]

            # skip if current state already at max registers
            if len(u.letters) >= num_registers:
                continue

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
            remove_count = random.randint(0, len(tau.letters))
            indices_to_remove = set(random.sample(range(len(tau.letters)), remove_count)) if remove_count > 0 else set()

            # compute target label
            v = tau.remove_by_indices(indices_to_remove)

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

            # add transition
            ra.add_transition(src, tau, indices_to_remove, tgt)
            added_transitions.add(key)
            num_added += 1

        return ra


    
if __name__ == "__main__":
    # Example usage
    alphabet = Alphabet(LetterType.REAL, comp_lt)
    generator = StructuredRandomRAGenerator(alphabet, seed=42)
    ra = generator.generate(num_states=6, num_registers=4, max_transitions=20, accepting_prob=0.4)

    print("Generated Random Register Automaton:")
    print(ra)     
    print(ra.to_text())
    
    text_repr = ra.to_text()
    with open("ra.txt", "w") as f:
        f.write(text_repr)

    # Load back
    with open("ra.txt") as f:
        text_data = f.read()
    print("===============================")
    ra2 = RegisterAutomaton.from_text(text_data)
    print(ra2.to_text())