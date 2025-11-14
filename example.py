import alphabet
from alphabet import LetterSeq, LetterType, comp_lt, comp_id, Alphabet
import dra
# import obtable


# -------------------------------
#           EXAMPLE
# -------------------------------

def get_example_ra_1():
    """
    accepts a1a2a3...an where either:
    1. a1 < a2, then ai < a1 or ai > a2 for all i >=3
    2. a1 > a2, then a2 < ai < a1 for all i >=3
    """
    alphabet = Alphabet(LetterType.REAL, comp_lt)
    targetRA = dra.RegisterAutomaton(alphabet)
    targetRA.add_location(0, "q0", accepting=False)
    targetRA.add_location(1, "q1", accepting=False)
    targetRA.add_location(2, "q2", accepting=True)
    targetRA.add_location(3, "q3", accepting=True)
    targetRA.add_location(4, "q4", accepting=False)
    targetRA.set_initial(0)
    
    tau_nat_1 = alphabet.make_sequence([3])
    
    tau_nat_2 = alphabet.make_sequence([3, 2])
    tau_nat_3 = alphabet.make_sequence([3, 4])

    tau_nat_4 = alphabet.make_sequence([3, 2, 2.5])

    tau_nat_5 = alphabet.make_sequence([3, 4, 2.5])
    tau_nat_6 = alphabet.make_sequence([3, 4, 5])

    tau_nat_5p = alphabet.make_sequence([3, 4, 3])

    tau_nat_6p = alphabet.make_sequence([3, 4, 4])

    tau_nat_7 = alphabet.make_sequence([3, 2, 1])

    tau_nat_7p = alphabet.make_sequence([3, 2, 3])
    tau_nat_8 = alphabet.make_sequence([3, 2, 4])

    tau_nat_8p = alphabet.make_sequence([3, 2, 2])
 
    # jump to state 4
    tau_nat_9 = alphabet.make_sequence([3, 4, 3.5])

    tau_nat_10 = alphabet.make_sequence([3, 3])
    
    targetRA.add_transition(0, tau_nat_1, {}, 1)
    targetRA.add_transition(1, tau_nat_2, {}, 2)
    targetRA.add_transition(1, tau_nat_3, {}, 3)
    targetRA.add_transition(1, tau_nat_10, {0,1}, 4)
    targetRA.add_transition(2, tau_nat_4, {2}, 2)
    targetRA.add_transition(3, tau_nat_5, {2}, 3)
    targetRA.add_transition(3, tau_nat_6, {2}, 3)

    targetRA.add_transition(2, tau_nat_7, {0,1,2}, 4)
    targetRA.add_transition(2, tau_nat_8, {0,1,2}, 4)
    targetRA.add_transition(2, tau_nat_7p, {0,1,2}, 4)
    targetRA.add_transition(2, tau_nat_8p, {0,1,2}, 4)
    targetRA.add_transition(3, tau_nat_9, {0,1,2}, 4)
    targetRA.add_transition(3, tau_nat_5p, {0,1, 2}, 4)
    targetRA.add_transition(3, tau_nat_6p, {0,1, 2}, 4)


    tau_nat_true = alphabet.make_sequence([3])
    targetRA.add_transition(4, tau_nat_true, {0}, 4)
    return targetRA

def solve_memorability_query_1(target: dra.RegisterAutomaton, u: alphabet.LetterSeq):
    if len(u.letters) <= 0:
        return target.get_alphabet().empty_sequence()
    if len(u.letters) == 1:
        return u
    
    is_accepted = target.is_accepted(u)
    if is_accepted:
        return u.get_prefix(2)
    else:
        return target.get_alphabet().empty_sequence()
    
def solve_memorability_query_2(target: dra.RegisterAutomaton, u: alphabet.LetterSeq):
    if len(u.letters) <= 0:
        return target.alphabet.empty_sequence()
    if len(u.letters) == 1:
        return u
    if len(u.letters) == 2:
        if u.letters[0] != u.letters[1]:
            return u
        else:
            return target.alphabet.empty_sequence()
    if len(u.letters) == 3:
        if u.letters[0] != u.letters[1] and u.letters[0] == u.letters[2]:
            return u.get_suffix(1)
        else:
            return target.alphabet.empty_sequence()
    if len(u.letters) == 4:
        is_accepted = target.is_accepted(u)
        if is_accepted:
            return target.alphabet.empty_sequence()
        else:
            return target.alphabet.empty_sequence()
    
    return target.alphabet.empty_sequence()
    
def get_example_ra_2():
    """
    accept when the word is the form of abab where a != b
    """
    alphabet = Alphabet(LetterType.REAL, comp_id)
    targetRA = dra.RegisterAutomaton(alphabet)

    targetRA.add_location(0, "ɛ", accepting=False)
    targetRA.add_location(1, "1", accepting=False)
    targetRA.add_location(2, "12", accepting=False)
    targetRA.add_location(3, "11", accepting=False) # sink state
    targetRA.add_location(4, "121", accepting=False)
    targetRA.add_location(5, "1212", accepting=True)

    targetRA.set_initial(0)
    
    tau_nat_1 = alphabet.make_sequence([1])
    targetRA.add_transition(0, tau_nat_1, {}, 1)

    tau_nat_11 = alphabet.make_sequence([1, 1])
    targetRA.add_transition(1, tau_nat_11, {0,1}, 3)
    targetRA.add_transition(3, tau_nat_1, {0}, 3)


    
    tau_nat_12 = alphabet.make_sequence([1, 2])
    targetRA.add_transition(1, tau_nat_12, {}, 2)

    
    tau_nat_121 = alphabet.make_sequence([1, 2, 1])
    tau_nat_122 = alphabet.make_sequence([1, 2, 2]) 
    tau_nat_123 = alphabet.make_sequence([1, 2, 3])
    targetRA.add_transition(2, tau_nat_121, {}, 4)
    targetRA.add_transition(2, tau_nat_122, {0,1,2}, 3)
    targetRA.add_transition(2, tau_nat_123, {0,1,2}, 3)

    
    tau_nat_1212 = alphabet.make_sequence([1, 2, 1, 2])
    targetRA.add_transition(4, tau_nat_1212, {0, 1, 2, 3}, 5)
    tau_nat_1211 = alphabet.make_sequence([1, 2, 1, 1])
    
    targetRA.add_transition(4, tau_nat_1211, {0, 1, 2, 3}, 3)
    tau_nat_1213 = alphabet.make_sequence([1, 2, 1, 3])
    targetRA.add_transition(4, tau_nat_1213, {0, 1, 2, 3}, 3)

    # go to sink state
    targetRA.add_transition(5, tau_nat_1, {0}, 3)
    # targetRA.add_transition(5, tau_nat_1, {0}, 3)


    return targetRA

def get_example_ra_3():
    """
    accept when the word is the form of abab where a < b
    """
    alphabet = Alphabet(LetterType.REAL, comp_lt)
    targetRA = dra.RegisterAutomaton(alphabet)

    targetRA.add_location(0, "ɛ", accepting=False)
    targetRA.add_location(1, "1", accepting=False)
    targetRA.add_location(2, "12", accepting=False)
    targetRA.add_location(3, "11", accepting=False) # sink state
    targetRA.add_location(4, "121", accepting=False)
    targetRA.add_location(5, "1212", accepting=True)

    targetRA.set_initial(0)
    
    tau_nat_1 = alphabet.make_sequence([1])
    targetRA.add_transition(0, tau_nat_1, {}, 1)

    tau_nat_11 = alphabet.make_sequence([1, 1])
    targetRA.add_transition(1, tau_nat_11, {0,1}, 3)
    targetRA.add_transition(3, tau_nat_1, {0}, 3)
    tau_nat_10 = alphabet.make_sequence([1, 0])
    targetRA.add_transition(1, tau_nat_10, {0,1}, 3)


    
    tau_nat_12 = alphabet.make_sequence([1, 2])
    targetRA.add_transition(1, tau_nat_12, {}, 2)

    
    tau_nat_121 = alphabet.make_sequence([1, 2, 1])
    tau_nat_122 = alphabet.make_sequence([1, 2, 2]) 
    tau_nat_123 = alphabet.make_sequence([1, 2, 3])
    tau_nat_121d5 = alphabet.make_sequence([1, 2, 1.5])
    tau_nat_120 = alphabet.make_sequence([1, 2, 0])
    targetRA.add_transition(2, tau_nat_121, {}, 4)
    targetRA.add_transition(2, tau_nat_121d5, {0, 1, 2}, 3)
    targetRA.add_transition(2, tau_nat_122, {0,1,2}, 3)
    targetRA.add_transition(2, tau_nat_123, {0,1,2}, 3)
    targetRA.add_transition(2, tau_nat_120, {0,1,2}, 3)
    
    tau_nat_1212 = alphabet.make_sequence([1, 2, 1, 2])
    targetRA.add_transition(4, tau_nat_1212, {0, 1, 2, 3}, 5)
    tau_nat_1211 = alphabet.make_sequence([1, 2, 1, 1])
    tau_nat_1210 = alphabet.make_sequence([1, 2, 1, 0])
    tau_nat_1211d5 = alphabet.make_sequence([1, 2, 1, 1.5])

    targetRA.add_transition(4, tau_nat_1211, {0, 1, 2, 3}, 3)
    targetRA.add_transition(4, tau_nat_1210, {0, 1, 2, 3}, 3)
    targetRA.add_transition(4, tau_nat_1211d5, {0, 1, 2, 3}, 3)

    tau_nat_1213 = alphabet.make_sequence([1, 2, 1, 3])
    targetRA.add_transition(4, tau_nat_1213, {0, 1, 2, 3}, 3)

    # go to sink state
    targetRA.add_transition(5, tau_nat_1, {0}, 3)
    # targetRA.add_transition(5, tau_nat_1, {0}, 3)

    return targetRA

def get_example_ra_4():
    """
    accept a non-empty word in non-decreasing order
    """
    alphabet = Alphabet(LetterType.REAL, comp_lt)
    targetRA = dra.RegisterAutomaton(alphabet)

    targetRA.add_location(0, "ɛ", accepting=False)
    targetRA.add_location(1, "1", accepting=True)
    targetRA.add_location(2, "12", accepting=False)
    
    targetRA.set_initial(0)

    
    tau_nat_1 = alphabet.make_sequence([1])
    targetRA.add_transition(0, tau_nat_1, {}, 1)
    
    tau_nat_11 = alphabet.make_sequence([1, 1])
    targetRA.add_transition(1, tau_nat_11, {0}, 1)
    tau_nat_12 = alphabet.make_sequence([1, 2])
    targetRA.add_transition(1, tau_nat_12, {0}, 1)
    
    tau_nat_10 = alphabet.make_sequence([1, 0])
    targetRA.add_transition(1, tau_nat_10, {0,1}, 2)

    targetRA.add_transition(2, tau_nat_1, {0}, 2)
    
    return targetRA
    
def get_example_ra_5():
    """
    accept words of the form x y z y where x < y < z
    """
    # Create alphabet (dense, e.g. real)
    alphabet = Alphabet(LetterType.REAL, comp_lt)  # or "float" depending on your code

    ra = dra.RegisterAutomaton(alphabet)

    # ---------------------
    # States
    # ---------------------
    # q0 -- first x read
    # q1 -- after x
    # q2 -- after y (x<y)
    # q3 -- after z (y<z)
    # q4 -- after y = accepting state

    ra.add_location(0, "q0")
    ra.add_location(1, "q1")
    ra.add_location(2, "q2")
    ra.add_location(3, "q3")
    ra.add_location(4, "q4", accepting=True)
    ra.add_location(5, "sink")  # sink state

    ra.set_initial(0)

    # -------------------------------------------------------
    # Transition 1: read x, store x in register → go to q1
    # -------------------------------------------------------
    # registers before = []
    # after reading x → registers = [x]
    # tau = [x]
    ra.add_transition(
        0,
        alphabet.make_sequence([0]),  # tau = [x]
        indices_to_remove=set(),       # store x
        target=1
    )

    # -------------------------------------------------------
    # Transition 2: read y, require y > x → go to q2
    # -------------------------------------------------------
    # registers before = [x]
    # extended = [x, y]
    # tau = [x, y] encodes x < y ordering via test_type
    ra.add_transition(
        1,
        alphabet.make_sequence([0, 1]),  # tau = [x, y]
        indices_to_remove={0},          # remove x, store y
        target=2
    )
    
    ra.add_transition(
        1,
        alphabet.make_sequence([0, 0]),  # tau = [x, y]
        indices_to_remove={0,1},    # clear registers
        target=5  # go to sink state
    )
    
    ra.add_transition(
        1,
        alphabet.make_sequence([0, -1]),  # tau = [x, y]
        indices_to_remove={0,1},
        target=5  # go to sink state
    )

    # -------------------------------------------------------
    # Transition 3: read z, require z > y → go to q3
    # -------------------------------------------------------
    # registers before = [x, y]
    # extended = [x, y, z]
    # tau enforces ordering x < y < z
    ra.add_transition(
        2,
        alphabet.make_sequence([0, 1]),
        indices_to_remove={1},  # remove y, store z
        target=3
    )
    
    ra.add_transition(
        2,
        alphabet.make_sequence([0, 0]),
        indices_to_remove={0,1},  # remove y, store z
        target=5  # go to sink state
    )
    
    ra.add_transition(
        2,
        alphabet.make_sequence([0, -1]),
        indices_to_remove={0,1},  # remove y, store z
        target=5  # go to sink state
    )

    # -------------------------------------------------------
    # Transition 4: read last y, require y = second register
    # -------------------------------------------------------
    # registers before = [x, y, z]
    # extended = [x, y, z, y]
    # tau requires equality of positions 1 and 3
    ra.add_transition(
        3,
        alphabet.make_sequence([0, 0]),
        indices_to_remove={0,1},  # remove z, y
        target=4
    )
    
    ra.add_transition(
        3,
        alphabet.make_sequence([0, 1]),
        indices_to_remove={0,1},  # remove z, y
        target=5  # go to sink state
    )
    
    
    ra.add_transition(
        3,
        alphabet.make_sequence([0, -1]),
        indices_to_remove={0,1},  # remove z, y
        target=5  # go to sink state
    )
    
    
    ra.add_transition(
        4,
        alphabet.make_sequence([0]),
        indices_to_remove={0},  # remove z, y
        target=5  # go to sink state
    )
    
    
    ra.add_transition(
        5,
        alphabet.make_sequence([0]),
        indices_to_remove={0},  # remove z, y
        target=5  # go to sink state
    )

    # Ready!
    return ra
    
ra = get_example_ra_5()
print(ra.to_text())
print(ra.to_dot())