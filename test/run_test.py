#!/usr/bin/env python3
import unittest
import numpy as np
import tempfile
import os
import nexusformat.nexus as nexus
import eniius
import json

class EniiusTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.rootdir = os.path.dirname(os.path.realpath(eniius.__file__))
        cls.detdat = os.path.join(cls.rootdir, 'instruments', 'detector.dat')

    @classmethod
    def tearDownClass(cls):
        with open('success', 'w') as f:
            f.write('success')
        cls.tmpdir.cleanup()

    # def test_save_nxs_from_mcstas(self):
    #     nxsfile = os.path.join(self.tmpdir.name, 'mcstas.nxs')
    #     instrfile = os.path.join(self.rootdir, 'instruments', 'isis_merlin.instr')
    #     wrapper = eniius.Eniius.from_mcstas(instrfile, self.detdat)
    #     wrapper.to_icp(nxsfile)
    #     with nexus.nxload(nxsfile) as nxs:
    #         self.assertTrue('mantid_workspace_1' in nxs)
    #         self.assertTrue('instrument' in nxs['mantid_workspace_1'])
    #         nxinst = nxs['mantid_workspace_1/instrument']
    #         self.assertTrue(isinstance(nxinst, nexus.NXinstrument))
    #         self.assertTrue('physical_detectors' in nxinst)
    #         self.assertTrue('physical_monitors' in nxinst)
    #         comp1 = nxinst[dir(nxinst)[0]]
    #         self.assertTrue('mcstas' in comp1)
    #         self.assertTrue(isinstance(comp1['mcstas'].nxvalue, str))
    #         self.assertTrue(isinstance(comp1['mcstas']._value, np.ndarray))
    #         self.assertTrue(isinstance(comp1['mcstas']._value, np.ndarray))
    #         self.assertEqual(comp1['mcstas']._value.dtype.kind, 'S')
    #         self.assertTrue('transformations' in comp1)
    #         self.assertTrue(isinstance(comp1['transformations'], nexus.NXtransformations))

    # def test_save_nxspe_from_merlin(self):
    #     Ei = 180.
    #     nxspefile = os.path.join(self.tmpdir.name, 'horace.nxspe')
    #     wrapper = eniius.Eniius(eniius.horace.merlin_instrument(Ei), self.detdat)
    #     wrapper.to_nxspe(nxspefile)
    #     with nexus.nxload(nxspefile) as nxspe:
    #         root = nxspe[dir(nxspe)[0]]
    #         self.assertTrue('NXSPE_info' in root)
    #         self.assertEqual(root['NXSPE_info/fixed_energy'].nxvalue, Ei)
    #         self.assertTrue('instrument' in root)
    #         self.assertTrue('fermi' in root['instrument'])
    #         self.assertEqual(root['instrument/fermi/energy'].nxvalue, Ei)
    #         self.assertTrue('sample' in root)


    # def test_save_nxspe_from_let(self):
    #     Ei = 3.7
    #     nxspefile = os.path.join(self.tmpdir.name, 'horace.nxspe')
    #     wrapper = eniius.Eniius(eniius.horace.let_instrument(Ei), self.detdat)
    #     wrapper.to_nxspe(nxspefile)
    #     with nexus.nxload(nxspefile) as nxspe:
    #         root = nxspe[dir(nxspe)[0]]
    #         self.assertTrue('NXSPE_info' in root)
    #         self.assertEqual(root['NXSPE_info/fixed_energy'].nxvalue, Ei)
    #         self.assertTrue('instrument' in root)
    #         self.assertTrue('fermi' in root['instrument'])
    #         self.assertEqual(root['instrument/fermi/energy'].nxvalue, Ei)
    #         self.assertTrue('sample' in root)

    # def test_save_json_from_mcstas(self):
    #     jsonfile = os.path.join(self.tmpdir.name, 'mcstas.json')
    #     instrfile = os.path.join(self.rootdir, 'instruments', 'isis_merlin.instr')
    #     wrapper = eniius.Eniius.from_mcstas(instrfile, self.detdat)
    #     wrapper.to_json(jsonfile)
    #     with open(jsonfile) as file:
    #         data = json.load(file)
    #
    #     nx_class_fields = ('name', 'type', 'children', 'attributes')
    #
    #     self.assertTrue(len(data) == 1)
    #     self.assertTrue('children' in data)
    #     children = data['children']
    #     self.assertTrue(len(children) == 1)
    #
    #     root = children[0]
    #     for field in nx_class_fields:
    #         self.assertTrue(field in root)
    #     self.assertTrue('entry' == root['name'])
    #     self.assertTrue(len(root['children']) == 1)
    #     self.assertTrue(len(root['attributes']) == 1)
    #     self.assertTrue(root['attributes'][0]['values'] == 'NXentry')
    #
    #     instrument = root['children'][0]
    #     for field in nx_class_fields:
    #         self.assertTrue(field in instrument)
    #     self.assertTrue(len(instrument['children']) == 14)
    #     self.assertTrue(len(instrument['attributes']) == 1)
    #     self.assertTrue(instrument['attributes'][0]['values'] == 'NXinstrument')
    #
    #     named_children = [x for x in instrument['children'] if 'name' in x]
    #     self.assertTrue(len(named_children) == 13)
    #     self.assertTrue('mcstas' in [x['name'] for x in named_children])
    #     mcstas_children = [x for x in named_children if x['name'] == 'mcstas']
    #     self.assertTrue(len(mcstas_children) == 1)
    #
    #     for field in nx_class_fields:
    #         self.assertTrue(field in mcstas_children[0])
    #     named_mcstas_children = [x for x in mcstas_children[0]['children'] if 'name' in x]
    #     self.assertTrue('declare' in [x['name'] for x in named_mcstas_children])
    #     declare = [x for x in named_mcstas_children if x['name'] == 'declare']
    #     self.assertTrue(len(declare) == 1)
    #
    #     for field in nx_class_fields:
    #         self.assertTrue(field in declare[0])
    #     parameters = declare[0]['children']
    #     for name in ('slit_curv', 'num_slits', 'width', 'len', 'phase_time', 'E_min', 'E_max'):
    #         self.assertTrue(len([x for x in parameters if x['config']['name'] == name]) == 1)
    #     # Check that extraneous empty parameters do not get saved:
    #     self.assertTrue(len([x for x in parameters if x['config']['name'] == '']) == 0)

    def test_save_slit_json_from_mcstas(self):
        from mccode.loader import load_mcstas_instr
        jsonfile = os.path.join(self.tmpdir.name, 'mcstas.json')
        instr_file = os.path.join(os.path.dirname(__file__), 'one_slit_explicit.instr')
        instr = load_mcstas_instr(instr_file)

        # Normally Eniius sets the sample position to be the origin, but that complicates comparing positions:
        origin = 'Origin'
        positions = {'Origin': (0, 0, 0), 'slit': (0., 0., 10.), 'sample': (0., 0., 20.)}

        wrapper = eniius.Eniius.from_mccode(instr, origin=origin)
        wrapper.to_json(jsonfile)
        with open(jsonfile) as file:
            data = json.load(file)

        nx_class_fields = ('name', 'type', 'children', 'attributes')

        self.assertTrue(len(data) == 1)
        self.assertTrue('children' in data)
        children = data['children']
        self.assertTrue(len(children) == 1)

        root = children[0]
        for field in nx_class_fields:
            self.assertTrue(field in root)
        self.assertTrue('entry' == root['name'])
        self.assertTrue(len(root['children']) == 1)
        self.assertTrue(len(root['attributes']) == 1)
        self.assertTrue(root['attributes'][0]['values'] == 'NXentry')

        instrument = root['children'][0]
        for field in nx_class_fields:
            self.assertTrue(field in instrument)
        self.assertTrue(len(instrument['children']) == 5)
        self.assertTrue(len(instrument['attributes']) == 1)
        self.assertTrue(instrument['attributes'][0]['values'] == 'NXinstrument')

        named_children = [x for x in instrument['children'] if 'name' in x]
        # There _was_ an instrument-level child named 'mcstas' before, but it has been removed.
        # Whether this was intentional or not is now debatable.
        # There is now one named child per component instance in the instrument
        self.assertEqual(len(instr.components), len(named_children))

        # self.assertTrue(len(named_children) == 4)
        # self.assertTrue('mcstas' in [x['name'] for x in named_children])
        # mcstas_children = [x for x in named_children if x['name'] == 'mcstas']
        # self.assertTrue(len(mcstas_children) == 1)
        #
        # for field in nx_class_fields:
        #     self.assertTrue(field in mcstas_children[0])
        # named_mcstas_children = [x for x in mcstas_children[0]['children'] if 'name' in x]
        # self.assertFalse('declare' in [x['name'] for x in named_mcstas_children])

        for instance, child in zip(instr.components, named_children):
            transformations = [x for x in child['children'] if 'name' in x and x['name'] == 'transformations']
            # extract depends_on from one of the ... 'module' datasets?! ...
            if not len(transformations) and origin == instance.name:
                # A missing transformation is an implicit position at the origin?
                continue
            self.assertEqual(len(transformations), 1)
            transformations = transformations[0]
            self.assertTrue('children' in transformations)
            self.assertTrue(len(transformations['children']) == 1)
            self.assertTrue('module' in transformations['children'][0])
            self.assertEqual('dataset', transformations['children'][0]['module'])
            module = transformations['children'][0]
            self.assertTrue('config' in module)
            self.assertTrue('attributes' in module)
            config = module['config']
            self.assertTrue('values' in config)
            distance = config['values']
            attributes = module['attributes']
            named_attributes = {x['name']: x for x in attributes if 'name' in x}
            self.assertTrue('vector' in named_attributes)
            self.assertTrue('depends_on' in named_attributes)
            self.assertTrue('transformation_type' in named_attributes)
            self.assertTrue('units' in named_attributes)
            self.assertTrue(all('values' in x for x in named_attributes.values()))
            vector = named_attributes['vector']['values']
            depends_on = named_attributes['depends_on']['values']
            transformation_type = named_attributes['transformation_type']['values']
            units = named_attributes['units']['values']
            self.assertEqual('translation', transformation_type)
            self.assertEqual('m', units)
            self.assertEqual(3, len(vector))
            self.assertEqual('.', depends_on)

            position = instance.orientation.position()
            # The next three tests ensure McCode returns the correct component positions:
            self.assertAlmostEqual(positions[instance.name][0], position.x)
            self.assertAlmostEqual(positions[instance.name][1], position.y)
            self.assertAlmostEqual(positions[instance.name][2], position.z)
            # And these three tests ensure Eniius is translating to JSON/NeXus correctly
            # The vector is the _direction_ of the translation, not the position itself
            self.assertAlmostEqual(position.length(), distance)
            direction = position / position.length()
            self.assertAlmostEqual(direction.x, vector[0])
            self.assertAlmostEqual(direction.y, vector[1])
            self.assertAlmostEqual(direction.z, vector[2])

    def test_simple_positioning(self):
        from math import pi, cos, sin
        from mccode.loader import parse_mcstas_instr
        from mccode.common import Expr
        from mccode.instr.orientation import Vector
        instr_contents = """DEFINE INSTRUMENT slightly_more_complex() TRACE
        COMPONENT origin = Arm() AT (0, 0, 0) ABSOLUTE
        COMPONENT guide_start = Arm() AT (0.01277, 0, 1.930338) RELATIVE origin ROTATED (0, -0.56, 0) RELATIVE origin
        COMPONENT guide = Arm() AT (0, 0, 0) RELATIVE guide_start
        COMPONENT guide_end = Arm() AT (0, 0, 4.33) RELATIVE guide
        END
        """
        instr = parse_mcstas_instr(instr_contents)
        origin = 'Origin'
        positions = {'origin': (0, 0, 0), 'guide_start': (0.01277, 0, 1.930338), 'guide': (0.01277, 0, 1.930338),
                     'guide_end': (0.01277 - 4.33 * sin(pi / 180 * 0.56), 0, 1.930338 + 4.33 * cos(pi / 180 * 0.56))}
        positions = {k: Vector(*[Expr.float(x) for x in v]) for k, v in positions.items()}
        for instance in instr.components:
            self.assertEqual(positions[instance.name], instance.orientation.position())
            self.assertEqual(positions[instance.name], instance.orientation.position('axes'))
            self.assertEqual(positions[instance.name], instance.orientation.position('coordinates'))
        pos_hat = (0.006615277, 0, 0.999978)
        pos = instr.components[2].orientation.position()
        distance = pos.length()
        vector = pos / distance
        self.assertAlmostEqual(vector.x, pos_hat[0], 6)
        self.assertAlmostEqual(vector.y, pos_hat[1], 6)
        self.assertAlmostEqual(vector.z, pos_hat[2], 6)
        self.assertAlmostEqual(distance, 1.930380239005777, 6)

        # Now verify that the wrapped positions are correct:
        wrapper = eniius.Eniius.from_mccode(instr, origin=origin)

        # Pull out the translation and rotation:
        self.assertEqual('transformations/guide_0_r', str(wrapper.nxs_obj['guide/depends_on']))
        trans = wrapper.nxs_obj['guide/transformations/guide_0_t']
        rot = wrapper.nxs_obj['guide/transformations/guide_0_r']

        self.assertEqual(trans.attrs['depends_on'], '.')
        self.assertEqual(trans.attrs['transformation_type'], 'translation')
        self.assertEqual(trans.attrs['units'], 'm')
        self.assertAlmostEqual(trans.attrs['vector'][0], pos_hat[0], 6)
        self.assertAlmostEqual(trans.attrs['vector'][1], pos_hat[1], 6)
        self.assertAlmostEqual(trans.attrs['vector'][2], pos_hat[2], 6)
        self.assertAlmostEqual(trans, distance)

        self.assertAlmostEqual(rot, -0.56, 3)
        self.assertEqual(rot.attrs['depends_on'], 'guide_0_t')
        self.assertEqual(rot.attrs['transformation_type'], 'rotation')
        self.assertEqual(rot.attrs['units'], 'degrees')


if __name__ == '__main__':
    unittest.main()

