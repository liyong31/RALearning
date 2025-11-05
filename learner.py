import word
import ra
# import obtable


# -------------------------------
#           EXAMPLE
# -------------------------------

def get_example_ra_1():
    """
    1. a1 < a2, then ai < a1 or ai > a2 for all i >=3
    2. a1 > a2, then a2 < ai < a1 for all i >=3
    """
    targetRA = ra.RegisterAutomaton()
    targetRA.add_location(0, "q0", accepting=False)
    targetRA.add_location(1, "q1", accepting=False)
    targetRA.add_location(2, "q2", accepting=True)
    targetRA.add_location(3, "q3", accepting=True)
    targetRA.add_location(4, "q4", accepting=False)
    targetRA.set_initial(0)
    
    tau_nat_1 = word.LetterSequence(
        [
            word.Letter(3, word.LetterType.REAL)
        ])
    tau_nat_2 = word.LetterSequence(
        [
            word.Letter(3, word.LetterType.REAL),
            word.Letter(2, word.LetterType.REAL)
        ])
    tau_nat_3 = word.LetterSequence(
        [
            word.Letter(3, word.LetterType.REAL),
            word.Letter(4, word.LetterType.REAL)
        ])
    tau_nat_4 = word.LetterSequence(
        [
            word.Letter(3, word.LetterType.REAL),
            word.Letter(2, word.LetterType.REAL),
            word.Letter(2.5, word.LetterType.REAL)
        ])
    tau_nat_5 = word.LetterSequence(
        [
            word.Letter(3, word.LetterType.REAL),
            word.Letter(4, word.LetterType.REAL),
            word.Letter(2.5, word.LetterType.REAL)
        ])
    tau_nat_6 = word.LetterSequence(
        [
            word.Letter(3, word.LetterType.REAL),
            word.Letter(4, word.LetterType.REAL),
            word.Letter(5, word.LetterType.REAL)
        ])
    tau_nat_7 = word.LetterSequence(
        [
            word.Letter(3, word.LetterType.REAL),
            word.Letter(2, word.LetterType.REAL),
            word.Letter(1, word.LetterType.REAL)
        ])
    tau_nat_8 = word.LetterSequence(
        [
            word.Letter(3, word.LetterType.REAL),
            word.Letter(2, word.LetterType.REAL),
            word.Letter(4, word.LetterType.REAL)
        ])
    # jump to state 4
    tau_nat_9 = word.LetterSequence(
        [
            word.Letter(3, word.LetterType.REAL),
            word.Letter(4, word.LetterType.REAL),
            word.Letter(3.5, word.LetterType.REAL)
        ])

    tau_nat_10 = word.LetterSequence(   
        [
            word.Letter(3, word.LetterType.REAL),
            word.Letter(3, word.LetterType.REAL)
        ])
    targetRA.add_transition(0, tau_nat_1, {}, 1)
    targetRA.add_transition(1, tau_nat_2, {}, 2)
    targetRA.add_transition(1, tau_nat_3, {}, 3)
    targetRA.add_transition(1, tau_nat_10, {0,1}, 4)
    targetRA.add_transition(2, tau_nat_4, {2}, 2)
    targetRA.add_transition(3, tau_nat_5, {2}, 3)
    targetRA.add_transition(3, tau_nat_6, {2}, 3)
    targetRA.add_transition(2, tau_nat_7, {0,1,2}, 4)
    targetRA.add_transition(2, tau_nat_8, {0,1,2}, 4)
    targetRA.add_transition(3, tau_nat_9, {0,1,2}, 4)

    tau_nat_true = word.LetterSequence(
        [
            word.Letter(3, word.LetterType.REAL)
        ])
    targetRA.add_transition(4, tau_nat_true, {0}, 4)
    return targetRA

def get_example_ra_2():
    """
    accept when the word ends in abab
    """
    RA = ra.RegisterAutomaton()

    RA.add_location(0, "ɛ", accepting=False)
    RA.add_location(1, "1", accepting=False)
    RA.add_location(2, "12", accepting=False)
    RA.add_location(3, "11", accepting=False) # sink state
    RA.add_location(4, "121", accepting=False)
    RA.add_location(5, "1212", accepting=True)

    RA.set_initial(0)
    
    tau_nat_1 = word.LetterSequence(
        [
            word.Letter(1,  word.LetterType.REAL)
        ]
    )
    RA.add_transition(0, tau_nat_1, {}, 1)

    tau_nat_11 = word.LetterSequence(
        [
            word.Letter(1,  word.LetterType.REAL),
            word.Letter(1,  word.LetterType.REAL)
        ]
    )
    RA.add_transition(1, tau_nat_11, {0,1}, 3)
    # RA.add_transition(3, tau_nat_1, {0}, 3)
    # tau_nat_2 = word.LetterSequence(
    #     [
    #         word.Letter(1,  word.LetterType.REAL)
    #     ]
    # )
    RA.add_transition(3, tau_nat_1, {0}, 3)


    
    tau_nat_12 = word.LetterSequence(
        [
            word.Letter(1,  word.LetterType.REAL),
            word.Letter(2,  word.LetterType.REAL)
        ]
    )
    RA.add_transition(1, tau_nat_12, {}, 2)

    
    tau_nat_121 = word.LetterSequence(
        [
            word.Letter(1,  word.LetterType.REAL),
            word.Letter(2,  word.LetterType.REAL),
            word.Letter(1,  word.LetterType.REAL)
        ]
    )
    tau_nat_122 = word.LetterSequence(
        [
            word.Letter(1,  word.LetterType.REAL),
            word.Letter(2,  word.LetterType.REAL),
            word.Letter(2,  word.LetterType.REAL)
        ]
    )
    tau_nat_123 = word.LetterSequence(
        [
            word.Letter(1,  word.LetterType.REAL),
            word.Letter(2,  word.LetterType.REAL),
            word.Letter(3,  word.LetterType.REAL)
        ]
    )
    RA.add_transition(2, tau_nat_121, {}, 4)
    RA.add_transition(2, tau_nat_122, {0,1,2}, 3)
    RA.add_transition(2, tau_nat_123, {0,1,2}, 3)

    
    tau_nat_1212 = word.LetterSequence(
        [
            word.Letter(1,  word.LetterType.REAL),
            word.Letter(2,  word.LetterType.REAL),
            word.Letter(1,  word.LetterType.REAL),
            word.Letter(2,  word.LetterType.REAL)
        ]
    )
    RA.add_transition(4, tau_nat_1212, {0, 1, 2, 3}, 5)
    tau_nat_1211 = word.LetterSequence(
        [
            word.Letter(1,  word.LetterType.REAL),
            word.Letter(2,  word.LetterType.REAL),
            word.Letter(1,  word.LetterType.REAL),
            word.Letter(1,  word.LetterType.REAL)
        ]
    )
    RA.add_transition(4, tau_nat_1211, {0, 1, 2, 3}, 3)
    tau_nat_1213 = word.LetterSequence(
        [
            word.Letter(1,  word.LetterType.REAL),
            word.Letter(2,  word.LetterType.REAL),
            word.Letter(1,  word.LetterType.REAL),
            word.Letter(3,  word.LetterType.REAL)
        ]
    )
    RA.add_transition(4, tau_nat_1213, {0, 1, 2, 3}, 3)

    # go to sink state
    RA.add_transition(5, tau_nat_1, {0}, 3)

    return RA

if __name__ == "__main__":
    

    RA = get_example_ra_2()
    print(RA)
    
    targetRA = get_example_ra_1()
    
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

    # --- create some sequences for testing ---

# All ℕ type
seqA = word.LetterSequence(
    [
        word.Letter(1, word.LetterType.NAT),
        word.Letter(5, word.LetterType.NAT),
        word.Letter(5, word.LetterType.NAT),
        word.Letter(9, word.LetterType.NAT),
    ]
)

seqB = word.LetterSequence(
    [
        word.Letter(3, word.LetterType.NAT),
        word.Letter(7, word.LetterType.NAT),
        word.Letter(7, word.LetterType.NAT),
        word.Letter(10, word.LetterType.NAT),
    ]
)

seqC = word.LetterSequence(
    [
        word.Letter(2, word.LetterType.NAT),
        word.Letter(2, word.LetterType.NAT),
        word.Letter(2, word.LetterType.NAT),
        word.Letter(2, word.LetterType.NAT),
    ]
)

seqD = word.LetterSequence(
    [
        word.Letter(9, word.LetterType.NAT),
        word.Letter(1, word.LetterType.NAT),
        word.Letter(5, word.LetterType.NAT),
        word.Letter(5, word.LetterType.NAT),
    ]
)

seqE = word.LetterSequence(
    [
        word.Letter(1, word.LetterType.NAT),
        word.Letter(9, word.LetterType.NAT),
        word.Letter(5, word.LetterType.NAT),
        word.Letter(5, word.LetterType.NAT),
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
print("seqA vs seqC:", word.is_same_word_type(seqA, seqC, word.comp_lt))
print("seqA vs seqD:", word.is_same_word_type(seqA, seqD, word.comp_lt))
print("seqA vs seqE:", word.is_same_word_type(seqA, seqE, word.comp_lt))
