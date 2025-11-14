import random
from typing import Set
from alphabet import Alphabet, LetterType, Letter, LetterSeq, comp_lt
from dra import RegisterAutomaton

class RandomRAGenerator:
    """
    Random generator for deterministic Register Automata (RAs).
    """

    def __init__(self, alphabet: Alphabet, seed: int = 0):
        random.seed(seed)
        self.alphabet = alphabet

    def random_letter_seq(self, length: int) -> LetterSeq:
        """Generate a random LetterSeq of given length."""
        letters = [Letter(random.randint(0, 4), self.alphabet.letter_type) for _ in range(length)]
        return LetterSeq(letters)

    def generate(
        self,
        num_locations: int = 5,
        max_registers: int = 4,
        max_transitions: int = 8,
        accepting_prob: float = 0.3
    ) -> RegisterAutomaton:
        """
        Generate a random deterministic Register Automaton (RA).
        """

        ra = RegisterAutomaton(self.alphabet)

        # --- Create locations
        for i in range(num_locations):
            name = f"L{i}"
            accepting = random.random() < accepting_prob
            ra.add_location(i, name, accepting)

        # --- Pick initial location
        ra.set_initial(0)

        # --- Create transitions
        all_transitions = set()
        num_added = 0

        while num_added < max_transitions:
            src = random.randrange(num_locations)
            tgt = random.randrange(num_locations)
            tau_len = random.randint(1, max_registers)
            tau = self.random_letter_seq(tau_len)

            # Choose random indices to remove (simulate register forgetting)
            remove_count = random.randint(0, tau_len - 1)
            indices_to_remove = set(random.sample(range(tau_len), remove_count))

            # Enforce determinism: no duplicate tau from the same source
            key = (src, str(tau))
            if key in all_transitions:
                continue

            all_transitions.add(key)
            ra.add_transition(src, tau, indices_to_remove, tgt)
            num_added += 1

        return ra
    
if __name__ == "__main__":
    # Example usage
    alphabet = Alphabet(LetterType.REAL, comp_lt)
    generator = RandomRAGenerator(alphabet, seed=42)
    ra = generator.generate(num_locations=3, max_registers=2, max_transitions=5)

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