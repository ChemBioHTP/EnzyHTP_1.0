#!/bin/bash
#SBATCH --job-name=ETIY127A          # Assign an 8-character name to your job
#SBATCH --account=xxx
#SBATCH --partition=turing
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --ntasks=6
#SBATCH --mem=50G
#SBATCH --time=5-00:00:00         # Total run time limit (HH:MM:SS)
#SBATCH --export=ALL

# Script generated by EnzyHTP in 2022-04-21 00:16:19

export AMBERHOME=/dors/csb/apps/amber19/
export CUDA_HOME=$AMBERHOME/cuda/10.0.130
export LD_LIBRARY_PATH=$AMBERHOME/cuda/10.0.130/lib64:$AMBERHOME/cuda/RHEL7/10.0.130/lib:$LD_LIBRARY_PATH

g16 < xxx.gjf > xxx.out