import os
from unittest_utils import PeakRDLTestcase


class TestInstance(PeakRDLTestcase):

    def rdl_file(self):
        return os.path.join(self.testdata_dir, "instance.rdl")

    def test_no_instance_is_unchanged(self):
        self.run_commandline(['dump', self.rdl_file(), '--top', 'instance_top'])
        captured = self.capsys.readouterr()
        self.assertIn("instance_top.u_narrow.r1", captured.out)
        self.assertIn("instance_top.u_wide.r1", captured.out)
        self.assertIn("instance_top.top_reg", captured.out)

    def test_instance_reroots(self):
        self.run_commandline([
            'dump', self.rdl_file(), '--top', 'instance_top',
            '--instance', 'u_narrow',
        ])
        captured = self.capsys.readouterr()
        self.assertIn("u_narrow.r1", captured.out)
        self.assertNotIn("u_wide", captured.out)
        self.assertNotIn("top_reg", captured.out)

    def test_instance_honours_rdl_parameter_override(self):
        self.run_commandline([
            'dump', self.rdl_file(), '--top', 'instance_top',
            '--instance', 'u_narrow', '-F',
        ])
        narrow = self.capsys.readouterr().out

        self.run_commandline([
            'dump', self.rdl_file(), '--top', 'instance_top',
            '--instance', 'u_wide', '-F',
        ])
        wide = self.capsys.readouterr().out

        self.assertIn("[1:0] val", narrow)   # FIELD_WIDTH=2
        self.assertIn("[6:0] val", wide)     # FIELD_WIDTH=7

    def test_instance_honours_propagated_parameter(self):
        # A parameter set at a parent and propagated down is inherited, which
        # --top on the leaf type would lose.
        self.run_commandline([
            'dump', self.rdl_file(), '--top', 'instance_top',
            '--instance', 'u_wrap.u_leaf', '-F',
        ])
        captured = self.capsys.readouterr()
        self.assertIn("[8:0] val", captured.out)   # FIELD_WIDTH=9

        self.run_commandline(['dump', self.rdl_file(), '--top', 'instance_block', '-F'])
        captured = self.capsys.readouterr()
        self.assertIn("[0:0] val", captured.out)   # falls back to the default

    def test_instance_nested_path(self):
        self.run_commandline([
            'dump', self.rdl_file(), '--top', 'instance_top',
            '--instance', 'u_sub.u_mid', '-F',
        ])
        captured = self.capsys.readouterr()
        self.assertIn("[3:0] val", captured.out)   # FIELD_WIDTH=4

    def test_instance_bad_path_errors(self):
        self.run_commandline([
            'dump', self.rdl_file(), '--top', 'instance_top',
            '--instance', 'u_nonexistent',
        ], expects_error=True)
        captured = self.capsys.readouterr()
        self.assertIn("no such instance path", captured.err)

    def test_instance_non_addrmap_errors(self):
        self.run_commandline([
            'dump', self.rdl_file(), '--top', 'instance_top',
            '--instance', 'top_reg',
        ], expects_error=True)
        captured = self.capsys.readouterr()
        self.assertIn("not an 'addrmap' component", captured.err)

    def test_instance_array_element(self):
        self.run_commandline([
            'dump', self.rdl_file(), '--top', 'instance_top',
            '--instance', 'u_arr[2]', '-F',
        ])
        captured = self.capsys.readouterr()
        self.assertIn("u_arr[2].r1", captured.out)
        self.assertIn("[2:0] val", captured.out)   # FIELD_WIDTH=3

    def test_instance_malformed_path_errors(self):
        for path in ['.u_narrow', '', ' ']:
            with self.subTest(path=path):
                self.run_commandline([
                    'dump', self.rdl_file(), '--top', 'instance_top',
                    '--instance', path,
                ], expects_error=True)
                captured = self.capsys.readouterr()
                self.assertIn("invalid instance path", captured.err)

    def test_instance_index_out_of_range_errors(self):
        self.run_commandline([
            'dump', self.rdl_file(), '--top', 'instance_top',
            '--instance', 'u_arr[99]',
        ], expects_error=True)
        captured = self.capsys.readouterr()
        self.assertIn("invalid instance path", captured.err)
        self.assertIn("out of range", captured.err)

    def test_instance_wrong_dimensions_errors(self):
        self.run_commandline([
            'dump', self.rdl_file(), '--top', 'instance_top',
            '--instance', 'u_arr[1][2]',
        ], expects_error=True)
        captured = self.capsys.readouterr()
        self.assertIn("invalid instance path", captured.err)
        self.assertIn("dimensions", captured.err)

    def test_instance_array_without_index(self):
        # Array elements are identical apart from address, so an unindexed path
        # exports the shared definition.
        for path in ['u_arr', 'u_arr[]']:
            with self.subTest(path=path):
                self.run_commandline([
                    'dump', self.rdl_file(), '--top', 'instance_top',
                    '--instance', path, '-F',
                ])
                captured = self.capsys.readouterr()
                self.assertIn("u_arr[4].r1", captured.out)
                self.assertIn("[2:0] val", captured.out)   # FIELD_WIDTH=3

    def test_instance_nested_array_without_index(self):
        self.run_commandline([
            'dump', self.rdl_file(), '--top', 'instance_top',
            '--instance', 'u_nest[].u_inner', '-F',
        ])
        captured = self.capsys.readouterr()
        self.assertIn("[5:0] val", captured.out)   # FIELD_WIDTH=6

    def test_instance_parent_ref(self):
        self.run_commandline([
            'dump', self.rdl_file(), '--top', 'instance_top',
            '--instance', 'u_narrow.^.u_wide', '-F',
        ])
        captured = self.capsys.readouterr()
        self.assertIn("u_wide.r1", captured.out)
        self.assertIn("[6:0] val", captured.out)
        self.assertNotIn("u_narrow", captured.out)

    def test_instance_parent_ref_above_top_errors(self):
        for path in ['^', 'u_narrow.^.^']:
            with self.subTest(path=path):
                self.run_commandline([
                    'dump', self.rdl_file(), '--top', 'instance_top',
                    '--instance', path,
                ], expects_error=True)
                captured = self.capsys.readouterr()
                self.assertIn("not within top component", captured.err)
