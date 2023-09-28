"""Defines SystemConfig() which holds configuration settings for processes that will be spawned by 
enzy_htp. Controls number of cores, memory usage, and locations of temp directories. Values can
be set/accessed via string keys. A global instance of SystemConfig() is owned by the module singleton
config variable. File also contains default_system_config() which creates a default version of 
the SystemConfig() object.

Author: Qianzhen (QZ) Shao <qianzhen.shao@vanderbilt.edu>
Author: Chris Jurich <chris.jurich@vanderbilt.edu>

Date: 2022-10-16
"""
import os
from typing import Any, List
from copy import deepcopy
from time import strftime, localtime

from .base_config import BaseConfig
from enzy_htp.core import _LOGGER
from enzy_htp.core import enzyhtp_info


class SystemConfig(BaseConfig):
    """Class that holds system settings for enzy_htp. Similar to other classes in this
    sub-module, SHOULD NOT be directly created by the end users. Instead, it should be 
    accessed via the singleton config variable. 

    Attributes:
        N_CORES: int() describing max number of cores enzy_htp has access to.
        MEM_PER_CORE: int() max memory per core in megabytes (1GB = 1000).
        WORK_DIR: str() saying which directory enzy_htp is being run from.
        SCRATCH_DIR: str() with default temp directory. Set to WORK_DIR/scratch by default.
        CHILDREN_SCRIPT_WATERMARK: str() The watermark for EnzyHTP generated scripts.
    """

    N_CORES: int = 24
    """Number of cores each process managed by enzy_htp has access to."""

    MEM_PER_CORE: int = 2000
    """Memory in megabytes that each enzy_htp process has."""

    WORK_DIR: str = os.getcwd()
    """Directory work is being done in by enzy_htp."""

    SCRATCH_DIR: str = f"{WORK_DIR}/scratch"
    """Default temp directory for enzy_htp. Defaults to WORK_DIR/scratch"""

    CHILDREN_SCRIPT_WATERMARK: str = f"Script generated by EnzyHTP {str(enzyhtp_info.get_version())} in {strftime('%Y-%m-%d %H:%M:%S', localtime())}"
    """The watermark for EnzyHTP generated scripts"""

    JOB_ID_LOG_PATH: str = "DEFAULT"
    """The path for the log file that stores all the job ids for submitted ClusterJobs.
    (default: job_obj.sub_dir/submitted_job_ids.log)"""

    def required_executables(self) -> List[str]:
        """A list of all required executables for SystemConfig."""
        return list()

    def required_env_vars(self) -> List[str]:
        """A list of all required environment variables for SystemConfig."""
        return list()

    def required_py_modules(self) -> List[str]:
        """A list of all required environment python modules for SystemConfig."""
        return list()


def default_system_config() -> SystemConfig:
    """Creates a deep-copied default version of the SystemConfig() class."""
    return deepcopy(SystemConfig())
