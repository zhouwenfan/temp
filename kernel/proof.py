# Author: Bohua Zhan

from kernel.thm import Thm

class ProofException(Exception):
    pass

class ProofItem():
    """An item in a proof, consisting of the following data:

    - id: an identifier for reference by later proof items.
    - th: theorem statement (as a sequent).
    - rule: derivation rule used to derive the theorem.
    - args: arguments to the rule.
    - prevs: previous sequents used.

    """
    def __init__(self, id, th, rule, args = None, prevs = []):
        self.id = id
        self.th = th
        self.rule = rule
        self.args = args
        self.prevs = prevs

    def __str__(self):
        if self.args:
            str_args = " " + repr(self.args)
        else:
            str_args = ""

        if self.prevs:
            str_prevs = " from " + ", ".join(str(prev) for prev in self.prevs)
        else:
            str_prevs = ""

        return self.id + ": " + str(self.th) + " by " + self.rule + str_args + str_prevs

    def __repr__(self):
        return str(self)

class Proof():
    """Proof objects represent proofs in the natural deduction format.

    Each proof consists of a list of items, where each item contains a
    theorem, which is derived from zero or more previous theorems using
    one of the deduction rules.

    """
    def __init__(self, *assums):
        """Initialization can take a list of n assumptions, and generates
        first n steps A1, ..., An using Thm.assume on the assumptions.

        """
        self.proof = []
        for (id, assum) in zip(range(len(assums)), assums):
            item = ProofItem("A" + str(id+1), Thm.assume(assum), "assume", args = assum)
            self.proof.append(item)

    def add_item(self, id, th, rule, args = None, prevs = []):
        """Add the given item to the end of the proof."""
        self.proof.append(ProofItem(id, th, rule, args, prevs))

    def get_items(self):
        """Returns the list of items."""
        return self.proof

    def get_last_item(self):
        """Returns the last item."""
        return self.proof[-1]

    def get_num_item(self):
        """Returns the number of items."""
        return len(self.proof)

    def get_thm(self):
        """Returns the theorem obtained by the proof."""
        if self.proof:
            return self.proof[-1].th
        else:
            raise ProofException()

    def __str__(self):
        return "\n".join(str(item) for item in self.proof)

    def __repr__(self):
        return str(self)
