from zenlog import log
from dataclasses import dataclass
from typing import Union
from mccode_antlr.instr import Instance
from mccode_antlr.common import Expr
from nexusformat.nexus import NXfield
from .instr import NXInstr


COMPONENT_GROUP_TO_NEXUS = dict(Guide='NXguide', Collimator='NXcollimator')
COMPONENT_CATEGORY_TO_NEXUS = dict(sources='NXmoderator', monitors='NXdetector')
COMPONENT_TYPE_NAME_TO_NEXUS = dict(
    DiskChopper='NXdisk_chopper',
    FermiChopper='NXfermi_chopper',
    FermiChopper_ILL='NXfermi_chopper',
    Fermi_chop2a='NXfermi_chopper',
    Filter_gen='NXfilter',
    Filter_graphite='NXfilter',
    Elliptic_guide_gravity='NXguide',
    Mirror='NXmirror',
    Monochromator_flat='NXmonochromator',
    Monochromator_curved='NXmonochromator',
    Monochromator_pol='NXpolarizer',
    Pol_SF_ideal='NXflipper',
    Pol_bender='NXpolarizer',
    Pol_mirror='NXpolarizer',
    SNS_source='NXmoderator',
    SNS_source_analytic='NXmoderator',
    Source_pulsed='NXmoderator',
    Selector='NXvelocity_selector',
    V_selector='NXvelocity_selector',
    ViewModISIS='NXmoderator',
)
# Each entry here maps a NeXus component to a McStas component
# The second element is a mapping of NeXus component parameters to McStas parameters
# The third element is a mapping of NeXus component parameters to McStas position paramters
NEXUS_TO_COMPONENT = dict(
    NXaperture=['Slit', {'x_gap': 'xwidth', 'y_gap': 'yheight'}, ],
    NXcollimator=['Collimator_linear', {'divergence_x': 'divergence', 'divergence_y': 'divergenceV'}, ],
    NXdetector=['Monitor_nD', {}, ],
    NXdisk_chopper=['DiskChopper', {'slits': 'nslit', 'rotation_speed': 'nu', 'radius': 'radius', 'slit_angle': 'theta_0', 'slit_height': 'yheight', 'phase': 'phase'}, ],
    NXfermi_chopper=['FermiChopper', {'rotation_speed': 'nu', 'radius': 'radius', 'slit': 'w', 'r_slit': 'curvature', 'number': 'nslit', 'width': 'xwidth', 'height': 'yheight'}, {'distance': 'set_AT'}, ],
    NXguide=['Guide', {'m_value': 'm'}, ],
    NXslit=['Slit', {'x_gap': 'xwidth', 'y_gap': 'yheight'}, ],
    NXsample=['Incoherent', {}, ],
    NXmoderator=['Moderator', {}, {'distance': 'set_AT'}, ]
)


@dataclass
class NXInstance:
    instr: NXInstr
    obj: Instance
    index: int
    transforms: dict[str, NXfield]
    only_nx: bool
    nx: Union[None, dict, NXfield] = None

    def parameter(self, name):
        """
        Pull out a named instance parameter -- if it's value is not a constant, attempt to evaluate it
        using the Instr declare and initialize sections
        """
        par = self.obj.get_parameter(name)
        if par is None:
            log.warn(f'It appears that {self.obj.type.name} does not define the parameter {name}')
            return None

        expr = par.value
        # log.info(f'get parameter {name} which is {par}  and expr {repr(expr)}')
        if expr.is_constant:
            return expr.value

        # Check if the expression depends on one of the instrument parameters (and thus needs a NXlog stream)
        # First resolve any declare-variables
        evaluated = expr.evaluate(self.instr.declared)
        if evaluated.is_constant:
            return evaluated.value
        # Then check for instrument parameter(s)
        dependencies = [par for par in self.instr.instr.parameters if evaluated.depends_on(par.name)]
        log.warn(f'The parameter {name} for component instance {self.obj.name} '
                 f' depends on an instrument parameter and has value {expr}')
        return evaluated

    def expr2nx(self, expr: Expr):
        return self.instr.expr2nx(expr)

    def nx_parameter(self, name):
        """Retrieve the named instance parameter and convert to a NeXus compatible value"""
        return self.expr2nx(self.parameter(name))

    def make_nx(self, nx_class, *args, **kwargs):
        return self.instr.make_nx(nx_class, *args, **kwargs)

    def __post_init__(self):
        from json import dumps
        from nexusformat.nexus import NXtransformations
        from eniius.utils import outer_transform_dependency, mccode_component_eniius_data
        self.nx = getattr(self, self.obj.type.name, self.default_translation)()
        self.nx['mcstas'] = dumps({'instance': str(self.obj), 'order': self.index})
        if self.transforms:
            self.nx['transformations'] = NXtransformations(**self.transforms)
            most_dependent = outer_transform_dependency(self.nx['transformations'])
            for name, insert in mccode_component_eniius_data(self.obj, only_nx=self.only_nx).items():
                self.nx[name] = insert
                if not hasattr(self.nx[name], 'depends_on'):
                    self.nx[name].attrs['depends_on'] = most_dependent
                most_dependent = outer_transform_dependency(self.nx['transformations'])
            self.nx['depends_on'] = f'transformations/{most_dependent}'

    def get_nx_type(self):
        if self.obj.type.name in COMPONENT_TYPE_NAME_TO_NEXUS:
            return COMPONENT_TYPE_NAME_TO_NEXUS[self.obj.type.name]
        elif self.obj.type.category in COMPONENT_CATEGORY_TO_NEXUS:
            return COMPONENT_CATEGORY_TO_NEXUS[self.obj.type.category]
        if any(self.obj.type.name.startswith(x) for x in COMPONENT_GROUP_TO_NEXUS):
            return [t for k, t in COMPONENT_GROUP_TO_NEXUS.items() if self.obj.type.name.startswith(k)][0]
        return 'NXnote'

    def default_translation(self):
        import nexusformat.nexus as nexus
        nx_type = self.get_nx_type()
        nx_2_mc = NEXUS_TO_COMPONENT.get(nx_type, ({}, {}))[1]
        return getattr(nexus, nx_type)(**{n: self.nx_parameter(m) for n, m in nx_2_mc.items()})

    def Slit(self):
        """The Slit component _must_ define (xmin, xmax) _or_ xwidth, and similarly the y-named parameters"""
        from nexusformat.nexus import NXslit
        if self.obj.defines_parameter('xwidth'):
            x_gap = self.parameter('xwidth')
            x_zero = Expr.float(0)
        else:
            x_gap = self.parameter('xmax') - self.parameter('xmin')
            x_zero = self.parameter('xmax') + self.parameter('xmin')
        if self.obj.defines_parameter('ywidth'):
            y_gap = self.parameter('ywidth')
            y_zero = Expr.float(0)
        else:
            y_gap = self.parameter('ymax') - self.parameter('ymin')
            y_zero = self.parameter('ymax') + self.parameter('ymin')

        if isinstance(x_zero, Expr) or isinstance(y_zero, Expr):
            log.warn(f'{self.obj.name} has a non-constant x or y zero, which requires special handling for NeXus')
        elif abs(x_zero) or abs(y_zero):
            log.warn(f'{self.obj.name} should be translated by [{x_zero}, {y_zero}, 0] via eniius_data METADATA')
        return self.make_nx(NXslit, x_gap=x_gap, y_gap=y_gap)

    def Guide(self):
        from nexusformat.nexus import NXguide
        from eniius.nxoff import NXoff
        off_pars = {k: self.nx_parameter(k) for k in ('l', 'w1', 'h1', 'w2', 'h2')}
        for k in ('w', 'h'):
            off_pars[f'{k}2'] = off_pars[f'{k}1'] if off_pars[f'{k}2'] == 0 else off_pars[f'{k}2']
        return self.make_nx(NXguide, m_value=self.parameter('m'), geometry=NXoff.from_wedge(**off_pars).to_nexus())

    Guide_channeled = Guide
    Guide_gravity = Guide
    Guide_simple = Guide
    Guide_wavy = Guide

    def Collimator_linear(self):
        from nexusformat.nexus import NXcollimator
        from eniius.nxoff import NXoff
        pars = {k: self.nx_parameter(v) for k, v in (('l', 'length'), ('w1', 'xwidth'), ('h1', 'yheight'))}
        return self.make_nx(NXcollimator, divergence_x=self.parameter('divergence'),
                            divergence_y=self.parameter('divergenceV'),
                            geometry=NXoff.from_wedge(**pars).to_nexus())

    def DiskChopper(self):
        from nexusformat.nexus import NXdisk_chopper
        mpars = {k: self.parameter(k) for k in ('nslit', 'nu', 'radius', 'theta_0', 'phase', 'yheight')}
        pars = {'slits': mpars['nslit'],
                'rotation_speed': self.make_nx(NXfield, mpars['nu'], units='Hz'),
                'radius': self.make_nx(NXfield, mpars['radius'], units='m'),
                'slit_angle': self.make_nx(NXfield, mpars['theta_0'], units='degrees'),
                'phase': self.make_nx(NXfield, mpars['phase'], units='degrees'),
                'slit_height': self.make_nx(NXfield, mpars['yheight'] if mpars['yheight'] else mpars['radius'], units='m')}
        nslit, delta = mpars['nslit'], mpars['theta_0'] / 2.0
        slit_edges = [y * 360.0 / nslit + x for y in range(int(nslit)) for x in (-delta, delta)]
        nx_slit_edges = [self.expr2nx(se) for se in slit_edges]
        return self.make_nx(NXdisk_chopper, slit_edges=NXfield(nx_slit_edges, units='degrees'), **pars)

    def Elliptic_guide_gravity(self):
        from nexusformat.nexus import NXguide
        from numpy import arange, sqrt
        from eniius.nxoff import NXoff
        if not '"mid"' == self.obj.get_parameter('dimensionsAt'):
            log.warn('Only midpoint geometry supported by Elliptic_guide_gravity translator')
            log.info(f'The current guide has {self.obj.get_parameter("dimensionsAt")} specified')

        def ellipse_width(minor, distance, at):
            major = sqrt((distance / 2) ** 2 + minor ** 2)
            return 0 if abs(at) > major else minor * sqrt(1 - (at / major) ** 2)

        pars = dict(xw='xwidth', xi='linxw', xo='loutxw', yw='yheight', yi='linyh', yo='loutyh', l='l')
        p = {k: self.parameter(v) for k, v in pars.items()}
        n = 10
        rings = arange(n + 1) / n
        faces, vertices = [], []
        for x in rings:
            w = ellipse_width(p['xw'] / 2, p['xi'] + p['l'] + p['xo'], p['xi'] / 2 + (x - 0.5) * p['l'] - p['xo'] / 2)
            h = ellipse_width(p['yw'] / 2, p['yi'] + p['l'] + p['yo'], p['yi'] / 2 + (x - 0.5) * p['l'] - p['yo'] / 2)
            z = x * p['l']
            vertices.extend([[-w, -h, z], [-w, h, z], [w, h, z], [w, -h, z]])

        for i in range(n):
            j0, j1, j2, j3, j4, j5, j6, j7 = [4 * i + k for k in range(8)]
            faces.extend([[j0, j1, j5, j4], [j1, j2, j6, j5], [j2, j3, j7, j6], [j3, j0, j4, j7]])

        nx_vertices = [[self.expr2nx(expr) for expr in vector] for vector in vertices]
        nx_faces = [[self.expr2nx(expr) for expr in face] for face in faces]

        return NXguide(geometry=NXoff(nx_vertices, nx_faces).to_nexus())

