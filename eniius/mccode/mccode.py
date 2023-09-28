from zenlog import log
from dataclasses import dataclass, field
from mccode.instr import Instr, Orient
from .instr import NXInstr

log.level('error')

@dataclass
class NXMcCode:
    nxinstr: NXInstr
    origin_name: str = None
    indexes: dict[str, int] = field(default_factory=dict)
    orientations: dict[str, Orient] = field(default_factory=dict)

    def __post_init__(self):
        from copy import deepcopy
        for index, instance in enumerate(self.nxinstr.instr.components):
            self.indexes[instance.name] = index
            self.orientations[instance.name] = deepcopy(instance.orientation)
            print(f'\nComponent instance # {index} -- {instance.name}')
            print(repr(instance.orientation))
            print(repr(self.orientations[instance.name]))
        # Attempt to re-center all component dependent orientations on the sample
        if self.origin_name is None:
            samples = [instance for instance in self.nxinstr.instr.components if "samples" == instance.type.category]
        else:
            samples = [instance for instance in self.nxinstr.instr.components if self.origin_name == instance.name]

        if not samples:
            msg = '"sample" category components' if self.origin_name is None else f'component named {self.origin_name}'
            log.warn(f'No {msg} in instrument, using ABSOLUTE positions')
        elif self.origin_name is not None and len(samples) > 1:
            log.error(f'{len(samples)} components named {self.origin_name}; using the first')
        elif len(samples) > 1:
            log.warn(f'More than one "sample" category component. Using {samples[0].name} for origin name')
        if samples:
            self.origin_name = samples[0].name
            # find the inverse of the position _and_ rotation of the origin sample
            origin_offset = samples[0].orientation.inverse()
            # add this to all components (recentering on the origin)
            for name in self.orientations:
                self.orientations[name] = self.orientations[name] + origin_offset

    def transformations(self, name):
        from .orientation import NXOrient
        return NXOrient(self.nxinstr, self.orientations[name]).transformations(name)

    def component(self, name, only_nx=True):
        """Return a NeXus NXcomponent corresponding to the named McStas component instance"""
        from .instance import NXInstance
        instance = self.nxinstr.instr.components[self.indexes[name]]
        transformations = self.transformations(name)
        nx = NXInstance(self.nxinstr, instance, self.indexes[name], transformations, only_nx=only_nx)
        if transformations and nx.nx['transformations'] != transformations:
            # if the component modifed the transformations group, make sure we don't use our version again
            del self.orientations[name]
        return nx

    def instrument(self, only_nx=True):
        from .instr import NXInstr
        from nexusformat.nexus import NXinstrument
        nx = NXinstrument()  # this is a NeXus class
        nx['mcstas'] = self.nxinstr.to_nx()
        for name in self.indexes:
            nx[name] = self.component(name, only_nx=only_nx).nx

        return nx
