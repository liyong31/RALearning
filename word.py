from fractions import Fraction
from typing import List, Set, Dict, Union, Tuple

from typing import Callable
from unittest import result

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
        # letter sequence can be empty list
        if len(letters) > 0:
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
    
    def remove(self, indices: Set[int]):
        # create a new LetterSequence without letters at the given indices
        result = []
        for i in range(len(self.letters)):
            if not (i in indices):
                result.append(self.letters[i])
        return LetterSequence(result)
    
    '''
    we return a function that can map any letter to its corresponding letter
    '''
    def get_bijective_mapping_dense(self, other: 'LetterSequence') -> Callable[[Letter], Letter]:
        if self.letter_type != other.letter_type:
            raise ValueError("Cannot compute bijective mapping between different letter types")
        if len(self.letters) != len(other.letters):
            raise ValueError("Cannot compute bijective mapping between sequences of different lengths")
        # sort both sequences, not in place
        self_sorted = sorted(self.letters, key=lambda x: x.value)
        other_sorted = sorted(other.letters, key=lambda x: x.value)

        def mapper(c: Letter) -> Letter:
            if c.letter_type != self.letter_type:
                raise ValueError("Input letter has wrong type for this mapping")
            v = c.value
            v0 = self_sorted[0].value
            v_last = self_sorted[-1].value

            if v < v0:
                mapped_value = (v - v0) + other_sorted[0].value
            elif v >= v_last:
                mapped_value = (v - v_last) + other_sorted[-1].value
            else:
                # find the interval in which v lies and linearly interpolate
                mapped_value = other_sorted[-1].value
                for i in range(len(self_sorted) - 1):
                    vi = self_sorted[i].value
                    vj = self_sorted[i + 1].value
                    if vi <= v < vj:
                        oi = other_sorted[i].value
                        oj = other_sorted[i + 1].value
                        mapped_value = (v - vi) * (oj - oi) / (vj - vi) + oi
                        break

            return Letter(mapped_value, other.letter_type)

        return mapper

    def __len__(self):
        return len(self.letters)

    # create a new LetterSequence by appending another LetterSequence
    def append_sequence(self, other: 'LetterSequence'):
        if len(other.letters) == 0:
            return self
        if len(self.letters) == 0:
            self.letter_type = other.letter_type
        
        if other.letter_type != self.letter_type:
            raise ValueError(
                f"Cannot append sequence of type {other.letter_type} "
                f"to a sequence of type {self.letter_type}"
            )
        return LetterSequence(self.letters + other.letters)
            

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


# from typing import Callable
Numeric = Union[int, float, Fraction]


def is_same_word_type(
    seq1: LetterSequence, seq2: LetterSequence, comp: Callable[[Numeric, Numeric], object]
) -> bool:
    """
    Returns True iff two LetterSequences induce the same comparison pattern,
    using the provided comparator comp.

    Parameters:
        seq1, seq2: LetterSequence of equal length and same type
        comp: a function comp(x, y) -> value
              Any return value is allowed; only equality between returned values matters.

    Example comparator signatures:
        comp(x, y): return True if x < y else False
        comp(x, y): return x == y   # boolean

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
