
import sys
from dra import RegisterAutomaton
from teacher import find_difference

def main():
    if len(sys.argv) != 3:
        print("Usage: python eqcheck.py <file1> <file2>")
        sys.exit(1)
    
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    
    with open(file1, 'r') as f:
        text1 = f.read()
    ra1 = RegisterAutomaton.from_text(text1)
    
    with open(file2, 'r') as f:
        text2 = f.read()
    ra2 = RegisterAutomaton.from_text(text2)
    
    empty = ra1.alphabet.empty_sequence()
    diff = find_difference(ra1, empty, ra2, empty)
    
    if diff is None:
        print("The two register automata are equivalent.")
    else:
        print(f"The two register automata are not equivalent. Distinguishing word: {diff}")

if __name__ == "__main__":
    main()