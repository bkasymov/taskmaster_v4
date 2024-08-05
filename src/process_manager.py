import logging
import subprocess
import os
import signal
import time


class ProcessInfo:
    def __init__(self, process: subprocess.Popen, cmd: str, config: dict):
        self.process = process
        self.cmd = cmd
        self.config = config
        self.restarts = 0
        self.start_time = time.monotonic()
        self.end_time = None
        
    def update_status(self):
        if self.process.poll() is not None and self.end_time is None:
	        self.end_time = time.monotonic()
    
    @property
    def status(self):
        return "running" if self.process.poll() is None else "finished"
    
    @property
    def uptime(self):
        if self.end_time:
	        return self.end_time - self.start_time
        return time.monotonic() - self.start_time


class ProcessManager:
	def __init__(self, config: dict, logger: logging.Logger):
		self.config = config
		self.logger = logger
		self.processes = {}
  
	def start_initial_processes(self):
		for program_name, program_config in self.config["programs"].items():
			if program_config["autostart"]:
				self.start_program(program_name)
	
	def start_program(self, program_name: str):
		if program_name not in self.config["programs"]:
			self.logger.warning(f"Program {program_name} not found in config")
			return
		program_config = self.config["programs"][program_name]
		self.processes[program_name] = [
			self._create_process_info(program_name, program_config)
			for _ in range(program_config["numprocs"])
		]
		self.logger.info(f"Started program: {program_name}")
	
	def _create_process_info(self, program_name: str, program_config: dict) -> ProcessInfo:
		process = self._start_process(program_name, program_config)
		return ProcessInfo(process, program_config["cmd"], program_config)
	
	def _start_process(self, program_name: str, program_config: dict) -> subprocess.Popen:
		env = os.environ.copy()
		env.update(program_config.get("env", {}))
		
		umask = int(program_config["umask"], 8)
		old_umask = os.umask(umask)
		try:
			with open(program_config["stdout"], "w") as stdout, open(program_config["stderr"], "w") as stderr:
				process = subprocess.Popen(
					program_config['cmd'],
					shell=True,
					stdout=stdout,
					stderr=stderr,
					env=env,
					cwd=program_config["workingdir"],
				)
			
			self.logger.info(f"Started process {process.pid} for program {program_name} with umask {umask:03o}")
			return process
		finally:
			os.umask(old_umask)
			
	def stop_program(self, program_name: str):
		if program_name not in self.processes:
			self.logger.warning(f"Process with {program_name} is not running")
			return
		
		program_config = self.config["programs"][program_name]
		stop_signal = getattr(signal, f"SIG{program_config['stopsignal']}")
		
		for process_info in self.processes[program_name]:
			process_info.process.send_signal(stop_signal)
		
		time.sleep(program_config["stoptime"])
		
		for process_info in self.processes[program_name]:
			if process_info.process.poll() is None:
				process_info.process.kill()
			process_info.update_status()
		
		del self.processes[program_name]
		self.logger.info(f"Stopped program: {program_name}")
	
	def restart_all_programs(self):
		for program_name in list(self.processes.keys()):
			self.restart_program(program_name)
	
	def restart_program(self, program_name: str):
		self.stop_program(program_name)
		self.start_program(program_name)
	
	def get_status(self):
		status = {}
		for program_name, process_infos in self.processes.items():
			status[program_name] = []
			for process_info in process_infos:
				process_info.update_status()
				status[program_name].append({
					"pid": process_info.process.pid,
					"cmd": process_info.cmd,
					"status": process_info.status,
					"restarts": process_info.restarts,
					"uptime": f"{process_info.uptime:.3f}",
				})
		return status
	
	def update_config(self, new_config: dict):
		old_programs = set(self.config["programs"].keys())
		new_programs = set(new_config["programs"].keys())
		
		for program_name in old_programs - new_programs:
			self.stop_program(program_name)
		
		for program_name in new_programs - old_programs:
			if new_config["programs"][program_name]["autostart"]:
				self.start_program(program_name)
		
		for program_name in old_programs & new_programs:
			if self.config["programs"][program_name] != new_config["programs"][program_name]:
				self.restart_program(program_name)
		
		self.config = new_config
	
	def check_and_restart(self):
		for program_name, process_infos in self.processes.items():
			program_config = self.config["programs"][program_name]
			for i, process_info in enumerate(process_infos):
				process_info.update_status()
				if process_info.status == "finished":
					if (program_config["autorestart"] == "always" or
							(program_config["autorestart"] == "unexpected" and
							 process_info.process.returncode not in program_config["exitcodes"])):
						self._restart_process(program_name, i)
	
	def _restart_process(self, program_name: str, index: int):
		program_config = self.config["programs"][program_name]
		process_info = self.processes[program_name][index]
		if process_info.restarts < program_config["startretries"]:
			new_process = self._start_process(program_name, program_config)
			new_process_info = ProcessInfo(new_process, program_config["cmd"], program_config)
			new_process_info.restarts = process_info.restarts + 1
			self.processes[program_name][index] = new_process_info
			self.logger.info(f"Restarted process for {program_name} (PID: {new_process.pid})")
		else:
			self.logger.warning(f"Failed to restart {program_name} after {program_config['startretries']} attempts")