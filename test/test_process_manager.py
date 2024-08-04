import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import time
from process_manager import ProcessManager, ProcessInfo

class TestProcessManager(unittest.TestCase):
    def setUp(self):
        self.logger_mock = Mock()
        self.config = {
            "programs": {
                "test_program": {
                    "cmd": "echo 'test'",
                    "numprocs": 1,
                    "autostart": True,
                    "autorestart": "unexpected",
                    "exitcodes": [0],
                    "startretries": 3,
                    "starttime": 1,
                    "stopsignal": "TERM",
                    "stoptime": 2,
                    "stdout": "/tmp/test.out",
                    "stderr": "/tmp/test.err",
                    "workingdir": "/tmp",
                    "umask": "022",
                    "env": {"TEST": "value"}
                }
            }
        }
        self.process_manager = ProcessManager(self.config, self.logger_mock)

    @patch('subprocess.Popen')
    def test_start_program(self, mock_popen):
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        self.process_manager.start_program("test_program")

        mock_popen.assert_called_once()
        self.assertIn("test_program", self.process_manager.processes)
        self.assertEqual(len(self.process_manager.processes["test_program"]), 1)
        self.logger_mock.info.assert_called_with("Started program: test_program")

    @patch('subprocess.Popen')
    def test_stop_program(self, mock_popen):
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        self.process_manager.start_program("test_program")
        self.process_manager.stop_program("test_program")

        mock_process.send_signal.assert_called_once()
        mock_process.kill.assert_called_once()
        self.assertNotIn("test_program", self.process_manager.processes)
        self.logger_mock.info.assert_called_with("Stopped program: test_program")

    @patch('subprocess.Popen')
    def test_restart_program(self, mock_popen):
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        self.process_manager.start_program("test_program")
        self.process_manager.restart_program("test_program")

        self.assertEqual(mock_popen.call_count, 2)
        self.assertIn("test_program", self.process_manager.processes)
        self.assertEqual(len(self.process_manager.processes["test_program"]), 1)

    @patch('subprocess.Popen')
    def test_get_status(self, mock_popen):
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        self.process_manager.start_program("test_program")
        status = self.process_manager.get_status()

        self.assertIn("test_program", status)
        self.assertEqual(status["test_program"][0]["status"], "running")
        self.assertEqual(status["test_program"][0]["pid"], 12345)

    @patch('subprocess.Popen')
    def test_update_config(self, mock_popen):
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        self.process_manager.start_program("test_program")

        new_config = self.config.copy()
        new_config["programs"]["new_program"] = {
            "cmd": "echo 'new'",
            "numprocs": 1,
            "autostart": True
        }

        self.process_manager.update_config(new_config)

        self.assertIn("new_program", self.process_manager.processes)
        self.assertEqual(mock_popen.call_count, 2)

    @patch('subprocess.Popen')
    def test_check_and_restart(self, mock_popen):
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.side_effect = [None, 0, None]  # Simulate process ending and restarting
        mock_popen.return_value = mock_process

        self.process_manager.start_program("test_program")
        self.process_manager.check_and_restart()

        self.assertEqual(mock_popen.call_count, 2)
        self.assertEqual(self.process_manager.processes["test_program"][0].restarts, 1)

    @patch('subprocess.Popen')
    def test_environment_variables(self, mock_popen):
        mock_process = Mock()
        mock_popen.return_value = mock_process

        self.process_manager.start_program("test_program")

        _, kwargs = mock_popen.call_args
        self.assertIn("TEST", kwargs["env"])
        self.assertEqual(kwargs["env"]["TEST"], "value")

    @patch('subprocess.Popen')
    def test_working_directory(self, mock_popen):
        mock_process = Mock()
        mock_popen.return_value = mock_process

        self.process_manager.start_program("test_program")

        _, kwargs = mock_popen.call_args
        self.assertEqual(kwargs["cwd"], "/tmp")

if __name__ == '__main__':
    unittest.main()