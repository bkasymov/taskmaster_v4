import subprocess
import time
import os
import signal
import yaml
import tempfile
import sys


class TaskmasterTester:
	def __init__(self, taskmaster_dir):
		self.taskmaster_dir = taskmaster_dir
		self.taskmaster_process = None
		self.temp_dir = tempfile.mkdtemp()
	
	def start_taskmaster(self, config):
		config_path = os.path.join(self.temp_dir, 'config.yaml')
		with open(config_path, 'w') as f:
			yaml.dump(config, f)
		
		taskmaster_path = os.path.join(self.taskmaster_dir, 'taskmaster.py')
		self.taskmaster_process = subprocess.Popen(
			[sys.executable, taskmaster_path, config_path],
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True,
			cwd=self.taskmaster_dir
		)
		time.sleep(2)  # Give Taskmaster time to start
	
	def stop_taskmaster(self):
		if self.taskmaster_process:
			self.taskmaster_process.terminate()
			self.taskmaster_process.wait()
			self.taskmaster_process = None
	
	def send_command(self, command):
		self.taskmaster_process.stdin.write(command + '\n')
		self.taskmaster_process.stdin.flush()
		time.sleep(1)  # Give Taskmaster time to process the command
	
	def check_process_status(self, program_name):
		self.send_command(f"status {program_name}")
		output = self.taskmaster_process.stdout.readline()
		return "RUNNING" in output
	
	def check_file_content(self, file_path, expected_content):
		with open(file_path, 'r') as f:
			content = f.read()
		return expected_content in content
	
	def run_tests(self):
		print("Starting Taskmaster tests...")
		
		# Test Configuration 1
		config1 = {
			'programs': {
				'echo_test': {
					'cmd': "echo 'Hello, Taskmaster!'",
					'numprocs': 1,
					'autostart': True,
					'autorestart': 'unexpected',
					'exitcodes': [0],
					'startretries': 3,
					'starttime': 1,
					'stopsignal': 'TERM',
					'stoptime': 5,
					'stdout': '/tmp/echo_test.stdout',
					'stderr': '/tmp/echo_test.stderr'
				},
				'sleep_test': {
					'cmd': "sleep 60",
					'numprocs': 2,
					'autostart': False,
					'autorestart': 'never'
				}
			}
		}
		self.start_taskmaster(config1)
		assert self.check_process_status('echo_test'), "echo_test should be running"
		assert not self.check_process_status('sleep_test'), "sleep_test should not be running"
		self.send_command("start sleep_test")
		assert self.check_process_status('sleep_test'), "sleep_test should be running after manual start"
		self.stop_taskmaster()
		
		# Test Configuration 2
		config2 = {
			'programs': {
				'env_test': {
					'cmd': "env",
					'numprocs': 1,
					'autostart': True,
					'autorestart': 'never',
					'stdout': '/tmp/env_test.stdout',
					'stderr': '/tmp/env_test.stderr',
					'env': {
						'TEST_VAR': "Hello from Taskmaster",
						'PATH': "/usr/local/bin:/usr/bin:/bin"
					}
				}
			}
		}
		self.start_taskmaster(config2)
		time.sleep(2)  # Give time for the process to run
		assert self.check_file_content('/tmp/env_test.stdout',
		                               'TEST_VAR=Hello from Taskmaster'), "TEST_VAR not set correctly"
		assert self.check_file_content('/tmp/env_test.stdout',
		                               'PATH=/usr/local/bin:/usr/bin:/bin'), "PATH not set correctly"
		self.stop_taskmaster()
		
		# Add more tests for other configurations...
		
		print("All tests passed successfully!")


if __name__ == "__main__":
	taskmaster_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
	tester = TaskmasterTester(taskmaster_dir)
	tester.run_tests()