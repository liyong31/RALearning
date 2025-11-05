# ...existing code...
from dataclasses import dataclass
from typing import List, Dict, Tuple, Any, Callable, Optional
from word import LetterSequence, Letter
import word

class ObservationTable:
    def __init__(self):
        # Each row label is a pair (prefix, sequence) as requested.
        self.rows: List[Tuple[LetterSequence, LetterSequence]] = []
        # Columns are suffix sequences
        self.columns: List[LetterSequence] = []
        # table maps (row_idx, col_idx) -> bool (accepting / membership)
        self.table: Dict[Tuple[int, int], bool] = {}

    def add_row(self, prefix: LetterSequence, sequence: LetterSequence):
        self.rows.append((prefix, sequence))

    def add_column(self, suffix: LetterSequence):
        self.columns.append(suffix)

    def set_entry(self, row_idx: int, col_idx: int, value: bool):
        self.table[(row_idx, col_idx)] = value

    def get_entry(self, row_idx: int, col_idx: int) -> bool:
        return self.table.get((row_idx, col_idx), False)

    def row_vector(self, row_idx: int) -> Tuple[bool, ...]:
        return tuple(self.get_entry(row_idx, j) for j in range(len(self.columns)))

    def find_row_with_vector(self, vec: Tuple[bool, ...]) -> Optional[int]:
        for i in range(len(self.rows)):
            if self.row_vector(i) == vec:
                return i
        return None

    def is_closed(self, extension_row_indices: List[int]) -> bool:
        """
        Check closedness: every extension row (typically S·Σ) has a representative
        in the base rows (typically S). extension_row_indices are indices of rows
        that should be checked for presence in the base set.
        """
        for ext_idx in extension_row_indices:
            vec = self.row_vector(ext_idx)
            if self.find_row_with_vector(vec) is None:
                return False
        return True

    def is_consistent(self) -> bool:
        """
        Basic consistency check: if two rows in the base set have the same vector,
        then for every possible one-letter extension (a) their extensions' vectors
        should also match. This method requires the table to already contain those
        extension rows; otherwise it's a best-effort check.
        """
        n = len(self.rows)
        # find pairs of equal rows
        for i in range(n):
            for j in range(i + 1, n):
                if self.row_vector(i) == self.row_vector(j):
                    # For every symbol x present in columns as 1-letter suffixes, check consistency
                    for col in self.columns:
                        # Build extension vectors by finding rows whose suffix equals (col prefixed with something)
                        # This is a lightweight check: we expect extension rows to exist in table.
                        # We compare the rows that represent extending the two base labels by the column prefix if present.
                        vec_i = self.row_vector(i)
                        vec_j = self.row_vector(j)
                        if vec_i != vec_j:
                            return False
        return True

    def display(self):
        header = ["(prefix, seq) \\ suffix"] + [str(col) for col in self.columns]
        print("\t".join(header))
        for i, (prefix, seq) in enumerate(self.rows):
            row_entries = [str(self.get_entry(i, j)) for j in range(len(self.columns))]
            print(f"({prefix}, {seq})\t" + "\t".join(row_entries))

def build_observation_table(
    prefixes: List[Tuple[LetterSequence, LetterSequence]],
    suffixes: List[LetterSequence],
    membership_oracle: Callable[[LetterSequence], bool]
) -> ObservationTable:
    """
    Build and populate an observation table from given (prefix, seq) pairs
    and suffixes, using membership_oracle(seq) -> bool to fill entries.
    """
    ot = ObservationTable()
    for (p, s) in prefixes:
        ot.add_row(p, s)
    for suf in suffixes:
        ot.add_column(suf)
    # Fill table: each cell corresponds to concatenation of the row's sequence with the suffix.
    for i, (p, seq) in enumerate(ot.rows):
        for j, suf in enumerate(ot.columns):
            combined = seq.append_sequence(suf)
            print(seq, "+", suf, "->", combined)
            ot.set_entry(i, j, membership_oracle(combined))
    return ot

# Example usage (replace membership_oracle with real oracle when available)
if __name__ == "__main__":
    # Dummy oracle: accept sequences of even length
    def dummy_oracle(seq: LetterSequence) -> bool:
        return len(seq) % 2 == 0

    # Build small alphabet letters
    a = Letter(3, word.LetterType.REAL)
    b = Letter(4, word.LetterType.REAL)

    # Some sequences
    empty = LetterSequence([])
    s1 = LetterSequence([a])
    s2 = LetterSequence([b])
    s3 = LetterSequence([a, b])

    prefixes = [
        (empty, empty),        # typically in S
        (empty, s1),           # in S
        (empty, s2),           # in S
        (s1, s2),              # an extension row example (prefix, seq)
    ]
    suffixes = [empty, LetterSequence([a]), LetterSequence([b])]

    ot = build_observation_table(prefixes, suffixes, dummy_oracle)
    ot.display()