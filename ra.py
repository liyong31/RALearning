from typing import List, Set, Dict, Tuple, Callable

import word.LtterSequence as LetterSequence
import word.Letter as Letter
import word.Numeric as Numeric
import word

# -------------------------------
#     REGISTER AUTOMATON
# -------------------------------


## transition, the index starts from 0
class Transition:
    def __init__(self, source: int, tau: LetterSequence, E: Set[int], target: int):
        """
        (p, τ, E, q)
        source: state id p
        tau: LetterSequence (τ), homogeneous type guaranteed
        E: set of indices
        target: state id q
        """
        if not isinstance(tau, LetterSequence):
            raise ValueError("τ must be a LetterSequence")

        self.source = source
        self.tau = tau
        self.E = E
        self.target = target

    def __repr__(self):
        return f"({self.source}, {self.tau}, {self.E}, {self.target})"
    
class Location:
    def __init__(self, id: int, name: object, accepting: bool = False):
        self.id = id
        self.name = name
        self.accepting = accepting
        self.transitions: List[Transition] = []
        
    # add transitions
    def add_transition(self, p: int, tau: LetterSequence, E: Set[int], q: int):
        if p != self.id:
            raise ValueError("Transition with source {p} added to location {self.id}")
        self.transitions.append(Transition(p, tau, E, q))

    def __repr__(self):
        result = ""
        for t in self.transitions:
            result += f"  {t}\n"
        return f"Location({self.id}, name={self.name}, accepting={self.accepting}):\n{result}"



class RegisterAutomaton:
    def __init__(self):
        self.locations: Dict[int, Location] = {}
        self.initial = None
        # self.transitions: List[Transition] = []
        
    def __check_location_validity(self, p: int):
        if p not in self.locations:
            raise ValueError("p must be an existing location")

    def add_location(self, p: int, name: object, accepting: bool = False):
        self.locations[p] = Location(p, name, accepting)

    def add_transition(self, p: int, tau: LetterSequence, E: Set[int], q: int):
        self.__check_location_validity(p)
        self.__check_location_validity(q)
        self.locations[p].add_transition(p, tau, E, q)
        
    def set_initial(self, p: int):
        self.__check_location_validity(p)
        self.initial = p
    
    def set_final(self, p:int):
        self.__check_location_validity(p)
        self.locations[p].accepting = True

    def __repr__(self):
        result = "Register Automaton:\nLocations:\n"
        for loc in self.locations.values():
            result += f"  {loc}\n"
        return result
    
    def run(self, input_word: LetterSequence, 
            comp: Callable[[Numeric, Numeric], object] = comp_id
           ) -> List[Tuple[Location, LetterSequence]]:
        """
        Runs the automaton on the input word (sequence of letters).
        Returns the list of reachable configurations (q, v) at the end.
        """
        # Initial configuration: all locations with empty sequence
        configurations: List[(Location, LetterSequence)] = []
        current_configuration = (self.initial, LetterSequence([]))
        configurations.append(current_configuration)
        # Process each letter in the input word
        for a in input_word:
            current_location, v = current_configuration
            for t in self.locations[current_location].transitions:
                va_letters = v.letters + [a]
                va = LetterSequence(va_letters)
                # Check if va matches the pattern tau (same comparison pattern)
                if len(va.letters) != len(t.tau.letters):
                    continue  # length must match

                if va.letter_type != t.tau.letter_type:
                        continue  # type mismatch

                if word.is_same_word_type(va, t.tau, comp):
                        # Remove letters at positions in E (simultaneously)
                        # Positions in E are 1-based
                        v_prime = va.remove(t.E)
                        current_configuration = ((self.locations[t.target], v_prime))
                        configurations.append(current_configuration)

        return configurations
