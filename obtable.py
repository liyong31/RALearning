from typing import List, Dict, Tuple

class ObservationTable:
    def __init__(self):
        # Row labels: List of pairs of LetterSequence
        self.rows: List[Tuple[LetterSequence, LetterSequence]] = []

        # Column labels: List of LetterSequence
        self.columns: List[LetterSequence] = []

        # Entries: Dict mapping (row_idx, col_idx) -> bool
        self.table: Dict[Tuple[int, int], bool] = {}

    def add_row(self, prefix: LetterSequence, sequence: LetterSequence):
        """Add a new row labeled by (prefix, sequence)"""
        self.rows.append((prefix, sequence))

    def add_column(self, suffix: LetterSequence):
        """Add a new column labeled by suffix"""
        self.columns.append(suffix)

    def set_entry(self, row_idx: int, col_idx: int, value: bool):
        """Set the boolean value for a given row/column"""
        self.table[(row_idx, col_idx)] = value

    def get_entry(self, row_idx: int, col_idx: int) -> bool:
        """Retrieve the boolean value for a given row/column"""
        return self.table.get((row_idx, col_idx), False)

    def display(self):
        """Print the observation table"""
        # Header
        header = ["(prefix, seq) \\ suffix"] + [str(col) for col in self.columns]
        print("\t".join(header))

        for i, (prefix, seq) in enumerate(self.rows):
            row_entries = [str(self.get_entry(i, j)) for j in range(len(self.columns))]
            print(f"({prefix}, {seq})\t" + "\t".join(row_entries))
