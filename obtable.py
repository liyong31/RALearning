# ...existing code...
from dataclasses import dataclass
from typing import List, Set, Dict, Tuple, Any, Callable, Optional
from word import LetterSequence, Letter, Numeric, is_same_word_type
import word

'''
So, a table is organised in rows and columns.
Each row is labelled by a pair (prefix, sequence) and contains a vector of entries.
Each column is labelled by a suffix sequence and maps column to a position in the vector of entries.
The entry at (row, column) indicates whether the concatenation

'''

class TableRow:
    def __init__(self, prefix: LetterSequence
                 , memorable: LetterSequence
                 , comp: Callable[[Numeric, Numeric], bool]):
        # prefix word
        self.prefix = prefix
        # memorable word for prefix
        self.memorable = memorable
        self.comp = comp
        self.entries: List[bool] = []
        self.accepting = False
        
    def set_accepting(self, accepting: bool):
        self.accepting = accepting
        
    def get_accepting(self):
        return self.accepting

    def append_entry(self, value: bool):
        self.entries.append(value)
        
    def get_entry(self, col_idx: int):
        if col_idx >= len(self.entries):
            raise Exception("col_idx exceends length of row")
        return self.entries[col_idx]
    
    # we only check the memorable and prefix values        
    def __eq__(self, value):
        if not isinstance(value, TableRow):
            raise ValueError("Can only compare with another TableRow")
        if len(self.memorable) != len(value.memorable):
            return False
        # build mapping
        if not is_same_word_type(self.memorable, value.memorable, self.comp):
            return False
        
        return self.prefix == value.prefix and self.memorable == value.memorable

    def __repr__(self):
        return f"({self.prefix}, {self.memorable})"
    
    def __hash__(self):
        return hash((tuple(self.prefix.letters), tuple(self.memorable.letters)))
    
class ObservationTable:
    def __init__(self, comp: Callable[[Numeric, Numeric], bool]
                 , membership_oracle: Callable[[LetterSequence], bool]
                 , memorability_oracle : Callable[[LetterSequence], LetterSequence]):
        self.comparator = comp
        # Each row label is a pair (prefix, sequence) as requested.
        self.rows: List[TableRow] = []
        # Columns are suffix sequences
        self.columns: List[LetterSequence] = []
        # only record those extensions that might be moved to rows
        self.ext_rows : List[Set[Tuple[LetterSequence, LetterSequence]]] = []
        # to save membership queries, we can save inequal rows for extended rows
        self.unequal_for_ext_rows: Dict[Tuple[LetterSequence, LetterSequence], Set[TableRow]] = {}
        # table maps (row_idx, col_idx) -> bool (accepting / membership)
        # self.table: Dict[Tuple[int, int], bool] = {}
        self.membership_oracle = membership_oracle
        self.memorability_oracle = memorability_oracle
    
    def exists_row(self, prefix: LetterSequence, memorable: LetterSequence):
        r = TableRow(prefix, memorable, self.comparator)
        for row in self.rows:
            if row == r:
                return row
        return None
            

    def add_row(self, prefix: LetterSequence, memorable: LetterSequence):
        row = TableRow(prefix, memorable, self.comparator)
        self.rows.append(row)
        mq_result = self.membership_oracle(prefix)
        row.set_accepting(mq_result)
        # now fill the table
        for column_idx in range(len(self.columns)):
            suffix = self.columns[column_idx]
            composed_seq = LetterSequence(prefix.letters + suffix.letters)
            row.append_entry(self.membership_oracle(composed_seq))
        ext_set = self.generate_extended_rows(row)
        self.ext_rows.append(ext_set)
        return row

    def add_column(self, suffix: LetterSequence):
        self.columns.append(suffix)
        # now, for every row, we need to ask membership queries
        for row in self.rows:
            mq_result = self.membership_oracle(LetterSequence(row.prefix.letters + suffix.letters))
            row.append_entry(mq_result)
    
    # only need to do this for a new added row        
    def generate_extended_rows(self, row: TableRow):
        print("row", row.prefix)
        extensions = row.prefix.get_letter_extension(self.comparator)
        print(extensions)
        print("extensions", extensions.letter_type)
        ext_set : Set[Tuple[LetterSequence, LetterSequence]]= set()
        for letter in extensions.letters:
            ext_row = row.prefix.append_sequence(LetterSequence([letter]))
            memorable_ext_row = self.memorability_oracle(ext_row)
            ext_set.add((ext_row, memorable_ext_row))
        return ext_set

    def get_entry(self, row_idx: int, col_idx: int) -> bool:
        return self.rows[row_idx].get((row_idx, col_idx), False)
    
    # check whether an extended row is equivalent to a current representative
    def is_equivalent(self, row: TableRow, ext_prefix: LetterSequence, ext_memorable: LetterSequence):
        """
        we check for every row (u, v), whether the extended row (u', v') is equivalent to all columns w such that
        first check whether memorable words are of the same type, if no, return False
        otherwise, obtain a map sigma from v' to v
        check whether sigma(u') w in L iff uw in L
        """
        print("=====================================")
        print("Check row ", row.prefix, row.memorable)
        print("Search for ", ext_prefix, ext_memorable)
        if row in self.unequal_for_ext_rows[(ext_prefix, ext_memorable)]:
            return False
        # check whether it is the same row
        if row.prefix == ext_prefix and row.memorable == ext_memorable:
            return True
        print("row mem", row.memorable)
        print("ext mem", ext_memorable)
        if not word.is_same_word_type(row.memorable, ext_memorable, self.comparator):
            self.unequal_for_ext_rows[(ext_prefix, ext_memorable)].add(row)
            return False
        sigma = ext_memorable.get_bijective_mapping_dense(row.memorable)
        print("ext_prefix:", ext_prefix)
        print("ext_mem:", ext_memorable)
        print("mem refix:", row.memorable)
        mapped_ext_prefix = LetterSequence([sigma(l) for l in ext_prefix.letters])
        for column_idx in range(len(self.columns)):
            suffix = self.columns[column_idx]
            composed_seq = LetterSequence(mapped_ext_prefix.letters + suffix.letters)
            mq_result = self.membership_oracle(composed_seq)
            if mq_result != row.get_entry(column_idx):
                self.unequal_for_ext_rows[(ext_prefix, ext_memorable)].add(row)
                return False
        return True
    
    def find_equivalent_row(self, ext_prefix: LetterSequence, ext_memorable: LetterSequence):
            # ensure cache key exists to avoid KeyError inside is_equivalent
            print(self.unequal_for_ext_rows)
            self.unequal_for_ext_rows.setdefault((ext_prefix, ext_memorable), set())
            for idx, row in enumerate(self.rows):
                if self.is_equivalent(row, ext_prefix, ext_memorable):
                    print("Found row", idx)
                    return idx
            return -1
    
    def pretty_print(self):
        if not self.rows or not self.columns:
            print("(empty table)")
            return

        # Convert all entries to strings for width computation
        col_labels = [str(c) for c in self.columns]

        # Compute widths
        col_width = max(len(label) for label in col_labels + ["Result"]) + 2
        row_label_width = max(len(str((r.prefix, r.memorable))) for r in self.rows) + 2

        # Header
        header = " " * row_label_width + "".join(f"{label:>{col_width}}" for label in col_labels)
        print(header)
        print("-" * len(header))

        # Rows
        for row in self.rows:
            row_label = f"{(row.prefix, row.memorable)}"
            entries = [("✓" if row.get_entry(j) else "✗") for j in range(len(self.columns))]
            row_str = f"{row_label:<{row_label_width}}" + "".join(f"{e:>{col_width}}" for e in entries)
            print(row_str)


# Example usage (replace membership_oracle with real oracle when available)
if __name__ == "__main__":
    # Dummy oracle: accept sequences of even length
    t = ObservationTable(lambda x, y: x == y, None, None)
    t.columns = [LetterSequence([Letter(1, word.LetterType.REAL)]), LetterSequence([Letter(2, word.LetterType.REAL)]), LetterSequence([Letter(1, word.LetterType.REAL), Letter(2, word.LetterType.REAL)])]
    row1 = TableRow(LetterSequence([Letter(1, word.LetterType.REAL)]), LetterSequence([Letter(3, word.LetterType.REAL)]), lambda x,y: x==y)
    row1.entries = [True, False, True]
    row2 = TableRow(LetterSequence([Letter(2, word.LetterType.REAL)]), LetterSequence([Letter(4, word.LetterType.REAL)]), lambda x,y: x==y)
    row2.entries = [False, True, False]
    t.rows = [row1, row2]

    t.pretty_print()