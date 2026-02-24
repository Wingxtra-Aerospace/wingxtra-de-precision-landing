import ast
import os
import pathlib
import types
from types import SimpleNamespace
import unittest


class DatabusParseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src_path = pathlib.Path('src/wingxtra_pl/main.py')
        source = src_path.read_text(encoding='utf-8')
        tree = ast.parse(source)
        fn_nodes = [
            n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name in {'_parse_port', '_parse_host', 'resolve_databus_endpoint'}
        ]
        mod = types.ModuleType('parse_funcs')
        mod.os = os
        mod_ast = ast.Module(body=fn_nodes, type_ignores=[])
        exec(compile(mod_ast, str(src_path), 'exec'), mod.__dict__)
        cls.parse_port = staticmethod(mod._parse_port)
        cls.parse_host = staticmethod(mod._parse_host)
        cls.resolve_databus_endpoint = staticmethod(mod.resolve_databus_endpoint)

    def test_parse_port_accepts_valid_values(self):
        self.assertEqual(self.parse_port('60000', 'env'), 60000)
        self.assertEqual(self.parse_port(14550, 'cli'), 14550)

    def test_parse_port_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            self.parse_port(0, 'env')
        with self.assertRaises(ValueError):
            self.parse_port(70000, 'cfg')

    def test_parse_port_rejects_non_numeric(self):
        with self.assertRaises(ValueError):
            self.parse_port('abc', 'env')

    def test_parse_host_accepts_nonempty(self):
        self.assertEqual(self.parse_host('127.0.0.1', 'env'), '127.0.0.1')
        self.assertEqual(self.parse_host(' localhost ', 'cfg'), 'localhost')

    def test_parse_host_rejects_empty(self):
        with self.assertRaises(ValueError):
            self.parse_host('   ', 'env')

    def test_parse_errors_include_source(self):
        with self.assertRaisesRegex(ValueError, "environment variable DATABUS_PORT"):
            self.parse_port('bad', 'environment variable DATABUS_PORT')
        with self.assertRaisesRegex(ValueError, "--databus-host"):
            self.parse_host('   ', '--databus-host')

    def test_resolve_endpoint_precedence_cli_over_env_over_cfg(self):
        old_host = os.environ.get('DATABUS_HOST')
        old_port = os.environ.get('DATABUS_PORT')
        try:
            os.environ['DATABUS_HOST'] = 'env-host'
            os.environ['DATABUS_PORT'] = '14000'
            cfg = {'mavlink_out': {'databus_host': 'cfg-host', 'databus_port': 15000}}
            args = SimpleNamespace(databus_host='cli-host', databus_port=13000)
            self.assertEqual(self.resolve_databus_endpoint(args, cfg), ('cli-host', 13000))

            args2 = SimpleNamespace(databus_host=None, databus_port=None)
            self.assertEqual(self.resolve_databus_endpoint(args2, cfg), ('env-host', 14000))

            os.environ.pop('DATABUS_HOST', None)
            os.environ.pop('DATABUS_PORT', None)
            self.assertEqual(self.resolve_databus_endpoint(args2, cfg), ('cfg-host', 15000))
        finally:
            if old_host is None:
                os.environ.pop('DATABUS_HOST', None)
            else:
                os.environ['DATABUS_HOST'] = old_host
            if old_port is None:
                os.environ.pop('DATABUS_PORT', None)
            else:
                os.environ['DATABUS_PORT'] = old_port

    def test_resolve_rejects_invalid_cli_port(self):
        cfg = {'mavlink_out': {'databus_host': 'cfg-host', 'databus_port': 15000}}
        args = SimpleNamespace(databus_host='cli-host', databus_port=70000)
        with self.assertRaisesRegex(ValueError, "--databus-port"):
            self.resolve_databus_endpoint(args, cfg)

    def test_resolve_rejects_invalid_env_port(self):
        old_port = os.environ.get('DATABUS_PORT')
        old_host = os.environ.get('DATABUS_HOST')
        try:
            os.environ['DATABUS_HOST'] = 'env-host'
            os.environ['DATABUS_PORT'] = 'abc'
            cfg = {'mavlink_out': {'databus_host': 'cfg-host', 'databus_port': 15000}}
            args = SimpleNamespace(databus_host=None, databus_port=None)
            with self.assertRaisesRegex(ValueError, "environment variable DATABUS_PORT"):
                self.resolve_databus_endpoint(args, cfg)
        finally:
            if old_port is None:
                os.environ.pop('DATABUS_PORT', None)
            else:
                os.environ['DATABUS_PORT'] = old_port
            if old_host is None:
                os.environ.pop('DATABUS_HOST', None)
            else:
                os.environ['DATABUS_HOST'] = old_host

    def test_resolve_fails_when_no_explicit_endpoint(self):
        old_port = os.environ.get('DATABUS_PORT')
        old_host = os.environ.get('DATABUS_HOST')
        try:
            os.environ.pop('DATABUS_PORT', None)
            os.environ.pop('DATABUS_HOST', None)
            cfg = {'mavlink_out': {'databus_host': None, 'databus_port': None}}
            args = SimpleNamespace(databus_host=None, databus_port=None)
            with self.assertRaisesRegex(ValueError, "No runtime endpoint discovery is performed"):
                self.resolve_databus_endpoint(args, cfg)
        finally:
            if old_port is None:
                os.environ.pop('DATABUS_PORT', None)
            else:
                os.environ['DATABUS_PORT'] = old_port
            if old_host is None:
                os.environ.pop('DATABUS_HOST', None)
            else:
                os.environ['DATABUS_HOST'] = old_host


if __name__ == '__main__':
    unittest.main()
