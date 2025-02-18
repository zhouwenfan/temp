# Author: Bohua Zhan

import unittest

from kernel.type import Type, TVar, TFun, boolT
from kernel.term import Term, Var, Const, Comb, Abs, Bound
from kernel.thm import Thm
from kernel.proof import Proof
from kernel.macro import ProofMacro
from kernel.theory import Theory, TheoryException, CheckProofException
from kernel.extension import AxType, AxConstant, Constant, Theorem, TheoryExtension
from kernel.report import ProofReport, ExtensionReport

thy = Theory.EmptyTheory()

Ta = TVar("a")
Tb = TVar("b")
Tab = TFun(Ta, Tb)
x = Var("x", Ta)
y = Var("y", Ta)
z = Var("z", Ta)
f = Var("f", Tab)
A = Var("A", boolT)
B = Var("B", boolT)
C = Var("C", boolT)

# A simple macro
class beta_conv_rhs_macro(ProofMacro):
    """Reduce the right side of th by beta-conversion."""

    def __init__(self):
        self.level = 1
        self.sig = Term

    def eval(self, thy, args, ths):
        th = ths[0]
        assert Term.is_equals(th.prop), "beta_conv_rhs"
        rhs = th.prop.rhs

        return Thm.transitive(th, Thm.beta_conv(rhs))

    def expand(self, prefix, thy, args, prevs):
        id, th = prevs[0]
        assert Term.is_equals(th.prop), "beta_conv_rhs"
        rhs = th.prop.rhs

        prf = Proof()
        prf.add_item(prefix + (0,), "beta_conv", args=rhs)
        prf.add_item(prefix + (1,), "transitive", prevs=[id, prefix + (0,)])
        return prf


class TheoryTest(unittest.TestCase):
    def testEmptyTheory(self):
        self.assertEqual(thy.get_type_sig("bool"), 0)
        self.assertEqual(thy.get_type_sig("fun"), 2)
        self.assertEqual(thy.get_term_sig("equals"), TFun(Ta,Ta,boolT))
        self.assertEqual(thy.get_term_sig("implies"), TFun(boolT,boolT,boolT))

    def testCheckType(self):
        test_data = [
            Ta,
            TFun(Ta, Tb),
            TFun(TFun(Ta, Ta), Tb),
            TFun(boolT, boolT),
            TFun(TFun(Ta, boolT), boolT),
        ]

        for T in test_data:
            self.assertEqual(thy.check_type(T), None)

    def testCheckTypeFail(self):
        test_data = [
            Type("bool", Ta),
            Type("bool", Ta, Ta),
            Type("fun"),
            Type("fun", Ta),
            Type("fun", Ta, Ta, Ta),
            TFun(Type("bool", Ta), Type("bool")),
            TFun(Type("bool"), Type("bool", Ta)),
            Type("random")
        ]

        for T in test_data:
            self.assertRaises(TheoryException, thy.check_type, T)

    def testCheckTerm(self):
        test_data = [
            x,
            Term.mk_equals(x, y),
            Term.mk_equals(f, f),
            Term.mk_implies(A, B),
            Abs("x", Ta, Term.mk_equals(x, y)),
        ]

        for t in test_data:
            self.assertEqual(thy.check_term(t), None)

    def testCheckTermFail(self):
        test_data = [
            Const("random", Ta),
            Const("equals", TFun(Ta, Tb, boolT)),
            Const("equals", TFun(Ta, Ta, Tb)),
            Const("implies", TFun(Ta, Ta, boolT)),
            Comb(Const("random", Tab), x),
            f(Const("random", Ta)),
            Abs("x", Ta, Const("random", Ta)),
        ]

        for t in test_data:
            self.assertRaises(TheoryException, thy.check_term, t)

    def testCheckProof(self):
        """Proof of [A, A --> B] |- B."""
        A_to_B = Term.mk_implies(A, B)
        prf = Proof(A_to_B, A)
        prf.add_item(2, "implies_elim", prevs=[0, 1])

        rpt = ProofReport()
        self.assertEqual(thy.check_proof(prf, rpt), Thm([A_to_B, A], B))
        self.assertEqual(rpt.steps, 3)

    def testCheckProof2(self):
        """Proof of |- A --> A."""
        prf = Proof(A)
        prf.add_item(1, "implies_intr", args=A, prevs=[0])

        rpt = ProofReport()
        self.assertEqual(thy.check_proof(prf, rpt), Thm.mk_implies(A,A))
        self.assertEqual(rpt.steps, 2)

    def testCheckProof3(self):
        """Proof of [x = y, y = z] |- f z = f x."""
        x_eq_y = Term.mk_equals(x,y)
        y_eq_z = Term.mk_equals(y,z)
        prf = Proof(x_eq_y, y_eq_z)
        prf.add_item(2, "transitive", prevs=[0, 1])
        prf.add_item(3, "symmetric", prevs=[2])
        prf.add_item(4, "reflexive", args=f)
        prf.add_item(5, "combination", prevs=[4, 3])

        rpt = ProofReport()
        th = Thm([x_eq_y, y_eq_z], Term.mk_equals(f(z),f(x)))
        self.assertEqual(thy.check_proof(prf, rpt), th)
        self.assertEqual(rpt.steps, 6)

    def testCheckProof4(self):
        """Proof of |- x = y --> x = y by instantiating an existing theorem."""
        thy = Theory.EmptyTheory()
        thy.add_theorem("trivial", Thm.mk_implies(A,A))

        x_eq_y = Term.mk_equals(x,y)
        prf = Proof()
        prf.add_item(0, "theorem", args="trivial")
        prf.add_item(1, "substitution", args={"A" : x_eq_y}, prevs=[0])

        rpt = ProofReport()
        th = Thm.mk_implies(x_eq_y,x_eq_y)
        self.assertEqual(thy.check_proof(prf, rpt), th)
        self.assertEqual(rpt.steps, 2)

    def testCheckProof5(self):
        """Empty instantiation."""
        thy = Theory.EmptyTheory()
        thy.add_theorem("trivial", Thm.mk_implies(A,A))

        x_eq_y = Term.mk_equals(x,y)
        prf = Proof()
        prf.add_item(0, "theorem", args="trivial")
        prf.add_item(1, "substitution", args={}, prevs=[0])

        rpt = ProofReport()
        th = Thm.mk_implies(A,A)
        self.assertEqual(thy.check_proof(prf, rpt), th)
        self.assertEqual(rpt.steps_stat(), (1, 1, 0))
        self.assertEqual(rpt.th_names, {"trivial"})

    def testCheckProofFail(self):
        """Previous item not found."""
        prf = Proof()
        prf.add_item(0, "implies_intr", prevs=[1])

        self.assertRaisesRegex(CheckProofException, "previous item not found", thy.check_proof, prf)

    def testCheckProofFail2(self):
        """Invalid derivation."""
        prf = Proof(A)
        prf.add_item(1, "symmetric", prevs=[0])

        self.assertRaisesRegex(CheckProofException, "invalid derivation", thy.check_proof, prf)

    def testCheckProofFail3(self):
        """Invalid input to derivation."""
        prf = Proof(A)
        prf.add_item(1, "implies_intr", prevs=[0])

        self.assertRaisesRegex(CheckProofException, "invalid input to derivation", thy.check_proof, prf)

    def testCheckProofFail4(self):
        """Output does not match."""
        prf = Proof(A)
        prf.add_item(1, "implies_intr", args=A, prevs=[0], th = Thm.mk_implies(A,B))

        self.assertRaisesRegex(CheckProofException, "output does not match", thy.check_proof, prf)

    def testCheckProofFail5(self):
        """Theorem not found."""
        prf = Proof()
        prf.add_item(0, "theorem", args="random")

        self.assertRaisesRegex(CheckProofException, "theorem not found", thy.check_proof, prf)

    def testCheckProofFail6(self):
        """Typing error: statement is not non-boolean."""
        prf = Proof(x)

        self.assertRaisesRegex(CheckProofException, "typing error", thy.check_proof, prf)

    def testCheckProofFail7(self):
        """Typing error: type-checking failed."""
        prf = Proof(Comb(Var("P", TFun(Tb, boolT)), x))

        self.assertRaisesRegex(CheckProofException, "typing error", thy.check_proof, prf)

    def testCheckProofFail8(self):
        """Proof method not found."""
        prf = Proof()
        prf.add_item(0, "random")

        self.assertRaisesRegex(CheckProofException, "proof method not found", thy.check_proof, prf)

    def testAssumsSubset(self):
        """res_th is OK if assumptions is a subset of that of seq.th."""
        prf = Proof()
        prf.add_item(0, "assume", args=A, th=Thm([A, B], A))

        self.assertEqual(thy.check_proof(prf), Thm([A, B], A))

    def testAssumsSubsetFail(self):
        """res_th is not OK if assumptions is not a subset of that of seq.th."""
        prf = Proof()
        prf.add_item(0, "assume", args=A, th=Thm([], A))

        self.assertRaisesRegex(CheckProofException, "output does not match", thy.check_proof, prf)

    def testCheckProofMacro(self):
        """Proof checking with simple macro."""
        thy = Theory.EmptyTheory()
        thy.add_proof_macro("beta_conv_rhs", beta_conv_rhs_macro())
        
        t = Comb(Abs("x", Ta, Bound(0)), x)

        prf = Proof()
        prf.add_item(0, "reflexive", args=t)
        prf.add_item(1, "beta_conv_rhs", prevs=[0])
        th = Thm.mk_equals(t,x)

        # Check obtaining signature
        self.assertEqual(thy.get_proof_rule_sig("beta_conv_rhs"), Term)

        # Check proof without trusting beta_conv_rhs
        rpt = ProofReport()
        self.assertEqual(thy.check_proof(prf, rpt), th)
        self.assertEqual(rpt.steps_stat(), (0, 3, 0))
        self.assertEqual(rpt.macros_expand, {"beta_conv_rhs"})

        # Check proof while trusting beta_conv_rhs
        rpt = ProofReport()
        self.assertEqual(thy.check_proof(prf, rpt, check_level=1), th)
        self.assertEqual(rpt.steps_stat(), (0, 1, 1))
        self.assertEqual(rpt.macros_eval, {"beta_conv_rhs"})

    def testCheckProofGap(self):
        """Check proof with gap."""
        prf = Proof()
        prf.add_item(0, "sorry", th = Thm.mk_implies(A,B))
        prf.add_item(1, "sorry", th = Thm([], A))
        prf.add_item(2, "implies_elim", prevs=[0, 1])

        rpt = ProofReport()
        self.assertEqual(thy.check_proof(prf, rpt), Thm([], B))
        self.assertEqual(rpt.gaps, [Thm.mk_implies(A, B), Thm([], A)])

    def testUncheckedExtend(self):
        """Unchecked extension."""
        thy = Theory.EmptyTheory()
        thy_ext = TheoryExtension()

        id_const = Const("id", TFun(Ta,Ta))
        id_def = Abs("x", Ta, Bound(0))
        id_simps = Term.mk_equals(id_const(x), x)

        thy_ext.add_extension(Constant("id", id_def))        
        thy_ext.add_extension(Theorem("id.simps", Thm([], id_simps)))

        self.assertEqual(thy.unchecked_extend(thy_ext), None)
        self.assertEqual(thy.get_term_sig("id"), TFun(Ta, Ta))
        self.assertEqual(thy.get_theorem("id_def"), Thm.mk_equals(id_const, id_def))
        self.assertEqual(thy.get_theorem("id.simps"), Thm([], id_simps))

    def testCheckedExtend(self):
        """Checked extension: adding an axiom."""
        thy = Theory.EmptyTheory()
        thy_ext = TheoryExtension()

        id_simps = Term.mk_equals(Comb(Const("id", TFun(Ta,Ta)),x), x)
        thy_ext.add_extension(Theorem("id.simps", Thm([], id_simps)))

        ext_report = thy.checked_extend(thy_ext)
        self.assertEqual(thy.get_theorem("id.simps"), Thm([], id_simps))
        self.assertEqual(ext_report.get_axioms(), [("id.simps", Thm([], id_simps))])

    def testCheckedExtend2(self):
        """Checked extension: proved theorem."""
        thy = Theory.EmptyTheory()
        thy_ext = TheoryExtension()

        id_const = Const("id", TFun(Ta,Ta))
        id_def = Abs("x", Ta, Bound(0))
        id_simps = Term.mk_equals(id_const(x), x)

        # Proof of |- id x = x from |- id = (%x. x)
        prf = Proof()
        prf.add_item(0, "theorem", args="id_def")  # id = (%x. x)
        prf.add_item(1, "reflexive", args=x)  # x = x
        prf.add_item(2, "combination", prevs=[0, 1])  # id x = (%x. x) x
        prf.add_item(3, "beta_conv", args=id_def(x))  # (%x. x) x = x
        prf.add_item(4, "transitive", prevs=[2, 3])  # id x = x

        thy_ext.add_extension(Constant("id", id_def))
        thy_ext.add_extension(Theorem("id.simps", Thm([], id_simps), prf))

        ext_report = thy.checked_extend(thy_ext)
        self.assertEqual(thy.get_theorem("id.simps"), Thm([], id_simps))
        self.assertEqual(ext_report.get_axioms(), [])

    def testCheckedExtend3(self):
        """Axiomatized constant."""
        thy = Theory.EmptyTheory()
        thy_ext = TheoryExtension()

        thy_ext.add_extension(AxType("nat", 0))
        thy_ext.add_extension(AxConstant("id", TFun(Ta,Ta)))
        ext_report = thy.checked_extend(thy_ext)
        self.assertEqual(thy.get_type_sig("nat"), 0)
        self.assertEqual(thy.get_term_sig("id"), TFun(Ta,Ta))
        self.assertEqual(ext_report.get_axioms(), [("nat", 0), ("id", TFun(Ta,Ta))])

if __name__ == "__main__":
    unittest.main()
