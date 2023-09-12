from zenlog import log
from dataclasses import dataclass
from mccode.instr import Instr
from nexusformat.nexus import NXfield


@dataclass
class NXInstr:
    instr: Instr

    def to_nx(self):
        # quick and very dirty:
        return NXfield(str(self.instr))
