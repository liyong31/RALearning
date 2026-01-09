
import sys
from dra import RegisterAutomaton



def main():
    if len(sys.argv) != 2:
        print("Usage: python eqcheck.py <file1> ")
        sys.exit(1)
    
    file1 = sys.argv[1]
    
    with open(file1, 'r') as f:
        text1 = f.read()
    ra1 = RegisterAutomaton.from_text(text1)
    
    print(ra1.to_dot())
if __name__ == "__main__":
    main()