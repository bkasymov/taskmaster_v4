import unittest
from unittest.mock import MagicMock, patch
from io import StringIO
import sys

from control_shell import ControlShell


class TestControlShell(unittest.TestCase):
	def setUp(self):
		self.taskmaster_mock = MagicMock()
		self.shell = ControlShell(self.taskmaster_mock)
	
	def test_do_status_all(self):
		self.taskmaster_mock.status.return_value = {
			"program1": [{"pid": 123, "cmd": "test", "status": "running", "restarts": 0, "uptime": 60}],
			"program2": [{"pid": 456, "cmd": "test2", "status": "stopped", "restarts": 1, "uptime": 30}]
		}
		self.taskmaster_mock.config = {"programs": {"program1": {}, "program2": {}}}
		
		with patch('sys.stdout', new=StringIO()) as fake_out:
			self.shell.do_status("")
			output = fake_out.getvalue()
		
		self.assertIn("program1", output)
		self.assertIn("program2", output)
		self.assertIn("123", output)
		self.assertIn("456", output)
	
	def test_do_status_specific_program(self):
		self.taskmaster_mock.status.return_value = {
			"program1": [{"pid": 123, "cmd": "test", "status": "running", "restarts": 0, "uptime": 60}]
		}
		self.taskmaster_mock.config = {"programs": {"program1": {}}}
		
		with patch('sys.stdout', new=StringIO()) as fake_out:
			self.shell.do_status("program1")
			output = fake_out.getvalue()
		
		self.assertIn("program1", output)
		self.assertIn("123", output)
		self.assertNotIn("program2", output)
	
	def test_do_start_all(self):
		self.taskmaster_mock.status.return_value = {
			"program1": [],
			"program2": []
		}
		
		with patch('sys.stdout', new=StringIO()) as fake_out:
			self.shell.do_start("all")
		
		self.taskmaster_mock.start_program.assert_any_call("program1")
		self.taskmaster_mock.start_program.assert_any_call("program2")
	
	def test_do_start_specific_program(self):
		with patch('sys.stdout', new=StringIO()) as fake_out:
			self.shell.do_start("program1")
		
		self.taskmaster_mock.start_program.assert_called_once_with("program1")
	
	def test_do_stop(self):
		with patch('sys.stdout', new=StringIO()) as fake_out:
			self.shell.do_stop("program1")
		
		self.taskmaster_mock.stop_program.assert_called_once_with("program1")
	
	def test_do_restart(self):
		with patch('sys.stdout', new=StringIO()) as fake_out:
			self.shell.do_restart("program1")
		
		self.taskmaster_mock.restart_program.assert_called_once_with("program1")
	
	def test_do_reload(self):
		with patch('sys.stdout', new=StringIO()) as fake_out:
			self.shell.do_reload("")
		
		self.taskmaster_mock.reload_config.assert_called_once()
	
	def test_do_quit(self):
		result = self.shell.do_quit("")
		self.assertTrue(result)
		self.taskmaster_mock.stop_all_programs.assert_called_once()
	
	def test_do_cat(self):
		self.taskmaster_mock.config = {
			"programs": {
				"program1": {"cmd": "test", "numprocs": 1}
			}
		}
		
		with patch('sys.stdout', new=StringIO()) as fake_out:
			self.shell.do_cat("program1")
			output = fake_out.getvalue()
		
		self.assertIn("program1", output)
		self.assertIn("cmd: test", output)
		self.assertIn("numprocs: 1", output)
	
	def test_command_history(self):
		self.shell.precmd("status")
		self.shell.precmd("start program1")
		
		with patch('sys.stdout', new=StringIO()) as fake_out:
			self.shell.do_history("")
			output = fake_out.getvalue()
		
		self.assertIn("status", output)
		self.assertIn("start program1", output)


if __name__ == '__main__':
	unittest.main()