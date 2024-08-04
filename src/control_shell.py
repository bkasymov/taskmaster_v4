import cmd
import signal
import sys

import yaml
from prettytable import PrettyTable

class ControlShell(cmd.Cmd):
    intro = (
        "Hey!😊\n"
        "Welcome to the Taskmaster control shell.\n"
        "Type 'help' or '？' to list commands."
    )
    prompt = "(taskmaster) "
    

    def __init__(self, taskmaster):
        """
        Initialize the control shell
        :param taskmaster:
        """
        super().__init__()
        self.taskmaster = taskmaster
        self.command_history = []
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def help_history(self):
        print("Show command history.")

    def help_status(self):
        print("Show status of programs.")

    def help_start(self):
        print("Start a program or all programs.")

    def help_stop(self):
        print("Stop a program.")

    def help_restart(self):
        print("Restart a program.")

    def help_reload(self):
        print("Reload the configuration.")

    def help_quit(self):
        print("Exit the shell.")

    def help_exit(self):
        print("Exit the shell.")
    
    def do_history(self, arg: str):
        for i, command in enumerate(self.command_history, 1):
            print(f"{i}: {command}")
    
    def help_cat(self):
        print("Show the configuration of a program.")
    
    def do_status(self, arg):
        """
        Show the status of programs or a specific program if specified as an argument
        :param arg:
        :return:
        """
        status = self.taskmaster.status()
        config_programs = set(self.taskmaster.config["programs"].keys())
        
        table = PrettyTable()
        table.field_names = ["Program", "PID", "Command", "Status", "Restarts", "Uptime"]
        table.align["Program"] = "l"
        
        if arg:
            if arg in config_programs:
                if arg in status:
                    for process in status[arg]:
                        table.add_row([arg, process['pid'], process['cmd'], process['status'], process['restarts'],
                                       f"{process['uptime']} seconds"])
                else:
                    table.add_row([arg, "N/A", "N/A", "not started", "N/A", "N/A"])
            else:
                print(f"Program {arg} not found")
                return
        else:
            for program_name in config_programs:
                if program_name in status:
                    for process in status[program_name]:
                        table.add_row([program_name, process['pid'], process['cmd'], process['status'], process['restarts'],
                                       f"{process['uptime']} seconds"])
                else:
                    table.add_row([program_name, "N/A", "N/A", "not started", "N/A", "N/A"])
        print(table)
    
    def do_start(self, arg: str):
        """
        Start a program or all programs if specified as an argument or 'all'
        :param arg:
        :return:
        """
        if not arg:
            print("Please specify a program name or 'all' to start all programs")
            return
        if arg == 'all':
            programs = self.taskmaster.config["programs"]
            for program_name in programs.keys():
                self.taskmaster.start_program(program_name)
                self._print_program_status(program_name)
        else:
            self.taskmaster.start_program(arg)
            self._print_program_status(arg)

    def do_stop(self, arg: str):
        if arg == 'all':
            self.taskmaster.stop_all_programs()
            print("All programs stopped")
        if not arg:
            print("Please specify a program name")
            return
        self.taskmaster.stop_program(arg)
        self._print_program_status(arg)
    
    def do_restart(self, arg: str):
        if not arg:
            print("Please specify a program name or 'all' to restart all programs")
            return
        
        if arg.lower() == 'all':
            self.taskmaster.restart_all_programs()
            print("All programs restarted")
            return
        
        self.taskmaster.restart_program(arg)
        self._print_program_status(arg)

    def do_reload(self, arg: str):
        self.taskmaster.reload_config()
        print("Configuration reloaded. Current status:")
        self.do_status(arg)

    def do_quit(self, arg: str):
        print("Exiting Taskmaster...")
        self.taskmaster.stop_all_programs()
        return True

    def do_exit(self, arg):
        return self.do_quit(arg)
    
    def do_cat(self, arg: str):
        """
        Show the configuration of a program
        :param arg:
        :return:
        """
        if not arg:
            print("Please specify a program name")
            return
        status = self.taskmaster.config["programs"].get(arg)
        if status:
            print(f"\nConfiguration for {arg}:")
            print(yaml.dump({arg: status}, default_flow_style=False))
        else:
            print(f"Program {arg} not found")
    
    def _print_program_status(self, program_name: str):
        """
        Print the status of a program to the console
        :param program_name:
        :return:
        """
        status = self.taskmaster.status()
        if program_name in status:
            print(f"Status of {program_name}:")
            table = PrettyTable()
            table.field_names = ["Program", "PID", "Command", "Status", "Restarts", "Uptime"]
            for process in status[program_name]:
                table.add_row([program_name, process['pid'], process['cmd'], process['status'], process['restarts'],
                               f"{process['uptime']} seconds"])
            print(table)
        else:
            print(f"Program {program_name} not found")
    
    def signal_handler(self):
        print("\nReceived SIGINT, stopping all programs and exiting...")
        self.taskmaster.stop_all_programs()
        sys.exit(0)
    
    def precmd(self, line: str):
        """
        Add the command to the history before executing it
        :param line:
        :return:
        """
        if line != '':
            self.command_history.append(line)
        return line