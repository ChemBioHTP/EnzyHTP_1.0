from subprocess import run
import re
import pytest

from core import clusters
from core.job_manager import *

command_2_run = ['g16 < xxx.gjf > xxx.out']
env_settings_list =  [  'module load GCC/6.4.0-2.28  OpenMPI/2.1.1', 
                        'module load Amber/17-Python-2.7.14', 
                        'module unload Python/2.7.14 numpy/1.13.1-Python-2.7.14']
res_keywords_dict = {   'core_type' : 'cpu',
                        'node_cores' : '24',
                        'job_name' : 'job_name',
                        'partition' : 'production',
                        'mem_per_core' : '4G',
                        'walltime' : '24:00:00',
                        'account' : 'xxx'}

env_settings_str = '''module load GCC/6.4.0-2.28  OpenMPI/2.1.1
module load Amber/17-Python-2.7.14
module unload Python/2.7.14 numpy/1.13.1-Python-2.7.14'''
res_keywords_str = '''#!/bin/bash
#SBATCH --core_type=cpu
#SBATCH --node_cores=24
#SBATCH --job_name=job_name
#SBATCH --partition=production
#SBATCH --mem_per_core=4G
#SBATCH --walltime=24:00:00
#SBATCH --account=xxx
'''
env_settings_dict = {'head' : env_settings_str, 'tail': 'echo hello'}

correct_sub_script_str = r'''#!/bin/bash
#SBATCH --core_type=cpu
#SBATCH --node_cores=24
#SBATCH --job_name=job_name
#SBATCH --partition=production
#SBATCH --mem_per_core=4G
#SBATCH --walltime=24:00:00
#SBATCH --account=xxx

# Script generated by EnzyHTP in [0-9]+-[0-9]+-[0-9]+ [0-9]+:[0-9]+:[0-9]+

module load GCC/6\.4\.0-2\.28  OpenMPI/2\.1\.1
module load Amber/17-Python-2\.7\.14
module unload Python/2\.7\.14 numpy/1\.13\.1-Python-2\.7\.14

g16 < xxx\.gjf > xxx\.out
'''

correct_sub_script_str_2 = r'''#!/bin/bash
#SBATCH --core_type=cpu
#SBATCH --node_cores=24
#SBATCH --job_name=job_name
#SBATCH --partition=production
#SBATCH --mem_per_core=4G
#SBATCH --walltime=24:00:00
#SBATCH --account=xxx

# Script generated by EnzyHTP in [0-9]+-[0-9]+-[0-9]+ [0-9]+:[0-9]+:[0-9]+

module load GCC/6\.4\.0-2\.28  OpenMPI/2\.1\.1
module load Amber/17-Python-2\.7\.14
module unload Python/2\.7\.14 numpy/1\.13\.1-Python-2\.7\.14

g16 < xxx\.gjf > xxx\.out

echo hello
'''


sub_script_str = '''#!/bin/bash
#SBATCH --partition=debug
#SBATCH --job-name=JM-test
#SBATCH --nodes=1
#SBATCH --tasks-per-node=24
#SBATCH --mem-per-cpu=2G
#SBATCH --time=30:00
#SBATCH --account=yang_lab_csb

module load Gaussian/16.B.01
mkdir $TMPDIR/$SLURM_JOB_ID
export GAUSS_SCRDIR=$TMPDIR/$SLURM_JOB_ID

g16 < TS-2-dp-opt.gjf > TS-2-dp-opt.out
rm -r $TMPDIR/$SLURM_JOB_ID
trap 'rm -rf $TMPDIR/$SLURM_JOB_ID' EXIT'''

sub_script_long_str = '''#!/bin/bash
#SBATCH --partition=production
#SBATCH --job-name=JM-test
#SBATCH --nodes=1
#SBATCH --tasks-per-node=24
#SBATCH --mem-per-cpu=2G
#SBATCH --time=3-00:00:00
#SBATCH --account=yang_lab_csb

module load Gaussian/16.B.01
mkdir $TMPDIR/$SLURM_JOB_ID
export GAUSS_SCRDIR=$TMPDIR/$SLURM_JOB_ID

g16 < QM_test.gjf > QM_test.out
trap 'rm -rf $TMPDIR/$SLURM_JOB_ID' EXIT'''

def get_array_sub_str(idx):
    return f'''#!/bin/bash
#SBATCH --partition=production
#SBATCH --job-name=JM-test
#SBATCH --nodes=1
#SBATCH --tasks-per-node=24
#SBATCH --mem-per-cpu=2G
#SBATCH --time=3-00:00:00
#SBATCH --account=yang_lab_csb

module load Gaussian/16.B.01
mkdir $TMPDIR/$SLURM_JOB_ID
export GAUSS_SCRDIR=$TMPDIR/$SLURM_JOB_ID

g16 < QM_test.gjf > QM_test_{idx}.out
trap 'rm -rf $TMPDIR/$SLURM_JOB_ID' EXIT'''

cluster = clusters.accre.Accre()

test_sub_dir = './test/core/test_file/'
test_file_paths = [f'{test_sub_dir}QM_test.out'] # paths to be cleaned

def test_ClusterJob_config_by_list():
    job = ClusterJob.config_job(
        commands = command_2_run,
        cluster = cluster,
        env_settings = env_settings_list,
        res_keywords = res_keywords_dict
    )
    assert re.match(correct_sub_script_str, job.sub_script_str) != None 

def test_ClusterJob_config_by_str():
    job = ClusterJob.config_job(
        commands = command_2_run,
        cluster = cluster,
        env_settings = env_settings_str,
        res_keywords = res_keywords_str
    )
    assert re.match(correct_sub_script_str, job.sub_script_str) != None 

def test_ClusterJob_config_by_dict():
    job = ClusterJob.config_job(
        commands = command_2_run,
        cluster = cluster,
        env_settings = env_settings_dict,
        res_keywords = res_keywords_dict
    )
    assert re.match(correct_sub_script_str_2, job.sub_script_str) != None 

def test_ClusterJob_config_also_submit_info():
    test_sub_script_path = test_sub_dir+'/test.cmd'
    job = ClusterJob.config_job(
        commands = command_2_run,
        cluster = cluster,
        env_settings = env_settings_str,
        res_keywords = res_keywords_str,
        sub_dir=test_sub_dir,
        sub_script_path=test_sub_script_path
    )
    info = job.submit(debug=1)
    test_file_paths.append(test_sub_script_path)
    assert info == (f'sbatch {os.path.abspath(test_sub_script_path)}', test_sub_dir, test_sub_script_path)

def test_ClusterJob_preset():
    job = ClusterJob.config_job(
        commands = command_2_run,
        cluster = cluster,
        env_settings = cluster.G16_CPU_ENV,
        res_keywords = cluster.CPU_RES
    )
    # print(job.sub_script_str)

@pytest.mark.accre
def test_ClusterJob_submit_job_id_ACCRE():
    '''
    only run on accre
    '''
    job = ClusterJob(clusters.accre.Accre(), sub_script_str=sub_script_str)
    job.submit( sub_dir=test_sub_dir,
                script_path=f'{test_sub_dir}test.cmd')
    test_file_paths.extend([job.job_cluster_log, job.sub_script_path])
    run(f'scancel {job.job_id}', timeout=20, check=True,  text=True, shell=True, capture_output=True)
    assert len(job.job_cluster_log) > 0
    assert len(job.job_id) > 0

@pytest.mark.accre
def test_ClusterJob_submit_default_script_path_ACCRE():
    '''
    only run on accre
    '''
    job = ClusterJob(clusters.accre.Accre(), sub_script_str=sub_script_str)
    job.submit(sub_dir=test_sub_dir)
    test_file_paths.extend([job.job_cluster_log, job.sub_script_path])
    # use explictly the scancel here to decouple the test
    run(f'scancel {job.job_id}', timeout=20, check=True,  text=True, shell=True, capture_output=True)
    assert len(job.job_id) > 0

@pytest.mark.accre
def test_ClusterJob_kill_job_ACCRE():
    '''
    only run on accre
    '''
    job = ClusterJob(clusters.accre.Accre(), sub_script_str=sub_script_str)
    job.submit(sub_dir=test_sub_dir)
    test_file_paths.extend([job.job_cluster_log, job.sub_script_path])
    job.kill()

@pytest.mark.accre
def test_ClusterJob_get_state_ACCRE():
    '''
    only run on accre
    '''
    job = ClusterJob(clusters.accre.Accre(), sub_script_str=sub_script_str)
    job.submit(sub_dir=test_sub_dir)
    test_file_paths.extend([job.job_cluster_log, job.sub_script_path])
    assert job.get_state()[0] in ['pend', 'run']
    job.kill()
    assert job.get_state()[0] == 'cancel'

@pytest.mark.accre
@pytest.mark.long
def test_ClusterJob_wait_to_end_ACCRE():
    '''
    only run on accre
    '''
    job = ClusterJob(clusters.accre.Accre(), sub_script_str=sub_script_long_str)
    # submit and record the file
    job.submit(sub_dir=test_sub_dir)
    test_file_paths.extend([job.job_cluster_log, job.sub_script_path])

    Config.debug = 2
    job.wait_to_end(60)
    # TODO add some assert

@pytest.mark.temp
@pytest.mark.accre
@pytest.mark.long
def test_ClusterJob_wait_to_array_end_ACCRE():
    # make the test array
    jobs = []
    for i in range(10):
        jobs.append(ClusterJob( clusters.accre.Accre(), 
                                sub_script_str=get_array_sub_str(i), 
                                sub_dir=test_sub_dir, 
                                sub_script_path=f'{test_sub_dir}/test_{i}.cmd'))
    # job array



### utilities ###
@pytest.mark.clean
def test_clean_files():
    for f_path in test_file_paths:
        if os.path.isfile(f_path):
            os.remove(f_path)
        else:
            print(f'no such file {f_path}')
