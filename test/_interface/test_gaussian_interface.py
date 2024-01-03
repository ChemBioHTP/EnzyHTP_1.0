"""Testing enzy_htp._interface.gaussian_interface.py
Author: Qianzhen (QZ) Shao <shaoqz@icloud.com>
Date: 2023-12-29
"""
import re
import pytest
import os

from enzy_htp.core.clusters.accre import Accre
import enzy_htp.core.file_system as fs
from enzy_htp.chemical.level_of_theory import QMLevelofTheory, MMLevelofTheory
from enzy_htp._config.armer_config import ARMerConfig
from enzy_htp.structure import structure_constraint as stru_cons
from enzy_htp.structure.structure_region import create_region_from_selection_pattern
from enzy_htp.structure.structure_operation.charge import init_charge
from enzy_htp import PDBParser
from enzy_htp import interface
from enzy_htp._interface.gaussian_interface import GaussianSinglePointEngine

DATA_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/data/"
WORK_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/work_dir/"
sp = PDBParser()
gi = interface.gaussian

@pytest.mark.accre
def test_single_point_make_job_lv1():
    """Test GaussianSinglePointEngine().make_job()
    Using Accre as an example cluster
    level 1:
    - full structure (only 1 ligand)"""
    test_stru = sp.get_structure(f"{DATA_DIR}H5J.pdb")
    test_stru.assign_ncaa_chargespin({"H5J" : (0,1)})
    test_method = QMLevelofTheory(
        basis_set="6-31G(d)",
        method="HF",
        solvent="water",
        solv_method="SMD",
    )
    cluster_job_config = {
        "cluster" : Accre(),
        "res_keywords" : {"account" : "yang_lab_csb",
                         "partition" : "production"}
    }

    qm_engine = gi.build_single_point_engine(
        region=None,
        method=test_method,
        keep_geom=True,
        cluster_job_config=cluster_job_config,
        work_dir=f"{WORK_DIR}/QM_SPE/"
    )
    test_job, test_egg = qm_engine.make_job(test_stru)

    answer_pattern = r"""#!/bin/bash
#SBATCH --nodes=1
#SBATCH --tasks-per-node=8
#SBATCH --job-name=QM_SPE_EnzyHTP
#SBATCH --partition=production
#SBATCH --mem-per-cpu=3G
#SBATCH --time=3-00:00:00
#SBATCH --account=yang_lab_csb
#SBATCH --export=NONE

# Script generated by EnzyHTP [0-9]\.[0-9]\.[0-9] in [0-9]+-[0-9]+-[0-9]+ [0-9]+:[0-9]+:[0-9]+

module load Gaussian/16\.B\.01
mkdir \$TMPDIR/\$SLURM_JOB_ID
export GAUSS_SCRDIR=\$TMPDIR/\$SLURM_JOB_ID

g16 < .*test/_interface/work_dir//QM_SPE//gaussian_spe_?[0-9]*\.gjf > .*test/_interface/work_dir//QM_SPE//gaussian_spe_?[0-9]*\.out

rm -rf \$TMPDIR/\$SLURM_JOB_ID
"""
    answer_gout_pattern = r".*test/_interface/work_dir//QM_SPE//gaussian_spe_?[0-9]*\.out"

    assert re.match(answer_pattern, test_job.sub_script_str)
    assert re.match(answer_gout_pattern, test_egg.gout_path)

    fs.safe_rmdir(qm_engine.work_dir)

def test_build_single_point_engine_default():
    """as said in the name. Assert several default values
    as samples."""
    gi = interface.gaussian
    md_step: GaussianSinglePointEngine = gi.build_single_point_engine()
    assert md_step.method == QMLevelofTheory(
        basis_set = "def2-svp",
        method = "pbe0",
        solvent = None,
        solv_method = None,
    )
    assert md_step.region == None
    assert md_step.cluster_job_config["res_keywords"] == ARMerConfig.QM_SPE_CPU_RES
    assert md_step.keep_geom == True
    assert md_step.capping_method == "res_ter_cap"

def test_build_single_point_engine_res_keywords():
    """as said in the name. Assert several default values
    as samples."""
    gi = interface.gaussian
    md_step: GaussianSinglePointEngine = gi.build_single_point_engine(
        cluster_job_config={
            "cluster" : None,
            "res_keywords" : {"partition" : "production",
                                "account" : "yang_lab",}
        })
    assert md_step.cluster_job_config["cluster"] is None
    assert md_step.cluster_job_config["res_keywords"]["core_type"] == "cpu"
    assert md_step.cluster_job_config["res_keywords"]["partition"] == "production"
    assert md_step.cluster_job_config["res_keywords"]["nodes"] == "1"
    assert md_step.cluster_job_config["res_keywords"]["node_cores"] ==  "8"
    assert md_step.cluster_job_config["res_keywords"]["job_name"] ==  "QM_SPE_EnzyHTP"
    assert md_step.cluster_job_config["res_keywords"]["mem_per_core"] ==  "3G"
    assert md_step.cluster_job_config["res_keywords"]["walltime"] ==  "3-00:00:00"
    assert md_step.cluster_job_config["res_keywords"]["account"] ==  "yang_lab"

def test_get_method_keyword_from_name():
    """as name"""
    test_name = "b3lyp-d3"
    answer_kw = "b3lyp em=gd3"
    test_kw = gi.get_method_keyword_from_name(test_name)
    assert answer_kw == test_kw

    test_name = "b3lyp-d3bj"
    answer_kw = "b3lyp em=gd3bj"
    test_kw = gi.get_method_keyword_from_name(test_name)
    assert answer_kw == test_kw

    test_name = "b3lyp-D3(BJ)"
    answer_kw = "b3lyp em=gd3bj"
    test_kw = gi.get_method_keyword_from_name(test_name)
    assert answer_kw == test_kw

    test_name = "pbe0-D3(BJ)"
    answer_kw = "pbe1pbe em=gd3bj"
    test_kw = gi.get_method_keyword_from_name(test_name)
    assert answer_kw == test_kw

def test_lot_to_keyword():
    """as name"""
    test_lot = QMLevelofTheory(
        basis_set="6-31G(d)",
        method="HF",
        solvent="water",
        solv_method="SMD",
    )
    answer_kw = ("HF 6-31G(d) scrf=(SMD,solvent=water)", [], [])
    test_kw = gi.lot_to_keyword(test_lot)
    assert answer_kw == test_kw

def test_get_geom_lines():
    """as name.
    answer confirmed using GaussView manually"""
    test_atoms = sp.get_structure(f"{DATA_DIR}H5J.pdb").atoms
    answer_lines = [
        "O         26.31000000     -2.47500000    -48.71100000",
        "N         26.99300000     -2.19100000    -49.70300000",
        "O         28.21800000     -1.97000000    -49.63900000",
        "C         26.34700000     -2.11100000    -50.99500000",
        "C         24.96800000     -2.35600000    -51.09900000",
        "H         24.35300000     -2.60600000    -50.24700000",
        "C         27.13100000     -1.78700000    -52.12100000",
        "H         28.18900000     -1.61100000    -51.99600000",
        "C         26.56500000     -1.69700000    -53.38000000",
        "H         27.16700000     -1.44800000    -54.24200000",
        "C         25.17500000     -1.93700000    -53.52700000",
        "C         24.40200000     -2.26500000    -52.36300000",
        "C         23.03800000     -2.45000000    -52.83000000",
        "H         22.29200000     -2.70700000    -52.09200000",
        "N         22.84300000     -2.29500000    -54.05600000",
        "O         24.50900000     -1.89000000    -54.63400000",
    ]
    geom_lines = gi.get_geom_lines(test_atoms, [])

    assert geom_lines == answer_lines

def test_get_geom_lines_w_cons(): # TODO finish this when needed
    """as name.
    answer confirmed using GaussView manually"""
    test_atoms = sp.get_structure(f"{DATA_DIR}H5J.pdb").atoms
    answer_lines = [
    ]
    geom_lines = gi.get_geom_lines(test_atoms, ["TODO"])
    assert False

def test_make_mol_spec():
    """as name"""
    test_stru = sp.get_structure(f"{DATA_DIR}KE_07_R7_2_S.pdb")
    test_stru_region = create_region_from_selection_pattern(
        test_stru, "br. (resi 254 around 5)"
    )
    init_charge(test_stru_region)
    constraints = []
    answer = [
        "0 1",
        "N         25.65500000     -2.33200000    -59.79200000",
        "H         26.38700000     -3.02400000    -59.72400000",
        "C         25.56900000     -1.31200000    -58.75300000",
        "H         24.65400000     -0.73900000    -58.90300000",
        "C         25.51900000     -1.96200000    -57.36400000",
        "H         26.43300000     -2.53200000    -57.19600000",
        "H         25.42900000     -1.18700000    -56.60300000",
        "H         24.65900000     -2.63000000    -57.30500000",
        "C         26.73000000     -0.34400000    -58.83800000",
        "O         27.85400000     -0.75100000    -59.09700000",
        "N         28.72900000      2.45900000    -56.57900000",
        "H         29.45200000      1.86600000    -56.96100000",
        "C         28.98600000      3.13500000    -55.30400000",
        "H         28.06700000      3.16600000    -54.71800000",
        "C         30.09100000      2.44100000    -54.48900000",
        "H         30.97000000      2.31700000    -55.12200000",
        "C         30.46400000      3.27600000    -53.25300000",
        "H         29.58600000      3.40000000    -52.61900000",
        "H         31.24700000      2.76600000    -52.69200000",
        "H         30.82400000      4.25500000    -53.57000000",
        "C         29.63800000      1.04800000    -54.05000000",
        "H         29.19400000      0.56100000    -54.91800000",
        "H         30.52700000      0.49800000    -53.74000000",
        "C         28.64000000      1.06700000    -52.92000000",
        "H         27.75100000      1.61600000    -53.22900000",
        "H         28.36400000      0.04500000    -52.66100000",
        "H         29.08300000      1.55400000    -52.05100000",
        "C         29.41000000      4.56700000    -55.59400000",
        "O         30.30100000      4.79800000    -56.41300000",
        "N         21.61000000     -0.01500000    -59.74700000",
        "H         22.41400000     -0.58200000    -59.97600000",
        "C         21.53700000      0.57400000    -58.41600000",
        "H         20.54700000      1.00100000    -58.25700000",
        "C         21.79000000     -0.48300000    -57.34500000",
        "H         22.73000000     -0.99200000    -57.55800000",
        "H         21.85200000      0.00100000    -56.37000000",
        "O         20.74200000     -1.41900000    -57.33700000",
        "H         20.90900000     -2.08000000    -56.66100000",
        "C         22.57500000      1.67100000    -58.28500000",
        "O         23.73300000      1.48500000    -58.65900000",
        "N         24.15400000      3.66700000    -55.27400000",
        "H         24.97000000      3.55100000    -55.85800000",
        "C         24.31900000      3.56400000    -53.82500000",
        "H         23.33100000      3.52100000    -53.36700000",
        "C         25.32400000      1.99300000    -53.28000000",
        "H         24.94000000      1.09900000    -53.77100000",
        "H         26.38200000      2.11000000    -53.51600000",
        "C         25.23900000      1.74200000    -51.80500000",
        "C         26.23900000      1.90000000    -50.89200000",
        "H         27.20100000      2.24600000    -51.27000000",
        "N         25.78900000      1.57200000    -49.63700000",
        "H         26.33700000      1.59800000    -48.78900000",
        "C         24.47200000      1.19600000    -49.72300000",
        "C         23.59500000      0.78100000    -48.73200000",
        "H         23.95100000      0.72700000    -47.70300000",
        "C         22.29700000      0.45600000    -49.12700000",
        "H         21.57600000      0.12800000    -48.37800000",
        "C         21.90300000      0.53900000    -50.43900000",
        "H         20.88500000      0.28000000    -50.73200000",
        "C         22.78200000      0.95300000    -51.43200000",
        "H         22.41700000      1.00100000    -52.45800000",
        "C         24.09300000      1.28900000    -51.07300000",
        "C         25.21200000      4.69300000    -53.33100000",
        "O         26.40400000      4.74200000    -53.63900000",
        "N         15.66700000      2.11700000    -52.11000000",
        "H         16.28000000      2.89200000    -52.31800000",
        "C         16.17100000      1.04900000    -51.27300000",
        "H         15.42700000      0.25500000    -51.33700000",
        "C         18.08300000      0.22400000    -51.69700000",
        "H         18.21600000      0.33100000    -52.77400000",
        "H         18.79900000      0.86100000    -51.17800000",
        "C         18.31400000     -1.22700000    -51.29900000",
        "H         18.46100000     -1.36400000    -50.22800000",
        "H         17.39600000     -1.72700000    -51.60600000",
        "C         19.47900000     -1.81700000    -52.04400000",
        "O         19.38100000     -1.96800000    -53.23800000",
        "O         20.50600000     -2.01300000    -51.44000000",
        "C         16.31400000      1.54800000    -49.84500000",
        "O         16.85300000      2.63300000    -49.62300000",
        "N         17.44400000     -3.74400000    -48.76800000",
        "H         17.37300000     -2.76600000    -48.52800000",
        "C         18.75200000     -4.35900000    -48.75900000",
        "H         18.79300000     -5.13900000    -49.51900000",
        "C         19.85500000     -3.32000000    -49.05800000",
        "H         19.55300000     -2.76000000    -49.94300000",
        "H         19.89700000     -2.64900000    -48.20000000",
        "C         21.22300000     -3.93000000    -49.28900000",
        "C         21.95300000     -4.46400000    -48.23100000",
        "H         21.53000000     -4.42200000    -47.22700000",
        "C         23.19200000     -5.04000000    -48.43500000",
        "H         23.75700000     -5.44900000    -47.59800000",
        "C         23.71400000     -5.09100000    -49.70900000",
        "O         24.94700000     -5.67400000    -49.88800000",
        "H         25.33100000     -5.99800000    -49.07000000",
        "C         23.01600000     -4.57500000    -50.77900000",
        "H         23.42600000     -4.62700000    -51.78800000",
        "C         21.77900000     -3.98400000    -50.56200000",
        "H         21.22700000     -3.55300000    -51.39700000",
        "C         18.96400000     -4.95800000    -47.38200000",
        "O         18.91200000     -4.23300000    -46.38200000",
        "N         21.72000000     -6.74700000    -45.16100000",
        "H         21.36300000     -5.96300000    -44.63300000",
        "C         23.09700000     -7.15900000    -44.93700000",
        "H         23.50100000     -7.62300000    -45.83700000",
        "C         23.96800000     -5.95700000    -44.57400000",
        "H         23.58100000     -5.48700000    -43.67000000",
        "H         24.99200000     -6.28900000    -44.40100000",
        "H         23.95300000     -5.23700000    -45.39200000",
        "C         23.14700000     -8.18500000    -43.83300000",
        "O         22.76200000     -7.89000000    -42.71000000",
        "N         26.06900000      0.37100000    -42.37700000",
        "H         25.12300000      0.38500000    -42.73200000",
        "C         27.14600000      0.00500000    -43.29200000",
        "H         26.72900000     -0.27600000    -44.25900000",
        "C         28.09800000      1.18000000    -43.49400000",
        "H         28.48200000      1.51300000    -42.53000000",
        "H         28.92900000      0.87500000    -44.13000000",
        "O         27.39700000      2.23900000    -44.11200000",
        "H         27.99000000      2.98200000    -44.24200000",
        "C         27.87200000     -1.24400000    -42.82100000",
        "O         29.09500000     -1.33600000    -42.88300000",
        "N         17.29500000     -7.39500000    -51.61700000",
        "H         17.03100000     -6.53500000    -51.15800000",
        "C         18.70400000     -7.59200000    -51.96700000",
        "H         18.78900000     -8.29300000    -52.79700000",
        "C         19.40900000     -6.28100000    -52.35600000",
        "H         19.42500000     -5.61000000    -51.49700000",
        "C         20.83500000     -6.57700000    -52.79500000",
        "H         20.81900000     -7.24700000    -53.65400000",
        "H         21.33200000     -5.64600000    -53.07000000",
        "H         21.37700000     -7.04900000    -51.97600000",
        "C         18.66000000     -5.56500000    -53.47100000",
        "H         17.64900000     -5.33100000    -53.13800000",
        "H         19.18100000     -4.64200000    -53.72500000",
        "H         18.61300000     -6.20900000    -54.34900000",
        "C         19.39700000     -8.22300000    -50.76200000",
        "O         19.39100000     -7.68100000    -49.65000000",
        "N         31.90400000     -9.94500000    -48.39200000",
        "H         31.51000000    -10.16400000    -47.48800000",
        "C         32.33700000     -8.57300000    -48.64400000",
        "H         31.71400000     -8.12000000    -49.41600000",
        "C         32.21200000     -7.74100000    -47.36300000",
        "H         31.17100000     -7.87400000    -47.06900000",
        "H         32.86200000     -8.18500000    -46.60900000",
        "C         32.51900000     -6.25100000    -47.48600000",
        "H         33.55000000     -6.13200000    -47.81800000",
        "C         31.59200000     -5.59000000    -48.47700000",
        "H         30.56000000     -5.70900000    -48.14500000",
        "H         31.83100000     -4.52900000    -48.54700000",
        "H         31.71400000     -6.05500000    -49.45500000",
        "C         32.41700000     -5.56400000    -46.12000000",
        "H         33.13100000     -6.01500000    -45.43100000",
        "H         32.63900000     -4.50300000    -46.22900000",
        "H         31.40800000     -5.68500000    -45.72600000",
        "C         33.76500000     -8.51500000    -49.17400000",
        "O         34.69500000     -8.96500000    -48.50600000",
        "N         23.85100000    -10.48800000    -53.65100000",
        "H         23.66200000    -10.95100000    -52.77300000",
        "C         24.91000000     -9.49800000    -53.69200000",
        "H         25.30000000     -9.42400000    -54.70700000",
        "C         24.39400000     -8.12300000    -53.26500000",
        "H         23.52500000     -7.85600000    -53.86600000",
        "H         24.12100000     -8.11700000    -52.21000000",
        "C         25.39700000     -7.03000000    -53.45400000",
        "N         25.72100000     -6.13600000    -52.46200000",
        "C         26.63400000     -5.29100000    -52.91800000",
        "H         27.02000000     -4.49200000    -52.28500000",
        "N         26.91600000     -5.62100000    -54.16400000",
        "H         27.58300000     -5.15400000    -54.76100000",
        "C         26.15800000     -6.70600000    -54.52800000",
        "H         26.25300000     -7.12600000    -55.52900000",
        "C         26.07600000     -9.91400000    -52.81700000",
        "O         25.87900000    -10.41100000    -51.70000000",
        "N         27.27500000     -9.68000000    -53.35500000",
        "H         27.22500000     -9.43200000    -54.33300000",
        "C         28.61000000     -9.87100000    -52.74700000",
        "H         29.31500000     -9.22600000    -53.27100000",
        "C         28.66700000     -9.54400000    -51.24900000",
        "H         28.02800000    -10.25500000    -50.72500000",
        "H         29.69800000     -9.66800000    -50.91600000",
        "C         28.20900000     -8.14300000    -50.94900000",
        "H         28.51200000     -7.50600000    -51.78000000",
        "H         27.12100000     -8.15300000    -50.87800000",
        "C         28.79700000     -7.60100000    -49.65300000",
        "H         28.68800000     -8.32900000    -48.84900000",
        "H         29.85200000     -7.35900000    -49.78200000",
        "N         28.08000000     -6.38500000    -49.28400000",
        "H         27.37400000     -6.47100000    -48.56700000",
        "C         28.29200000     -5.18600000    -49.82700000",
        "N         27.55500000     -4.15000000    -49.45500000",
        "H         26.83300000     -4.27200000    -48.75900000",
        "H         27.71900000     -3.24300000    -49.86900000",
        "N         29.23700000     -5.02900000    -50.74100000",
        "H         29.79700000     -5.82000000    -51.02500000",
        "H         29.39400000     -4.11900000    -51.15000000",
        "C         29.16200000    -11.26200000    -53.02600000",
        "O         28.50700000    -12.26500000    -52.78500000",
        "N         23.34200000     -9.14400000    -58.49500000",
        "H         23.49600000     -9.67700000    -57.65100000",
        "C         23.86600000     -7.79200000    -58.56000000",
        "H         23.47300000     -7.31900000    -59.46000000",
        "C         23.47600000     -6.87700000    -57.28100000",
        "H         22.38800000     -6.89800000    -57.21800000",
        "H         23.89900000     -7.38100000    -56.41200000",
        "C         24.01200000     -5.25900000    -57.31600000",
        "H         25.09300000     -5.22700000    -57.17600000",
        "H         23.75700000     -4.80800000    -58.27500000",
        "C         23.42200000     -4.58700000    -56.34300000",
        "H         23.50900000     -5.14200000    -55.40900000",
        "H         23.89600000     -3.61200000    -56.23100000",
        "C         21.77700000     -4.37700000    -56.72600000",
        "H         21.69300000     -3.84200000    -57.67200000",
        "H         21.30200000     -5.35400000    -56.81800000",
        "N         21.19000000     -3.69800000    -55.79300000",
        "H         21.63000000     -2.79300000    -55.70800000",
        "H         20.21500000     -3.57700000    -56.02700000",
        "H         21.26700000     -4.19400000    -54.91600000",
        "C         25.37100000     -7.81600000    -58.32000000",
        "O         25.85200000     -8.54500000    -57.45900000",
        "N         29.25300000     -5.16900000    -58.90200000",
        "H         29.88200000     -5.86400000    -58.52600000",
        "C         29.73100000     -3.79600000    -59.02000000",
        "H         29.13100000     -3.26300000    -59.75700000",
        "C         29.62600000     -3.05800000    -57.67300000",
        "H         30.26400000     -2.17500000    -57.69800000",
        "H         28.58500000     -2.75100000    -57.57400000",
        "C         30.01300000     -3.93100000    -56.48500000",
        "O         31.12200000     -4.50900000    -56.48100000",
        "O         29.22300000     -4.01700000    -55.52900000",
        "C         31.15600000     -3.78400000    -59.54500000",
        "O         31.36700000     -3.74200000    -60.75900000",
        "C         30.53751029    -11.30935363    -53.62243028",
        "H         30.83514817    -12.34918355    -53.75883569",
        "H         31.23813886    -10.81281996    -52.95142288",
        "H         30.52957968    -10.80115148    -54.58645553",
        "C         26.30878812      0.60965704    -40.91564978",
        "H         26.53005600     -0.33960700    -40.42740875",
        "H         25.41651542      1.05064204    -40.47173688",
        "H         27.15259949      1.28879098    -40.79549790",
        "C         27.43025395      2.61656018    -57.31278027",
        "H         27.22664118      1.70999455    -57.88297462",
        "H         27.50042975      3.46734154    -57.99021915",
        "H         26.62869879      2.78487002    -56.59385180",
        "C         32.24840952     -3.85185152    -58.51931115",
        "H         32.46404165     -4.89591763    -58.29156184",
        "H         31.92457908     -3.33879819    -57.61400063",
        "H         33.14309743     -3.37069066    -58.91389289",
        "C         22.82999172     -9.88545129    -59.69420703",
        "H         22.19847415    -10.71068738    -59.36464377",
        "H         23.67350935    -10.27464681    -60.26401564",
        "H         22.24885139     -9.20549364    -60.31679078",
        "C         20.52547477      0.19625648    -60.76148298",
        "H         20.41011065     -0.70835350    -61.35882117",
        "H         20.79540105      1.03055513    -61.40860164",
        "H         19.59019527      0.41774408    -60.24779776",
        "C         26.99996878     -2.31935456    -42.24378763",
        "H         26.05298806     -2.34318931    -42.78332485",
        "H         26.81630530     -2.10731906    -41.19070374",
        "H         27.50203360     -3.28158294    -42.34240034",
        "C         23.69375569     -9.53827704    -44.17897611",
        "H         22.89662900    -10.27825695    -44.10508581",
        "H         24.49420979     -9.79154785    -43.48413503",
        "H         24.08319018     -9.51978928    -45.19665778",
        "C         28.69965275      5.65853677    -54.84971897",
        "H         29.27796364      5.92656365    -53.96532137",
        "H         27.71303321      5.30636076    -54.54933432",
        "H         28.59723908      6.52859828    -55.49793299",
        "C         16.24948254     -8.41573149    -51.95611719",
        "H         15.29833655     -8.11706480    -51.51502705",
        "H         16.54976462     -9.38467230    -51.55779400",
        "H         16.14689339     -8.47985570    -53.03918716",
        "C         23.01761993    -10.76391637    -54.86728443",
        "H         22.62833008    -11.78079320    -54.81384350",
        "H         23.63462901    -10.65430393    -55.75889079",
        "H         22.18968311    -10.05623565    -54.90450817",
        "C         16.20810748     -4.51417754    -49.12771689",
        "H         15.38315149     -4.18729522    -48.49444243",
        "H         16.38907929     -5.57773349    -48.97352560",
        "H         15.96173562     -4.33153445    -50.17347948",
        "C         20.03994806     -9.55652191    -51.00353075",
        "H         19.27945957    -10.33630440    -50.95839187",
        "H         20.79467837     -9.73620055    -50.23817153",
        "H         20.50773984     -9.55764334    -51.98783081",
        "C         14.26301955      2.11586684    -52.63805076",
        "H         13.92528689      1.08660406    -52.76050800",
        "H         14.24011468      2.62588868    -53.60087478",
        "H         13.61279038      2.63329193    -51.93296189",
        "C         24.64502730     -2.39314185    -60.89934675",
        "H         24.36069055     -3.43158252    -61.07032794",
        "H         25.08134909     -1.97850077    -61.80784720",
        "H         23.76582116     -1.81435929    -60.61706266",
        "C         26.41415526      1.09824444    -58.57309796",
        "H         27.32773221      1.62040020    -58.28819180",
        "H         25.68679162      1.16481310    -57.76427923",
        "H         26.00149524      1.54810705    -59.47587830",
        "C         26.21814054     -6.94520261    -59.19980953",
        "H         27.01882128     -7.54358597    -59.63488274",
        "H         26.64566789     -6.13902719    -58.60400875",
        "H         25.60045417     -6.52680516    -59.99421756",
        "C         33.93550957     -7.92781472    -50.54372258",
        "H         34.37924097     -8.67430258    -51.20273648",
        "H         34.58883826     -7.05762899    -50.48359431",
        "H         32.96160784     -7.62960161    -50.93135817",
        "C         27.83778453     -5.52054314    -59.25354314",
        "H         27.25697422     -5.63399459    -58.33799459",
        "H         27.82741155     -6.45620608    -59.81220608",
        "H         27.40977830     -4.72456808    -59.86256808",
        "C         20.84550185     -7.43006008    -46.17029773",
        "H         20.16704308     -8.11129696    -45.65643880",
        "H         21.46920707     -7.99028515    -46.86658552",
        "H         20.27016136     -6.68090412    -46.71382847",
        "C         19.21229793     -6.43537269    -47.30638199",
        "H         18.25841177     -6.96251818    -47.33206897",
        "H         19.73321871     -6.66578145    -46.37728009",
        "H         19.82305290     -6.74169447    -48.15539455",
        "C         24.56291790      5.73334064    -52.46706494",
        "H         25.12081188      5.82656690    -51.53512923",
        "H         23.53747072      5.43375833    -52.25169199",
        "H         24.56382556      6.68858992    -52.99163620",
        "C         31.97043734    -11.00461929    -49.45161929",
        "H         31.25948347    -11.79621593    -49.21421593",
        "H         32.97889237    -11.41631310    -49.48631310",
        "H         31.72006465    -10.56477688    -50.41677688",
        "C         22.08497851      2.94505587    -57.66317963",
        "H         22.84137568      3.32435551    -56.97583975",
        "H         21.16143557      2.74816432    -57.11913996",
        "H         21.90015818      3.68003947    -58.44632557",
        "C         22.86983180      4.08675894    -55.92570122",
        "H         22.84958607      3.71852760    -56.95158464",
        "H         22.80490456      5.17462909    -55.92566942",
        "H         22.03068352      3.66889082    -55.36991944",
        "C         15.71922489      0.67888627    -48.77687834",
        "H         14.98026684      0.01372695    -49.22403054",
        "H         15.23983090      1.30751740    -48.02675748",
        "H         16.50875943      0.08920886    -48.31148307",
    ]
    test_result = gi._make_mol_spec(
        test_stru,
        [test_stru_region],
        constraints,
    )
    assert set(test_result) == set(answer)


def test_is_gaussian_completed():
    """test as name"""
    test_gout = f"{DATA_DIR}complete_spe.out"
    assert gi.is_gaussian_completed(test_gout)

    test_gout = f"{DATA_DIR}incomplete_spe.out"
    assert not gi.is_gaussian_completed(test_gout)
