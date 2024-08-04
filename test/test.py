import unittest
import os
import signal
import time
import yaml
from taskmaster import Taskmaster


class TestTaskmaster(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.config_file = 'test_config.yaml'
		cls.create_test_config()
		cls.taskmaster = Taskmaster(cls.config_file)
	
	@classmethod
	def tearDownClass(cls):
		os.remove(cls.config_file)
	
	@classmethod
	def create_test_config(cls):
		config = {
			"programs": {
				"test_program": {
					"cmd": "python -c 'import time; print(\"Running\"); time.sleep(30)'",
					"numprocs": 2,
					"umask": "022",
					"workingdir": "/tmp",
					"autostart": True,
					"autorestart": "unexpected",
					"exitcodes": [0, 2],
					"startretries": 3,
					"starttime": 5,
					"stopsignal": "TERM",
					"stoptime": 10,
					"stdout": "/tmp/test_program.stdout",
					"stderr": "/tmp/test_program.stderr",
					"env": {
						"TEST_VAR": "test_value"
					}
				}
			}
		}
		with open(cls.config_file, 'w') as f:
			yaml.dump(config, f)
	
	def test_control_shell(self):
		# Test start, stop, and restart commands
		self.taskmaster.control_shell.do_start('test_program')
		status = self.taskmaster.status()
		self.assertEqual(len(status['test_program']), 2)
		self.assertEqual(status['test_program'][0]['status'], 'running')
		
		self.taskmaster.control_shell.do_stop('test_program')
		status = self.taskmaster.status()
		self.assertEqual(status['test_program'][0]['status'], 'stopped')
		
		self.taskmaster.control_shell.do_restart('test_program')
		status = self.taskmaster.status()
		self.assertEqual(status['test_program'][0]['status'], 'running')
	
	def test_configuration_loading(self):
		config = self.taskmaster.config
		self.assertIn('test_program', config['programs'])
		self.assertEqual(config['programs']['test_program']['numprocs'], 2)
	
	def test_logging(self):
		# Assuming logs are written to a file
		self.taskmaster.control_shell.do_start('test_program')
		time.sleep(1)  # Give some time for logging
		with open('/tmp/taskmaster.log', 'r') as log_file:
			log_content = log_file.read()
		self.assertIn('Started program: test_program', log_content)
	
	def test_hot_reload(self):
		original_config = self.taskmaster.config
		new_config = original_config.copy()
		new_config['programs']['test_program']['numprocs'] = 3
		
		with open(self.config_file, 'w') as f:
			yaml.dump(new_config, f)
		
		self.taskmaster.reload_config()
		self.assertEqual(self.taskmaster.config['programs']['test_program']['numprocs'], 3)
	
	def test_command_execution(self):
		self.taskmaster.control_shell.do_start('test_program')
		time.sleep(1)
		with open('/tmp/test_program.stdout', 'r') as f:
			output = f.read()
		self.assertIn('Running', output)
	
	def test_process_count(self):
		self.taskmaster.control_shell.do_start('test_program')
		status = self.taskmaster.status()
		self.assertEqual(len(status['test_program']), 2)
	
	def test_autostart(self):
		self.taskmaster.process_manager.start_initial_processes()
		status = self.taskmaster.status()
		self.assertIn('test_program', status)
		self.assertEqual(status['test_program'][0]['status'], 'running')
	
	def test_autorestart(self):
		self.taskmaster.control_shell.do_start('test_program')
		initial_pid = self.taskmaster.process_manager.processes['test_program'][0].pid
		os.kill(initial_pid, signal.SIGTERM)
		time.sleep(2)  # Give some time for restart
		new_pid = self.taskmaster.process_manager.processes['test_program'][0].pid
		self.assertNotEqual(initial_pid, new_pid)
	
	def test_exit_codes(self):
		# Modify config to use a script with different exit codes
		self.taskmaster.config['programs']['test_program']['cmd'] = 'python -c "import sys; sys.exit(2)"'
		self.taskmaster.control_shell.do_start('test_program')
		time.sleep(2)  # Give some time for execution and restart
		status = self.taskmaster.status()
		self.assertEqual(status['test_program'][0]['status'], 'running')
	
	def test_start_time(self):
		start_time = time.time()
		self.taskmaster.control_shell.do_start('test_program')
		status = self.taskmaster.status()
		self.assertGreaterEqual(time.time() - start_time,
		                        self.taskmaster.config['programs']['test_program']['starttime'])
	
	def test_stop_signal(self):
		self.taskmaster.control_shell.do_start('test_program')
		start_time = time.time()
		self.taskmaster.control_shell.do_stop('test_program')
		self.assertLessEqual(time.time() - start_time, self.taskmaster.config['programs']['test_program']['stoptime'])
	
	def test_stdout_stderr_redirection(self):
		self.taskmaster.control_shell.do_start('test_program')
		time.sleep(1)
		self.assertTrue(os.path.exists('/tmp/test_program.stdout'))
		self.assertTrue(os.path.exists('/tmp/test_program.stderr'))
	
	def test_env_variables(self):
		self.taskmaster.config['programs']['test_program'][
			'cmd'] = 'python -c "import os; print(os.environ.get(\'TEST_VAR\'))"'
		self.taskmaster.control_shell.do_start('test_program')
		time.sleep(1)
		with open('/tmp/test_program.stdout', 'r') as f:
			output = f.read().strip()
		self.assertEqual(output, 'test_value')
	
	def test_working_directory(self):
		self.taskmaster.config['programs']['test_program']['cmd'] = 'python -c "import os; print(os.getcwd())"'
		self.taskmaster.control_shell.do_start('test_program')
		time.sleep(1)
		with open('/tmp/test_program.stdout', 'r') as f:
			output = f.read().strip()
		self.assertEqual(output, '/tmp')
	
	def test_umask(self):
		self.taskmaster.config['programs']['test_program']['cmd'] = 'python -c "import os; print(oct(os.umask(0)))"'
		self.taskmaster.control_shell.do_start('test_program')
		time.sleep(1)
		with open('/tmp/test_program.stdout', 'r') as f:
			output = f.read().strip()
		self.assertEqual(output, '0o022')


if __name__ == '__main__':
	unittest.main()