import cmd
from prettytable import PrettyTable


class ControlShell(cmd.Cmd):
    intro = (
        "Welcome to the Taskmaster control shell. Type 'help' or '?' to list commands."
    )
    prompt = "(taskmaster) "

    def __init__(self, taskmaster):
        super().__init__()
        self.taskmaster = taskmaster
    
    def do_status(self, arg):
        status = self.taskmaster.status()
        config_programs = set(self.taskmaster.config["programs"].keys())
        
        table = PrettyTable()
        table.field_names = ["Program", "PID", "Command", "Status", "Restarts", "Uptime"]
        table.align["Program"] = "l"  # выравнивание по левому краю для столбца "Program"
        
        for program_name in config_programs:
            if program_name in status:
                for process in status[program_name]:
                    table.add_row([program_name, process['pid'], process['cmd'], process['status'], process['restarts'],
                                   f"{process['uptime']} seconds"])
            else:
                table.add_row([program_name, "N/A", "N/A", "not started", "N/A", "N/A"])
        print(table)
    
    def do_start(self, arg):
        if not arg:
            print("Please specify a program name or 'all' to start all programs")
            return
        if arg == 'all':
            status = self.taskmaster.status()
            for program_name in status.keys():
                self.taskmaster.start_program(program_name)
                self._print_program_status(program_name)
        else:
            self.taskmaster.start_program(arg)
            self._print_program_status(arg)

    def do_stop(self, arg):
        if not arg:
            print("Please specify a program name")
            return
        self.taskmaster.stop_program(arg)
        self._print_program_status(arg)

    def do_restart(self, arg):
        if not arg:
            print("Please specify a program name")
            return
        self.taskmaster.restart_program(arg)
        self._print_program_status(arg)

    def do_reload(self, arg):
        self.taskmaster.reload_config()
        print("Configuration reloaded. Current status:")
        self.do_status(arg)

    def do_quit(self, arg):
        print("Exiting Taskmaster...")
        return True

    def do_exit(self, arg):
        return self.do_quit(arg)
    
    def _print_program_status(self, program_name):
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
