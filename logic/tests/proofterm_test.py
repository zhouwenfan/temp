# Author: Bohua Zhan

import unittest

from kernel.type import TVar, TFun
from kernel.term import Var, Term
from kernel.thm import Thm
from kernel.proof import Proof
from logic import basic
from logic.proofterm import ProofTerm

thy = basic.load_theory('logic_base')

Ta = TVar("a")
x = Var("x", Ta)
y = Var("y", Ta)
z = Var("z", Ta)
f = Var("f", TFun(Ta,Ta,Ta))

class ProofTermTest(unittest.TestCase):
    def testExport(self):
        """Basic case."""
        pt1 = ProofTerm.assume(Term.mk_equals(x,y))
        pt2 = ProofTerm.assume(Term.mk_equals(y,z))
        pt3 = ProofTerm.transitive(pt1, pt2)

        prf = pt3.export()
        self.assertEqual(len(prf.items), 3)
        self.assertEqual(thy.check_proof(prf), pt3.th)

    def testExport2(self):
        """Repeated theorems."""
        pt1 = ProofTerm.assume(Term.mk_equals(x,y))
        pt2 = ProofTerm.reflexive(f)
        pt3 = ProofTerm.combination(pt2, pt1)  # f x = f y
        pt4 = ProofTerm.combination(pt3, pt1)  # f x x = f y y

        prf = pt4.export()
        self.assertEqual(len(prf.items), 4)
        self.assertEqual(thy.check_proof(prf), pt4.th)

    def testExport3(self):
        """Case with atoms."""
        pt1 = ProofTerm.atom(0, Thm.mk_equals(x,y))
        pt2 = ProofTerm.atom(1, Thm.mk_equals(y,z))
        pt3 = ProofTerm.transitive(pt1, pt2)

        prf = Proof()
        prf.add_item(0, rule="sorry", th=Thm.mk_equals(x,y))
        prf.add_item(1, rule="sorry", th=Thm.mk_equals(y,z))
        pt3.export(prf=prf)

        self.assertEqual(thy.check_proof(prf), Thm.mk_equals(x,z))

if __name__ == "__main__":
    unittest.main()
