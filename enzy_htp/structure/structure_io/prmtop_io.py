"""Generation/construction of Structure() objects from .prmtop files and exporting these objects to this file format. 
Definition of .prmtop format (http://ambermd.org/FileFormats.php#topology). All parsing is done within enzy_htp using 
this parser only. The PrmtopParser has no private data and serves as a namespace for .prmtop I/O conversion functions.

Author: Qianzhen Shao <shaoqz@icloud.com>
Date: 2023-10-28
"""
from typing import Dict, List
import re
from itertools import chain

from ._interface import StructureParserInterface
from ..structure import Structure, convert_res_to_structure

import enzy_htp.core.file_system as fs
import enzy_htp.core.fortran_helper as fh
from enzy_htp.core.logger import _LOGGER
from enzy_htp.core.exception import FileFormatError

class PrmtopParser(StructureParserInterface):
    """the parser for Gaussian prmtop files"""
    def __init__(self) -> None:  # pylint: disable=super-init-not-called
        """pass"""
        pass

    @classmethod
    def get_structure(cls, path: str) -> Structure:
        """Converting a .prmtop file (as its path) into the Structure()
        also assign charges as prmtop contains.
        NOTE that this structure dont have actual coordinates/geometry
        Arg:
            path:
                the file path of the prmtop file
        Return:
            Structure()"""
        pass # TODO: add when need

    @classmethod
    def get_file_str(cls, stru: Structure) -> str:
        """convert a Structure() to .prmtop file content."""
        pass # TODO: add when need

    @classmethod
    def save_structure(cls, out_path: str, stru: Structure) -> str:
        """save a Structure() to .prmtop file.
        return the out_path"""
        pass # TODO: add when need

    @classmethod
    def _parse_prmtop_file(cls, path: str) -> Dict:
        """parse prmtop file to a data dictionary.

        the return data dictionary strictly follows keywords defined
        in https://ambermd.org/prmtop.pdf.
        Example:
            {
            "VERSION_STAMP" : "V0001.000",
            "DATE" : "01/03/24 16:27:03",
            "TITLE" : "default_name",
            ...
            }"""
        if not fs.has_content( path ):
            _LOGGER.error(f"The supplied file {path} does not exist or is empty. Exiting...")
            raise ValueError

        result = {}
        content: str = fs.content_from_file( path )
        sections = content.split("%FLAG")

        for sec in sections:
            if sec.find("%VERSION") != -1:
                result.update(cls._parse_version(sec))
                continue
            sec_name = sec.splitlines()[0].strip()
            result.update(cls.section_parser_mapper()[sec_name](sec))

        return result

    @classmethod
    def section_parser_mapper(cls):
        """the mapper that map section type/name to the parser function"""
        return {
            "TITLE" : cls._parse_title,
            "POINTERS" : cls._parse_pointers,
            "ATOM_NAME" : cls._parse_atom_name,
            "CHARGE" : cls._parse_charge,
            "ATOMIC_NUMBER" : cls._parse_atomic_number,
            "MASS" : cls._parse_mass,
            "ATOM_TYPE_INDEX" : cls._parse_atom_type_index,
            "NUMBER_EXCLUDED_ATOMS" : cls._parse_number_excluded_atoms,
            "NONBONDED_PARM_INDEX" : cls._parse_nonbonded_parm_index,
            "RESIDUE_LABEL" : cls._parse_residue_label,
            "RESIDUE_POINTER" : cls._parse_residue_pointer,
            "BOND_FORCE_CONSTANT" : cls._parse_bond_force_constant,
            "BOND_EQUIL_VALUE" : cls._parse_bond_equil_value,
            "ANGLE_FORCE_CONSTANT" : cls._parse_angle_force_constant,
            "ANGLE_EQUIL_VALUE" : cls._parse_angle_equil_value,
            "DIHEDRAL_FORCE_CONSTANT" : cls._parse_dihedral_force_constant,
            "DIHEDRAL_PERIODICITY" : cls._parse_dihedral_periodicity,
            "DIHEDRAL_PHASE" : cls._parse_dihedral_phase,
            "SCEE_SCALE_FACTOR" : cls._parse_scee_scale_factor,
            "SCNB_SCALE_FACTOR" : cls._parse_scnb_scale_factor,
            "SOLTY" : cls._parse_solty,
            "LENNARD_JONES_ACOEF" : cls._parse_lennard_jones_acoef,
            "LENNARD_JONES_BCOEF" : cls._parse_lennard_jones_bcoef,
            "BONDS_INC_HYDROGEN" : cls._parse_bonds_inc_hydrogen,
            "BONDS_WITHOUT_HYDROGEN" : cls._parse_bonds_without_hydrogen,
            "ANGLES_INC_HYDROGEN" : cls._parse_angles_inc_hydrogen,
            "ANGLES_WITHOUT_HYDROGEN" : cls._parse_angles_without_hydrogen,
            "DIHEDRALS_INC_HYDROGEN" : cls._parse_dihedrals_inc_hydrogen,
            "DIHEDRALS_WITHOUT_HYDROGEN" : cls._parse_dihedrals_without_hydrogen,
            "EXCLUDED_ATOMS_LIST" : cls._parse_excluded_atoms_list,
            "HBOND_ACOEF" : cls._parse_hbond_acoef,
            "HBOND_BCOEF" : cls._parse_hbond_bcoef,
            "HBCUT" : cls._parse_hbcut,
            "AMBER_ATOM_TYPE" : cls._parse_amber_atom_type,
            "TREE_CHAIN_CLASSIFICATION" : cls._parse_tree_chain_classification,
            "JOIN_ARRAY" : cls._parse_join_array,
            "IROTAT" : cls._parse_irotat,
            "RADIUS_SET" : cls._parse_radius_set,
            "RADII" : cls._parse_radii,
            "SCREEN" : cls._parse_screen,
            "SOLVENT_POINTERS" : cls._parse_solvent_pointers,
            "ATOMS_PER_MOLECULE" : cls._parse_atoms_per_molecule,
            "BOX_DIMENSIONS" : cls._parse_box_dimensions,
            "CAP_INFO" : cls._parse_cap_info,
            "CAP_INFO2" : cls._parse_cap_info2,
            "POLARIZABILITY" : cls._parse_polarizability,
            "IPOL" : cls._parse_ipol,
        }

    @classmethod
    def _parse_version(cls, content: str) -> Dict:
        """parse the 'version' section from prmtop file format
        see test for example of the return."""
        pattern = r"%VERSION  VERSION_STAMP = (.+)DATE = (.+)"
        version_stamp, data = re.match(pattern, content.strip()).groups()

        return {
            "VERSION_STAMP" : version_stamp.strip(),
            "DATE" : data.strip(),            
        }

    @classmethod
    def _parse_general(cls, content: str) -> Dict:
        """parse general data section from prmtop file format"""
        (key, fmt, body) = content.split('\n', 2) # TODO this not work when multiple FORMAT is in the file but it is a rare case when IFPERT == 1
        key = key.strip()
        fmt = fmt.strip().lstrip("%")
        body = re.sub('\n', '', body)
        data = fh.parse_data(fmt, body, reduce=False)
        data = list(chain.from_iterable(data))
        return {key : data}

    @classmethod
    def _parse_title(cls, content: str) -> Dict:
        """parse the 'title' section of prmtop file format."""
        result = cls._parse_general(content)
        result["TITLE"] = "".join(result["TITLE"])
        return result

    @classmethod
    def _parse_atom_name(cls, content: str) -> Dict:
        """parse the 'atom_name' section of prmtop file format."""
        result = cls._parse_general(content)
        return result

    @classmethod
    def _parse_charge(cls, content: str) -> Dict:
        """parse the 'charge' section of prmtop file format."""
        result = cls._parse_general(content)
        return result

    @classmethod
    def _parse_atomic_number(cls, content: str) -> Dict:
        """parse the 'atomic_number' section of prmtop file format."""
        result = cls._parse_general(content)
        return result

    @classmethod
    def _parse_residue_label(cls, content: str) -> Dict:
        """parse the 'residue_label' section of prmtop file format."""
        result = cls._parse_general(content)
        return result

    @classmethod
    def _parse_residue_pointer(cls, content: str) -> Dict:
        """parse the 'residue_pointer' section of prmtop file format. TODO"""
        result = cls._parse_general(content)
        return result

    # region unfullfilled TODO finish these when needed. I didnt make them directly use _parse_general because we dont want to store too much we dont need in the mem.
    @classmethod
    def _parse_pointers(cls, content: str) -> Dict:
        """parse the 'pointers' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_mass(cls, content: str) -> Dict:
        """parse the 'mass' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_atom_type_index(cls, content: str) -> Dict:
        """parse the 'atom_type_index' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_number_excluded_atoms(cls, content: str) -> Dict:
        """parse the 'number_excluded_atoms' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_nonbonded_parm_index(cls, content: str) -> Dict:
        """parse the 'nonbonded_parm_index' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_bond_force_constant(cls, content: str) -> Dict:
        """parse the 'bond_force_constant' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_bond_equil_value(cls, content: str) -> Dict:
        """parse the 'bond_equil_value' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_angle_force_constant(cls, content: str) -> Dict:
        """parse the 'angle_force_constant' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_angle_equil_value(cls, content: str) -> Dict:
        """parse the 'angle_equil_value' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_dihedral_force_constant(cls, content: str) -> Dict:
        """parse the 'dihedral_force_constant' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_dihedral_periodicity(cls, content: str) -> Dict:
        """parse the 'dihedral_periodicity' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_dihedral_phase(cls, content: str) -> Dict:
        """parse the 'dihedral_phase' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_scee_scale_factor(cls, content: str) -> Dict:
        """parse the 'scee_scale_factor' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_scnb_scale_factor(cls, content: str) -> Dict:
        """parse the 'scnb_scale_factor' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_solty(cls, content: str) -> Dict:
        """parse the 'solty' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_lennard_jones_acoef(cls, content: str) -> Dict:
        """parse the 'lennard_jones_acoef' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_lennard_jones_bcoef(cls, content: str) -> Dict:
        """parse the 'lennard_jones_bcoef' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_bonds_inc_hydrogen(cls, content: str) -> Dict:
        """parse the 'bonds_inc_hydrogen' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_bonds_without_hydrogen(cls, content: str) -> Dict:
        """parse the 'bonds_without_hydrogen' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_angles_inc_hydrogen(cls, content: str) -> Dict:
        """parse the 'angles_inc_hydrogen' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_angles_without_hydrogen(cls, content: str) -> Dict:
        """parse the 'angles_without_hydrogen' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_dihedrals_inc_hydrogen(cls, content: str) -> Dict:
        """parse the 'dihedrals_inc_hydrogen' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_dihedrals_without_hydrogen(cls, content: str) -> Dict:
        """parse the 'dihedrals_without_hydrogen' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_excluded_atoms_list(cls, content: str) -> Dict:
        """parse the 'excluded_atoms_list' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_hbond_acoef(cls, content: str) -> Dict:
        """parse the 'hbond_acoef' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_hbond_bcoef(cls, content: str) -> Dict:
        """parse the 'hbond_bcoef' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_hbcut(cls, content: str) -> Dict:
        """parse the 'hbcut' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_amber_atom_type(cls, content: str) -> Dict:
        """parse the 'amber_atom_type' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_tree_chain_classification(cls, content: str) -> Dict:
        """parse the 'tree_chain_classification' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_join_array(cls, content: str) -> Dict:
        """parse the 'join_array' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_irotat(cls, content: str) -> Dict:
        """parse the 'irotat' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_radius_set(cls, content: str) -> Dict:
        """parse the 'radius_set' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_radii(cls, content: str) -> Dict:
        """parse the 'radii' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_screen(cls, content: str) -> Dict:
        """parse the 'screen' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_solvent_pointers(cls, content: str) -> Dict:
        """parse the 'solvent_pointers' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_atoms_per_molecule(cls, content: str) -> Dict:
        """parse the 'atoms_per_molecule' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_box_dimensions(cls, content: str) -> Dict:
        """parse the 'box_dimensions' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_cap_info(cls, content: str) -> Dict:
        """parse the 'cap_info' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_cap_info2(cls, content: str) -> Dict:
        """parse the 'cap_info2' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_polarizability(cls, content: str) -> Dict:
        """parse the 'polarizability' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        result = {}

        return result

    @classmethod
    def _parse_ipol(cls, content: str) -> Dict:
        """parse the 'ipol' section of prmtop file format. TODO"""
        # return cls._parse_general(content)
        # NOTE this is an example that general dont work
        result = {}

        return result
    # endregion
