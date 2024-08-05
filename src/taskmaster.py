import signal
import sys
import time
from config_parser import ConfigParser
from process_manager import ProcessManager
from control_shell import ControlShell
from logger import setup_logger
import threading


class Taskmaster:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.logger = setup_logger()
        self.config_parser = ConfigParser(config_file)
        self.config = self.config_parser.parse()
        self.process_manager = ProcessManager(self.config, self.logger)
        self.control_shell = ControlShell(self)
        self.is_running = threading.Event()
        self.is_running.set()

    def stop_all_programs(self):
        for program_name in self.config["programs"]:
            self.stop_program(program_name)

    def run_without_shell(self):
        self.process_manager.start_initial_processes()
        while self.is_running.is_set():
            self.process_manager.check_and_restart()
            time.sleep(1)

    def compare_configs(self, old_config: dict, new_config: dict):
        """
        Compare two configurations and print the differences
        :param old_config:
        :param new_config:
        :return:
        """
        old_programs = set(old_config["programs"].keys())
        new_programs = set(new_config["programs"].keys())
        
        added_programs = new_programs - old_programs
        removed_programs = old_programs - new_programs
        common_programs = old_programs & new_programs
        
        if added_programs:
            print("Added programs:")
            for program_name in added_programs:
                print(f"  {program_name}")
        
        if removed_programs:
            print("Removed programs:")
            for program_name in removed_programs:
                print(f"  {program_name}")
        
        for program in common_programs:
            if old_config["programs"][program] != new_config["programs"][program]:
                print(f"Changed program: {program}")
                old_program_config = old_config["programs"][program]
                new_program_config = new_config["programs"][program]
                for key in old_program_config.keys():
                    if old_program_config[key] != new_program_config.get(key):
                        print(f"  {key} changed from {old_program_config[key]} to {new_program_config.get(key)}")
                for key in new_program_config.keys():
                    if key not in old_program_config:
                        print(f"  {key} added with value {new_program_config[key]}")

    def reload_config(self):
        old_config = self.config
        try:
            new_config = self.config_parser.parse()
            self.compare_configs(old_config, new_config)
            self.process_manager.update_config(new_config)
            self.logger.info("Configuration reloaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")

    def sighup_handler(self, signum, frame):
        self.logger.info("Received SIGHUP, reloading configuration")
        self.reload_config()

    def sigint_handler(self, signum, frame):
        self.logger.info("Received SIGINT, shutting down...")
        self.is_running.clear()
        self.stop_all_programs()
        sys.exit(0)

    def run(self):
        signal.signal(signal.SIGHUP, self.sighup_handler)
        signal.signal(signal.SIGINT, self.sigint_handler)
        self.process_manager.start_initial_processes()

        def check_processes():
            while self.is_running.is_set():
                self.process_manager.check_and_restart()
                time.sleep(1)

        checker_thread = threading.Thread(target=check_processes)
        checker_thread.daemon = True
        checker_thread.start()

        try:
            self.control_shell.cmdloop()
        except KeyboardInterrupt:
            self.sigint_handler(None, None)

    
    def status(self):
        return self.process_manager.get_status()

    def start_program(self, program_name: str):
        self.process_manager.start_program(program_name)

    def stop_program(self, program_name: str):
        self.process_manager.stop_program(program_name)

    def restart_all_programs(self):
        self.process_manager.restart_all_programs()

    def restart_program(self, program_name: str):
        self.process_manager.restart_program(program_name)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python taskmaster.py <config_file>")
        sys.exit(1)

    taskmaster = Taskmaster(sys.argv[1])
    taskmaster.run()
