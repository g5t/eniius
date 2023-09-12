from .mcstas import NXMcStas, get_instr
from .writer import Writer
from .nexus import get_nx_component
from nexusformat.nexus import nxload, NXfield


class Eniius:

    def __init__(self, nxs_obj=None, detector_dat=None, ei=None):
        from nexusformat import NXfermi_chopper
        self.nxs_obj = nxs_obj
        self.detector_dat = detector_dat
        self.ei = ei
        self._name = 'NeXus_instrument'
        if self.ei is None:
            fermi = get_nx_component(self.nxs_obj, nxtype=NXfermi_chopper)
            if fermi is not None and 'energy' in fermi:
                self.ei = fermi.energy.nxvalue

    def to_icp(self, filename):
        if not filename.endswith('.nxs'):
            filename += '.nxs'
        writer = Writer(self.nxs_obj)
        writer.to_icp(filename, self.detector_dat)

    def to_json(self, filename, indent=4, only_nx=True, absolute_depends_on=False):
        if not filename.endswith('.json'):
            filename += '.json'
        writer = Writer(self.nxs_obj)
        writer.to_json(filename, indent=indent, only_nx=only_nx, absolute_depends_on=absolute_depends_on)

    def to_nxspe(self, filename):
        if self.ei is None:
            raise RuntimeError('NXS instrument has no incident energy set. Cannot write NXSPE file')
        if not filename.endswith('.nxspe'):
            filename += '.nxspe'
        writer = Writer(self.nxs_obj)
        writer.to_nxspe(filename, self.ei, self.detector_dat)

    # def to_mcstas(self):
    #     from nexusformat.nexus import NXinstrument
    #     from eniius.nexus import Nxinst2McStas
    #     if self.nxs_obj.nxclass == 'NXinstrument':
    #         nxs_inst = self.nxs_obj
    #     else:
    #         nxs_inst = get_nx_component(self.nxs_obj, nxtype=NXinstrument)
    #     return NXinst2McStas(self.name, nxs_inst)

    # def to_instr(self, filename):
    #     if not filename.endswith('.instr'):
    #         filename += '.instr'
    #     mcstas_obj = self.to_mcstas().mc_inst
    #     instr_txt = mcstas_obj.read_instrument_file()
    #     with open(filename, 'w') as f:
    #         f.write(instr_txt)ouchtou

    @property
    def name(self):
        try:
            return self.nxs_obj['name'].nxvalue
        except:
            return self._name

    @name.setter
    def name(self, value):
        self._name = value
        try:
            self.nxs_obj['name'] = NXfield(value=value)
        except:
            pass

    @classmethod
    def from_mccode(cls, mccode_instr, detector_dat=None, ei=None, only_nx=True):
        from .mccode import NXMcCode
        nxs_obj = NXMcCode(mccode_instr).instrument(only_nx=only_nx)
        nxs_obj['name'] = NXfield(value=mccode_instr.name)
        return cls(nxs_obj, detector_dat, ei)

    @classmethod
    def from_mcstasscript(cls, mss_obj, detector_dat=None, ei=None, only_nx=True):
        nxs_obj = NXMcStas(mss_obj).NXinstrument(only_nx=only_nx)
        nxs_obj['name'] = NXfield(value=mss_obj.name)
        return cls(nxs_obj, detector_dat, ei)

    @classmethod
    def from_mcstas(cls, infile, detector_dat=None, ei=None, only_nx=True):
        mcstas_obj = get_instr(infile)
        nxs_obj = NXMcStas(mcstas_obj).NXinstrument(only_nx=only_nx)
        nxs_obj['name'] = NXfield(value=mcstas_obj.name)
        return cls(nxs_obj, detector_dat, ei)

    @classmethod
    def from_nxs(cls, infile, detector_dat=None, ei=None):
        return cls(nxload(infile), detector_dat, ei)
