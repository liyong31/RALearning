import bisect
from typing import Iterable, Iterator, Generic, TypeVar

T = TypeVar("T")

class SortedSet(Generic[T]):
    def __init__(self, iterable: Iterable[T] | None = None):
        self.data: list[T] = []
        if iterable is not None:
            for x in iterable:
                self.add(x)

    def add(self, x: T) -> None:
        """Add element in sorted order (if not already present)."""
        i = bisect.bisect_left(self.data, x)
        if i == len(self.data) or self.data[i] != x:
            self.data.insert(i, x)

    def discard(self, x: T) -> None:
        """Remove element if present."""
        i = bisect.bisect_left(self.data, x)
        if i < len(self.data) and self.data[i] == x:
            self.data.pop(i)

    def __contains__(self, x: T) -> bool:
        i = bisect.bisect_left(self.data, x)
        return i < len(self.data) and self.data[i] == x

    def __iter__(self) -> Iterator[T]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return f"SortedSet({self.data})"

    def __str__(self) -> str:
        return "{" + ", ".join(str(x) for x in self.data) + "}"
    
    def union(self, other: Iterable[T]) -> "SortedSet[T]":
        """Return a new SortedSet containing elements from self and other iterable."""
        result = SortedSet(self.data)  # copy current elements
        for x in other:
            result.add(x)
        return result
    
# from alphabet import Letter, LetterType, LetterSeq, Alphabet, comp_lt
# alpa = Alphabet(LetterType.RATIONAL, comp_lt)
# letters = [alpa.make_letter(5), alpa.make_letter(2), alpa.make_letter(3)]
# s = SortedSet(letters)

# print(s)          # {Letter(2), Letter(3), Letter(5)}

# s.add(alpa.make_letter(4))
# print(s)          # {Letter(2), Letter(3), Letter(4), Letter(5)}

# print(alpa.make_letter(3) in s)  # True
# print(len(s))           # 4

# for l in s:
#     print(l)
    
# seq1 = alpa.form_sequence([alpa.make_letter(1), alpa.make_letter(2)])
# seq2 = alpa.form_sequence([alpa.make_letter(1)])
# seq3 = alpa.form_sequence([alpa.make_letter(1), alpa.make_letter(3)])
# seq4 = alpa.form_sequence([alpa.make_letter(1), alpa.make_letter(2), alpa.make_letter(3)])

# # Create sorted set from list of LetterSeq
# sset = SortedSet([seq1, seq2, seq3, seq4])

# print(sset)
# # Output (length-lexicographic): {[1], [1, 2], [1, 3], [1, 2, 3]}

# # Add a new sequence
# sset.add(alpa.form_sequence([alpa.make_letter(0)]))
# print(sset)
# # {[0], [1], [1, 2], [1, 3], [1, 2, 3]}

# # Iteration is deterministic
# for seq in sset:
#     print(seq)
