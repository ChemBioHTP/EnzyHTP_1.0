#!/bin/bash
#SBATCH --job-name=JM_ARA
#SBATCH --account=yang_lab_csb
#SBATCH --partition=production
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=10G
#SBATCH --time=2-00:00:00

export PGI_FASTMATH_CPU=sandybridge
export OMP_THREAD_LIMIT=256

# Gaussian (for formchk)
module load Gaussian/16.B.01
# AmberTool (for tleap antechamber parmchk)
source /home/shaoq1/bin/amber_env/amber-accre.sh
# Multiwfn
module load GCC/6.4.0-2.28  OpenMPI/2.1.1
export KMP_STACKSIZE=200000000
export Multiwfnpath=/home/jiany37/Software_installed/Multiwfn_3.7_bin_Linux_noGUI
export PATH=$PATH:$Multiwfnpath
# EnzyHTP
source ~/bin/miniconda3/bin/activate
conda activate MutaGen
export PYTHONPATH=$PYTHONPATH:~/bin/EnzyHTP

python -u FAcD-gen-ara.py > FAcD-gen-ara.py.out