"""TODO

Author: Chris Jurich <chris.jurich@vanderbilt.edu>
Date: 2023-04-01
"""


from ..core.logger import _LOGGER
from enzy_htp.core import file_system as fs
from enzy_htp.core import env_manager as em


from enzy_htp._config.bcl_config import BCLConfig, default_bcl_config

class BCLInterface:
    
    def __init__(self, config: BCLConfig = None) -> None:
        """Simplistic constructor that optionally takes an BCLConfig object as its only argument.
        Also checks if the current environment is compatible with the AmberInterface().
        """
        self.config_ = config
        if not self.config_:
            self.config_ = default_bcl_config()
        self.env_manager_ = em.EnvironmentManager(
            env_vars=self.config_.required_env_vars(),
            exectubles=self.config_.required_executables(),
        )
        self.env_manager_.check_environment()
        self.compatible_env_ = self.env_manager_.is_missing()
