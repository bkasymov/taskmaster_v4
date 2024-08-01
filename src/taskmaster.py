import signal
import sys
import time
from config_parser import ConfigParser
from process_manager import ProcessManager
from control_shell import ControlShell
from logger import setup_logger


class Taskmaster:
    def __init__(self, config_file):
        self.config_file = config_file
        self.logger = setup_logger()
        self.config_parser = ConfigParser(config_file)
        self.config = self.config_parser.parse()
        self.process_manager = ProcessManager(self.config, self.logger)
        self.control_shell = ControlShell(self)

    def reload_config(self):
        try:
            new_config = self.config_parser.parse()
            self.process_manager.update_config(new_config)
            self.logger.info("Configuration reloaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")

    def sighup_handler(self, signum, frame):
        self.logger.info("Received SIGHUP, reloading configuration")
        self.reload_config()

    def run(self):
        signal.signal(signal.SIGHUP, self.sighup_handler)
        self.process_manager.start_initial_processes()

        def check_processes():
            while True:
                self.process_manager.check_and_restart()
                time.sleep(1)

        import threading

        checker_thread = threading.Thread(target=check_processes)
        checker_thread.daemon = True
        checker_thread.start()

        self.control_shell.cmdloop()

    def status(self):
        return self.process_manager.get_status()

    def start_program(self, program_name):
        self.process_manager.start_program(program_name)

    def stop_program(self, program_name):
        self.process_manager.stop_program(program_name)

    def restart_program(self, program_name):
        self.process_manager.restart_program(program_name)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python taskmaster.py <config_file>")
        sys.exit(1)

    taskmaster = Taskmaster(sys.argv[1])
    taskmaster.run()
