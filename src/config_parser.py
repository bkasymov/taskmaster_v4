import yaml
from schema import Schema, And, Use, Optional, SchemaError
import os
import signal

class ConfigValidationError(Exception):
	pass


class ConfigParser:
	"""
	Parses the configuration file and validates the configuration,
	preserving user-defined values and applying defaults only when necessary.
	"""
	default_values = {
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
	
	@staticmethod
	def validate_directory(path):
		if not os.path.isdir(path):
			raise ConfigValidationError(f"Directory does not exist: {path}")
		return path
	
	@staticmethod
	def validate_signal(sig):
		if not hasattr(signal, f"SIG{sig}"):
			raise ConfigValidationError(f"Invalid signal: {sig}")
		return sig
	
	schema = Schema({
		"programs": {
			str: {
				"cmd": str,
				Optional("numprocs"): And(int, lambda n: n > 0, error="numprocs must be a positive integer"),
				Optional("umask"): And(str, lambda s: len(s) == 3 and s.isdigit(),
				                       error="umask must be a 3-digit string"),
				Optional("workingdir"): And(str, validate_directory),
				Optional("autostart"): bool,
				Optional("autorestart"): And(
					str,
					Use(str.lower),
					lambda s: s in ("always", "never", "unexpected"),
					error="autorestart must be 'always', 'never', or 'unexpected'"
				),
				Optional("exitcodes"): [
					And(int, lambda n: -128 <= n <= 255, error="exitcodes must be integers between -128 and 255")],
				Optional("startretries"): And(int, lambda n: n >= 0,
				                              error="startretries must be a non-negative integer"),
				Optional("starttime"): And(int, lambda n: n >= 0, error="starttime must be a positive integer or zero"),
				Optional("stopsignal"): And(str, validate_signal),
				Optional("stoptime"): And(int, lambda n: n >= 0, error="stoptime must be a positive integer or zero"),
				Optional("stdout"): str,
				Optional("stderr"): str,
				Optional("env"): {Optional(str): str}
			}
		}
	})
	
	def __init__(self, config_file: str) -> None:
		self.config_file = config_file
	
	def parse(self):
		"""
		Parse the configuration file, validate it, and apply default values
		only for missing fields.
		"""
		try:
			with open(self.config_file, "r") as file:
				config = yaml.safe_load(file)
			
			validated_config = self.schema.validate(config)
			return self.apply_defaults(validated_config)
		except (SchemaError, yaml.YAMLError, IOError, ConfigValidationError) as e:
				raise ConfigValidationError(e)
	@classmethod
	def apply_defaults(cls, config):
		"""
		Apply default values to the configuration only for missing fields
		"""
		for program_config in config["programs"].values():
			for key, default_value in cls.default_values.items():
				if key not in program_config:
					program_config[key] = default_value
		return config