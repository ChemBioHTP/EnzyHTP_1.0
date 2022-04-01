"""Structure parser function that takes a pdb file as input and returns an enzy_htp.structure.Structure() object.
Setup as a single function. Users should only call the high level function structure_from_pdb()

Author: Qianzhen (QZ) Shao <qianzhen.shao@vanderbilt.edu>
Author: Chris Jurich <chris.jurich@vanderbilt.edu>
Date: 2022-03-29
"""
import os
import string
import warnings
import pandas as pd
from collections import defaultdict
from biopandas.pdb import PandasPdb
from typing import List, Set, Dict, Tuple


from .atom import Atom
from .metal_atom import MetalAtom
from .residue import Residue
from .solvent import Solvent, residue_to_solvent
from .ligand import Ligand, residue_to_ligand
from .chain import Chain
from .structure import Structure
from enzy_htp.core import _LOGGER
import enzy_htp.core.file_system as fs

def __name_chains(mapper: defaultdict) -> None:
    """Function takes a defaultdict(list) of Residues and ensures consistent naming of chains."""
    def legal_chain_names(mapper) -> List[str]:
        result = list(string.ascii_uppercase)
        taken = set(list(mapper.keys()))
        result = list(filter(lambda s: s not in taken, result))
        return list(reversed(result))
    key_names = set(list(map(lambda kk: kk.strip(), mapper.keys())))
    if "" not in key_names:
        return mapper
    unnamed = list(mapper[""])
    del mapper[""]

    names = legal_chain_names(mapper)
    unnamed = sorted(unnamed, key=lambda r: -r.min_line())
    new_chain: List[Residue] = [unnamed.pop()]

    while len(unnamed):
        new_res = unnamed.pop()
        if new_chain[-1].neighbors(new_res):
            new_chain.append(new_res)
            continue

        new_name = names.pop()
        mapper[new_name] = new_chain
        new_chain = [new_res]

    if len(new_chain):
        new_name = names.pop()
        mapper[new_name] = new_chain

    return mapper

def __build_residues( df: pd.DataFrame ) -> Dict[str,Residue]:
    mapper = defaultdict(list)
    for i, row in df.iterrows():
        aa = Atom(**row)
        mapper[aa.residue_key()].append(aa)
    
    result : Dict[str, Residue] = dict()
    for res_key, atoms in mapper.items():
        result[res_key] = Residue(
            residue_key=res_key, atoms=sorted(atoms, key=lambda a: a.atom_number)
        )
    return result 


def __build_chains(mapper : Dict[str, Residue]) -> Dict[str,Chain]:
    chain_mapper = defaultdict(list)
    for res in mapper.values():
        chain_mapper[res.chain()].append(res)
    chain_mapper = __name_chains(chain_mapper)
    result : Dict[str,Chain] = dict()
    # ok this is where we handle missing chain ids
    for chain_name, residues in chain_mapper.items():
        result[chain_name] = Chain(
            chain_name, sorted(residues, key=lambda r: r.num())
        )
    return result


def __get_metalatoms(chains : Dict[str,Chain]) -> Tuple[ List[Chain], List[MetalAtom]] :
    metalatoms : List[MetalAtom] = list()
    for cname, chain in chains.items():
        if chain.is_metal():
            metalatoms.append(chain)
            del chains[cname]
    
    if not metalatoms:
        return (chains, metalatoms)
    # Break pseudo residues into atoms and convert to Metalatom object
    holders = []
    for pseudo_resi in metalatoms:
        for metal in pseudo_resi:
            holders.append(Metalatom.fromAtom(metal))
    metalatoms = holders
    # clean empty chains
    for i in range(len(raw_chains) - 1, -1, -1):
        if len(raw_chains[i]) == 0:
            del raw_chains[i]

    return raw_chains, metalatoms


def __get_ligands(chains : Dict[str,Chain], ligand_list=None) -> Tuple[Dict[str,Chain],List[Ligand]]: 
    bad_chains = []
    ligands = []
    for cname, chain in chains.items():

        if chain.is_HET():
            continue

        for idx, residue in enumerate(chain.residues()[::-1]):
            if ligand_list is not None and residue.name in ligand_list:
                _LOGGER.info(
                    f"Structure: Found user assigned ligand in raw {chain.name()} {residue.name} {residue.num_}"
                )
                ligands.append(residue)
                del chain[idx]
            elif not residue.is_rd_solvent() and not residue.is_rd_non_ligand():
                _LOGGER.warning(
                    f"Structure: Found ligand in raw {chain.name()} {residue.name} {residue.num_}"
                )
                ligands.append(residue)
                del chain[idx]

        if chain.empty():
            bad_chains.append(cname)

    for bc in bad_chains:
        chains[bc]

    return (chains, list(map(residue_to_ligand, ligands)))


def get_solvents(chains : Dict[str,Chain]) -> Tuple[Dict[str,Chain],List[Solvent]]:
    """
    get solvent from raw chains and clean chains by deleting the solvent part
    -----
    Method: Assume metal/ligand/solvent can anywhere. Base on rd_solvent_list
    """
    solvents = []
    bad_chains = []
    for cname, chain in chains.items():
        for idx, residue in enumerate(chain.residues()[::-1]):
            if residue.is_rd_solvent():
                _LOGGER.warning(
                    f"Structure: found solvent in raw {residue.name} {residue.id}"
                )
                solvents.append(residue)
                del chain[idx]

        if chain.empty():
            bad_chains.append(cname)
    # Convert pseudo residues to Ligand object
    for bc in bad_chains:
        del chains[bc]

    return ( chains, list(map(residue_to_solvent, solvents)))


def ligand_from_pdb( fname : str, net_charge: float = None ) -> Ligand:
#def from_pdb(
#    fname : str ,
#    resi_id=None,
#    resi_name=None,
#    net_charge=None,
#    input_type="PDB_line",
#) -> Ligand:
    """
    generate resi from PDB. Require 'ATOM' and 'HETATM' lines.
    ---------
    resi_input = PDB_line (or line_str or file or path)
    resi_id : int (use the number in the line by default // support customize)
    net_charge : user assigned net charge for further use
    Use PDB_line in the list to init each atom
    """
    warnings.filterwarnings('ignore')
    # adapt general input // converge to a list of PDB_line (resi_lines)
    parser = PandasPdb()
    parser.read_pdb(fname)
    atoms = list(map(lambda pr: Atom(**pr[1]), parser.df['HETATM'].iterrows()))
    #TODO(CJ) figure out the residue key
    result = Residue( '..10', atoms )
    result = residue_to_ligand( result )
    result.net_charge = net_charge
    return result
    # Default resi_id
    if resi_id is None:
        resi_id = resi_lines[0].resi_id
    # get name from first line
    if resi_name is None:
        resi_name = resi_lines[0].resi_name
    # get child atoms
    atoms = []
    for pdb_l in resi_lines:
        atoms.append(Atom.fromPDB(pdb_l))

    return Ligand(atoms, resi_id, resi_name, net_charge=net_charge)


def __check_valid_pdb( pdbname : str ) -> None:
    """Helper function that ensures the supplied pdbname is a valid pdb file. 
    Private to structure.structure_parser.py. Should NOT be called externally."""
    ext : str = fs.get_file_ext(pdbname)
    if ext.lower() != '.pdb':
        _LOGGER.error(f"Supplied file '{pdbname}' is NOT a PDB file. Exiting...")
        exit( 0 )
    
    if not os.path.exists( pdbname ):
         _LOGGER.error(f"Supplied file '{pdbname}' does NOT exist. Exiting...")
         exit( 0 )
    
    fh = open( pdbname, 'r' )
    contents = fh.read()
    fh.close()
   
    if not contents.isascii():
        _LOGGER.error(f"The PDB '{pdbname}' contains non-ASCII text and is invalid. Exiting...")
        exit( 0 )

def structure_from_pdb(fname: str) -> Structure:
    """Method that creates a Structure() object from a supplied .pdb file. Checks that the input file is good first."""
    __check_valid_pdb( fname ) 
    parser = PandasPdb()
    parser.read_pdb(fname)
    res_mapper : Dict[str,Residue] = __build_residues( parser.df['ATOM'] )
    chain_mapper : Dict[str, Chain] = __build_chains( res_mapper )
    metal_atoms : List[MetalAtom] = list()
    (chain_mapper, metalatoms) = __get_metalatoms( chain_mapper )
    (chain_mapper, ligands ) = __get_ligands( chain_mapper ) 
    (chain_mapper, solvents ) = get_solvents( chain_mapper )
    result = Structure(
        chains=chain_mapper,
        metal_atoms=metal_atoms,
        solvents=solvents,
        ligands=ligands
	)
    
    return result
