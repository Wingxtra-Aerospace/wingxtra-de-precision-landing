import ast
import pathlib
import types
import unittest


class DatabusParseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src_path = pathlib.Path('src/wingxtra_pl/main.py')
        source = src_path.read_text(encoding='utf-8')
        tree = ast.parse(source)
        fn_nodes = [
            n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name in {'_parse_port', '_parse_host'}
        ]
        mod = types.ModuleType('parse_funcs')
        mod_ast = ast.Module(body=fn_nodes, type_ignores=[])
        exec(compile(mod_ast, str(src_path), 'exec'), mod.__dict__)
        cls.parse_port = staticmethod(mod._parse_port)
        cls.parse_host = staticmethod(mod._parse_host)

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


if __name__ == '__main__':
    unittest.main()
