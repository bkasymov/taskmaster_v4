import cmd


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
        for program_name, processes in status.items():
            print(f"{program_name}:")
            for process in processes:
                print(f"    PID {process['pid']}:")
                print(f"    Command: {process['cmd']}")
                print(f"    Status: {process['status']}")
                print(f"    Restarts: {process['restarts']}")
                print(f"    Uptime: {process['uptime']} seconds")

    def do_start(self, arg):
        if not arg:
            print("Please specify a program name")
            return
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
            for process in status[program_name]:
                print(f"  PID {process['pid']}:")
                print(f"    Command: {process['cmd']}")
                print(f"    Status: {process['status']}")
                print(f"    Restarts: {process['restarts']}")
                print(f"    Uptime: {process['uptime']} seconds")
        else:
            print(f"Program {program_name} not found")
