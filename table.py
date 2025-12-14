# observation_table.py
from typing import List, Set, Dict, Tuple, Callable
from alphabet import LetterSeq, Alphabet


class TableRow:
    """
    Represents a row in the observation table.
    Each row is labeled by (row_prefix, row_memorable) and contains entries for all columns.
    """
    def __init__(self, row_prefix: LetterSeq, row_memorable: LetterSeq):
        self.row_prefix = row_prefix
        self.row_memorable = row_memorable
        self.membership_entries: List[bool] = []
        self.row_accepting: bool = False

    def set_accepting(self, accepting: bool):
        self.row_accepting = accepting

    def append_entry(self, value: bool):
        self.membership_entries.append(value)

    def get_entry(self, col_index: int) -> bool:
        if col_index >= len(self.membership_entries):
            raise IndexError("Column index exceeds row length")
        return self.membership_entries[col_index]

    def __eq__(self, other):
        return (
            isinstance(other, TableRow) and
            self.row_prefix == other.row_prefix and
            self.row_memorable == other.row_memorable
        )

    def __hash__(self):
        return hash((tuple(self.row_prefix.letters), tuple(self.row_memorable.letters)))

    def __repr__(self):
        return f"({self.row_prefix}, {self.row_memorable})"


class ObservationTable:
    """
    Represents an observation table for learning register automata.
    Maintains rows (prefixes + memorable sequences) and columns (suffix sequences).
    """
    def __init__(
        self,
        alphabet: Alphabet,
        membership_query: Callable[[LetterSeq], bool],
        memorable_sequence_query: Callable[[LetterSeq], LetterSeq]
    ):
        self.alphabet = alphabet
        self.membership_query = membership_query
        self.memorable_sequence_query = memorable_sequence_query

        self.table_rows: List[TableRow] = []
        self.table_suffixes: List[LetterSeq] = []
        self.extended_row_candidates: List[Set[Tuple[LetterSeq, LetterSeq]]] = []
        self.inconsistent_rows_cache: Dict[Tuple[LetterSeq, LetterSeq], Set[TableRow]] = {}

    # -----------------------
    # Row operations
    # -----------------------
    def get_row_index(self, row_prefix: LetterSeq, row_memorable: LetterSeq) -> int:
        for idx, row in enumerate(self.table_rows):
            if row.row_prefix == row_prefix and row.row_memorable == row_memorable:
                return idx
        return -1

    def insert_row(self, row_prefix: LetterSeq, row_memorable: LetterSeq) -> TableRow:
        row = TableRow(row_prefix, row_memorable)
        row.set_accepting(self.membership_query(row_prefix))

        # Fill row entries for existing suffixes
        for suffix in self.table_suffixes:
            joined_seq = self.alphabet.concat_sequences(row_prefix, suffix)
            row.append_entry(self.membership_query(joined_seq))

        self.table_rows.append(row)
        # Compute extended row candidates
        self.extended_row_candidates.append(self.generate_extended_rows(row))
        return row

    # -----------------------
    # Column operations
    # -----------------------
    def get_column_index(self, suffix: LetterSeq) -> int:
        for idx, col in enumerate(self.table_suffixes):
            if col == suffix:
                return idx
        return -1

    def insert_column(self, suffix: LetterSeq):
        if self.get_column_index(suffix) >= 0:
            return
        self.table_suffixes.append(suffix)
        # Update entries for all rows
        for row in self.table_rows:
            joined_seq = self.alphabet.concat_sequences(row.row_prefix, suffix)
            row.append_entry(self.membership_query(joined_seq))

    # -----------------------
    # Extended row handling
    # -----------------------
    def generate_extended_rows(self, row: TableRow) -> Set[Tuple[LetterSeq, LetterSeq]]:
        """
        Generate all candidate extended rows for a given row by extending its prefix.
        Returns a set of (extended_prefix, extended_memorable) tuples.
        """
        extensions = row.row_memorable.get_letter_extension(self.alphabet.comparator)
        extended_set: Set[Tuple[LetterSeq, LetterSeq]] = set()
        for letter in extensions.letters:
            extended_prefix = row.row_prefix.concat(LetterSeq([letter]))
            extended_memorable = self.memorable_sequence_query(extended_prefix)
            extended_set.add((extended_prefix, extended_memorable))
        return extended_set

    # -----------------------
    # Equivalence checking
    # -----------------------
    def check_equivalence_with_reference_row(
        self, reference_row: TableRow, candidate_prefix: LetterSeq, candidate_memorable: LetterSeq
    ) -> bool:
        """
        Checks if a candidate row (candidate_prefix, candidate_memorable) is equivalent
        to a reference row over all columns.
        """
        self.inconsistent_rows_cache.setdefault((candidate_prefix, candidate_memorable), set())
        if reference_row in self.inconsistent_rows_cache[(candidate_prefix, candidate_memorable)]:
            return False

        if not self.alphabet.test_type(reference_row.row_memorable, candidate_memorable):
            self.inconsistent_rows_cache[(candidate_prefix, candidate_memorable)].add(reference_row)
            return False

        mapper = candidate_memorable.get_bijective_map(reference_row.row_memorable)
        mapped_prefix = self.alphabet.apply_map(candidate_prefix, mapper)

        for col_idx, suffix in enumerate(self.table_suffixes):
            joined_seq = mapped_prefix.concat(suffix)
            if self.membership_query(joined_seq) != reference_row.get_entry(col_idx):
                self.inconsistent_rows_cache[(candidate_prefix, candidate_memorable)].add(reference_row)
                return False

        return True

    def get_equivalent_row_index(self, candidate_prefix: LetterSeq, candidate_memorable: LetterSeq) -> int:
        """
        Return the index of an existing row equivalent to the candidate row, or -1 if none.
        """
        # self.inconsistent_rows_cache.setdefault((candidate_prefix, candidate_memorable), set())
        idx = self.get_row_index(candidate_prefix, candidate_memorable)
        if idx >= 0:
            return idx
        for idx, row in enumerate(self.table_rows):
            if self.check_equivalence_with_reference_row(row, candidate_prefix, candidate_memorable):
                return idx
        return -1

    # -----------------------
    # Utilities
    # -----------------------
    def pretty_print(self, log_printer=print):
        if not self.table_rows or not self.table_suffixes:
            log_printer("(empty table)")
            return

        col_labels = [str(c) for c in self.table_suffixes]
        col_width = max(len(label) for label in col_labels + ["Result"]) + 2
        row_label_width = max(len(str((r.row_prefix, r.row_memorable))) for r in self.table_rows) + 2

        header = " " * row_label_width + "".join(f"{label:>{col_width}}" for label in col_labels)
        log_printer(header)
        log_printer("-" * len(header))

        for row in self.table_rows:
            row_label = f"{(row.row_prefix, row.row_memorable)}"
            entries = [("✓" if row.get_entry(j) else "✗") for j in range(len(self.table_suffixes))]
            row_str = f"{row_label:<{row_label_width}}" + "".join(f"{e:>{col_width}}" for e in entries)
            log_printer(row_str)
