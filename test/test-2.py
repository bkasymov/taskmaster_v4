import subprocess
import time
import os
import signal
import yaml
import sys

class TaskmasterTester:
    def __init__(self, taskmaster_path, config_path):
        self.taskmaster_path = taskmaster_path
        self.config_path = config_path
        self.taskmaster_process = None

    def start_taskmaster(self):
        self.taskmaster_process = subprocess.Popen(
            [sys.executable, self.taskmaster_path, self.config_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(2)  # Give Taskmaster time to start

    def stop_taskmaster(self):
        if self.taskmaster_process:
            self.taskmaster_process.terminate()
            self.taskmaster_process.wait()
            self.taskmaster_process = None

    def send_command(self, command):
        print(f"Sending command: {command}")
        self.taskmaster_process.stdin.write(command + '\n')
        self.taskmaster_process.stdin.flush()
        time.sleep(1)  # Give Taskmaster time to process the command

    def get_status(self):
        self.send_command("status")
        output = ""
        while True:
            line = self.taskmaster_process.stdout.readline()
            if not line or line.strip() == "":
                break
            output += line
        print(f"Status output:\n{output}")
        return output

    def check_process_status(self, program_name, expected_status):
        status_output = self.get_status()
        return f"{program_name}: {expected_status}" in status_output

    def check_file_content(self, file_path, expected_content):
        with open(file_path, 'r') as f:
            content = f.read()
        return expected_content in content

    def run_tests(self):
        print("Starting Taskmaster tests...")

        self.start_taskmaster()

        # Test 1: Check autostart programs
        assert self.check_process_status('echo_test', 'RUNNING'), "echo_test should be running"
        assert not self.check_process_status('sleep_test', 'RUNNING'), "sleep_test should not be running"

        # Test 2: Start a non-autostart program
        self.send_command("start sleep_test")
        assert self.check_process_status('sleep_test', 'RUNNING'), "sleep_test should be running after manual start"

        # Test 3: Check output files
        time.sleep(1)  # Give time for output to be written
        assert self.check_file_content('../result/echo_test.stdout', 'Hello, Taskmaster!'), "echo_test output incorrect"

        # Test 4: Check environment variables
        assert self.check_file_content('../result/custom_env.stdout', 'CUSTOM_VAR=custom_value'), "custom_env CUSTOM_VAR not set correctly"
        assert self.check_file_content('../result/custom_env.stdout', '/custom/path'), "custom_env PATH not set correctly"

        # Test 5: Check auto-restart
        time.sleep(3)  # Give time for fast_exit to restart
        assert self.check_process_status('fast_exit', 'RUNNING'), "fast_exit should be restarted and running"

        # Test 6: Stop a program
        self.send_command("stop echo_test")
        time.sleep(1)
        assert not self.check_process_status('echo_test', 'RUNNING'), "echo_test should not be running after stop command"

        # Test 7: Restart a program
        self.send_command("restart sleep_test")
        time.sleep(1)
        assert self.check_process_status('sleep_test', 'RUNNING'), "sleep_test should be running after restart command"

        self.stop_taskmaster()

        print("All tests passed successfully!")

if __name__ == "__main__":
    taskmaster_path = "src/taskmaster.py"
    config_path = "src/config.yaml"
    tester = TaskmasterTester(taskmaster_path, config_path)
    tester.run_tests()