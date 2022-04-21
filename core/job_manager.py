"""Manage the job queue for running jobs on a cluster. Interface with different linux resource managers (e.g. slurm)
The general workflow is
    (take job commands)
    1) compile the submission script 
    2) submit and monitor the job 
    3) record the completion of the job.
    (give files containing the stdout/stderr)
In a dataflow point of view it should be analogous to subprocess.run()

Feature:
    - Allow users to add support for their own clusters. (By making new ClusterInterface classes)

Author: Qianzhen (QZ) Shao <qianzhen.shao@vanderbilt.edu>
Date: 2022-04-13
"""
from subprocess import run
from typing import Union
from plum import dispatch
import os

from .clusters import *  # pylint: disable=unused-wildcard-import,wildcard-import
from core.clusters._interface import ClusterInterface
from helper import line_feed
from Class_Conf import Config

class ClusterJob():
    '''
    This class handle jobs for cluster calculation
    API:
    constructor:
        ClusterJob.config_job()
    property:
        cluster:    cluster used for running the job (pick from list in /core/cluster/)
        sub_script_str: submission script content
        sub_script_path: submission script path
    method:
        submit()
    '''

    def __init__(self,
                 cluster: ClusterInterface,
                 sub_script_str: str
                 ) -> None:
        self.cluster = cluster
        self.sub_script_str = sub_script_str
        
        self.sub_script_path: str

    ### config (construct object) ###
    @classmethod
    def config_job( cls, 
                commands: Union[list[str], str],
                cluster: ClusterInterface,
                env_settings: Union[list[str], str],
                res_keywords: dict[str, str]
                ) -> 'ClusterJob':
        '''
        config job and generate a ClusterJob instance (cluster, sub_script_str)

        Args:
        commands: 
            commands to run. Can be a str of commands or a list containing strings of commands.
        cluster: 
            cluster for running the job. Should be a ClusterInterface object. 
            Available clusters can be found under core/clusters as python class defination.
            To define a new cluster class for support, reference the ClusterInterface requirement.
        env_settings: 
            environment settings in the submission script. Can be a string or list of strings
            for cmds in each line.
            Since environment settings are attached to job types. It is more conserved than the command.
            **Use presets in ClusterInterface classes to save effort**
        res_keywords: 
            resource settings. Can be a dictionary indicating each keywords or the string of the whole section.
            The name and value should be exactly the same as required by the cluster.
            **Use presets in ClusterInterface classes to save effort**
        
        Return:
        A ClusterJob object

        Example:
        >>> cluster = accre.Accre()
        >>> job = ClusterJob.config_job(
                        commands = 'g16 < xxx.gjf > xxx.out',
                        cluster = cluster,
                        env_settings = [cluster.AMBER_GPU_ENV, cluster.G16_CPU_ENV],
                        res_keywords = cluster.CPU_RES
                    )
        >>> print(job.sub_script_str)    
        #!/bin/bash
        #SBATCH --core_type=cpu
        #SBATCH --node_cores=24
        #SBATCH --job_name=job_name
        #SBATCH --partition=production
        #SBATCH --mem_per_core=4G
        #SBATCH --walltime=24:00:00
        #SBATCH --account=xxx

        #Script generated by EnzyHTP in 2022-04-21 14:09:18

        export AMBERHOME=/dors/csb/apps/amber19/
        export CUDA_HOME=$AMBERHOME/cuda/10.0.130
        export LD_LIBRARY_PATH=$AMBERHOME/cuda/10.0.130/lib64:$AMBERHOME/cuda/RHEL7/10.0.130/lib:$LD_LIBRARY_PATH
        module load Gaussian/16.B.01
        mkdir $TMPDIR/$SLURM_JOB_ID
        export GAUSS_SCRDIR=$TMPDIR/$SLURM_JOB_ID

        g16 < xxx.gjf > xxx.out
        '''
        command_str = cls._get_command_str(commands)
        env_str = cls._get_env_str(env_settings)
        res_str = cls._get_res_str(res_keywords, cluster)
        sub_script_str = cls._get_sub_script_str(
                            command_str, 
                            env_str, 
                            res_str, 
                            f'# {Config.WATERMARK}{line_feed}'
                            )

        return cls(cluster, sub_script_str)

    @staticmethod
    @dispatch
    def _get_command_str(cmd: list) -> str:
        return line_feed.join(cmd)+line_feed

    @staticmethod
    @dispatch
    def _get_command_str(cmd: str) -> str:
        return cmd+line_feed

    @staticmethod
    @dispatch
    def _get_env_str(env: list) -> str:
        return line_feed.join(env)+line_feed

    @staticmethod
    @dispatch
    def _get_env_str(env: str) -> str:
        return env+line_feed

    @staticmethod
    @dispatch
    def _get_res_str(res: dict, 
                     cluster: ClusterInterface) -> str:
        return cluster.format_resource_str(res)

    @staticmethod
    @dispatch
    def _get_res_str(res: str, 
                     cluster: ClusterInterface) -> str:
        return res

    @staticmethod
    def _get_sub_script_str(command_str: str, env_str: str, res_str: str, watermark: str) -> str:
        '''
        combine command_str, env_str, res_str to sub_script_str
        '''
        sub_script_str= line_feed.join((res_str, watermark, env_str, command_str))
        return sub_script_str

    ### submit ###
    def submit(self, sub_dir, script_path=None, debug=0):
        '''
        submit the job to the cluster queue. Make the submission script. Submit.
        Arg:
            sub_dir: dir for submission. commands in the sub script usually run under this dir. 
            script_path: path for submission script generation. '
                         (default: sub_dir/submit.cmd; 
                          will be sub_dir/submit_#.cmd if the file exists
                          # is a growing index)
                         
        Return:
            self.job_id

        Attribute added:
            sub_script_path
            job_id
            sub_dir
        
        Example:
            >>> sub_dir = '/EnzyHTP-test/test_job_manager/'
            >>> job.submit( sub_dir= sub_dir,
                            script_path= sub_dir + 'test.cmd')
        '''
        # make default value for filename
        if script_path is None:
            script_path = sub_dir + '/submit.cmd'
            i = 0
            while os.path.isfile(script_path):
                i += 1
                script_path = sub_dir + f'/submit_{i}.cmd'  # TODO(shaoqz): move to helper

        self.sub_script_path = self._deploy_sub_script(script_path)
        self.job_id = self.cluster.submit_job(sub_dir, script_path, debug=debug)
        self.sub_dir = sub_dir

        return self.job_id

    def _deploy_sub_script(self, out_path: str) -> None:
        '''
        deploy the submission scirpt for current job
        store the out_path to self.sub_script_path
        '''
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(self.sub_script_str)
        return out_path
            
    ### kill ###
    def kill(self):
        '''
        kill the job with the job_id
        '''
        self.cluster.kill_job(self.job_id)

    ### monitor ###


    ### misc ###
    @dispatch
    def _(self):
        '''
        dummy method for dispatch
        '''
        pass