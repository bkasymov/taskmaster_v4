import atexit
import logging
import subprocess
import os
import signal
import time


class ProcessInfo:
	"""
	Class to store information about a process
	"""
	
	def __init__(self, process: subprocess.Popen, cmd: str, config: dict):
		self.process = process
		self.cmd = cmd
		self.config = config
		self.restarts = 0
		self.start_time = time.time()


class ProcessManager:
	"""
	Class to manage processes
	"""
	
	def __init__(self, config: dict, logger: logging.Logger):
		"""
		Initialize the ProcessManager
		:param config:
		:param logger:
		"""
		self.config = config
		self.logger = logger
		self.processes = {}
	
	def start_initial_processes(self):
		"""
		Start all programs that have autostart set to True
		:return:
		"""
		for program_name, program_config in self.config["programs"].items():
			if program_config["autostart"]:
				self.start_program(program_name)
	
	def start_program(self, program_name: str):
		"""
		Start a program with the given name and configuration from the config file
		:param program_name:
		:return:
		"""
		program_config = self.config["programs"][program_name]
		for i in range(program_config["numprocs"]):
			process = self._start_process(program_name, program_config)
			if program_name not in self.processes:
				self.processes[program_name] = []
			self.processes[program_name].append(
				ProcessInfo(process, program_config["cmd"], program_config)
			)
		self.logger.info(f"Started program: {program_name}")
	
	def _start_process(self, program_name: str, program_config: dict):
		"""
		Start a process with the given name and configuration
		Copy the environment variables from the current environment and update with the environment variables from the config
		:param program_name:
		:param program_config:
		:return:
		"""
		env = os.environ.copy()
		env.update(program_config.get("env", {}))
		
		with (open(program_config["stdout"], "w") as stdout,
		      open(program_config["stderr"], "w") as stderr):
			process = subprocess.Popen(
				program_config["cmd"],
				shell=True,
				stdout=stdout,
				stderr=stderr,
				env=env,
				cwd=program_config["workingdir"],
				preexec_fn=lambda: os.umask(int(program_config["umask"], 8)),
			)
		
		self.logger.info(f"Started process {process.pid} for program {program_name}")
		return process
	
	def stop_program(self, program_name: str):
		"""
		Stop a program with the given name and all its processes by
		sending the stop signal and then killing the process
		:param program_name:
		:return:
		"""
		if program_name not in self.processes:
			self.logger.warning(f"Program {program_name} is not running")
			return
		
		program_config = self.config["programs"][program_name]
		stop_signal = getattr(signal, f"SIG{program_config['stopsignal']}")
		
		for process_info in self.processes[program_name]:
			process_info.process.send_signal(stop_signal)
		
		time.sleep(program_config["stoptime"])
		
		for process_info in self.processes[program_name]:
			if process_info.process.poll() is None:
				process_info.process.kill()
		
		del self.processes[program_name]
		self.logger.info(f"Stopped program: {program_name}")
	
	def restart_program(self, program_name: str):
		"""
		Restart a program with the given name by stopping it and then starting it again
		:param program_name:
		:return:
		"""
		self.stop_program(program_name)
		self.start_program(program_name)
	
	def get_status(self):
		"""
		Get the status of all programs and their processes
		:return:
		"""
		status = {}
		for program_name, process_infos in self.processes.items():
			status[program_name] = []
			for process_info in process_infos:
				if process_info.process.poll() is None:
					status_text = "running"
				else:
					status_text = "finished"
				status[program_name].append(
					{
						"pid": process_info.process.pid,
						"cmd": process_info.cmd,
						"status": status_text,
						"restarts": process_info.restarts,
						"uptime": int(time.time() - process_info.start_time),
					}
				)
		return status
	
	def update_config(self, new_config: dict):
		"""
		Update the configuration of the ProcessManager
		:param new_config:
		:return:
		"""
		old_programs = set(self.config["programs"].keys())
		new_programs = set(new_config["programs"].keys())
		
		for program_name in old_programs - new_programs:
			self.stop_program(program_name)
		
		for program_name in new_programs - old_programs:
			if new_config["programs"][program_name]["autostart"]:
				self.start_program(program_name)
		
		for program_name in old_programs & new_programs:
			"""
				if the program config has changed, restart the program
			"""
			if (
					self.config["programs"][program_name]
					!= new_config["programs"][program_name]
			):
				self.restart_program(program_name)
		
		self.config = new_config
	
	def check_and_restart(self):
		"""
		Check all processes and restart them if they are not running
		:return:
		"""
		for program_name, process_infos in self.processes.items():
			program_config = self.config["programs"][program_name]
			for i, process_info in enumerate(process_infos):
				if process_info.process.poll() is not None:
					if (
							program_config["autorestart"] == "always"
							or program_config["autorestart"] == "unexpected"
					):
						self._restart_process(program_name, i)
	
	def _restart_process(self, program_name: str, index: int):
		"""
		Restart a process for a program with the given name and index in the list of processes
		:param program_name:
		:param index:
		:return:
		"""
		program_config = self.config["programs"][program_name]
		old_process_info = self.processes[program_name][index]
		if old_process_info.restarts < program_config["startretries"]:
			new_process = self._start_process(program_name, program_config)
			self.processes[program_name][index] = ProcessInfo(
				new_process, program_config["cmd"], program_config
			)
			self.processes[program_name][index].restarts = old_process_info.restarts + 1
			self.logger.info(
				f"Restarted process for {program_name} (PID: {new_process.pid})"
			)
		else:
			self.logger.warning(
				f"Failed to restart {program_name} after {program_config['startretries']} attempts"
			)
