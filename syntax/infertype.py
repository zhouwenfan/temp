# Author: Bohua Zhan

"""Hindley-Milner type inference algorithm."""

from kernel.type import HOLType, TVar, TFun
from kernel.term import Term
from kernel import term
from util import unionfind


class TypeInferenceException(Exception):
    def __init__(self, err):
        self.str = str


def is_internal_type(T):
    """Whether T is an internal type used for type inference
    (and hence can be unified).

    """
    return T.ty == HOLType.TVAR and T.name.startswith("_t")

def unify(uf, T1, T2):
    """Unification of two types. This modifies the supplied union-find
    data structure.
    
    """
    T1 = uf.find(T1)
    T2 = uf.find(T2)
    if T1.ty == HOLType.TYPE and T2.ty == HOLType.TYPE and T1.name == T2.name:
        for i in range(len(T1.args)):
            unify(uf, T1.args[i], T2.args[i])
    elif T1.ty == HOLType.TVAR and T2.ty == HOLType.TVAR and T1.name == T2.name:
        return
    elif is_internal_type(T1):
        uf.union(T2, T1, force_first=True)
    elif is_internal_type(T2):
        uf.union(T1, T2, force_first=True)
    else:
        raise TypeInferenceException("Unable to unify " + str(T1) + " with " + str(T2))

def type_infer(thy, ctxt, t, *, forbid_internal=True):
    """Perform type inference on the given term. The input term
    has all types marked None, except those subterms whose type is
    explicitly given.
    
    """
    uf = unionfind.UnionFind()

    # Number of internal type variables created.
    num_internal = 0

    # Returns a new type variable.
    def new_type():
        nonlocal num_internal
        T = TVar("_t" + str(num_internal))
        num_internal += 1
        return T

    # Add type and all subtypes to union-find.
    def add_type(T):
        for Ts in T.get_tsubs():
            if not uf.has_key(Ts):
                uf.insert(Ts)

    # Infer the type of T.
    def infer(t, bd_vars):
        # Var case: if type is not known, try to obtain it from context,
        # otherwise, make a new type.
        if t.is_var():
            if t.T is None:
                if t.name in ctxt:
                    t.T = ctxt[t.name]
                else:
                    t.T = new_type()
            add_type(t.T)
            return t.T

        # Const case: if type is not known, obtain it from theory,
        # replacing arbitrary variables by new types.
        elif t.is_const():
            if t.T is None:
                T = thy.get_term_sig(t.name)
                Tvars = T.get_tvars()
                tyinst = dict()
                for Tv in Tvars:
                    tyinst[Tv.name] = new_type()
                t.T = T.subst(tyinst)
            add_type(t.T)
            return t.T

        # Comb case: recursively infer type of fun and arg, then
        # unify funT with argT => resT, where resT is a new type.
        elif t.is_comb():
            funT = infer(t.fun, bd_vars)
            argT = infer(t.arg, bd_vars)
            resT = new_type()
            add_type(TFun(argT, resT))
            unify(uf, funT, TFun(argT, resT))
            return resT

        # Abs case: if var_T is not known, make a new type. Recursively
        # call infer on the body under the context where var_name has
        # type var_T. The resulting type is var_T => body_T.
        elif t.is_abs():
            if t.var_T is None:
                t.var_T = new_type()
                add_type(t.var_T)
            bodyT = infer(t.body, [t.var_T] + bd_vars)
            resT = TFun(t.var_T, bodyT)
            add_type(resT)
            return resT

        # Bound variables should not appear during inference.
        elif t.is_bound():
            return bd_vars[t.n]

        else:
            raise TypeError()

    infer(t, [])

    # Replace vars and constants with the appropriate type.
    tyinst = dict()
    for i in range(num_internal):
        rep = uf.find(TVar("_t" + str(i)))
        if forbid_internal and is_internal_type(rep):
            raise TypeInferenceException("Unspecified type\n" + repr(t))
        if not is_internal_type(rep):
            tyinst["_t" + str(i)] = rep

    for i in range(100):
        repr_t = repr(t)
        t.subst_type_inplace(tyinst)
        if repr_t == repr(t):
            break
    assert i != 99, "type_infer: infinite loop at substitution."

    return t

def infer_printed_type(thy, t):
    """Infer the types that should be printed.
    
    The algorithm is as follows:
    1. Replace all constant types with None.
    2. Apply type-inference on the resulting type.
    3. For the first internal type variable that appears, find a constant
       whose type contains that variable, set that constant to print_type.
    4. Repeat until no internal type variables appear.
    
    """
    def clear_const_type(t):
        if t.is_const() and not hasattr(t, "print_type"):
            t.backupT = t.T
            t.T = None
        elif t.is_comb():
            clear_const_type(t.fun)
            clear_const_type(t.arg)
        elif t.is_abs() and not hasattr(t, "print_type"):
            t.backup_var_T = t.var_T
            t.var_T = None
            clear_const_type(t.body)

    def recover_const_type(t):
        if t.is_const():
            t.T = t.backupT
        elif t.is_comb():
            recover_const_type(t.fun)
            recover_const_type(t.arg)
        elif t.is_abs():
            t.var_T = t.backup_var_T
            recover_const_type(t.body)

    for i in range(100):
        clear_const_type(t)
        type_infer(thy, dict(), t, forbid_internal=False)

        def has_internalT(T):
            return any(is_internal_type(subT) for subT in T.get_tsubs())

        to_replace, to_replaceT = None, None
        def find_to_replace(t):
            nonlocal to_replace, to_replaceT
            if t.is_const() and has_internalT(t.T):
                if to_replace is None or len(str(t.T)) < len(str(to_replaceT)):
                    to_replace = t
                    to_replaceT = t.T
            elif t.is_abs() and has_internalT(t.var_T):
                if to_replace is None or len(str(t.var_T)) < len(str(to_replaceT)):
                    to_replace = t
                    to_replaceT = t.var_T
                find_to_replace(t.body)
            elif t.is_comb():
                find_to_replace(t.fun)
                find_to_replace(t.arg)

        find_to_replace(t)
        recover_const_type(t)

        if to_replace is None:
            break

        to_replace.print_type = True

    assert i != 99, "infer_printed_type: infinite loop."

    return None
