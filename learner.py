from fractions import Fraction
from typing import List, Set, Dict, Union, Tuple

from typing import Callable

# -------------------------------
#      LETTERS & SEQUENCES
# -------------------------------


class LetterType:
    NAT = "N"  # Natural numbers
    RAT = "Q"  # Rational numbers
    REAL = "R"  # Real numbers

class Letter:
    def __init__(self, value: Union[int, float, Fraction], letter_type: str):
        if letter_type not in {LetterType.NAT, LetterType.RAT, LetterType.REAL}:
            raise ValueError("letter_type must be one of N, Q, R")

        # Type validation
        if letter_type == LetterType.NAT:
            if not (isinstance(value, int) and value >= 0):
                raise ValueError("ℕ requires a non-negative integer")

        if letter_type == LetterType.RAT:
            if not isinstance(value, Fraction):
                value = Fraction(value)

        if letter_type == LetterType.REAL:
            if not isinstance(value, (int, float)):
                raise ValueError("ℝ requires int or float")
            value = float(value)

        self.value = value
        self.letter_type = letter_type

    def __repr__(self):
        return f"{self.value}:{self.letter_type}"


class LetterSequence:
    def __init__(self, letters: List[Letter]):
        if not letters:
            raise ValueError("LetterSequence cannot be empty")

        self.letter_type = letters[0].letter_type

        # Enforce homogeneity
        for l in letters:
            if l.letter_type != self.letter_type:
                raise ValueError("All letters in the sequence must have the same type")

        self.letters = letters

    def append(self, letter: Letter):
        if letter.letter_type != self.letter_type:
            raise ValueError(
                f"Cannot append letter of type {letter.letter_type} "
                f"to a sequence of type {self.letter_type}"
            )
        self.letters.append(letter)

    def __repr__(self):
        return "[" + ", ".join(repr(l) for l in self.letters) + "]"


# ========================
# word type
# ========================


# Equality-only comparator (identity test)
def comp_id(x, y):
    """
    Returns True if x == y, else False.
    """
    return x == y


# Strict order comparator
def comp_lt(x, y):
    """
    Returns True if x < y, else False.
    """
    return x < y


from typing import Callable


def is_same_word_type(
    seq1: LetterSequence, seq2: LetterSequence, comp: Callable[[float, float], object]
) -> bool:
    """
    Returns True iff two LetterSequences induce the same comparison pattern,
    using the provided comparator comp.

    Parameters:
        seq1, seq2: LetterSequence of equal length and same type
        comp: a function comp(x, y) -> value
              Any return value is allowed; only equality between returned values matters.

    Example comparator signatures:
        comp(x, y): return -1 if x < y else 0 if x == y else 1
        comp(x, y): return x < y   # boolean
        comp(x, y): return (x < y, x == y)

    Requirements:
        • len(seq1) == len(seq2)
        • seq1.letter_type == seq2.letter_type
    """

    if len(seq1.letters) != len(seq2.letters):
        return False

    if seq1.letter_type != seq2.letter_type:
        return False

    n = len(seq1.letters)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            c1 = comp(seq1.letters[i].value, seq1.letters[j].value)
            c2 = comp(seq2.letters[i].value, seq2.letters[j].value)
            if c1 != c2:
                return False

    return True


# -------------------------------
#     REGISTER AUTOMATON
# -------------------------------


class Location:
    def __init__(self, name: str, accepting: bool = False):
        self.name = name
        self.accepting = accepting

    def __repr__(self):
        return f"Location({self.name}, accepting={self.accepting})"


class Transition:
    def __init__(self, source: str, tau: LetterSequence, E: Set[int], target: str):
        """
        (p, τ, E, q)
        source: name of p
        tau: LetterSequence (τ), homogeneous type guaranteed
        E: set of indices
        target: name of q
        """
        if not isinstance(tau, LetterSequence):
            raise ValueError("τ must be a LetterSequence")

        self.source = source
        self.tau = tau
        self.E = E
        self.target = target

    def __repr__(self):
        return f"({self.source}, {self.tau}, {self.E}, {self.target})"


class RegisterAutomaton:
    def __init__(self):
        self.locations: Dict[str, Location] = {}
        self.transitions: List[Transition] = []

    def add_location(self, name: str, accepting: bool = False):
        self.locations[name] = Location(name, accepting)

    def add_transition(self, p: str, tau: LetterSequence, E: Set[int], q: str):
        if p not in self.locations or q not in self.locations:
            raise ValueError("Both p and q must be existing locations")
        self.transitions.append(Transition(p, tau, E, q))

    def __repr__(self):
        result = "Register Automaton:\nLocations:\n"
        for loc in self.locations.values():
            result += f"  {loc}\n"
        result += "Transitions:\n"
        for t in self.transitions:
            result += f"  {t}\n"
        return result
    
    def run(self, input_word: List[Letter], 
            comp: Callable[[float, float], object] = comp_id
           ) -> List[Tuple[Location, LetterSequence]]:
        """
        Runs the automaton on the input word (sequence of letters).
        Returns the list of reachable configurations (q, v) at the end.
        """
        # Initial configuration: all locations with empty sequence
        configurations: List[Tuple[Location, LetterSequence]] = [
            (loc, LetterSequence([])) for loc in self.locations.values()
        ]

        # Process each letter in the input word
        for a in input_word:
            new_configurations: List[Tuple[Location, LetterSequence]] = []

            for (loc, v) in configurations:
                for t in self.transitions:
                    if t.source != loc.name:
                        continue

                    # Extend the current sequence with input letter a
                    va_letters = v.letters + [a]
                    va = LetterSequence(va_letters)

                    # Check if va matches the pattern tau (same comparison pattern)
                    if len(va.letters) != len(t.tau.letters):
                        continue  # length must match

                    if va.letter_type != t.tau.letter_type:
                        continue  # type mismatch

                    if is_same_word_type(va, t.tau, comp):
                        # Remove letters at positions in E (simultaneously)
                        # Positions in E are 1-based
                        v_prime_letters = [letter for idx, letter in enumerate(va.letters, 1)
                                           if idx not in t.E]
                        v_prime = LetterSequence(v_prime_letters)
                        new_configurations.append((self.locations[t.target], v_prime))

            # Update configurations for next letter
            configurations = new_configurations

        return configurations


# -------------------------------
#           EXAMPLE
# -------------------------------

if __name__ == "__main__":
    RA = RegisterAutomaton()

    RA.add_location("l0", accepting=False)
    RA.add_location("l1", accepting=True)

    # Homogeneous ℕ sequence: [5, 3, 42]
    tau_nat = LetterSequence(
        [
            Letter(5, LetterType.NAT),
            Letter(3, LetterType.NAT),
            Letter(42, LetterType.NAT),
        ]
    )

    RA.add_transition("l0", tau_nat, {1, 3}, "l1")

    print(RA)

    # --- create some sequences for testing ---

# All ℕ type
seqA = LetterSequence(
    [
        Letter(1, LetterType.NAT),
        Letter(5, LetterType.NAT),
        Letter(5, LetterType.NAT),
        Letter(9, LetterType.NAT),
    ]
)

seqB = LetterSequence(
    [
        Letter(3, LetterType.NAT),
        Letter(7, LetterType.NAT),
        Letter(7, LetterType.NAT),
        Letter(10, LetterType.NAT),
    ]
)

seqC = LetterSequence(
    [
        Letter(2, LetterType.NAT),
        Letter(2, LetterType.NAT),
        Letter(2, LetterType.NAT),
        Letter(2, LetterType.NAT),
    ]
)

seqD = LetterSequence(
    [
        Letter(9, LetterType.NAT),
        Letter(1, LetterType.NAT),
        Letter(5, LetterType.NAT),
        Letter(5, LetterType.NAT),
    ]
)

seqE = LetterSequence(
    [
        Letter(1, LetterType.NAT),
        Letter(9, LetterType.NAT),
        Letter(5, LetterType.NAT),
        Letter(5, LetterType.NAT),
    ]
)


# --- run tests ---
print(seqA, seqB, seqC, seqD, seqE)

print("### Using comp_id (equality only) ###")
print("seqA vs seqB:", is_same_word_type(seqA, seqB, comp_id))
print("seqA vs seqC:", is_same_word_type(seqA, seqC, comp_id))
print("seqA vs seqD:", is_same_word_type(seqA, seqD, comp_id))
print("seqA vs seqE:", is_same_word_type(seqA, seqE, comp_id))

print("\n### Using comp_lt (order only) ###")
print("seqA vs seqB:", is_same_word_type(seqA, seqB, comp_lt))
print("seqA vs seqC:", is_same_word_type(seqA, seqC, comp_lt))
print("seqA vs seqD:", is_same_word_type(seqA, seqD, comp_lt))
print("seqA vs seqE:", is_same_word_type(seqA, seqE, comp_lt))
