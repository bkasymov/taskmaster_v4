import unittest
import os
import subprocess
import time
import signal
from taskmaster import Taskmaster
import threading
import yaml
import psutil

RESULT_DIR = "../result"
CONFIG_FILE = "test_config.yaml"


class TestListTmpConfig(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		if not os.path.exists(RESULT_DIR):
			os.makedirs(RESULT_DIR)
	
	@classmethod
	def tearDownClass(cls):
		if os.path.exists(CONFIG_FILE):
			os.remove(CONFIG_FILE)
		for file in os.listdir(RESULT_DIR):
			os.remove(os.path.join(RESULT_DIR, file))
		os.rmdir(RESULT_DIR)
	
	def setUp(self):
		for file in os.listdir(RESULT_DIR):
			os.remove(os.path.join(RESULT_DIR, file))
	
	def create_config(self, umask):
		config = {
			"programs": {
				"list_tmp": {
					"cmd": "ls -la /tmp",
					"numprocs": 1,
					"umask": umask,
					"workingdir": ".",
					"autostart": True,
					"autorestart": "never",
					"exitcodes": [0],
					"startretries": 1,
					"starttime": 1,
					"stopsignal": "TERM",
					"stoptime": 5,
					"stdout": os.path.join(RESULT_DIR, "list_tmp.stdout"),
					"stderr": os.path.join(RESULT_DIR, "list_tmp.stderr")
				}
			}
		}
		with open(CONFIG_FILE, "w") as f:
			yaml.dump(config, f)
	
	def test_umask_variations(self):
		umask_values = ["000", "022", "077"]
		expected_permissions = ["666", "644", "600"]
		
		for umask, expected_perm in zip(umask_values, expected_permissions):
			with self.subTest(umask=umask):
				self.create_config(umask)
				taskmaster = Taskmaster(CONFIG_FILE)
				
				taskmaster_thread = threading.Thread(target=taskmaster.run_without_shell)
				taskmaster_thread.daemon = True
				taskmaster_thread.start()
				
				time.sleep(2)
				
				stdout_file = os.path.join(RESULT_DIR, "list_tmp.stdout")
				self.assertTrue(os.path.exists(stdout_file), f"Файл {stdout_file} не создан")
				
				st_mode = os.stat(stdout_file).st_mode & 0o777
				actual_perms = oct(st_mode)[-3:]
				self.assertEqual(actual_perms, expected_perm,
				                 f"Неправильные права доступа для umask {umask}: ожидалось {expected_perm}, получено {actual_perms}")
				
				taskmaster.stop_all_programs()
				time.sleep(1)
	
	def test_other_config_parameters(self):
		self.create_config("022")
		taskmaster = Taskmaster(CONFIG_FILE)
		
		taskmaster_thread = threading.Thread(target=taskmaster.run_without_shell)
		taskmaster_thread.daemon = True
		taskmaster_thread.start()
		
		time.sleep(2)
		
		status = taskmaster.status()
		self.assertEqual(len(status["list_tmp"]), 1, "Количество процессов должно быть 1")
		
		self.assertTrue(all(proc["status"] == "running" for proc in status["list_tmp"]),
		                "Процесс должен быть запущен автоматически")
		
		stdout_file = os.path.join(RESULT_DIR, "list_tmp.stdout")
		with open(stdout_file, "r") as f:
			output = f.read()
		self.assertIn("/tmp", output, "Вывод команды должен содержать /tmp")
		
		for proc in status["list_tmp"]:
			pid = proc["pid"]
			process = psutil.Process(pid)
			self.assertEqual(process.cwd(), os.getcwd(), "Рабочая директория должна быть текущей директорией")
		
		pid = status["list_tmp"][0]["pid"]
		os.kill(pid, signal.SIGTERM)
		time.sleep(2)
		new_status = taskmaster.status()
		self.assertEqual(len(new_status["list_tmp"]), 0, "Процесс не должен быть перезапущен")
		
		result = subprocess.run(["ls", "-la", "/tmp"], capture_output=True)
		self.assertEqual(result.returncode, 0, "Команда должна завершиться с кодом 0")
		
		taskmaster.start_program("list_tmp")
		time.sleep(1)
		taskmaster.stop_program("list_tmp")
		time.sleep(6)
		final_status = taskmaster.status()
		self.assertFalse("list_tmp" in final_status, "Программа должна быть остановлена")
		
		taskmaster.stop_all_programs()
		time.sleep(1)


if __name__ == "__main__":
	unittest.main()