import yaml
from schema import Schema, And, Use, Optional, SchemaError
import os
import signal
from typing import Dict, Any, Tuple, List
import subprocess

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
	def validate_command(cmd: str) -> str:
		command = cmd.split()[0]
		try:
			subprocess.run(["which", command], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		except subprocess.CalledProcessError:
			raise ConfigValidationError(f"Command not found: {command}")
		return cmd
	
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
				config = yaml.safe_load(file)
			
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