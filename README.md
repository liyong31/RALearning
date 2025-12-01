# RALearning

RALT (Register Automata Learning Tool) takes as input a deterministic register automaton (DRA) and outputs a minimal canonical DRA.

Usage:
```
python3 ralt.py --inp ra2.txt --out ra.txt
``` 

Note that this tool only takes *complete* and *well-typed* DRA as target automaton.
The completeness and well-typeness properties are required for running a word and testing equivalence of two given configurations.


## The Register Automaton Input Format

This input format specifies a **register automaton (RA)** over an ordered data domain. The automaton is defined by its alphabet, initial location, set of locations with associated register value notations, and transitions describing how registers are updated and compared with the input data.

All comments should start with a symbol `#`; the content after will be ignored

---

### Global Header

#### `alphabet: <alphabet-set>, <binary-relation>`
This field specifies the **data domain** and its **ordering relation**.  
The alphabet set can be either **real** or **rational** and the binary relation can be either **=** or **<**.

Example: 
```
alphabet: real, <
```

#### `initial: 0`
Indicates the **initial location** of the automaton (location ID `0`).
The initial state will always be 0.

---

### Locations

Each location is described by three components:
```
<id> "<register valuation notation>" accepting=<True|False>
```

- **id**: numeric identifier of the location.  
- **register valuation**: a list of the values currently stored in the registers at that location.
  - Example: `"[0.0]"` means the automaton has one register storing `0.0`.
- **accepting**: Boolean indicating whether the location is accepting.

Example:
```
1 "[0.0]" accepting=True
```


This means: location 1 has one register with value 0.0 and is accepting.

---

### Transitions

Each transition is written as: 
```
<s> -> <t> : tau=[v₁, v₂, ...], E={i₁, i₂, ...}
```

Where:

- **s -> t**: transition from source location `s` to target location `t`.
- **tau**: a list representing the **register vlaue type**, describing the expected ordering/equality relationships between:
  - the current input symbol, and  
  - the registers at location `s`.
- **E**: a set of register indices whose values will be removed.

Example:
```
1 -> 5 : tau=[0.0,1.0], E={0,1}
```
This means tht the transition from location 1 to location 5 is enabled when the memorble word concatenated with the input letter matches the pattern `[0.0,1.0]`.
- The values in registers 0 and 1 are cleared.

---

A full example of complete and well-typed DRA accepting non-decreasing sequence is given below:
```
# Register Automaton
alphabet: real, <
initial: 0
locations:
  0 "ɛ" accepting=False
  1 "1" accepting=True
  2 "12" accepting=False

transitions:
  0 -> 1 : tau=[1.0], E={}
  1 -> 1 : tau=[1.0,1.0], E={0}
  1 -> 1 : tau=[1.0,2.0], E={0}
  1 -> 2 : tau=[1.0,0.0], E={0,1}
  2 -> 2 : tau=[1.0], E={0}
```

---

## Experiments

For information about running experiments (learning $L_n$ languages, randomly generated DRAs, etc.), see the [experiments README](experiments/README.md).



