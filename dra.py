from fractions import Fraction
from typing import List, Set, Dict, Tuple, Optional
import re
from typing import TextIO
from alphabet import Alphabet, LetterSeq, Letter, LetterType, comp_lt, comp_id


# -------------------------------
#     REGISTER AUTOMATON
# -------------------------------


class Transition:
    """Represents a transition (p, τ, E, q) in a Register Automaton."""

    def __init__(self, source: int, tau: LetterSeq, indices_to_remove: Set[int], target: int):
        if not isinstance(tau, LetterSeq):
            raise TypeError("τ must be a LetterSeq")

        self.source: int = source
        self.tau: LetterSeq = tau
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

    def add_transition(self, source: int, tau: LetterSeq, indices_to_remove: Set[int], target: int) -> None:
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
Configuration = Tuple[int, LetterSeq, Optional[Transition]]


class RegisterAutomaton:
    """A Register Automaton over dense alphabets (ℚ or ℝ)."""

    def __init__(self, alphabet: Alphabet):
        self.locations: Dict[int, Location] = {}
        self.initial: Optional[int] = None
        self.alphabet: Alphabet = alphabet

    # -------------------------------
    #       STRUCTURE MANAGEMENT
    # -------------------------------

    def get_alphabet(self) -> Alphabet:
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

    def add_transition(self, source: int, tau: LetterSeq, indices_to_remove: Set[int], target: int) -> None:
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

    def step(self, configuration: Configuration, letter: Letter) -> Optional[Configuration]:
        """Advance one step based on the input letter."""
        location_id, register_seq, _ = configuration
        extended_seq = register_seq.append(letter)

        for transition in self.locations[location_id].transitions:
            if len(extended_seq) != len(transition.tau):
                continue
            if extended_seq.letter_type != transition.tau.letter_type:
                continue
            if self.alphabet.test_type(extended_seq, transition.tau):
                new_register_seq = extended_seq.remove_by_indices(transition.indices_to_remove)
                return (transition.target, new_register_seq, transition)

        return None  # no valid transition

    def run(self, input_seq: LetterSeq) -> List[Configuration]:
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

    def is_accepted(self, input_seq: LetterSeq) -> bool:
        """Check whether the automaton accepts the given alphabet."""
        configs = self.run(input_seq)
        final_location_id, _, _ = configs[-1]
        return self.locations[final_location_id].accepting
    
    def get_sink_rejecting_locations(self) -> Set[int]:
        """Return the IDs of all sink rejecting locations."""
        sink_rejecting_ids = set()
        for loc_id, loc in self.locations.items():
            if not loc.accepting and all(t.target == loc_id for t in loc.transitions):
                sink_rejecting_ids.add(loc_id)
        return sink_rejecting_ids
    
    # make automaton complete in terms of transitions
    def make_complete(self) -> None:
        """Make the automaton complete by adding a sink rejecting location."""
        sink_rej_locs = self.get_sink_rejecting_locations()
        sink_rej_loc = next(iter(sink_rej_locs), -1)

        # by default, we have these assumption:
        # 1. tau = m l where l is the last letter in the register sequence after appending the input letter
        # 2. m is the shared sequence for all transitions from that location
        missing_letters_map: Dict[int, Set[Letter]] = {}
        memorable_seq_map: Dict[int, LetterSeq] = {}
        for loc in self.locations.values():
            if loc.id in sink_rej_locs:
                continue  # skip existing sink rejecting locations

            # collect all letters used in transitions from this location
            memorable_seq = None
            used_letters: Set[Letter] = set()
            for t in loc.transitions:
                if len(t.tau) > 0:
                    used_letters.add(t.tau.letters[-1])  # last letter in tau
                memorable_seq = t.tau.get_prefix(len(t.tau) - 1)  # all but last letter
            if memorable_seq is None:
                memorable_seq = self.alphabet.empty_sequence()
            memorable_seq_map[loc.id] = memorable_seq
            # determine missing letters
            all_letters = set(memorable_seq.get_letter_extension(self.alphabet.comparator).letters) 
            missing_letters = all_letters - used_letters
            if missing_letters:
                missing_letters_map[loc.id] = missing_letters
            
        # create sink location
        if missing_letters_map:
            if sink_rej_loc >= 0:
                sink_id = sink_rej_loc
            else:
                sink_id = max(self.locations.keys(), default=-1) + 1
                self.add_location(sink_id, name="sink", accepting=False)
            memorable_seq_map[sink_id] = self.alphabet.empty_sequence()
            # add transitions to sink for missing letters
            for loc_id, missing_letters in missing_letters_map.items():
                loc = self.locations[loc_id]
                # get memorable sequence from any transition
                memorable_seq = memorable_seq_map.get(loc_id, None)
                for letter in missing_letters:
                    tau = memorable_seq.append(letter)
                    loc.add_transition(
                        source=loc_id,
                        tau=tau,
                        indices_to_remove=set(range(len(tau))),  # remove all registers
                        target=sink_id
                    )
            # Add self-loop on sink
            self.locations[sink_id].add_transition(
                source=sink_id,
                tau=self.alphabet.make_sequence([0.0]),  # empty sequence
                indices_to_remove={0},
                target=sink_id
            )

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
                e_str = "{" + ",".join(map(str, sorted(t.indices_to_remove))) + "}" if t.indices_to_remove else "{}"
                label = f"{tau_str}, E={e_str}"
                lines.append(f'  {t.source} -> {t.target} [label="{label}"];')

        lines.append("}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        content = "\n".join(f"  {loc}" for loc in self.locations.values())
        return f"RegisterAutomaton(\n{content}\n)"

    # -------------------------------
    #          TEXT EXPORT
    # -------------------------------
    def to_text(self) -> str:
        """Return a human-readable text representation."""
        lines = []
        lines.append("# Register Automaton")
        # Alphabet: show ordering or equality comparator
        if self.alphabet.comparator == comp_lt:
            comp_str = "<"
        else:
            comp_str = "="
        lines.append(f"alphabet: {self.alphabet.letter_type}, {comp_str}")
        lines.append(f"initial: {self.initial}")

        lines.append("locations:")
        for loc_id, loc in self.locations.items():
            lines.append(f"  {loc_id} \"{loc.name}\" accepting={loc.accepting}")

        lines.append("\ntransitions:")
        for loc in self.locations.values():
            for t in loc.transitions:
                tau_str = ",".join(str(l.value) for l in t.tau.letters)
                if t.indices_to_remove:
                    e_str = "{" + ",".join(map(str, sorted(t.indices_to_remove))) + "}"
                else:
                    e_str = "{}"
                lines.append(f"  {t.source} -> {t.target} : tau=[{tau_str}], E={e_str}")

        return "\n".join(lines)

    # -------------------------------
    #          TEXT PARSING
    # -------------------------------
    @staticmethod
    def from_text(text: str) -> "RegisterAutomaton":
        """
        Parse a RegisterAutomaton from the text format produced by to_text().
        The 'alphabet:' line determines the comparator (< or =).
        """

        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
        alphabet = Alphabet(LetterType.REAL, comp_lt)  # default, will be updated below
        ra = RegisterAutomaton(alphabet)
        
        i = 0
        # the sections must appear in order: alphabet, initial, locations, transitions
        # --- Parse alphabet line ---
        if not lines[i].startswith("alphabet:"):
            raise ValueError("Expected 'alphabet:' line")
        _, alpha_desc = lines[i].split(":", 1)
        alpha_desc = alpha_desc.strip()

        # Expected format: "<type>, <" or "<type>, ="
        parts = [p.strip() for p in alpha_desc.split(",")]
        if len(parts) != 2:
            raise ValueError("Malformed alphabet line")

        letter_type_str, comp_symbol = parts

        # Update alphabet letter type
        alphabet.letter_type = letter_type_str

        # Parse comparator symbol
        if comp_symbol == "<":
            alphabet.comparator = comp_lt
        elif comp_symbol == "=":
            alphabet.comparator = comp_id
        else:
            raise ValueError(f"Unknown comparator symbol: {comp_symbol}")

        i += 1

        initial_id = -1
        # --- Parse initial ---
        if not lines[i].startswith("initial:"):
            raise ValueError("Expected 'initial:' line")
        initial_id = int(lines[i].split(":")[1].strip())
        i += 1

        # --- Parse locations ---
        if lines[i] != "locations:":
            raise ValueError("Expected 'locations:' section")
        i += 1

        while i < len(lines) and not lines[i].startswith("transitions"):
            # Format: "<id> <name> accepting=<bool>"
            m = re.match(r'(\d+)\s+"([^"]+)"\s+accepting=(True|False)', lines[i])
            if not m:
                raise ValueError(f"Cannot parse location line: {lines[i]}")

            loc_id = int(m.group(1))
            name = m.group(2)
            accepting = m.group(3) == "True"

            ra.add_location(loc_id, name, accepting)
            i += 1
        # with locations parsed, set initial
        ra.set_initial(initial_id)

        # --- Parse transitions ---
        if lines[i] != "transitions:":
            raise ValueError("Expected 'transitions:' section")
        i += 1

        while i < len(lines):
            # Example line:
            #   0 -> 1 : tau=[1,2], E={0,2}
            line = lines[i]
            left, right = line.split(":")
            left = left.strip()
            right = right.strip()

            # Parse "0 -> 1"
            src_str, _, tgt_str = left.split()
            src, tgt = int(src_str), int(tgt_str)

            # Parse tau list
            tau_part, e_part = right.split(", E=")
            tau_str = tau_part.split("=", 1)[1].strip()
            tau_str = tau_str[1:-1]   # remove [ ]

            if tau_str:
                x_strs = [x.strip() for x in tau_str.split(",")]
                x_values = [float(x) if alphabet.letter_type == LetterType.REAL else Fraction(x)
                            for x in x_strs]
                tau_letters = [alphabet.make_letter(x)
                                for x in x_values]
            else:
                tau_letters = []

            tau = alphabet.form_sequence(tau_letters)

            # Parse E-set
            e_str = e_part.strip()
            e_str = e_str[1:-1]  # remove { }

            if e_str:
                indices_to_remove = {int(x) for x in e_str.split(",")}
            else:
                indices_to_remove = set()

            # Add transition
            ra.add_transition(
                source=src,
                tau=tau,
                indices_to_remove=indices_to_remove,
                target=tgt
            )
            i += 1
        return ra
