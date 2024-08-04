import shutil
import unittest
import tempfile
import os
from config_parser import ConfigParser
from schema import SchemaError


class TestConfigParser(unittest.TestCase):
	def setUp(self):
	    self.temp_dir = tempfile.mkdtemp(dir='/tmp')
	
	def tearDown(self):
		shutil.rmtree(self.temp_dir)
	
	def create_config_file(self, content):
		config_file = os.path.join(self.temp_dir, 'config.yaml')
		with open(config_file, 'w') as f:
			f.write(content)
		return config_file
	
	def test_parse_valid_config(self):
		config_content = """
        programs:
          test_program:
            cmd: "echo hello"
        """
		config_file = self.create_config_file(config_content)
		parser = ConfigParser(config_file)
		config = parser.parse()
		
		self.assertIn('test_program', config['programs'])
		self.assertEqual(config['programs']['test_program']['cmd'], 'echo hello')
		self.assertEqual(config['programs']['test_program']['numprocs'], 1)  # default value
	
	def test_parse_invalid_config(self):
		config_content = """
        programs:
          test_program:
            invalid_key: "value"
        """
		config_file = self.create_config_file(config_content)
		parser = ConfigParser(config_file)
		
		with self.assertRaises(SchemaError):
			parser.parse()
	
	def test_apply_defaults(self):
		config = {
			'programs': {
				'test_program': {
					'cmd': 'echo hello'
				}
			}
		}
		parser = ConfigParser('')  # file path is not used in this test
		config_with_defaults = parser.apply_defaults(config)
		
		self.assertEqual(config_with_defaults['programs']['test_program']['numprocs'], 1)
		self.assertEqual(config_with_defaults['programs']['test_program']['umask'], '022')
		self.assertEqual(config_with_defaults['programs']['test_program']['autostart'], True)
	
	def test_validate_config_valid(self):
		config = {
			'programs': {
				'test_program': {
					'cmd': 'echo hello',
					'numprocs': 2,
					'umask': '022',
					'autostart': False,
					'autorestart': 'always',
					'exitcodes': [0, 1],
					'startretries': 3,
					'starttime': 5,
					'stopsignal': 'TERM',
					'stoptime': 10,
					'stdout': '/tmp/test.log',
					'stderr': '/tmp/test.err',
					'env': {'TEST': 'value'}
				}
			}
		}
		parser = ConfigParser('')  # file path is not used in this test
		parser.validate_config(config)  # Should not raise an exception
	
	def test_validate_config_invalid(self):
		config = {
			'programs': {
				'test_program': {
					'cmd': 'echo hello',
					'numprocs': 0,  # Invalid: should be > 0
					'umask': '0222',  # Invalid: should be 3 digits
					'autorestart': 'invalid',  # Invalid: not in allowed values
					'stopsignal': 'INVALID',  # Invalid: not in allowed values
				}
			}
		}
		parser = ConfigParser('')  # file path is not used in this test
		with self.assertRaises(SchemaError):
			parser.validate_config(config)
	
	def test_parse_with_env_variables(self):
		config_content = """
        programs:
          test_program:
            cmd: "echo hello"
            env:
              TEST_VAR: "test_value"
              ANOTHER_VAR: "another_value"
        """
		config_file = self.create_config_file(config_content)
		parser = ConfigParser(config_file)
		config = parser.parse()
		
		self.assertEqual(config['programs']['test_program']['env']['TEST_VAR'], 'test_value')
		self.assertEqual(config['programs']['test_program']['env']['ANOTHER_VAR'], 'another_value')


if __name__ == '__main__':
	unittest.main()