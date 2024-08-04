import yaml
from schema import Schema, And, Use, Optional

class ConfigParser:
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

    schema = Schema(
        {
            "programs": {
                str: {
                    "cmd": str,
                    Optional("numprocs", default=1): And(int, lambda n: n > 0),
                    Optional("umask", default="022"): And(str, lambda s: len(s) == 3 and s.isdigit()),
                    Optional("workingdir", default="."): str,
                    Optional("autostart", default=True): bool,
                    Optional("autorestart", default="unexpected"): And(
                        str,
                        Use(str.lower),
                        lambda s: s in ("always", "never", "unexpected"),
                    ),
                    Optional("exitcodes", default=[0]): [int],
                    Optional("startretries", default=3): And(int, lambda n: n >= 0),
                    Optional("starttime", default=5): And(int, lambda n: n > 0),
                    Optional("stopsignal", default="TERM"): And(
                        str,
                        lambda s: s in ("TERM", "HUP", "INT", "QUIT", "KILL"),
                    ),
                    Optional("stoptime", default=10): And(int, lambda n: n > 0),
                    Optional("stdout", default="/dev/null"): str,
                    Optional("stderr", default="/dev/null"): str,
                    Optional("env", default={}): {Optional(str): str}
                }
            }
        }
    )

    def __init__(self, config_file):
        self.config_file = config_file

    def parse(self):
        with open(self.config_file, "r") as file:
            config = yaml.safe_load(file)

        config = self.apply_defaults(config)
        self.validate_config(config)
        return config

    def apply_defaults(self, config):
        config_copy = config.copy()
        for program_name, program_config in config_copy["programs"].items():
            for key, default_value in self.default_values.items():
                if key not in program_config:
                    program_config[key] = default_value
        return config_copy

    def validate_config(self, config):
        self.schema.validate(config)