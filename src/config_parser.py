import yaml
from schema import Schema, And, Use, Optional, SchemaError
import os
import signal
from typing import Dict, Any, Tuple, List
import subprocess
import shlex
import re



class ConfigValidationError(Exception):
	pass


class ConfigParser:
	DEFAULT_VALUES: Dict[str, Any] = {
		"numprocs": 1,
		"umask": "022",
		"workingdir": ".",
		"autostart": True,
		"autorestart": "unexpected",
		"exitcodes": [0],
		"startretries": 3,
		"starttime": 5,
		"stopsignal": "TERM",
		"stoptime": 10,
		"stdout": "/dev/null",
		"stderr": "/dev/null",
		"env": {}
	}
	
	def __init__(self, config_file: str):
		self.config_file = config_file
	
	@staticmethod
	def validate_directory(path: str) -> str:
		if not os.path.isdir(path):
			raise ConfigValidationError(f"Directory does not exist: {path}")
		return path
	
	@staticmethod
	def validate_file_path(path: str) -> str:
		if path == "/dev/null":
			return path
		directory = os.path.dirname(path)
		if not os.path.isdir(directory):
			raise ConfigValidationError(f"Directory does not exist for file: {directory}")
		return path
	
	@staticmethod
	def validate_signal(sig: str) -> str:
		if not hasattr(signal, f"SIG{sig}"):
			raise ConfigValidationError(f"Invalid signal: {sig}")
		return sig
	
	@staticmethod
	def get_system_commands():
		system_paths = ['/usr/bin', '/bin', '/usr/local/bin']
		commands = set()
		for path in system_paths:
			if os.path.exists(path):
				commands.update(os.listdir(path))
		return commands
	
	@classmethod
	def validate_command(cls, cmd: str) -> str:
		system_commands = cls.get_system_commands()
		
		def is_valid_command(command):
			return command in system_commands or subprocess.run(['which', command], stdout=subprocess.DEVNULL,
			                                                    stderr=subprocess.DEVNULL).returncode == 0
		
		try:
			sub_commands = cmd.replace('&&', ';;').replace('||', ';;').split(';;')
			
			for sub_cmd in sub_commands:
				tokens = shlex.split(sub_cmd.strip())
				if tokens:
					main_command = tokens[0]
					if not is_valid_command(main_command):
						raise ConfigValidationError(f"Command not found: {main_command}")
			
			return cmd
		except ValueError as e:
			raise ConfigValidationError(f"Invalid command syntax: {e}")
	
	@classmethod
	def get_schema(cls) -> Schema:
		return Schema({
			"programs": {
				str: {
					"cmd": And(str, cls.validate_command),
					Optional("numprocs"): And(int, lambda n: n > 0),
					Optional("umask"): And(str, lambda s: len(s) == 3 and s.isdigit()),
					Optional("workingdir"): And(str, cls.validate_directory),
					Optional("autostart"): bool,
					Optional("autorestart"): And(str, Use(str.lower), lambda s: s in ("always", "never", "unexpected")),
					Optional("exitcodes"): [And(int, lambda n: -128 <= n <= 255)],
					Optional("startretries"): And(int, lambda n: n >= 0),
					Optional("starttime"): And(int, lambda n: n >= 0),
					Optional("stopsignal"): And(str, cls.validate_signal),
					Optional("stoptime"): And(int, lambda n: n >= 0),
					Optional("stdout"): And(str, cls.validate_file_path),
					Optional("stderr"): And(str, cls.validate_file_path),
					Optional("env"): {Optional(str): str}
				}
			}
		})
	
	def parse(self) -> Tuple[str, Dict[str, Any]]:
		try:
			with open(self.config_file, "r") as file:
				content = file.read()
			
			programs_count = len(re.findall(r'^\s*programs\s*:', content, re.MULTILINE))
			if programs_count == 0:
				raise ConfigValidationError("Missing 'programs' key in configuration")
			elif programs_count > 1:
				raise ConfigValidationError("Multiple 'programs' keys found in configuration")
			
			config = yaml.safe_load(content)
			
			if "programs" not in config:
				raise ConfigValidationError("Missing 'programs' key in configuration")
			
			validated_config = self.get_schema().validate(config)
			return None, self.apply_defaults(validated_config)
		except SchemaError as e:
			return f"Schema validation error: {e}", None
		except yaml.YAMLError as e:
			return f"YAML parsing error: {e}", None
		except IOError as e:
			return f"File I/O error: {e}", None
		except ConfigValidationError as e:
			return f"Configuration validation error: {e}", None
		except Exception as e:
			return f"Unexpected error: {e}", None
	
	@classmethod
	def apply_defaults(cls, config: Dict[str, Any]) -> Dict[str, Any]:
		for program_config in config["programs"].values():
			for key, default_value in cls.DEFAULT_VALUES.items():
				if key not in program_config:
					program_config[key] = default_value
		return config
