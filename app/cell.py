from kernel.report import ProofReport
from server import tactic


class Cell(object):
    def __init__(self, vars, assums, concl, origin, ctxt=None):
        self.__proof = tactic.init_proof(vars, assums, concl)
        self.__ctxt = ctxt if ctxt is not None else dict()
        self.assums = assums
        self.concl = concl
        self.orgin = origin
        self.rpt = ProofReport()

    def update(self, origin):
        self.orgin = origin
