"""Defines an EnvironmentManager class that checks for applications and environment variables that enzy_htp needs.

Author: Chris Jurich, <chris.jurich@vanderbilt.edu>
Date: 2022-02-12
"""
import os
import shutil
from typing import List

from .logger import _LOGGER
from .exception import MissingEnvironmentElement


class EnvironmentManager:
    """Checks whether given applications and environment variables are set in the current environment.
	
	Attributes:
		env_vars_: A list of strings containing environment variables to check for.
		executables_: a list of strings containing executables to check for.
		missing_env_vars_: A list of strings corresponding to environment variables that are missing.	
		missing_executables_: A list of strings corresponding to executables that are missing.
	"""

    def __init__(self, **kwargs):
        self.env_vars_ = kwargs.get("env_vars", [])
        self.executables_ = kwargs.get("executables", [])
        self.mapper = dict()
        self.missing_env_vars_ = []
        self.missing_executables_ = []

    def add_executable(self, exe_name):
        self.executables_.append(exe_name)

    def add_env_var(self, env_var):
        self.env_vars_.append(env_var)

    def check_env_vars(self):
        for env_var in self.env_vars_:
            if os.getenv(env_var) is None:
                self.missing_env_vars_.append(env_var)

    def check_executables(self):

        def exe_exists(exe_name):
            full_path = os.path.expandvars(exe_name)
            return shutil.which(exe_name) is not None

        for exe in self.executables_:
            if not exe_exists(exe):
                self.missing_executables_.append(exe)
            else:
                self.mapper[exe] = shutil.which(exe)

    def display_missing(self):
        if not self.is_missing():
            _LOGGER.info("Environment has all required elements!")
            return
        _LOGGER.warning("Environment is missing some required elements...")

        if len(self.missing_executables_):
            _LOGGER.warning("\tMissing excecutables:")
            for me in self.missing_executables_:
                _LOGGER.warning(f"\t\t{me}")

        if len(self.missing_env_vars_):
            _LOGGER.warning("\tMissing environment variables:")
            for mev in self.missing_env_vars_:
                _LOGGER.warning(f"\t\t{mev}")

    def check_environment(self):
        _LOGGER.info("Checking environment for required elements...")
        self.check_env_vars()
        self.check_executables()
        self.display_missing()
        _LOGGER.info("Environment check completed!")

    def reset(self):
        self.executables_ = []
        self.missing_executables_ = []
        self.env_vars_ = []
        self.missing_env_vars_ = []

    def is_missing(self):
        return len(self.missing_executables_) or len(self.missing_env_vars_)

    def run_command(self, exe, args) -> List[str]:
        # TODO figure out something that happens when the whole things fails
        cmd = f"{self.mapper.get(exe,exe)} {' '.join(args)}"
        if exe in self.missing_executables_:
            _LOGGER.error(
                f"This environment is missing '{exe}' and cannot run the command '{cmd}'"
            )
            _LOGGER.error(f"Exiting...")
            exit(1)
        _LOGGER.info(f"Running command: '{cmd}'...")
        result = os.popen(cmd).read().splitlines()
        return result

    def __getattr__(self, key: str) -> str:
        return self.mapper[key]


#em = EnvironmentManager(
#    env_vars=["AMBERHOME"],
#    executables=[
#        "tleap",
#        "ambpdb",
#        "cpptraj",
#        "mpirun",
#        "$AMBERHOME/bin/sander.MPI",
#        "$AMBERHOME/bin/pmemd.cuda",
#        "$AMBERHOME/bin/MMPBSA.py.MPI",
#    ],
#)
