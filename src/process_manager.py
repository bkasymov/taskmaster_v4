import atexit
import subprocess
import os
import signal
import time


class ProcessInfo:
    def __init__(self, pid, cmd, config):
        self.pid = pid
        self.cmd = cmd
        self.config = config
        self.restarts = 0
        self.start_time = time.time()


class ProcessManager:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.processes = {}
        self.subprocesses = []
        atexit.register(self.cleanup)
    
    def cleanup(self):
        for process in self.subprocesses:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    process.kill()

    def start_initial_processes(self):
        for program_name, program_config in self.config["programs"].items():
            if program_config["autostart"]:
                self.start_program(program_name)

    def start_program(self, program_name):
        program_config = self.config["programs"][program_name]
        for i in range(program_config["numprocs"]):
            process = self._start_process(program_name, program_config)
            if program_name not in self.processes:
                self.processes[program_name] = []
            self.processes[program_name].append(
                ProcessInfo(process.pid, program_config["cmd"], program_config)
            )
        self.logger.info(f"Started program: {program_name}")
    
    def _start_process(self, program_name, program_config):
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

    def stop_program(self, program_name):
        if program_name not in self.processes:
            self.logger.warning(f"Program {program_name} is not running")
            return

        program_config = self.config["programs"][program_name]
        stop_signal = getattr(signal, f"SIG{program_config['stopsignal']}")

        for process_info in self.processes[program_name]:
            try:
                os.kill(process_info.pid, stop_signal)
            except ProcessLookupError:
                self.logger.warning(
                    f"Process {process_info.pid} for {program_name} not found"
                )

        time.sleep(program_config["stoptime"])

        for process_info in self.processes[program_name]:
            try:
                os.kill(process_info.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        del self.processes[program_name]
        self.logger.info(f"Stopped program: {program_name}")

    def restart_program(self, program_name):
        self.stop_program(program_name)
        self.start_program(program_name)

    
    def get_status(self):
        status = {}
        for program_name, process_infos in self.processes.items():
            status[program_name] = []
            for process_info in process_infos:
                try:
                    os.kill(process_info.pid, 0)
                    status_text = "running"
                except OSError:
                    status_text = "finished"
                status[program_name].append(
                    {
                        "pid": process_info.pid,
                        "cmd": process_info.cmd,
                        "status": status_text,
                        "restarts": process_info.restarts,
                        "uptime": int(time.time() - process_info.start_time),
                    }
                )
        return status

    def update_config(self, new_config):
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
        for program_name, process_infos in self.processes.items():
            program_config = self.config["programs"][program_name]
            for i, process_info in enumerate(process_infos):
                try:
                    os.kill(process_info.pid, 0)
                except OSError:
                    if (
                            program_config["autorestart"] == "always"
                            or program_config["autorestart"] == "unexpected"
                    ):
                        self._restart_process(program_name, i)

    def _restart_process(self, program_name, index):
        program_config = self.config["programs"][program_name]
        old_process = self.processes[program_name][index]
        if old_process.restarts < program_config["startretries"]:
            new_process = self._start_process(program_name, program_config)
            self.processes[program_name][index] = ProcessInfo(
                new_process.pid, program_config["cmd"], program_config
            )
            self.processes[program_name][index].restarts = old_process.restarts + 1
            self.logger.info(
                f"Restarted process for {program_name} (PID: {new_process.pid})"
            )
        else:
            self.logger.warning(
                f"Failed to restart {program_name} after {program_config['startretries']} attempts"
            )
