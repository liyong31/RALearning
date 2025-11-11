from typing import List, Set, Dict, Tuple, Callable


import word

# -------------------------------
#     REGISTER AUTOMATON
# -------------------------------


## transition, the index starts from 0
class Transition:
    def __init__(self, source: int, tau: word.LetterSequence, E: Set[int], target: int):
        """
        (p, τ, E, q)
        source: state id p
        tau: LetterSequence (τ), homogeneous type guaranteed
        E: set of indices
        target: state id q
        """
        if not isinstance(tau, word.LetterSequence):
            raise ValueError("τ must be a LetterSequence")

        self.source = source
        self.tau = tau
        self.E = E
        self.target = target
        
    def __eq__(self, value):
        if not isinstance(value, Transition):
            raise ValueError("Can only compare with another Transition")
        return (
            self.source == value.source and
            self.tau == value.tau and
            self.E == value.E and
            self.target == value.target
        )

    def __repr__(self):
        return f"({self.source}, {self.tau}, {self.E}, {self.target})"


class Location:
    def __init__(self, id: int, name: object, accepting: bool = False):
        self.id = id
        self.name = name
        self.accepting = accepting
        self.transitions: List[Transition] = []
        
    def get_id(self) -> int:
        return self.id

    # add transitions
    def add_transition(self, p: int, tau: word.LetterSequence, E: Set[int], q: int):
        if p != self.id:
            raise ValueError("Transition with source {p} added to location {self.id}")
        # check for duplicate transitions?
        for t in self.transitions:
            if t == Transition(p, tau, E, q):
                # raise  ValueError("Duplicate transition")
                return # already exists
        self.transitions.append(Transition(p, tau, E, q))
        
    def __eq__(self, value):
        if not isinstance(value, Location):
            raise ValueError("Can only compare with another Location")
        # only compare the id
        return (
            self.id == value.id
        )

    def __repr__(self):
        result = ""
        for t in self.transitions:
            result += f"  {t}\n"
        return f"Location({self.id}, name={self.name}, accepting={self.accepting}):\n{result}"

# different than classical configuration, we also keep track of the transition taken to reach the configuration
# this is useful for tracing the run
Configuration = Tuple[int, word.LetterSequence, Transition]

class RegisterAutomaton:
    def __init__(self, letter_type: word.LetterType):
        self.locations: Dict[int, Location] = {}
        self.initial = None
        self.letter_type = letter_type
        # self.transitions: List[Transition] = []
        
    def get_letter_type(self):
        return self.letter_type

    def __check_location_validity(self, p: int):
        if p not in self.locations:
            raise ValueError("p must be an existing location")

    def add_location(self, p: int, name: object, accepting: bool = False):
        self.locations[p] = Location(p, name, accepting)

    def add_transition(self, p: int, tau: word.LetterSequence, E: Set[int], q: int):
        self.__check_location_validity(p)
        self.__check_location_validity(q)
        self.locations[p].add_transition(p, tau, E, q)

    def set_initial(self, p: int):
        self.__check_location_validity(p)
        self.initial = p

    def get_initial(self) -> int:
        return self.initial

    def set_final(self, p: int):
        self.__check_location_validity(p)
        self.locations[p].accepting = True

    def __repr__(self):
        result = "Register Automaton:\nLocations:\n"
        for loc in self.locations.values():
            result += f"  {loc}\n"
        return result

    def step(
        self,
        current_configuration: Configuration,
        letter: word.Letter,
        comp: Callable[[word.Numeric, word.Numeric], object] = word.comp_id,
    ) -> Configuration: # type: ignore

        current_location, v, _ = current_configuration
        # Form va by appending the letter to v
        va = word.LetterSequence(v.letters + [letter])
        
        next_configuration = None
        
        for t in self.locations[current_location].transitions:
            # Check if va matches the pattern tau (same comparison pattern)
            if len(va.letters) != len(t.tau.letters):
                continue  # length must match

            if va.letter_type != t.tau.letter_type:
                continue  # type mismatch

            if word.is_same_word_type(va, t.tau, comp):
                # Remove letters at positions in E (simultaneously)
                # Positions in E are 1-based
                # print("transition matches, applying..., same type")
                # print("va before removal:", va)
                # print("removing indices (0-based):", t.E)
                v_prime = va.remove(t.E)
                # print("v' after removal:", v_prime)
                next_configuration = (t.target, v_prime, t)
                break

        return next_configuration

    def run(
        self,
        input_word: word.LetterSequence,
        comp: Callable[[word.Numeric, word.Numeric], object] = word.comp_id,
    ) -> List[Configuration]:
        """
        Runs the automaton on the input word (sequence of letters).
        Returns the list of reachable configurations (q, v) at the end.
        """
        # print("input word:", input_word)
        # Initial configuration: all locations with empty sequence
        configurations: List[Configuration] = []
        # first transition is None
        current_configuration = (self.initial, word.LetterSequence([]), None)
        configurations.append(current_configuration)
        # Process each letter in the input word
        for a in input_word.letters:
            # print("processing letter:", a)
            next_configuration = self.step(current_configuration, a, comp)
            if next_configuration:
                configurations.append(next_configuration)
                current_configuration = next_configuration
            else:
                break  # no valid transition, stop processing

        return configurations
    
    def is_accepted(
        self,
        input_word: word.LetterSequence,
        comp: Callable[[word.Numeric, word.Numeric], object] = word.comp_id,
    ) -> bool:
        """
        Checks if the input word is accepted by the automaton.
        An input word is accepted if the final configuration is in an accepting location.
        """
        configurations = self.run(input_word, comp)
        final_location_id, _ , _ = configurations[-1]
        final_location = self.locations[final_location_id]
        return final_location.accepting
