from typing import List, Set, Dict, Tuple, Optional
import alphabet


# -------------------------------
#     REGISTER AUTOMATON
# -------------------------------


class Transition:
    """Represents a transition (p, τ, E, q) in a Register Automaton."""

    def __init__(self, source: int, tau: alphabet.LetterSeq, indices_to_remove: Set[int], target: int):
        if not isinstance(tau, alphabet.LetterSeq):
            raise TypeError("τ must be a LetterSeq")

        self.source: int = source
        self.tau: alphabet.LetterSeq = tau
        self.indices_to_remove: Set[int] = set(indices_to_remove)
        self.target: int = target

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transition):
            return NotImplemented
        return (
            self.source == other.source
            and self.target == other.target
            and self.tau == other.tau
            and self.indices_to_remove == other.indices_to_remove
        )

    def __hash__(self):
        return hash((self.source, self.target, self.tau, frozenset(self.indices_to_remove)))

    def __repr__(self) -> str:
        indices_str = "{" + ",".join(map(str, sorted(self.indices_to_remove))) + "}" if self.indices_to_remove else "∅"
        return f"Transition({self.source} → {self.target}, τ={self.tau}, E={indices_str})"


class Location:
    """A location (state) in a Register Automaton."""

    def __init__(self, loc_id: int, name: str, accepting: bool = False):
        self.id: int = loc_id
        self.name: str = name
        self.accepting: bool = accepting
        self.transitions: List[Transition] = []

    def add_transition(self, source: int, tau: alphabet.LetterSeq, indices_to_remove: Set[int], target: int) -> None:
        """Adds a transition if it does not already exist."""
        if source != self.id:
            raise ValueError(f"Transition source {source} does not match location ID {self.id}")

        new_transition = Transition(source, tau, indices_to_remove, target)
        if new_transition not in self.transitions:
            self.transitions.append(new_transition)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Location):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self) -> str:
        header = f"Location({self.id}, name={self.name}, accepting={self.accepting})"
        transitions_str = "\n".join(f"  {t}" for t in self.transitions)
        return f"{header}\n{transitions_str}"


# A configuration is (location_id, register_values, last_transition)
Configuration = Tuple[int, alphabet.LetterSeq, Optional[Transition]]


class RegisterAutomaton:
    """A Register Automaton over dense alphabets (ℚ or ℝ)."""

    def __init__(self, alphabet: alphabet.Alphabet):
        self.locations: Dict[int, Location] = {}
        self.initial: Optional[int] = None
        self.alphabet: alphabet.Alphabet = alphabet

    # -------------------------------
    #       STRUCTURE MANAGEMENT
    # -------------------------------

    def get_alphabet(self) -> alphabet.Alphabet:
        return self.alphabet

    def get_letter_type(self) -> str:
        return self.alphabet.get_letter_type()

    def _check_location_exists(self, loc_id: int) -> None:
        if loc_id not in self.locations:
            raise ValueError(f"Unknown location ID: {loc_id}")

    def add_location(self, loc_id: int, name: str, accepting: bool = False) -> None:
        if loc_id in self.locations:
            raise ValueError(f"Location with ID {loc_id} already exists")
        self.locations[loc_id] = Location(loc_id, name, accepting)

    def add_transition(self, source: int, tau: alphabet.LetterSeq, indices_to_remove: Set[int], target: int) -> None:
        self._check_location_exists(source)
        self._check_location_exists(target)
        self.locations[source].add_transition(source, tau, indices_to_remove, target)

    def set_initial(self, loc_id: int) -> None:
        self._check_location_exists(loc_id)
        self.initial = loc_id
        
    def get_initial(self) -> int:
        return self.initial

    def set_final(self, loc_id: int) -> None:
        self._check_location_exists(loc_id)
        self.locations[loc_id].accepting = True

    # -------------------------------
    #       EXECUTION & ACCEPTANCE
    # -------------------------------

    def step(self, configuration: Configuration, letter: alphabet.Letter) -> Optional[Configuration]:
        """Advance one step based on the input letter."""
        location_id, register_seq, _ = configuration
        extended_seq = register_seq.append(letter)

        for transition in self.locations[location_id].transitions:
            if len(extended_seq) != len(transition.tau):
                continue
            if extended_seq.letter_type != transition.tau.letter_type:
                continue
            print(transition.tau, transition.tau.letter_type)
            if self.alphabet.test_type(extended_seq, transition.tau):
                new_register_seq = extended_seq.remove_by_indices(transition.indices_to_remove)
                return (transition.target, new_register_seq, transition)

        return None  # no valid transition

    def run(self, input_seq: alphabet.LetterSeq) -> List[Configuration]:
        """Simulate the automaton on an input alphabet."""
        if self.initial is None:
            raise ValueError("Initial location not set")

        configurations: List[Configuration] = [(self.initial, self.alphabet.empty_sequence(), None)]
        current = configurations[0]

        for letter in input_seq.letters:
            next_config = self.step(current, letter)
            if next_config is None:
                break
            configurations.append(next_config)
            current = next_config

        return configurations

    def is_accepted(self, input_seq: alphabet.LetterSeq) -> bool:
        """Check whether the automaton accepts the given alphabet."""
        configs = self.run(input_seq)
        final_location_id, _, _ = configs[-1]
        return self.locations[final_location_id].accepting

    # -------------------------------
    #           EXPORT
    # -------------------------------

    def to_dot(self) -> str:
        """Return a Graphviz DOT representation of the automaton."""
        lines = ["digraph RegisterAutomaton {", "  rankdir=LR;", "  node [shape=circle, fontsize=12];"]

        # nodes
        for loc_id, loc in self.locations.items():
            shape = "doublecircle" if loc.accepting else "circle"
            label = f"{loc.name}\\n(id={loc_id})"
            lines.append(f'  {loc_id} [label="{label}", shape={shape}];')

        # initial state
        if self.initial is not None:
            lines.append('  start [shape=point];')
            lines.append(f'  start -> {self.initial};')

        # transitions
        for loc in self.locations.values():
            for t in loc.transitions:
                tau_str = str(t.tau)
                e_str = "{" + ",".join(map(str, sorted(t.indices_to_remove))) + "}" if t.indices_to_remove else "∅"
                label = f"{tau_str}, E={e_str}"
                lines.append(f'  {t.source} -> {t.target} [label="{label}"];')

        lines.append("}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        content = "\n".join(f"  {loc}" for loc in self.locations.values())
        return f"RegisterAutomaton(\n{content}\n)"
