"""Here is everything job manager need to know about EXPANSE of SDSC
TODO: group them into a Slurm parent class

Author: Qianzhen (QZ) Shao <qianzhen.shao@vanderbilt.edu>
Date: 2022-04-13
"""
import re
import os
from subprocess import CompletedProcess, SubprocessError, run
import time

from Class_Conf import Config
from helper import round_by, run_cmd
from .accre import Accre


class Expanse(Accre):
    '''
    The EXPANSE interface
    '''
    #############################
    ### External use constant ###
    #############################
    NAME = 'EXPANSE'

    # environment presets #
    AMBER_ENV = { 
        'CPU': '''module load cpu/0.15.4  gcc/9.2.0  openmpi/3.1.6
module load amber/20''', # only this version have sander.MPI
        'GPU': '''module load gpu/0.15.4 openmpi/4.0.4
module load amber/20'''
    }

    G16_ENV = {
        'CPU':{ 'head' : '''module load cpu/0.15.4
module load gaussian/16.C.01
export TMPDIR=/scratch/$USER/job_$SLURM_JOB_ID
mkdir $TMPDIR
export GAUSS_SCRDIR=$TMPDIR''',
                'tail' : '''rm -rf $TMPDIR'''},
        'GPU': None
    }

    #############################
    ### Internal use constant ###
    #############################
    # command for submission
    SUBMIT_CMD = 'sbatch'
    # regex pattern for extracting job id from stdout
    JOB_ID_PATTERN = r'Submitted batch job ([0-9]+)'
    # command for control & monitor
    KILL_CMD = 'scancel'
    HOLD_CMD = 'scontrol hold'
    RELEASE_CMD = 'scontrol release'
    INFO_CMD = ['squeue', 'sacct'] # will check by order if previous one has no info
    # dict of job state
    JOB_STATE_MAP = {
        'pend' : ['CONFIGURING', 'PENDING', 'REQUEUE_FED', 'REQUEUE_HOLD', 'REQUEUED'],
        'run' : ['COMPLETING', 'RUNNING', 'STAGE_OUT'],
        'cancel' : ['CANCELLED', 'DEADLINE', 'TIMEOUT'],
        'complete' : ['COMPLETED'],
        'error' : ['BOOT_FAIL', 'FAILED', 'NODE_FAIL', 'OUT_OF_MEMORY', 'PREEMPTED', 'REVOKED', 'STOPPED', 'SUSPENDED'],
        'exception': ['RESIZING', 'SIGNALING', 'SPECIAL_EXIT', 'RESV_DEL_HOLD' ]
    }

    RES_KEYWORDS_MAP = { 
        'core_type' : None,
        'nodes':'nodes=',
        'node_cores' : {'cpu': 'ntasks-per-node=', 'gpu': 'gpu='},
        'job_name' : 'job-name=',
        'partition' : 'partition=',
        'mem_per_core' : {'cpu': 'mem=', 'gpu': 'mem='}, # previously using mem-per-gpu= change to mem= (calculate the total memory) base on issue #57
        'walltime' : 'time=',
        'account' : 'account='
    }

    PARTITION_VALUE_MAP = {
        'production' : {'cpu': 'shared',
                        'gpu': 'gpu-shared'},
        'debug': {'cpu': 'debug',
                  'gpu': 'gpu-debug'}
    } # TODO do we really want to make partition general and parse it for each cluster?

