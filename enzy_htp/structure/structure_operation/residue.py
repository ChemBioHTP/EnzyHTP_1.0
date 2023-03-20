"""Opertion of Residue(). functions in this module take Residue() as input and do 
operations on it.

Author: Qianzhen (QZ) Shao, <shaoqz@icloud.com>
Date: 2023-03-20
"""

from typing import Tuple, Union

from enzy_htp.core.logger import _LOGGER
import enzy_htp.chemical as chem
from ..structure import Residue, Atom


def deprotonate_residue(residue: Residue, target_atom: Union[None, Atom] = None) -> None:
    """
    deprotonate the {residue} on the {target_atom} (if provided).
    remove the acidic hydrogen attached to the {target_atom} and change the residue name
    correponding to chem.residue.DEPROTONATION_MAPPER or /resource/ProtonationState.cdx
    """
    new_resi_name, target_proton = get_default_deproton_info(residue, target_atom)
    if new_resi_name is None:
        if len(target_atom.attached_protons()) == 0:
            _LOGGER.info(f"target atom {target_atom} already have no H. keep original")
        else:
            _LOGGER.warning(
                f"cannot deprotonate {residue} on {target_atom}. keep original")
        return None
    _LOGGER.info(f"deprotonate {target_proton} from {residue}")
    residue.name = new_resi_name
    residue.find_atom_name(target_proton).delete_from_parent()
    #TODO rename/complete atoms after this (e.g.: ARG:NH1 case, HID -> HIE case)


def get_default_deproton_info(residue: Residue,
                              target_atom: Union[None, Atom] = None) -> Tuple:
    """
    return the default proton in the residue on the target_atom (if provided) to deprotonate
    Default HIP target is set to resulting HIE
    """
    r_name = residue.name
    # default target atom
    if target_atom is None:
        target_atom_name = list(chem.residue.DEPROTONATION_MAPPER[r_name].keys())[0]
    else:
        target_atom_name = target_atom.name

    depro_info = chem.residue.DEPROTONATION_MAPPER.get(r_name, None)
    if depro_info is None:
        _LOGGER.warn(
            f"no default protonation info for {r_name}. Consider make a standard for it")
        return None, None
    if r_name in ["HIE", "HID"]:
        _LOGGER.warn(
            f"deprotonation info for {residue} is actually a switching between HID/HIE")
    target_atom_depro_info = depro_info.get(target_atom_name, None)
    if target_atom_depro_info is None:
        _LOGGER.warn(
            f"no default protonation info for {target_atom_name} in {r_name}. Could be no proton on it. Consider make a standard for it if do"
        )
        return None, None
    return target_atom_depro_info
