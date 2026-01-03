from fractions import Fraction
from typing import List, Set, Dict, Union, Tuple, Callable

# -------------------------------
#     TYPE ALIASES
# -------------------------------
Numeric = Union[float, Fraction]


# -------------------------------
#     LETTER TYPES
# -------------------------------
class LetterType:
    RATIONAL = "rational"
    REAL = "real"


# -------------------------------
#     LETTER
# -------------------------------
class Letter:
    def __init__(self, value: Numeric, letter_type: str):
        if letter_type not in {LetterType.RATIONAL, LetterType.REAL}:
            raise ValueError("letter_type must be (rational) or (real)")

        if letter_type == LetterType.RATIONAL:
            self.value = Fraction(value)
        else:  # REAL
            if not isinstance(value, (int, float, Fraction)):
                raise ValueError("Real letters must be numeric")
            self.value = float(value)

        self.letter_type = letter_type

    def __eq__(self, other):
        return isinstance(other, Letter) and (
            self.letter_type == other.letter_type and self.value == other.value
        )
    
    def __lt__(self, other):
        if not isinstance(other, Letter):
            return NotImplemented

        # require same type for comparison
        if self.letter_type != other.letter_type:
            raise TypeError("Cannot compare Rational letter with Real letter")

        return self.value < other.value

    def __hash__(self):
        return hash((self.value, self.letter_type))

    def __repr__(self):
        return f"{self.value}"
    


# -------------------------------
#     LETTER SEQUENCE
# -------------------------------
class LetterSeq:
    def __init__(self, letters: List[Letter]):
        self.letters = letters
        if letters:
            # Ensure all letters share the same type
            first_type = letters[0].letter_type
            if any(l.letter_type != first_type for l in letters):
                raise ValueError("All letters in the sequence must have the same type")
            self.letter_type = first_type
        else:
            self.letter_type = None  # set dynamically when needed

    # --- Constructors ---
    @staticmethod
    def empty(letter_type: str) -> "LetterSeq":
        seq = LetterSeq([])
        seq.letter_type = letter_type
        return seq

    # --- Core operations ---
    def append(self, letter: Letter) -> "LetterSeq":
        if self.letter_type and letter.letter_type != self.letter_type:
            raise ValueError("Cannot append a letter of mismatched type")
        return LetterSeq(self.letters + [letter])
    
    def preappend(self, letter: Letter) -> "LetterSeq":
        if self.letter_type and letter.letter_type != self.letter_type:
            raise ValueError("Cannot append a letter of mismatched type")
        return LetterSeq([letter] + self.letters)

    def remove_by_indices(self, indices: Set[int]) -> "LetterSeq":
        remaining = [l for i, l in enumerate(self.letters) if i not in indices]
        if len(remaining) == 0:
            return LetterSeq.empty(self.letter_type)
        return LetterSeq(remaining)

    def __len__(self) -> int:
        return len(self.letters)

    def __eq__(self, other):
        return (
            isinstance(other, LetterSeq)
            and self.letter_type == other.letter_type
            and self.letters == other.letters
        )

    def __hash__(self):
        return hash(tuple(self.letters))

    def __repr__(self):
        return "[" + ", ".join(repr(l) for l in self.letters) + "]"

    # --- Utilities ---
    def get_prefix(self, length: int) -> "LetterSeq":
        if length <= 0:
            return LetterSeq.empty(self.letter_type)
        if length > len(self):
            raise ValueError("Prefix length exceeds sequence length")
        return LetterSeq(self.letters[:length])

    def get_suffix(self, start_index: int) -> "LetterSeq":
        if start_index < 0 or start_index >= len(self):
            return LetterSeq.empty(self.letter_type)
        return LetterSeq(self.letters[start_index:])
    
    # inside LetterSeq class
    def get_letter_extension(self, comparator: Callable[['Letter', 'Letter'], bool]) -> 'LetterSeq':
        """
        Returns a new LetterSeq that extends the current sequence by one or more letters
        based on the provided comparator. This is useful for generating candidate extensions
        in learning algorithms.

        Parameters
        ----------
        comparator : Callable[[Letter, Letter], bool]
            A comparison function, e.g., equality (comp_id) or less-than (comp_lt).

        Returns
        -------
        LetterSeq
            A new LetterSeq with extended letters.
        """
        if len(self.letters) == 0:
            # If sequence is empty, create a default letter of value 0
            return LetterSeq([Letter(0, self.letter_type)])

        # Sort letters by value, but remove redundant appearances
        sorted_letters = sorted(set(self.letters), key=lambda x: x.value)
        max_value = sorted_letters[-1].value
        min_value = sorted_letters[0].value

        if comparator == comp_id:
            # Identity comparator: just add one more letter with value > max
            return LetterSeq(self.letters + [Letter(max_value + 1, self.letter_type)])

        elif comparator == comp_lt:
            # Less-than comparator: insert midpoints between consecutive letters, plus one above max and below min
            extended_letters = []
            for i in range(len(sorted_letters) - 1):
                extended_letters.append(sorted_letters[i])
                if sorted_letters[i].value != sorted_letters[i + 1].value:
                    midpoint = (sorted_letters[i].value + sorted_letters[i + 1].value) / 2
                    extended_letters.append(Letter(midpoint, self.letter_type))
            extended_letters.append(sorted_letters[-1])
            # Add extra letters beyond current range
            extended_letters.append(Letter(max_value + 1, self.letter_type))
            extended_letters.append(Letter(min_value - 1, self.letter_type))
            return LetterSeq(extended_letters)

        else:
            raise ValueError("Unsupported comparator for letter extension")

    def concat(self, other: "LetterSeq") -> "LetterSeq":
        if other.letter_type != self.letter_type:
            raise ValueError("Cannot concatenate sequences of different types")
        if len(other) == 0 and len(self.letters) == 0:
            return LetterSeq.empty(self.letter_type)
        return LetterSeq(self.letters + other.letters)
    
    def index(self, x: Letter) -> int:
        for i, l in enumerate(self.letters):
            if x == l:
                return i
        return -1
    
    def get_letter(self, i: int) -> Letter:
        if i < 0 or i >= self.__len__():
            raise ValueError(f"Index outside the scope {i}")
        return self.letters[i]

    # --- Dense mapping ---
    def get_bijective_map(self, other: "LetterSeq") -> Callable[[Letter], Letter]:
        if self.letter_type != other.letter_type:
            raise ValueError("Letter type mismatch for bijective mapping")
        if len(self.letters) != len(other.letters):
            raise ValueError("Sequences must have the same length")

        if not self.letters:
            return lambda c: c  # empty identity map

        s_sorted = sorted(self.letters, key=lambda l: l.value)
        o_sorted = sorted(other.letters, key=lambda l: l.value)

        def mapper(letter: Letter) -> Letter:
            if letter.letter_type != self.letter_type:
                raise ValueError("Wrong letter type for mapping")

            v = letter.value
            v0, v_last = s_sorted[0].value, s_sorted[-1].value

            if v < v0:
                mapped = o_sorted[0].value + (v - v0)
            elif v >= v_last:
                mapped = o_sorted[-1].value + (v - v_last)
            else:
                mapped = o_sorted[-1].value
                for i in range(len(s_sorted) - 1):
                    vi, vj = s_sorted[i].value, s_sorted[i + 1].value
                    if vi <= v < vj:
                        oi, oj = o_sorted[i].value, o_sorted[i + 1].value
                        mapped = oi + (v - vi) * (oj - oi) / (vj - vi)
                        break

            return Letter(mapped, other.letter_type)

        return mapper


# -------------------------------
#     COMPARATORS
# -------------------------------
def comp_id(x: Numeric, y: Numeric) -> bool:
    return x == y


def comp_lt(x: Numeric, y: Numeric) -> bool:
    return x < y


def is_same_type(
    seq1: LetterSeq, seq2: LetterSeq, comp: Callable[[Numeric, Numeric], bool]
) -> bool:
    """Return True iff two LetterSeqs induce the same comparison pattern."""
    if len(seq1) != len(seq2) or seq1.letter_type != seq2.letter_type:
        return False

    for i in range(len(seq1)):
        for j in range(len(seq1)):
            if i == j:
                continue
            if comp(seq1.letters[i].value, seq1.letters[j].value) != comp(
                seq2.letters[i].value, seq2.letters[j].value
            ):
                return False
    return True


# -------------------------------
#     ALPHABET
# -------------------------------
class Alphabet:
    def __init__(self, letter_type: str, comparator: Callable[[Numeric, Numeric], bool]):
        if letter_type not in {LetterType.REAL, LetterType.RATIONAL}:
            raise ValueError("Invalid letter type for Alphabet")
        self.letter_type = letter_type
        self.comparator = comparator

    def make_letter(self, value: Numeric) -> Letter:
        return Letter(value, self.letter_type)

    def make_sequence(self, values: List[Numeric]) -> LetterSeq:
        if not values:
            return LetterSeq.empty(self.letter_type)
        return LetterSeq([self.make_letter(v) for v in values])
    
    def form_sequence(self, letters: List[Letter]):
        if len(letters) <= 0:
            return LetterSeq.empty(self.letter_type)
        else:
            return LetterSeq(letters)

    def empty_sequence(self) -> LetterSeq:
        return LetterSeq.empty(self.letter_type)

    def test_type(self, seq1: LetterSeq, seq2: LetterSeq) -> bool:
        return is_same_type(seq1, seq2, self.comparator)

    def concat_sequences(self, seq1: LetterSeq, seq2: LetterSeq) -> LetterSeq:
        return seq1.concat(seq2)

    def apply_map(
        self, seq: LetterSeq, mapping_fn: Callable[[Letter], Letter]
    ) -> LetterSeq:
        if not seq.letters:
            return self.empty_sequence()
        return LetterSeq([mapping_fn(l) for l in seq.letters])
