import yaml
from schema import Schema, And, Use, Optional


class ConfigParser:
    def __init__(self, config_file):
        self.config_file = config_file

    def parse(self):
        with open(self.config_file, "r") as file:
            config = yaml.safe_load(file)

        self.validate_config(config)
        return config

    def validate_config(self, config):
        schema = Schema(
            {
                "programs": {
                    str: {
                        "cmd": str,
                        "numprocs": And(int, lambda n: n > 0),
                        "umask": And(str, lambda s: len(s) == 3 and s.isdigit()),
                        "workingdir": str,
                        "autostart": bool,
                        "autorestart": And(
                            str,
                            Use(str.lower),
                            lambda s: s in ("always", "never", "unexpected"),
                        ),
                        "exitcodes": [int],
                        "startretries": And(int, lambda n: n >= 0),
                        "starttime": And(int, lambda n: n > 0),
                        "stopsignal": And(
                            str,
                            lambda s: s
                            in ("TERM", "HUP", "INT", "QUIT", "KILL"),
                        ),
                        "stoptime": And(int, lambda n: n > 0),
                        "stdout": str,
                        "stderr": str,
                        Optional("env"): {str: str},
                    }
                }
            }
        )

        schema.validate(config)
