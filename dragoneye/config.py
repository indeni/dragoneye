import os

import yaml


class Configuration:
    def __init__(self):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.yaml')
        with open(filepath, 'r') as config_file:
            self._config = yaml.safe_load(config_file)

    def get(self, key: str):
        return self._config[key]


config = Configuration()
