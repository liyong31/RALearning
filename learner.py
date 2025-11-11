from unittest import result
import example
import word
import sys
from word import Letter, LetterSequence, LetterType
from ra import RegisterAutomaton
from typing import List, Set, Tuple, Callable, Dict, Any
from obtable import TableRow, ObservationTable
from teacher import Teacher

class RALearner:
    """
    Learner for Register Automata (RA) using a table structure
    """
    def __init__(self, oracle: Teacher, comparator: Callable[[Letter, Letter], bool]
                 , letter_type: LetterType):
        self.oracle = oracle
        self.comparator = comparator
        self.already_started = False
        self.letter_type = letter_type
        self.next_loc_map : Dict[Tuple[LetterSequence, LetterSequence], int] = {}
        self.initial = 0
        # find states via its index
        # self.locations:List[TableRow] = []

    def is_accepted(self, seq: LetterSequence, comp: Callable[[Letter, Letter], bool]) -> bool:
        """
        Check if the given LetterSequence is accepted by the RA.
        """
        return self.oracle.is_accepted(seq, comp)
    
    def __get_empty_sequence(self):
        return LetterSequence.get_empty_sequence(self.letter_type)
    
    def __close_table_inner(self):
        self.next_loc_map.clear()
        # we need to make sure that every extended row has an equal row
        for ext_set in self.table.ext_rows:
            for ext_prefix, ext_memorable in ext_set:
                print("search equiv row for ", ext_prefix, ext_memorable)
                res = self.table.find_equivalent_row(ext_prefix, ext_memorable)
                if res < 0:
                    # not closed
                    print("add row", ext_prefix, ext_memorable)
                    self.table.add_row(ext_prefix, ext_memorable)
                    return False
                else:
                    print("({ext_prefix}, {ext_memorable}) -> res")
                    self.next_loc_map[ext_prefix, ext_memorable] = res
        return True
    
    def close_table(self):
        count = 0
        self.table.pretty_print()
        while True:
            res = self.__close_table_inner()
            self.table.pretty_print()
            count = count + 1
            if res :
                break
    
    def start_learning(self):
        if self.already_started:
            raise Exception("Learning has already been started.")
        self.already_started = True
        # Initial learning steps can be added here
         # Initialize the root of the tree with an empty LetterSequence
        self.table = ObservationTable(self.comparator
                                      , self.oracle.membership_query
                                      , self.oracle.memorability_query)
        # add empty column
        self.table.add_column(self.__get_empty_sequence())
        self.table.add_row(self.__get_empty_sequence(), self.__get_empty_sequence())
        # self.locations.append(row)
        self.close_table()
        # construct dra
        self.construct_hypothesis()
        
    def construct_hypothesis(self) -> None:
        # for ext_set in self.table.ext_rows:
        #     print("ext_set", ext_set)
        self.hypothesis = RegisterAutomaton(self.letter_type)
        # For each state node, add a location to the RA
        for idx, row in enumerate(self.table.rows):
            self.hypothesis.add_location(idx, row.prefix, row.get_accepting())
        for idx, row in enumerate(self.table.rows):
            # self.hypothesis.add_location(idx, row.prefix, row.get_accepting())
            for extended_label, extended_memorable in self.table.ext_rows[idx]:
                # print("curr", row.prefix, "extended_seq", extended_label)
                # add memorable sequence to the next_node
                # add transition from current state to next_node
                letter = extended_label.letters[-1]
                E = self.compute_E_set(row.memorable, letter, extended_memorable)
                print("curr idx", idx)
                print("mem ", row.memorable)
                print("letter ", letter)
                print("extended_mem ", extended_memorable)

                print("E set", E)
                self.hypothesis.add_transition(
                        idx,
                        row.memorable.append(letter),
                        E,
                        self.next_loc_map[extended_label, extended_memorable]
                    )
        self.hypothesis.set_initial(self.initial)
        

    def get_hypothesis(self) -> RegisterAutomaton:
        """
        Return the current hypothesis RA.
        """
        return self.hypothesis

    def compute_E_set(self, seq: LetterSequence, letter: Letter, memorable_seq: LetterSequence) -> Set[int]:
        """
        Compute the E set for the given LetterSequence.
        E set contains indices of letters that can be forgotten.
        """
        E = set()
        memorable_set = set(memorable_seq.letters)
        extended_list = seq.letters + [letter]
        for i in range(len(extended_list)):
            if extended_list[i] not in memorable_set:
                E.add(i)
            elif i < len(extended_list) - 1 and extended_list[i] == letter:
                E.add(i)
        return E

                
    def refine_hypothesis(self, cex_seq: LetterSequence):
        """
        Analyse a counterexample sequence that is misclassified by the current hypothesis.
        Returns information about the misclassification.
        seq = a1 a2 ... an
        states sequence = u0, u1, u2, ..., un
        u_i b_{i+1} sim_R u_i a_{i+1} for i = 0...n-1
        
        we know that MQ(u_{i-1} a_i ... an) = MQ(a1 ... a{i-1} ai ... an) 
        u_i = state reached after processing a1 ... ai
        """
        print("cex ", cex_seq)
        # we compare the prefix a1 ... ai with ui
        cex_mq_result = self.oracle.membership_query(cex_seq)
        print("cex mq ", cex_mq_result)
        # configuration = Tuple(location_id: int, word: LetterSequence, transition: Optional[Transition])
        configuration_seq = self.hypothesis.run(cex_seq, self.comparator)
        print(configuration_seq)
        curr_location = self.hypothesis.get_initial()
        curr_config = self.__get_empty_sequence()
        # curr_transition = None
        # num_letters = len(cex_seq.letters)
        for i in range(len(cex_seq.letters)):
            print("curr loc ", curr_location, " curr config ", curr_config)
            next_location, next_config, _ = self.hypothesis.step((curr_location, curr_config, None)
                                                                               , cex_seq.letters[i], self.comparator)
            print("next loc ", next_location, " next config ", next_config)

            # configuration should be ok
            cex_suffix = cex_seq.get_suffix(i+1)
            print("cex suffix", cex_suffix)
            # next_location_memorable = self.table.rows[next_location].memorable
            next_location_prefix = self.table.rows[next_location].prefix
            print("next loc", next_location_prefix)
            composed_seq = next_location_prefix.append_sequence(cex_suffix)
            mq_result = self.oracle.membership_query(composed_seq)
            if mq_result != cex_mq_result:
                # no need to add suffix?
                cex_prefix = cex_seq.get_prefix(i+1)
                # now compute the suffix?
                cex_prefix_memorable = self.oracle.memorability_query(cex_prefix)
                self.table.add_row(cex_prefix, cex_prefix_memorable)
                self.table.add_column(cex_suffix)
                break
            
            curr_location = next_location
            curr_config = next_config
        
        self.close_table()
        self.construct_hypothesis()
            
        
        # cex_suffix = LetterSequence(cex_seq.letters + [])
        # i = 0
        # num_letters = len(cex_seq.letters)
        # while i < num_letters:
        #     a_iplusone_letter = cex_seq.letters[i]
        #     # check whether u_i b_{i+1} and u_{i+1} are distinguishable by a_{i+2} ... a_n
        #     chosen_transition = configuration_seq[i][2]
        #     # (p, tau, E, q)
        #     print("chosen transition: ", chosen_transition)
        #     """
        #     tau = M(ui) b{i+1}, it matches a1 a_i a{i+1}
        #     we already know that MQ(ui a{i+1} ... an) = MQ(a1...an) 
        #     We want to check whether ui b{i+1} == ui a{i+1}
        #     M(ui b{i+1}) = M(ui a{i+1}) and whether MQ(ui b{i+1} a{i+2}...an) = MQ(...)
        #     if 
        #     """
        #     curr_location = chosen_transition.source
        #     next_location = chosen_transition.target
        #     # tau = M(u_i) b{i+1}, it matches a1 a_i a{i+1}
        #     # we already know that MQ(u_i a{i+1} ... an) = MQ(a1...an) 
        #     b_iplusone_letter = chosen_transition.tau[-1]
        #     u_i_seq = self.locations[curr_location].label
        #     u_i_b_seq = u_i_seq.append(b_iplusone_letter)
        #     u_i_a_seq = u_i_seq.append(a_iplusone_letter)
        #     # we obtain the map from u_i a_{i+1} to u_i b_{i+1}
        #     # we know that config . a{i+1} \sim_R u_i b{i+1}
        #     bi_map = u_i_a_seq.get_bijective_mapping_dense(u_i_b_seq)
        #     mapped_suffix = LetterSequence(
        #         [bi_map(l) for l in cex_seq.letters[i+1:]])
        #     mapped_seq = LetterSequence(u_i_b_seq.letters + mapped_suffix.letters)
        #     dummy_prefix = LetterSequence(
        #         [bi_map(l) for l in cex_seq.letters[:i+1]])
        #     # new sequence should have the same membership result as u_{i+1} ... a_n
        #     assert self.oracle.membership_query(mapped_seq) == cex_mq_result, "mapped sequence membership query result mismatch "
        #     # If the membership query result is the same, we can use this mapping
        #     u_iplusone = self.locations[next_location].label
        #     u_iplusone_memorable = self.memorables[next_location]
        #     u_i_b_seq_memorable = self.oracle.get_memorability_query(u_i_b_seq)
        #     assert word.is_same_word_type(u_i_b_seq_memorable, u_iplusone_memorable), "memorable sequence mismatch"
        #     bi_map = u_iplusone_memorable.get_bijective_mapping_dense(u_i_b_seq_memorable)
        #     mapped_prefix = LetterSequence(
        #         [bi_map(l) for l in u_iplusone.letters])
        #     mapped_seq = LetterSequence(mapped_prefix.letters + mapped_suffix.letters)
        #     mapped_seq_mq_result = self.oracle.membership_query(mapped_seq)
        #     if mapped_seq_mq_result == cex_mq_result:
        #         cex_seq = LetterSequence(dummy_prefix.letters + mapped_suffix.letters)
        #         continue
        #     else:
        #         # mapped suffix distinguishes u_i b_{i+1} and u_{i+1}
        #         self.refine_classification_tree(
        #             next_location,
        #             u_i_b_seq,
        #             u_i_b_seq_memorable,
        #             mapped_suffix
        #         )
        #         break
        #     i = i + 1
            
        # return None

if __name__ == "__main__":
    
    seqA = word.LetterSequence(
    [
        word.Letter(1, word.LetterType.REAL),
        word.Letter(2, word.LetterType.REAL),
        word.Letter(3, word.LetterType.REAL),
        word.Letter(4, word.LetterType.REAL)
    ]
    )
    seqB =  word.LetterSequence(
    [
        word.Letter(1, word.LetterType.REAL),
        word.Letter(2, word.LetterType.REAL),
        word.Letter(3, word.LetterType.REAL),
        word.Letter(2.5, word.LetterType.REAL)
    ]
    )
    bimap = seqA.get_bijective_mapping_dense(seqB)
    print("  Bijective mapping (A -> B):", list(map(bimap, seqA.letters)))
    
    target = example.get_example_ra_1()
    print(target.is_accepted(LetterSequence([Letter(0, word.LetterType.REAL)
                                             , Letter(1, word.LetterType.REAL)
                                             , Letter(1, word.LetterType.REAL)])))
    teacher = Teacher(target, word.comp_lt, example.solve_memorability_query_1)
    learner = RALearner(teacher, word.comp_lt, target.letter_type)
    learner.start_learning()
    while True:
        hypothesis = learner.get_hypothesis()
        print("Hypothesis", hypothesis)
        eq, cex = teacher.equivalence_query(hypothesis, [word.Letter(1, word.LetterType.REAL)
                                               , word.Letter(2, word.LetterType.REAL)
                                               , word.Letter(3, word.LetterType.REAL)
                                               , word.Letter(4, word.LetterType.REAL)
                                               , word.Letter(0, word.LetterType.REAL)]
                                  ,6)
        print("eq ", eq, "cex ", cex)
        if eq:
            print("Output hypothesis:\n", hypothesis)
            break
        
        learner.refine_hypothesis(cex)
    
    print("Learning completed...")    
    sys.exit(0)
    

    RA = example.get_example_ra_2()
    print("================== example 2 ==================")

    print(RA)
    
    seqA = word.LetterSequence(
    [
        word.Letter(1, word.LetterType.REAL),
        word.Letter(2, word.LetterType.REAL),
        word.Letter(1.5, word.LetterType.REAL),
        word.Letter(1.2, word.LetterType.REAL)
    ]
    )
    
    seqB = word.LetterSequence(
    [
        word.Letter(6, word.LetterType.REAL),
        word.Letter(7, word.LetterType.REAL),
        word.Letter(6, word.LetterType.REAL),
        word.Letter(7, word.LetterType.REAL)
    ]
    )
    
    seqC = word.LetterSequence(
    [
        word.Letter(6, word.LetterType.REAL),
        word.Letter(7, word.LetterType.REAL),
        word.Letter(6, word.LetterType.REAL),
        word.Letter(7, word.LetterType.REAL),
        word.Letter(7, word.LetterType.REAL)
    ]
    )
    
    seqD = word.LetterSequence(
    [
        word.Letter(6, word.LetterType.REAL),
        word.Letter(6, word.LetterType.REAL),
        word.Letter(6, word.LetterType.REAL),
        word.Letter(6, word.LetterType.REAL)
    ]
    )
    
    print("word:", seqA, RA.is_accepted(seqA, word.comp_id))
    print("word:", seqB, RA.is_accepted(seqB, word.comp_id))
    print("word:", seqC, RA.is_accepted(seqC, word.comp_id))
    print("word:", seqD, RA.is_accepted(seqD, word.comp_id))
    
    targetRA = example.get_example_ra_1()
    print("================== example 1 ==================")

    print(targetRA)
    
    seq1 = word.LetterSequence(
    [
        word.Letter(1, word.LetterType.REAL),
        word.Letter(2, word.LetterType.REAL),
        word.Letter(1.5, word.LetterType.REAL),
        word.Letter(1.2, word.LetterType.REAL)
    ]
    )
    
    seq2 = word.LetterSequence(
    [
        word.Letter(2, word.LetterType.REAL),
        word.Letter(1, word.LetterType.REAL),
        word.Letter(1.5, word.LetterType.REAL),
        word.Letter(1.2, word.LetterType.REAL)
    ])
    
    seq3 = word.LetterSequence(
    [
        word.Letter(4, word.LetterType.REAL),
        word.Letter(6, word.LetterType.REAL),
        word.Letter(9, word.LetterType.REAL),
        word.Letter(8, word.LetterType.REAL),
        word.Letter(3, word.LetterType.REAL)
    ])
    
    seq4 = word.LetterSequence(
    [
        word.Letter(4, word.LetterType.REAL),
        word.Letter(4, word.LetterType.REAL),
        word.Letter(9, word.LetterType.REAL),
        word.Letter(8, word.LetterType.REAL),
    ])
    
    print(targetRA.run(seq1, word.comp_lt))
    print(targetRA.run(seq2, word.comp_lt))

    print("word:", seq1, targetRA.is_accepted(seq1, word.comp_lt))
    print("word:", seq2, targetRA.is_accepted(seq2, word.comp_lt))
    print("word:", seq3, targetRA.is_accepted(seq3, word.comp_lt))
    print("word:", seq4, targetRA.is_accepted(seq4, word.comp_id))
    
    
    targetRA = example.get_example_ra_3()
    print("================== example 3 ==================")
    print(targetRA)
    
    seqRA1 = word.LetterSequence(
    [
        word.Letter(3, word.LetterType.REAL),
        word.Letter(2, word.LetterType.REAL),
        word.Letter(1, word.LetterType.REAL),
        word.Letter(4, word.LetterType.REAL),
    ]
    )

    print("word:", seqRA1, targetRA.is_accepted(seqRA1, word.comp_lt))

    
    seqRA1 = word.LetterSequence(
    [
        word.Letter(1, word.LetterType.REAL),
        word.Letter(2, word.LetterType.REAL),
        word.Letter(3, word.LetterType.REAL),
        word.Letter(4, word.LetterType.REAL),
    ]
    )
    print("word:", seqRA1, targetRA.is_accepted(seqRA1, word.comp_lt))

    
    seqRA1 = word.LetterSequence(
    [
        word.Letter(1, word.LetterType.REAL),
        word.Letter(1, word.LetterType.REAL),
        word.Letter(3, word.LetterType.REAL),
        word.Letter(4, word.LetterType.REAL),
    ]
    )
    print("word:", seqRA1, targetRA.is_accepted(seqRA1, word.comp_lt))
    
    seqRA1 = word.LetterSequence(
    [
        word.Letter(1, word.LetterType.REAL),
        word.Letter(1, word.LetterType.REAL),
        word.Letter(1, word.LetterType.REAL)
    ]
    )
    print("word:", seqRA1, targetRA.is_accepted(seqRA1, word.comp_lt))

    

    # --- create some sequences for testing ---

# All ℕ type
seqA = word.LetterSequence(
    [
        word.Letter(1, word.LetterType.REAL),
        word.Letter(5, word.LetterType.REAL),
        word.Letter(5, word.LetterType.REAL),
        word.Letter(9, word.LetterType.REAL),
    ]
)

seqB = word.LetterSequence(
    [
        word.Letter(3, word.LetterType.REAL),
        word.Letter(7, word.LetterType.REAL),
        word.Letter(7, word.LetterType.REAL),
        word.Letter(10, word.LetterType.REAL),
    ]
)

seqK = word.LetterSequence(
    [
        word.Letter(6, word.LetterType.REAL),
        word.Letter(8, word.LetterType.REAL),
        word.Letter(8, word.LetterType.REAL),
        word.Letter(10, word.LetterType.REAL),
    ]
)

seqC = word.LetterSequence(
    [
        word.Letter(2, word.LetterType.REAL),
        word.Letter(2, word.LetterType.REAL),
        word.Letter(2, word.LetterType.REAL),
        word.Letter(2, word.LetterType.REAL),
    ]
)

seqD = word.LetterSequence(
    [
        word.Letter(9, word.LetterType.REAL),
        word.Letter(1, word.LetterType.REAL),
        word.Letter(5, word.LetterType.REAL),
        word.Letter(5, word.LetterType.REAL),
    ]
)

seqE = word.LetterSequence(
    [
        word.Letter(1, word.LetterType.REAL),
        word.Letter(9, word.LetterType.REAL),
        word.Letter(5, word.LetterType.REAL),
        word.Letter(5, word.LetterType.REAL),
    ]
)


# --- run tests ---
print(seqA, seqB, seqC, seqD, seqE)

print("### Using comp_id (equality only) ###")
print("seqA vs seqB:", word.is_same_word_type(seqA, seqB, word.comp_id))

    
print("seqA vs seqC:", word.is_same_word_type(seqA, seqC, word.comp_id))
print("seqA vs seqD:", word.is_same_word_type(seqA, seqD, word.comp_id))
print("seqA vs seqE:", word.is_same_word_type(seqA, seqE, word.comp_id))

print("\n### Using comp_lt (order only) ###")
print("seqA vs seqB:", word.is_same_word_type(seqA, seqB, word.comp_lt))
if word.is_same_word_type(seqA, seqB, word.comp_id):
    bijective = seqA.get_bijective_mapping_dense(seqB)
    print("  Bijective mapping (A -> B):", list(map(bijective, seqK.letters)))
print("seqA vs seqC:", word.is_same_word_type(seqA, seqC, word.comp_lt))
print("seqA vs seqD:", word.is_same_word_type(seqA, seqD, word.comp_lt))
print("seqA vs seqE:", word.is_same_word_type(seqA, seqE, word.comp_lt))

seqA = word.LetterSequence(
    [
        word.Letter(1, word.LetterType.REAL)
    ]
)
seqB = word.LetterSequence(
    [
        word.Letter(2, word.LetterType.REAL)
    ]
)
bijective = seqA.get_bijective_mapping_dense(seqB)
print("\nSingle-letter sequences:")
print("  Bijective mapping (A -> B):", seqE, list(map(bijective, seqE.letters)))
