import example
import word
from word import Letter, LetterSequence
from ra import RegisterAutomaton
from typing import List, Tuple, Callable, Dict, Any

if __name__ == "__main__":
    

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
