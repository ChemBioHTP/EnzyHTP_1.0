'''
Created on Tue Nov 30 15:51:51 2021
@author: shaoqz
=====
High-throughput traj based calculation. (large amount of trajs generated by EnzyHTP forheaded)
=====
From_keyword_find
calc_MMPBSA
TODO: support 3A MMPBSA
'''
from subprocess import run, CalledProcessError
from glob import glob
import os
import mdtraj
import numpy as np

from Class_PDB import PDB
from Class_Structure import *
from Class_Conf import *
from AmberMaps import radii_map
from helper import line_feed, mkdir

class TrajCalcERROR(Exception):
    pass


class Traj_calc:
    '''
    Class of objects of htp traj based calculation
    -----
    name
    nc
    prmtop
    pdb
    '''
    def __init__(self, traj: str, prmtop: str, pdb: str=None, name: str=None) -> None:
        self.name = name
        self.traj = traj
        self.prmtop = prmtop
        self.pdb = pdb

    @classmethod
    def From_keyword_find(cls, path, keyword='', if_pdb = 1):
        '''
        Find all (.prmtop, .pdb and .nc file) groups for EnzyHTP result
        keyword search using 'find' with san check about file existance (used in 2021/11/30 - CHEM5420 final project)
        -----
        path: Search path root
        keyword: keyword used for search (in shell find style)
        -return--
        A list of Traj_calc objects: [Traj_calc(nc, prmtop, name, pdb), ...]
        '''
        traj_list = []
        cmd = ' '.join(['find', path, '-name', "'"+keyword+"'", '-type d'])
        p_path_list = run(cmd, check=True, text=True, shell=True, capture_output=True).stdout.strip().split('\n')
        for p_path in p_path_list:
            #--name--
            p_name = p_path.split('/')[-1]
            #--nc--
            p_traj = p_path+'/MD/prod.nc'
            #   san check
            if not os.path.exists(p_traj):
                print('INFO: Do not find nc file. Ignoring:', p_path)
                continue
            #--prmtop--
            p_prmtop = glob(p_path+'/*prmtop')
            #   san check
            if len(p_prmtop) == 0:
                print('WARNING: Do not find prmtop file while nc file exists. Ignoring:', p_path)
                continue
            if len(p_prmtop) > 1:
                print('WARNING: Found more than one prmtop files in:', p_path)
                print('Please choose between:', p_prmtop)
                raise TrajCalcERROR
            p_prmtop = p_prmtop[0]
            #--pdb--
            # find the pdb with the same name as prmtop. Based on the common procedure in the EnzyHTP
            if if_pdb:
                p_prm_name = p_prmtop[:-7]
                p_pdb = p_prm_name + '.pdb'
                if not os.path.exists(p_pdb):
                    print('WARNING: Do not find pdb file while nc and prmtop file exists. Ignoring:', p_path)
                    continue
            else:
                p_pdb = None

            traj_list.append(cls(p_traj, p_prmtop, p_pdb, p_name))
        
        return traj_list

    @classmethod
    def from_keyword_find_single_traj(cls, path, keyword=''):
        '''
        Find all (.prmtop, .pdb and .nc file) groups for EnzyHTP result
        keyword search using 'find' with san check about file existance (used in 2021/11/30 - CHEM5420 final project)
        -----
        path: Search path root
        keyword: keyword used for search (in shell find style)
        -return--
        A list of Traj_calc objects: [Traj_calc(nc, prmtop, name, pdb), ...]
        '''
        traj_list = []
        cmd = f'find {path} -wholename "{keyword}"'
        p_path = run(cmd, check=True, text=True, shell=True, capture_output=True).stdout.strip()
        if not p_path:
            print('WARNING: Do not find prmtop file in:', keyword)
        p_name = keyword
        p_path = os.path.dirname(p_path)
        #--name--
        p_name = p_path.split('/')[-1]
        #--nc--
        p_traj = p_path+'/MD/prod.mdcrd'
        #   san check
        if not os.path.exists(p_traj):
            print('INFO: Do not find mdcrd file. Ignoring:', p_path)
        #--prmtop--
        p_prmtop = glob(p_path+'/*prmtop')
        #   san check
        if len(p_prmtop) == 0:
            print('WARNING: Do not find prmtop file while nc file exists. Ignoring:', p_path)
        if len(p_prmtop) > 1:
            print('WARNING: Found more than one prmtop files in:', p_path)
            print('Please choose between:', p_prmtop)
            raise TrajCalcERROR
        p_prmtop = p_prmtop[0]
        #--pdb--
        # find the pdb with the same name as prmtop. Based on the common procedure in the EnzyHTP
        p_prm_name = p_prmtop[:-7]
        p_pdb = p_prm_name + '.pdb'
        if not os.path.exists(p_pdb):
            print('WARNING: Do not find pdb file while nc and prmtop file exists. Ignoring:', p_path)

        return cls(p_traj, p_prmtop, p_pdb, p_name)

    # === MMPBSA ===
    def update_Radii(self, igb=5):
        '''
        Update Radii for the MMGBSA calculation
        ---
        igb:        gb method used

        update self.prmtop to new_parm_path

        TODO support 3A MMPBSA
        '''
        # get radii
        radii = radii_map[str(igb)]

        mkdir('./tmp')
        prmtop_path = self.prmtop
        new_prmtop_path = prmtop_path[:-7]+'_'+radii+'.prmtop'
        # change Radii
        with open('./tmp/parmed.in','w') as of:
            of.write('changeRadii '+radii+line_feed)
            of.write('parmout '+new_prmtop_path+line_feed)
        try:
            run('parmed -p '+prmtop_path+' -i ./tmp/parmed.in', check=True, text=True, shell=True, capture_output=True)
        except CalledProcessError as err:
            raise TrajCalcERROR(err.stderr)
        self.prmtop = new_prmtop_path
        # clean
        if Config.debug < 2:
            try:
                run('rm parmed.log', check=True, text=True, shell=True, capture_output=True)
            except CalledProcessError:
                pass

        return new_prmtop_path


    def make_dry_frags(self, frag_str, igb=5, if_sol=0):
        '''
        Define MMPBSA fragments
        Make dry prmtop files for the MMPB(GB)SA calculation
        1. make new pdbs
        2. use tLeap to generate these from pdbs
        ---
        frag_str:   A str to define two fragments
                (Grammer)
                - same as pymol select grammer (So that you can confirm selection via pymol)
                - Use ':' to seperate two fragment (In the order of: receptor - ligand . This order only matters in the correspondance in the MMPBSA output)
                * TODO currently only chain id is accepted
                * DO NOT use original chain id in the pdb file. Count from A and from 1.
        igb:        gb method used
        if_sol:     if use also generate solvent prmtop with tleap. (Because Parmed cannot use in the amber instance on many clusters)
                
        update self.dc_prmtop, self.dl_prmtop, self.dr_prmtop
        '''
        # make new fragment pdbs
        frag1_str, frag2_str = frag_str.split(':')
        # --A pseudo PyMol grammar parser--
        # san check
        frag1_str = frag1_str.strip().split(' ')
        frag2_str = frag2_str.strip().split(' ')
        if frag1_str[0] not in ('c.', 'chain') or frag2_str[0] not in ('c.', 'chain'):
            raise TrajCalcERROR('ERROR: current version of make_dry_frags parser only take chain indexes. e.g. c. A+B:c. C')
        frag1_chains = frag1_str[1].split('+')
        frag2_chains = frag2_str[1].split('+')

        # make new pdb files TODO add method to copy chains to make a new stru_obj. Solve problem that there could be potential metal or ligand
        frag1_path = self.pdb[:-4]+'_frag1.pdb'
        frag2_path = self.pdb[:-4]+'_frag2.pdb'
        stru1 = Structure.fromPDB(self.pdb)
        for i in range(len(stru1.chains)-1,-1,-1):
            if stru1.chains[i].id not in frag1_chains:
                del stru1.chains[i]
        # san check
        if len(stru1.chains) == 0: raise TrajCalcERROR('ERROR: PDB'+ self.pdb+' do not contain chain: '+repr(frag1_chains))
        stru1.build(frag1_path)
        stru2 = Structure.fromPDB(self.pdb)
        for i in range(len(stru2.chains)-1,-1,-1):
            if stru2.chains[i].id not in frag2_chains:
                del stru2.chains[i]
        # san check
        if len(stru2.chains) == 0: raise TrajCalcERROR('ERROR: PDB '+ self.pdb +' do not contain chain: '+repr(frag2_chains))
        stru2.build(frag2_path)

        # convert frag pdbs to prmtop files
        self.dr_prmtop = self._pdb2prmtop_mmpbsa(frag1_path, igb=igb)
        self.dl_prmtop = self._pdb2prmtop_mmpbsa(frag2_path, igb=igb)
        self.dc_prmtop = self._pdb2prmtop_mmpbsa(self.pdb, igb=igb, out_path=self.pdb[:-4]+'_dc.prmtop')
        if if_sol:
            self.prmtop = PDB(self.pdb).PDB2FF(igb=igb, prm_out_path=self.pdb[:-4]+'_sc.prmtop', if_prm_only=1)[0]

    @staticmethod
    def _pdb2prmtop_mmpbsa(pdb_path, igb, out_path=None):
        '''
        A method to generate dry prmtop file for MMPBSA
        TODO generalize and combine with PDB2FF fragments
        '''
        radii = radii_map[str(igb)]
        if out_path == None:
            out_path = pdb_path[:-4]+'.prmtop' 
        mkdir('./tmp')
        with open('./tmp/leap_pdb2prmtop.in','w') as of:
            of.write('source leaprc.protein.ff14SB'+line_feed)
            of.write('inp = loadpdb '+ pdb_path +line_feed)
            of.write('set default PBRadii '+ radii +line_feed)
            of.write('saveamberparm inp '+out_path+' ./tmp/tmp.inpcrd'+line_feed)
            of.write('quit'+line_feed)
        
        try:
            run('tleap -s -f ./tmp/leap_pdb2prmtop.in', check=True, text=True, shell=True, capture_output=True)
        except CalledProcessError as err:
            raise TrajCalcERROR(err.stderr)
        # clean
        if Config.debug < 2:
            run('rm leap.log', check=0, text=True, shell=True, capture_output=True)

        return out_path

    # TODO add method using ante-MMPBSA.py

    def run_MMPBSA(self, in_file='', overwrite=0, out_path=''):
        '''
        Run MMPB(GB)SA using self.nc, self.prmtop. self.dl_prmtop, self.dr_prmtop, self.dc_prmtop
        MMPBSA settings in in_file or Config.Amber.MMPBSA.in_conf
        ---
        ncpu
        in_file: path of MMPBSA.in file.
        overwrite: if overwrite existing in_file
        out_path: result output path (default: ./"self.name"_MMPBSA.dat)
        ---
        '''
        # build in file
        if in_file == '':
            in_file = Config.Amber.MMPBSA.build_MMPBSA_in()
        else:
            if os.path.exists(in_file):
                if overwrite:
                    Config.Amber.MMPBSA.build_MMPBSA_in(in_file)
            else:
                Config.Amber.MMPBSA.build_MMPBSA_in(in_file)
        # define out file path
        if out_path == '':
            out_path = './' + self.name + '_MMPBSA.dat'
        # get dir
        out_dir = '/'.join(out_path.split('/')[:-1])
        if out_dir == '':
            out_dir = './'

        cmd = Config.get_PC_cmd() + ' python2 '+ Config.Amber.MMPBSA.get_MMPBSA_engine() + ' -O -i '+in_file+' -o '+out_path+' -sp '+ self.prmtop +' -cp '+ self.dc_prmtop +' -rp '+ self.dr_prmtop +' -lp '+ self.dl_prmtop + ' -y '+ self.nc
        if Config.debug >= 1:
            print('running:   ', cmd)
        try:
            run(cmd, check=True, text=True, shell=True, capture_output=True)
        except CalledProcessError as err:
            raise TrajCalcERROR(err.stderr)
        # clean
        if Config.debug < 2:
            run('rm reference.frc _MMPBSA_info', check=0, text=True, shell=True, capture_output=True)
        
        return out_path

    @classmethod
    def calc_MMPBSA(cls, traj_list, frag_str, igb=5, out_dir='', in_file='', use_parmed=1, prepare_only=0):
        '''
        1. update_Radii
        2. make_dry_frags
        3. run_MMPBSA
        -----
        traj_list: a list of Traj_calc objects
        frag_str:   A str to define two fragments
                (Grammer)
                - same as pymol select grammer (So that you can confirm selection via pymol)
                - Use ':' to seperate two fragment (In the order of: receptor - ligand . This order only matters in the correspondance in the MMPBSA output)
                * DO NOT use original chain id in the pdb file. Count from A and from 1.
        igb:        igb method used for MMGBSA (relate to Radii change)
        out_dir:    output dir of the data file
        in_file:    MMPBSA.in
        use_parmed: if use parmed the change the Radii
        prepare_only: if prepare the prmtop files only. (With accre this is nessessary since the Amber and MMPBSA is install with a lower version of Python and kills everythings use conda.)
        '''
        # clean out path
        if out_dir == '':
            out_dir = './'
        else:
            mkdir(out_dir)
        if out_dir[-1] != '/':
            out_dir = out_dir + '/'

        data_files = []

        for traj in traj_list:
            try:
                if use_parmed:
                    traj.update_Radii(igb=igb)
                    traj.make_dry_frags(frag_str, igb=igb)
                else:
                    traj.make_dry_frags(frag_str, igb=igb, if_sol=1)
                if not prepare_only:
                    data_file = traj.run_MMPBSA(in_file=in_file, out_path=out_dir+traj.name+'.dat')
                    data_files.append(data_file)
                else:
                    data_files.append((traj.name, traj.nc, traj.prmtop, traj.dl_prmtop, traj.dr_prmtop, traj.dc_prmtop))
            except TrajCalcERROR as err:
                print('ERROR:', err)
        return data_files

    # === RMSD clustering ===
    def get_rep_structure(self, target_mask: str, save_dir: str):
        """get representative structures of the trajectory"""
        from sklearn.cluster import KMeans
        traj = mdtraj.load(self.traj, top=self.prmtop)
        traj = traj.remove_solvent()
        atom_list = traj.topology.select(target_mask)
        frame_rmsd = mdtraj.rmsd(traj, traj, 0, atom_list)
        X = np.array(frame_rmsd).reshape(-1, 1)
        km = KMeans()
        km.fit(X)
        clusters = km.labels_
        representative_frames = [
            frame for i, frame in enumerate(traj) if frame_rmsd[i] == np.median(X[clusters == clusters[i]])]
        for i, rep_frame in enumerate(representative_frames):
            rep_frame.save_pdb(f"{save_dir}rep_stru_{i}.pdb")

def main():
    # Config.n_cores=4    
    # igb=5
    # frag_str = 'c. A+B:c. C'

    # traj_list = Traj_calc.From_keyword_find('.', keyword='1T83*')
    # data_files = Traj_calc.calc_MMPBSA(traj_list, frag_str, igb, out_dir='./MMPBSA-test1')
    # print(data_files)
    # with open('MMPBSA.dat','w') as of:
    #     of.write(repr(data_path))
    pass



if __name__ == "__main__":
    main()
