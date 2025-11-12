import sys
from typing import List, Set, Tuple, Dict
import example
import alphabet
from alphabet import Letter, LetterSeq, Alphabet
from dra import RegisterAutomaton
from table import ObservationTable
from teacher import Teacher


class RegisterAutomatonLearner:
    """
    Learner for Register Automata (RA) using an observation table.
    """

    def __init__(self, teacher: Teacher, alphabet: Alphabet):
        self.teacher = teacher
        self.alphabet = alphabet
        self.learning_started = False
        self.next_location_map: Dict[Tuple[LetterSeq, LetterSeq], int] = {}
        self.initial_location_id = 0
        self.observation_table: ObservationTable
        self.hypothesis: RegisterAutomaton

    def _close_table_once(self) -> bool:
        """
        Ensure every extended row has a corresponding representative row.
        Returns True if the table is closed, False otherwise.
        """
        self.next_location_map.clear()
        for extended_set in self.observation_table.extended_row_candidates:
            for extended_prefix, extended_memorable in extended_set:
                location_idx = self.observation_table.get_equivalent_row_index(
                    extended_prefix, extended_memorable
                )
                if location_idx < 0:
                    # Table is not closed, add new row
                    self.observation_table.insert_row(extended_prefix, extended_memorable)
                    return False
                else:
                    self.next_location_map[extended_prefix, extended_memorable] = location_idx
        return True

    def close_table(self):
        """
        Iteratively close the observation table until all extended rows have
        a corresponding representative location.
        """
        self.observation_table.pretty_print()
        while not self._close_table_once():
            self.observation_table.pretty_print()

    def start_learning(self):
        """
        Initialize the observation table and start the learning process.
        """
        if self.learning_started:
            raise RuntimeError("Learning has already been started.")

        self.learning_started = True

        # Initialize observation table
        self.observation_table = ObservationTable(
            self.alphabet,
            self.teacher.membership_query,
            self.teacher.memorability_query
        )

        # Add empty column and row
        empty_seq = self.alphabet.empty_sequence()
        self.observation_table.insert_column(empty_seq)
        self.observation_table.insert_row(empty_seq, empty_seq)

        # Close the table and build initial hypothesis
        self.close_table()
        self.construct_hypothesis()

    def construct_hypothesis(self):
        """
        Construct a Register Automaton hypothesis from the observation table.
        """
        self.hypothesis = RegisterAutomaton(self.alphabet)

        # Add locations
        for idx, row in enumerate(self.observation_table.table_rows):
            self.hypothesis.add_location(idx, row.row_prefix, row.row_accepting)

        # Add transitions between locations
        for idx, row in enumerate(self.observation_table.table_rows):
            for ext_prefix, ext_memorable in self.observation_table.extended_row_candidates[idx]:
                last_letter = ext_prefix.letters[-1]
                forget_set = self.compute_forget_set(row.row_memorable, last_letter, ext_memorable)
                # print("row.row_memorable", row.row_memorable.append(last_letter))
                self.hypothesis.add_transition(
                    idx,
                    row.row_memorable.append(last_letter),
                    forget_set,
                    self.next_location_map[ext_prefix, ext_memorable]
                )

        self.hypothesis.set_initial(self.initial_location_id)

    def get_hypothesis(self) -> RegisterAutomaton:
        return self.hypothesis

    def compute_forget_set(
        self, current_memorable: LetterSeq, new_letter: Letter, next_memorable: LetterSeq
    ) -> Set[int]:
        """
        Compute the set of positions in the sequence that can be forgotten.
        """
        forget_set = set()
        memorable_letters = set(next_memorable.letters)
        extended_sequence = current_memorable.letters + [new_letter]

        for idx, letter in enumerate(extended_sequence):
            if letter not in memorable_letters or (idx < len(extended_sequence) - 1 and letter == new_letter):
                forget_set.add(idx)

        return forget_set

    def refine_hypothesis(self, counterexample: LetterSeq):
        """
        Refine the hypothesis using a counterexample sequence that is misclassified.
        """
        print("Processing counterexample:", counterexample)
        target_acceptance = self.teacher.membership_query(counterexample)
        current_location = self.hypothesis.get_initial()
        current_sequence = self.alphabet.empty_sequence()

        for i, letter in enumerate(counterexample.letters):
            next_location, next_sequence, _ = self.hypothesis.step(
                (current_location, current_sequence, None), letter
            )

            suffix_seq = (
                self.alphabet.empty_sequence()
                if i + 1 == len(counterexample)
                else counterexample.get_suffix(i + 1)
            )

            location_memorable = self.observation_table.table_rows[next_location].row_memorable
            location_prefix = self.observation_table.table_rows[next_location].row_prefix

            prefix_seq = counterexample.get_prefix(i + 1)
            prefix_memorable = self.teacher.memorability_query(prefix_seq)

            should_add_row = False
            if not self.alphabet.test_type(location_memorable, prefix_memorable):
                should_add_row = True
            else:
                sigma = prefix_memorable.get_bijective_map(location_memorable)
                mapped_suffix = self.alphabet.apply_map(suffix_seq, sigma)
                composed_seq = location_prefix.concat(mapped_suffix)
                if self.teacher.membership_query(composed_seq) != target_acceptance:
                    should_add_row = True

            if should_add_row:
                mapped_prefix = self.alphabet.apply_map(prefix_seq, sigma)
                mapped_memorable = self.alphabet.apply_map(prefix_memorable, sigma)
                self.observation_table.insert_row(mapped_prefix, mapped_memorable)
                self.observation_table.insert_column(mapped_suffix)
                break

            current_location = next_location
            current_sequence = next_sequence

        self.close_table()
        self.construct_hypothesis()


if __name__ == "__main__":
    # Example usage
    ra_example = example.get_example_ra_2()
    print("Test acceptance:", ra_example.is_accepted(ra_example.alphabet.make_sequence([1, 2, 1, 2])))

    teacher = Teacher(ra_example, example.solve_memorability_query_2)
    learner = RegisterAutomatonLearner(teacher, ra_example.alphabet)
    learner.start_learning()

    max_iterations = 100
    iteration = 0
    while True:
        hypothesis = learner.get_hypothesis()
        print("Current Hypothesis:\n", hypothesis.to_dot())

        equivalent, counterexample = teacher.equivalence_query(
            hypothesis,
            [Letter(1, alphabet.LetterType.REAL),
             Letter(2, alphabet.LetterType.REAL),
             Letter(3, alphabet.LetterType.REAL),
             Letter(4, alphabet.LetterType.REAL),
             Letter(0, alphabet.LetterType.REAL)],
            6
        )

        if equivalent :
            print("Final hypothesis:\n", hypothesis)
            print(hypothesis.to_dot())
            break

        learner.refine_hypothesis(counterexample)
        iteration += 1

    print("Learning completed.")
    sys.exit(0)
