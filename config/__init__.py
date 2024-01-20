import os

from config.local import LocalConfig
from config.production import ProductionConfig

config_dict = {
    'local': LocalConfig,
    'prod': ProductionConfig
}


def get_environment_config(environment: str = None):
    environment = environment or os.environ.get('ENVIRONMENT', 'local')
    return config_dict[environment]


project_config = get_environment_config()
