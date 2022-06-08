"""Testing the enzy_htp.molecular_mechanics.AmberInterface class.

Author: Chris Jurich <chris.jurich@vanderbilt.edu>
Date: 2022-06-03
"""
from enzy_htp.core import file_system as fs
from enzy_htp import AmberInterface
from pathlib import Path

MM_BASE_DIR = Path(__file__).absolute().parent
MM_DATA_DIR = f"{MM_BASE_DIR}/data/"
MINIMIZE_INPUT_1 = f"{MM_DATA_DIR}/min_1.inp"
TARGET_MINIMIZE_INPUT_1 = f"{MM_DATA_DIR}/target_min_1.inp"
MINIMIZE_INPUT_2 = f"{MM_DATA_DIR}/min_2.inp"
TARGET_MINIMIZE_INPUT_2 = f"{MM_DATA_DIR}/target_min_2.inp"


def files_equivalent( fname1 : str, fname2 : str ) -> bool:
    """"""
    lines1, lines2 = fs.lines_from_file(fname1), fs.lines_from_file(fname2)
    
    if len(lines1) != len(lines2):
        return False

    for l1, l2 in zip(lines1, lines2):
        if l1 != l2:
            return False

    return True


def test_write_minimize_input_file():
    """Testing that minimization input files are generated correctly."""
    ai = AmberInterface()
    print(f"{MM_DATA_DIR}/min.inp")
    assert not Path(MINIMIZE_INPUT_1).exists()
    assert not Path(MINIMIZE_INPUT_2).exists()
    ai.write_minimize_input_file(MINIMIZE_INPUT_1, 2000)
    assert files_equivalent( MINIMIZE_INPUT_1, TARGET_MINIMIZE_INPUT_1)
    ai.write_minimize_input_file(MINIMIZE_INPUT_2, 1000)
    assert files_equivalent( MINIMIZE_INPUT_2, TARGET_MINIMIZE_INPUT_2)
    fs.safe_rm(MINIMIZE_INPUT_1)
    fs.safe_rm(MINIMIZE_INPUT_2)
    assert not Path(MINIMIZE_INPUT_1).exists()
    assert not Path(MINIMIZE_INPUT_2).exists()
