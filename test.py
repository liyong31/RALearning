
from dra import RegisterAutomaton
import alphabet
import teacher


file = "ra5.txt"
ra = None
with open(file) as f:
    text_data = f.read()
    print("===============================")
    ra = RegisterAutomaton.from_text(text_data)
    print(ra.to_text())
    print(ra.to_dot())
    
if ra:
    oracle = teacher.Teacher(ra)
    seq = ra.alphabet.make_sequence([0, -1, -0.5])
    mem_seq = teacher.get_memorable_seq(ra, seq)
    print("seq ", seq, " mem ", mem_seq)
    print("seq ", seq, " mem ", oracle.memorability_query(seq))

    
    seq = ra.alphabet.make_sequence([0, -1])
    mem_seq = teacher.get_memorable_seq(ra, seq)
    print("seq ", seq, " mem ", mem_seq)
    print("seq ", seq, " mem ", oracle.memorability_query(seq))


    
    seq = ra.alphabet.make_sequence([0, -1, 0])
    mem_seq = teacher.get_memorable_seq(ra, seq)
    print("seq ", seq, " mem ", mem_seq)
    print("seq ", seq, " mem ", oracle.memorability_query(seq))
    
    normalised_ra = ra.get_normalised_dra()
    print(normalised_ra.to_dot())

import random
import genra
import sys
num_tests = 10    
num_lower = 4
num_upper = 8

for i in range(num_tests):
    num_states = random.randint(num_lower, num_upper)
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 
            37, 41, 43, 47, 53, 59, 61, 67, 71, 73,
            79, 83, 89, 97]
    num_seed = random.choice(primes)
    print("test case #", i, "states ", num_states, "seed", num_seed)
    alph = alphabet.Alphabet(alphabet.LetterType.REAL, alphabet.comp_lt)
    generator = genra.StructuredRandomRAGenerator(alph, 3)
    print("generating dra...")
    dra = generator.generate(num_states=num_states)
    print("generating dra done...")
    print()
    file_name = "test.txt"
    with open(file_name, "w") as f:
        f.write(dra.to_text())
    print("Now learn DRA from ", file_name)
    import ralt
    try:
        ralt.exectute_learner(file_name, "ra.txt")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    

   