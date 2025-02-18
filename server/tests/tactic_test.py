# Author: Bohua Zhan

import unittest

from kernel.type import boolT, TVar, TFun
from kernel.term import Term, Var
from kernel.thm import Thm
from kernel.proof import ProofItem
from logic.proofterm import ProofTerm, ProofTermAtom
from logic import basic
from logic.logic import conj, disj, mk_if
from logic.nat import natT, plus, zero
from server import tactic
from syntax import printer

thy = basic.load_theory('nat')

class TacticTest(unittest.TestCase):
    def testRule(self):
        A = Var('A', boolT)
        B = Var('B', boolT)
        goal = Thm([], conj(B, A))
        pt = tactic.rule().get_proof_term(thy, ProofTerm.sorry(goal), args='conjI')
        prf = pt.export()
        self.assertEqual(thy.check_proof(prf), goal)

    def testRule2(self):
        A = Var('A', boolT)
        B = Var('B', boolT)
        goal = Thm([], disj(B, A))
        prev = ProofTermAtom(0, Thm.assume(disj(A, B)))
        pt = tactic.rule().get_proof_term(thy, ProofTerm.sorry(goal), args='disjE', prevs=[prev])
        prf = pt.export(prefix=(1,), subproof=False)
        self.assertEqual(prf.items[2], ProofItem(3, 'apply_theorem', args='disjE', prevs=[0, 1, 2]))

    def testRule3(self):
        A = Var('A', boolT)
        B = Var('B', boolT)
        goal = Thm([], disj(B, A))
        prev = ProofTermAtom(0, Thm.assume(B))
        pt = tactic.rule().get_proof_term(thy, ProofTerm.sorry(goal), args='disjI1', prevs=[prev])
        prf = pt.export(prefix=(1,), subproof=False)
        self.assertEqual(prf.items[0], ProofItem(1, 'apply_theorem_for', args=('disjI1', {}, {'A': B, 'B': A}), prevs=[0]))

    def testRule4(self):
        n = Var('n', natT)
        goal = Thm([], Term.mk_equals(plus(n, zero), n))
        inst = {'P': Term.mk_abs(n, goal.prop), 'x': n}
        pt = tactic.rule().get_proof_term(thy, ProofTerm.sorry(goal), args=('nat_induct', ({}, inst)))
        prf = pt.export()
        self.assertEqual(thy.check_proof(prf), goal)

    def testIntros(self):
        Ta = TVar('a')
        x = Var('x', Ta)
        P = Var('P', TFun(Ta, boolT))
        Q = Var('Q', TFun(Ta, boolT))
        goal = Thm([], Term.mk_all(x, Term.mk_implies(P(x), Q(x))))
        intros_tac = tactic.intros()
        pt = intros_tac.get_proof_term(thy, ProofTerm.sorry(goal), args=['x'])
        prf = pt.export()
        self.assertEqual(thy.check_proof(prf), goal)

    def testInduct(self):
        n = Var('n', natT)
        goal = Thm([], Term.mk_equals(plus(n, zero), n))
        induct_tac = tactic.var_induct()
        pt = induct_tac.get_proof_term(thy, ProofTerm.sorry(goal), args=('nat_induct', n))
        prf = pt.export()
        self.assertEqual(thy.check_proof(prf), goal)

    def testRewrite(self):
        n = Var('n', natT)
        goal = Thm.mk_equals(plus(zero, n), n)
        rewrite_tac = tactic.rewrite()
        pt = rewrite_tac.get_proof_term(thy, ProofTerm.sorry(goal), args='plus_def_1')
        prf = pt.export()
        self.assertEqual(thy.check_proof(prf), goal)

    def testRewrite2(self):
        Ta = TVar("a")
        a = Var("a", Ta)
        b = Var("b", Ta)
        eq_a = Term.mk_equals(a, a)
        goal = Thm.mk_equals(mk_if(eq_a, b, a), b)
        rewrite_tac = tactic.rewrite()
        pt = rewrite_tac.get_proof_term(thy, ProofTerm.sorry(goal), args='if_P')
        prf = pt.export()
        self.assertEqual(prf.items[0], ProofItem(0, 'sorry', th=Thm.mk_equals(a, a)))
        self.assertEqual(thy.check_proof(prf), goal)

    def testCases(self):
        A = Var('A', boolT)
        B = Var('B', boolT)
        C = Var('C', boolT)
        cases_tac = tactic.cases()
        pt = cases_tac.get_proof_term(thy, ProofTerm.sorry(Thm([B], C)), args=A)
        prf = pt.export()
        self.assertEqual(thy.check_proof(prf), Thm([B], C))


if __name__ == "__main__":
    unittest.main()
