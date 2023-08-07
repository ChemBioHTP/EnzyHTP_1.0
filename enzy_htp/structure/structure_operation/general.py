"""General opertion of Structure(). functions in this module take Structure() as input and do 
operations on it. Place holder for uncategorized functions.

Author: Qianzhen (QZ) Shao, <shaoqz@icloud.com>
Date: 2022-09-19
"""

import copy
from plum import dispatch

from enzy_htp.core.logger import _LOGGER
from ..structure import Structure, Solvent, Chain, Residue, Atom


def remove_solvent(stru: Structure) -> Structure:
    """
    remove all Solvent() for {stru}.
    Make changes in-place and return a reference of the changed
    original object.
    """
    _LOGGER.debug(f"removing {len(stru.solvents)} solvents")
    solv: Solvent
    for solv in stru.solvents:
        solv.delete_from_parent()

    return stru


def remove_empty_chain(stru: Structure) -> Structure:
    """
    remove empty chains
    Make changes in-place and return a reference of the changed
    original object.
    """
    ch: Chain
    # shallow copy to avoid iteration-deletion problem
    for ch in copy.copy(stru.chains):
        if ch.is_empty():
            _LOGGER.debug(f"removing {ch}")
            ch.delete_from_parent()
    return stru


def remove_non_peptide(stru: Structure) -> Structure:
    """remove the non-peptide parts of the structure. 
    Make changes in-place and return a reference of the changed original object."""
    non_peptides = list(filter(lambda c: not c.is_polypeptide(), stru.chains))
    ch: Chain
    for ch in non_peptides:
        ch.delete_from_parent()
    return stru


# @dispatch
def update_residues(stru: Structure, ref_stru: Structure) -> Structure:
    """
    Update atoms and residue names to residues in the stru
    The sequence should holds constant since it serves as reference
    Args:
        stru: the target structure
        ref_stru: the reference structure
    Returns:
        stru: the changed original structure
    """
    # san check for ref_stru
    stru.is_idx_subset(ref_stru)

    # update residues in stru with correponding residue idxes in ref_stru
    self_res_mapper = stru.residue_mapper
    ref_res: Residue
    for ref_res in ref_stru.residues:
        self_res = self_res_mapper[ref_res.key()]
        if self_res.name != ref_res.name:
            _LOGGER.info(
                f"updating {self_res.key()} {self_res.name} to {ref_res.name}")
            self_res.name = ref_res.name
        # this will also set self_res as parent
        self_res.atoms = copy.deepcopy(ref_res.atoms)
    stru.renumber_atoms()
    return stru


# @dispatch
# def update_residues(resi: Residue, ref_resi: Residue) -> Residue:  # pylint: disable=function-redefined
#     """
#     Update atoms and residue names to the single residue
#     (it doesnt matter if there are same in sequence)
#     Args:
#         resi: the target residue
#         ref_resi: the reference residue
#     Return:
#         the changed original residue
#     """
#     if resi.name != ref_resi.name:
#         _LOGGER.info(f"updating {resi.key()} {resi.name} to {ref_resi.name}")
#         resi.name = ref_resi.name
#     resi.atoms = copy.deepcopy(ref_resi.atoms)  # this will also set resi as parent
#     return resi
