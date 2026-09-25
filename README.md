# INVESTIGATION 001: Secret Knowledge Base (v3.0)

## 1. Player Registration and Profile

Before the investigation begins, the game identifies the user:

* **Sign In / Registration:** The player enters their name or nickname (or uses the current profile).
* **Progress Saving:** The system tracks player statistics:
  * Number of successfully completed cases.
  * Difficulty level chosen by the analyst (*Novice*, *Investigator*, *Chief Analyst*).
  * Total score and rating.

---

## 2. Gameplay and Campaign Structure

The player acts as an AI analyst for a cyber corporation investigating a server breach. The knowledge base (KB) consists of corporate security axioms, suspect testimonies, and system logs written as propositional logic formulas with human-readable explanations alongside them.

### Campaign Progression (Rounds)

* The campaign consists of a **series of rounds (cases)** — by default, a full cycle consists of **5 consecutive cases** of varying difficulty.
* In each round, the player chooses the investigation mode: **"Proof"** or **"Breach"**.
* **Successful completion of a round** is considered the correct proof of a hypothesis or the identification of a minimal inconsistency within a limited number of turns / without using penalty hints.
* After completing all rounds, the game summarizes the final report (score, analyst efficiency).

---

## 3. Game Modes

### Mode A: "Proof" (Deductive Analysis)

* **Objective:** Prove a specific hypothesis $H$ using deductive reasoning.
* **Briefing:** The game outputs the KB as a numbered list of formulas with explanations. Before the round starts, a consistency check (resolution on the KB) is performed so that the player always receives a consistent base.
* **Player's Turn:** Entering hypothesis $H$ (e.g., a simple literal `B` or a complex formula `A & ~C -> B`).
* **Processing:** The system adds $\neg H$ to the KB, reduces everything to CNF, and runs the resolution method (proof by contradiction).
* **Verdict:**
  * **Proved:** An empty clause was found for $KB \cup \{\neg H\}$. The *Derivation Tree* is shown.
  * **Refuted:** An empty clause was found for $KB \cup \{H\}$.
  * **Undetermined:** Resolution exhausted in both cases, meaning the KB says nothing about $H$.

### Mode B: "Breach" (Falsification Search)

* **Objective:** Find a minimal inconsistent subset of statements in a deliberately inconsistent base (a set that is incompatible together, but becomes consistent after removing any single element).
* **Verdict:** If the set is minimal and inconsistent, the case is solved. If extra statements are named or the set is consistent, the game asks to try again.

---

## 4. Difficulty Levels and Progression

| Difficulty Level | Variables in KB | Features and Constraints |
| :--- | :---: | :--- |
| **Novice** | 3–4 | One short derivation chain, unlimited hints. |
| **Investigator** | 5–6 | Multiple derivation paths, limited number of hints. |
| **Chief Analyst** | 7–8 | "False tracks" (relevant but consistent non-relevant statements). No hints. |

---

## 5. Formula Input Syntax

| Symbol | Meaning | Example |
| :---: | :--- | :--- |
| `~` | NOT (negation) | `~A` |
| `&` | AND (conjunction) | `A & B` |
| `v` | OR (disjunction) | `A v B` |
| `->` | Implication | `B -> S` |
| `<->` | Equivalence | `A <-> B` |
| `( )` | Grouping | `(A v B) -> C` |

*Variables are specified in uppercase letters (A, B, S, V). The legend is displayed in the briefing.*

---

## 6. Interaction Menu (CLI)

1. View player profile and round statistics
2. View the list of statements (axioms and testimonies of the current case)
3. Propose a hypothesis / name suspected statements
4. Request a hint (comparison pair / unpaired literals)
5. Show derivation tree of the previous hypothesis
6. End investigation (return to main menu)