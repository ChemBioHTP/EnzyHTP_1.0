"""Testing the enzy_htp.mutation.mutation_pattern.general.py submodule.
Author: QZ Shao <shaoqz@icloud.com>
Date: 2023-01-26
"""

import pytest
import os

from enzy_htp.core.exception import InvalidMutationPatternSyntax
from enzy_htp import PDBParser
from enzy_htp.mutation.mutation import Mutation
import enzy_htp.mutation.mutation_pattern.general as m_p

CURR_FILE = os.path.abspath(__file__)
CURR_DIR = os.path.dirname(CURR_FILE)
DATA_DIR = f"{CURR_DIR}/../data/"
sp = PDBParser()

@pytest.mark.interface
def test_decode_mutation_pattern():
    """dev run of the function"""
    test_mutation_pattern = (
        "KA162A, {RA154W, HA201A},"
        " r:2[resi 289 around 4 and not resi 36:larger,"
            " proj(id 1000, id 2023, positive, 10):more_negative_charge]*100"
        )
    test_pdb = f"{DATA_DIR}KE_07_R7_2_S.pdb"
    test_stru = sp.get_structure(test_pdb)

    m_p.decode_mutation_pattern(test_stru, test_mutation_pattern)

def test_seperate_mutants():
    """test the function use a made up mutation_pattern for KE
    use the len of the seperation result as the fingerprint to assert"""
    test_mutation_pattern = (
        "KA162A, {RA154W, HA201A},"
        " r:2[resi 289 around 4 and not resi 36:larger,"
            " proj(id 1000, id 2023, positive, 10):more_negative_charge]*100"
        )
    assert len(m_p.seperate_mutant_patterns(test_mutation_pattern)) == 3

def test_seperate_sections():
    """test the function use a made up mutation_pattern for KE
    use the len of the seperation result as the fingerprint to assert"""
    test_mutation_pattern = (
        "KA162A,"
        " r:2[resi 289 around 4 and not resi 36:larger,"
            " proj(id 1000, id 2023, positive, 10):more_negative_charge]*100,"
        "RA154W"
        )
    assert len(m_p.seperate_section_patterns(test_mutation_pattern)) == 3

def test_get_section_type():
    """test if the section type is correctly determined"""
    section_1 = "KA162A"
    section_2 = "r:2[resi 289 around 4 and not resi 36:larger]"
    section_3 = "a:[resi 289 around 4 and not resi 36:larger]"

    assert m_p.get_section_type(section_1) == "d"
    assert m_p.get_section_type(section_2) == "r"
    assert m_p.get_section_type(section_3) == "a"

def test_get_section_type_bad():
    """test if the section type raise the execption as expected."""
    section_bad = "x:KA162A"
    with pytest.raises(Exception) as exe:
        m_p.get_section_type(section_bad)
    assert exe.type == InvalidMutationPatternSyntax

def test_decode_direct_mutation():
    """test the function works as expected using a made up pattern and manually
    curated answer. test giving default chain id"""
    test_pdb = f"{DATA_DIR}KE_07_R7_2_S.pdb"
    test_stru = sp.get_structure(test_pdb)
    test_d_pattern = "RA154W"
    test_d_pattern_1 = "R154W"
    answer = Mutation(orig="R", target="W", chain_id="A", res_idx=154)

    assert m_p.decode_direct_mutation(test_stru, test_d_pattern) == answer
    assert m_p.decode_direct_mutation(test_stru, test_d_pattern_1) == answer