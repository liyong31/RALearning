
from dra import RegisterAutomaton
import teacher

def test_difference():
    """
        Test the difference finding procedure between two register automata
    """
    # build two RAs
    file_name = "./canos/exam2.txt"
    dra = None
    with open(file_name, 'r') as f:
        text = f.read()
        dra = RegisterAutomaton.from_text(text)

    # compare all pairs of representatives
    u = dra.alphabet.make_sequence([0, 1, 0, 1])
    v = dra.alphabet.make_sequence([0, 1, 0, 2])
    w = teacher.find_difference(dra, u, dra, v, None)
    print(f"Difference between {u} and {v}")
    if w is not None:
        print(f"Found difference: {w}")
    else:
        print("No difference found")
        
        
test_difference()