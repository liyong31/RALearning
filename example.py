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
    accepts a1a2a3...an where ai <= aj for all i < j
    """
    targetRA = ra.RegisterAutomaton()
    targetRA.add_location(0, "q0", accepting=True)
    targetRA.add_location(1, "q1", accepting=True)
    targetRA.add_location(2, "q2", accepting=False)

    targetRA.set_initial(0)
    
    tau_nat = word.LetterSeq(
        [
            word.Letter(1, word.LetterType.REAL)
        ])
    targetRA.add_transition(0, tau_nat, {}, 1)

    tau_nat_2 = word.LetterSeq(
        [
            word.Letter(1, word.LetterType.REAL),
            word.Letter(2, word.LetterType.REAL)
        ])
    # larger value
    targetRA.add_transition(1, tau_nat_2, {0}, 1)
    # equal value
    tau_nat_3 = word.LetterSeq(
        [
            word.Letter(1, word.LetterType.REAL),
            word.Letter(1, word.LetterType.REAL)
        ])
    targetRA.add_transition(1, tau_nat_3, {0}, 1)
    # smaller value
    tau_nat_4 = word.LetterSeq(
        [
            word.Letter(1, word.LetterType.REAL),
            word.Letter(0.5, word.LetterType.REAL)
        ])
    targetRA.add_transition(1, tau_nat_4, {0,1}, 2)
    targetRA.add_transition(2, tau_nat, {0}, 2)
    
    return targetRA
