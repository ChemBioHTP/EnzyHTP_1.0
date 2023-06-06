"""Defines a GaussianInterface class that serves as a bridge for enzy_htp to utilize Gaussian software. This serves
as a wrapper for all functionality provided by the Gaussian software package. Behavior is partially controlled by 
the GaussianConfig class owned by the interface. Supported operations include:
	+ QM Clustering
Author: Qianzhen (QZ) Shao <qianzhen.shao@vanderbilt.edu>
Author: Chris Jurich <chris.jurich@vanderbilt.edu>
Date: 2022-06-11
"""
from pathlib import Path
from typing import List, Tuple

from enzy_htp.core import file_system as fs
from enzy_htp.core import env_manager as em

# from enzy_htp.molecular_mechanics import Frame
from enzy_htp.structure import Structure, PDBParser
#structure_from_pdb

# from .gaussian_config import GaussianConfig, default_gaussian_config

# TODO(CJ): add .config() getter

from .base_interface import BaseInterface

class GaussianInterface(BaseInterface):
    """TODO(CJ)
    Attributes:
        config_:
        env_manager_ : The EnvironmentManager() class which ensure all required environment elements exist.
        compatible_env_ : A bool() indicating if the current environment is compatible with the object itself.
    """

    def __init__(self, parent, config: GaussianConfig = None) -> None:
        """Simplistic constructor that optionally takes a GaussianConfig object as its only argument.
        Calls parent class.
        """
        super().__init__(parent, config, default_amber_config)


    def PDB2QMMM(
        self,
        o_dir="",
        tag="",
        work_type="spe",
        qm="g16",
        keywords="",
        prmtop_path=None,
        prepi_path: dict = None,
        spin_list=[1, 1],
        ifchk=1,
    ):
        """
        generate QMMM input template based on [connectivity, atom order, work type, layer/freeze settings, charge settings]
        * NEED TO SET LAYER BY ATOM INDEX OR SELECT A LAYER PRESET (use Config.Gaussian.layer_preset and Config.Gaussian.layer_atoms)
        * define self.frames in the func
        --------
        qm          : QM program (default: g16 / Gaussian16)
        work_type   : QMMM calculation type (default: spe)
        o_dir       : out put directory of the input file (default: self.dir/QMMM/ )
        tag         : folder name tag for potential multiple mutations
        keywords    : additional keywords add to the work_type correlated route
        prmtop_path : provide prmtop file for determining charge and spin. use self.prmtop by default
        prepi_path  : a diction of prepin file path with each ligand name as key. (e.g.: {'4CO':'./ligand/xxx.prepin'})
        spin_list   : a list of spin for each layers. (Do not support auto judge of the spin now)
        ifchk       : if save chk and return chk paths
        <see more options in Config.Gaussian>
        ========
        Gaussian
        ========
        # route section (from config module / leave work type as an inp arg)
        # charge and spin
        # coordinate
                - atom label (from .lib)
                - atom charge
                - freeze part (general option / some presupposition / freeze MM)
                - layer (same as above)
                - xyz (1. new system 2. existing template (do we still need?) -- from pdb / mdcrd / gout) ref: ONIOM_template_tool
        # connectivity
        # missing parameters (ligand related?)
        ---------
        In Config.Gaussian
        ---------
        n_cores     : Cores for gaussian job (higher pirority)
        max_core    : Per core memory in MB for gaussian job (higher pirority)
        keywords    : a list of keywords that joined together when build
        layer_preset：default preset id copied to self.layer_preset
        layer_atoms : default layer_atoms copied to self.layer_atoms
        *om_lvl     : *(can only be edit manually before loading the module) oniom method level
        """
        # san check
        support_work_type = ["spe", "opt", "tsopt"]
        if work_type not in support_work_type:
            raise Exception("PDB2QMMM.work_type : only support: " +
                            repr(support_work_type))
        support_qm = ["g16"]
        if qm not in support_qm:
            raise Exception("PDB2QMMM.qm: only support: " + repr(support_qm))
        # default
        if prmtop_path == None:
            prmtop_path = self.prmtop_path
        # make folder
        if o_dir == "":
            o_dir = self.dir + "/QMMM" + tag
        mkdir(o_dir)
        # file path and name
        o_name = self.name + "_QMMM"
        g_temp_path = o_dir + "/" + o_name + ".gjf"
        # get stru
        self.get_stru()
        # get layer
        self._get_oniom_layer()
        # prepin path
        if prepi_path == None:
            prepi_path = self.prepi_path

        # build template
        if qm == "g16":
            self.route = self._get_oniom_g16_route(work_type, o_name, key_words=keywords)
            title = (
                "ONIOM input template generated by PDB2QMMM module of XXX(software name)"
                + line_feed)
            chrgspin = self._get_oniom_chrgspin(prmtop_path=prmtop_path,
                                                spin_list=spin_list)
            cnt_table = self.stru.get_connectivty_table(prepi_path=prepi_path)
            coord = self._get_oniom_g16_coord(
                prmtop_path)  # use connectivity info from the line above.
            add_prm = (self._get_oniom_g16_add_prm()
                       )  # test for rules of missing parameters

            # combine and write
            with open(g_temp_path, "w") as of:
                of.write(self.route)
                of.write(line_feed)
                of.write(title)
                of.write(line_feed)
                of.write(chrgspin)
                of.write(line_feed)
                of.write(coord)
                of.write(line_feed)
                of.write(cnt_table)
                of.write(line_feed)
                of.write(add_prm)

        # deploy to inp files
        frames = Frame.fromMDCrd(self.mdcrd)
        self.frames = frames
        gjf_paths = []
        chk_paths = []
        if Config.debug >= 1:
            print("Writing QMMM gjfs.")
        for i, frame in enumerate(frames):
            if ifchk:
                frame_path = frame.write_to_template(g_temp_path, index=str(i), ifchk=1)
                gjf_paths.append(frame_path[0])
                chk_paths.append(frame_path[1])
            else:
                gjf_paths.append(
                    frame.write_to_template(g_temp_path, index=str(i), ifchk=0))
        # run Gaussian job
        self.qmmm_out = PDB.Run_QM(gjf_paths)

        if ifchk:
            self.qmmm_chk = chk_paths
            return self.qmmm_out, self.qmmm_chk

        return self.qmmm_out

    def _get_oniom_layer(self):
        """
        get oniom layer base on self.layer_atoms or self.layer_preset
        save a Layer object to self.layer
        """
        #  san check (need at least a set or a preset mode)
        if self.layer_atoms == [] and self.layer_preset == 0:
            raise Exception(
                "PDB2QMMM: need layer setting. Please use self.set_oniom_layer.")
        # layer_atoms are in higher pirority
        if self.layer_atoms != []:
            self.layer = Layer(self, self.layer_atoms)
        else:
            self.layer = Layer.preset(self, self.layer_preset)

    def _get_oniom_g16_route(self, work_type, chk_name="chk_place_holder", key_words=""):
        """
        generate gaussian 16 ONIOM route section. Base on settings in the config module.
        -------
        work_type   : ONIOM calculation type (support: spe, ...)
        chk_name    : filename of chk (QMMM.chk by default / self.name + _QMMM.chk in the default workflow use.)
        key_words   : allow additional key words
        -------
        support edit keywords directly in module Config
        """
        chk = r"%chk=" + chk_name + ".chk" + line_feed
        proc = "%nprocshared=" + str(Config.n_cores) + line_feed
        mem = "%mem=" + str(Config.n_cores * Config.max_core) + "MB" + line_feed
        if type(key_words) == str and key_words != "":
            keyword_line = ("# " + " ".join(Config.Gaussian.keywords[work_type] + [
                key_words,
            ]) + line_feed)
        if type(key_words) == list:
            keyword_line = ("# " +
                            " ".join(Config.Gaussian.keywords[work_type] + key_words) +
                            line_feed)

        route = chk + proc + mem + keyword_line
        return route

    def _get_oniom_chrgspin(self, prmtop_path=None, spin_list=[1, 1]):
        """
        Determing charge and spin for each ONIOM layers. Base on *prmtop file* and layer settings in the *config* module.
        """
        chrgspin = None
        # san check
        if prmtop_path == None:
            if self.prmtop_path == None:
                raise Exception(
                    "Please provide or use PDB2FF() to generate a prmtop file before PDB2QMMM"
                )
            prmtop_path = self.prmtop_path

        # get charge list
        self.chrg_list_all = PDB.get_charge_list(prmtop_path)
        # init
        self.layer_chrgspin = []
        for j in range(len(self.layer)):
            self.layer_chrgspin.append(float(0))
        # add charge to layers
        for i, chrg in enumerate(self.chrg_list_all):
            for j, layer in enumerate(self.layer):
                if i + 1 in layer:
                    self.layer_chrgspin[j] += chrg

        # add spin
        if len(self.layer_chrgspin) != len(spin_list):
            raise Exception(
                "spin specification need to match the layer setting. e.g.: spin_list=[h_spin, l_spin]"
            )
        for i, spin in enumerate(spin_list):
            self.layer_chrgspin[i] = (self.layer_chrgspin[i], spin)
        # make string
        if len(self.layer) == 2:
            c1 = str(round(self.layer_chrgspin[0][0]))
            s1 = str(round(self.layer_chrgspin[0][1]))
            c2 = str(round(self.layer_chrgspin[1][0]))
            s2 = str(round(self.layer_chrgspin[1][1]))
            c3 = c2
            s3 = s2
            chrgspin = " ".join([c1, s1, c2, s2, c3, s3])
        else:
            raise Exception(
                "Only support 2 layers writing charge and spin. Update in the future")

        if Config.debug >= 1:
            print(chrgspin)

        return chrgspin

    def _get_oniom_g16_coord(self):
        """
        generate coordinate line. Base on *structure* and layer settings in the *config* module.
        Use element name as atom type for ligand atoms since they are mostly in QM regions.
        ---------------
        for a coord line:
            - element name
                - atom name (from .lib)
                - atom charge (from self.charge_list_all)
                - freeze part (general option / some presupposition)
                - xyz (from self.stru)
                - layer (general option / some presupposition)
        """
        coord = ""

        # amber default hold the chain - ligand - metal - solvent order
        a_id = 0
        for chain in self.stru.chains:
            for res in chain:
                for atom in res:
                    a_id += 1
                    # san check
                    if atom.id != a_id:
                        raise Exception("atom id error.")
                    if atom.id in self.layer[0]:
                        coord += atom.build_oniom("h", self.chrg_list_all[atom.id - 1])
                    else:
                        # consider connection
                        cnt_info = None
                        repeat_flag = 0
                        for cnt_atom in atom.connect:
                            if cnt_atom.id in self.layer[0]:
                                if repeat_flag:
                                    raise Exception(
                                        "A low layer atom is connecting 2 higher layer atoms"
                                    )
                                cnt_info = [
                                    "H",
                                    cnt_atom.get_pseudo_H_type(atom),
                                    cnt_atom.id,
                                ]
                                repeat_flag = 1
                        # general low layer
                        coord += atom.build_oniom("l",
                                                  self.chrg_list_all[atom.id - 1],
                                                  cnt_info=cnt_info)
        for lig in self.stru.ligands:
            for atom in lig:
                a_id += 1
                if atom.id != a_id:
                    raise Exception("atom id error.")
                if atom.id in self.layer[0]:
                    coord += atom.build_oniom("h",
                                              self.chrg_list_all[atom.id - 1],
                                              if_lig=1)
                else:
                    if Config.debug >= 1:
                        print(
                            "\033[1;31;0m In PDB2QMMM in _get_oniom_g16_coord: WARNING: Found ligand atom in low layer \033[0m"
                        )
                    # consider connection
                    cnt_info = None
                    repeat_flag = 0
                    for cnt_atom in atom.connect:
                        if repeat_flag:
                            raise Exception(
                                "A low layer atom is connecting 2 higher layer atoms")
                        if cnt_atom.id in self.layer[0]:
                            if Config.debug >= 1:
                                print(
                                    "\033[1;31;0m In PDB2QMMM in _get_oniom_g16_coord: WARNING: Found ligand atom"
                                    + str(atom.id) + " in seperate layers \033[0m")
                            cnt_info = [
                                "H",
                                cnt_atom.get_pseudo_H_type(atom),
                                cnt_atom.id,
                            ]
                            repeat_flag = 1
                    coord += atom.build_oniom(
                        "l",
                        self.chrg_list_all[atom.id - 1],
                        cnt_info=cnt_info,
                        if_lig=1,
                    )
        for atom in self.stru.metalatoms:
            a_id += 1
            if atom.id != a_id:
                raise Exception("atom id error.")
            if atom.id in self.layer[0]:
                coord += atom.build_oniom("h", self.chrg_list_all[atom.id - 1])
            else:
                coord += atom.build_oniom("l", self.chrg_list_all[atom.id - 1])
        for sol in self.stru.solvents:
            for atom in sol:
                a_id += 1
                if atom.id != a_id:
                    raise Exception("atom id error.")
                if atom.id in self.layer[0]:
                    coord += atom.build_oniom("h",
                                              self.chrg_list_all[atom.id - 1],
                                              if_sol=1)
                else:
                    # consider connection
                    cnt_info = None  # for future update
                    repeat_flag = 0
                    for cnt_atom in atom.connect:
                        if cnt_atom.id in self.layer[0]:
                            if Config.debug >= 1:
                                print(
                                    "\033[1;31;0m In PDB2QMMM in _get_oniom_g16_coord: WARNING: Found solvent atom"
                                    + str(atom.id) + " in seperate layers \033[0m")
                            if repeat_flag:
                                raise Exception(
                                    "A low layer atom is connecting 2 higher layer atoms")
                            cnt_info = [
                                "H",
                                cnt_atom.get_pseudo_H_type(atom),
                                cnt_atom.id,
                            ]
                            repeat_flag = 1
                    coord += atom.build_oniom(
                        "l",
                        self.chrg_list_all[atom.id - 1],
                        cnt_info=cnt_info,
                        if_sol=1,
                    )

        return coord

    def _get_oniom_g16_add_prm(self):
        """
        Add missing parameters for protein and custom atom types
        1. addition parameters for metal element that not exist in ff96
        2. Commonly missing line for no reason: 'HrmBnd1    N   CT   HC     35.0000     109.5000'
        3. What if ligand or artificial residue appears in the low layer TODO
        4. missing parameters brought by the pseudo boundary H
        """
        # 1
        add_prm = "HrmBnd1    N   CT   HC     35.0000     109.5000" + line_feed
        # 2
        atom_rec = []
        for atom in self.stru.metalatoms:
            if atom.parm != None:
                if atom.parm[0] not in atom_rec:
                    add_prm += "VDW   " + "   ".join(atom.parm) + line_feed
                    atom_rec.append(atom.parm[0])
        # 3
        # TODO
        # 4

        return add_prm

    @classmethod
    def Run_QM(cls, inp, prog="g16"):
        """
        Run QM with prog
        """
        if prog == "g16":
            outs = []
            for gjf in inp:
                out = gjf[:-3] + "out"
                if Config.debug > 1:
                    print("running: " + Config.Gaussian.g16_exe + " < " + gjf + " > " +
                          out)
                os.system(Config.Gaussian.g16_exe + " < " + gjf + " > " + out)
                outs.append(out)
            return outs

        if prog == "g09":
            outs = []
            for gjf in inp:
                out = gjf[:-3] + "out"
                if Config.debug > 1:
                    print("running: " + Config.Gaussian.g09_exe + " < " + gjf + " > " +
                          out)
                os.system(Config.Gaussian.g09_exe + " < " + gjf + " > " + out)
                outs.append(out)
            return outs

    def gjf_from_frame(self, outfile: str, route: str, frame) -> Tuple[str, str]:
        """TODO"""
        # TODO(CJ): incorporate memory from enzy_htp.config
        chk = str(Path(outfile).with_suffix(".chk"))
        contents: List[str] = [
            f"%chk={chk}",
            route,
            "",
            "QM Cluster Input Generated by EnzyHTP",
            "",
        ]
        # TODO(CJ): put in the actual charge/spin
        contents.append("0 1")
        contents.extend(frame.get_atom_lines())
        contents.extend(["", ""])
        fs.write_lines(outfile, contents)
        return outfile, chk

    def get_fchk(self, chks: List[str]) -> List[str]:
        """TODO"""
        result: List[str] = list()
        for chk in chks:
            fchk = str(Path(chk).with_suffix(".fchk"))
            result.append(fchk)
            self.env_manager_.run_command("formchk", [chk, fchk])

        return result

    def qm_cluster(
        self,
        frames,
        atom_mask: str,
        route: str,
        work_dir: str = "./qm_cluster/",
        cap_strat: str = "H",
        spin: int = 1,
    ) -> List[Tuple[str, str]]:
        """TODO(CJ):"""
        # TODO(CJ): add a check that the atom_mask is legal
        # make folder
        fs.safe_mkdir(work_dir)
        _ = list(map(lambda fr: fr.apply_mask(atom_mask, cap_strat), frames))
        cluster_inputs: List[str] = list()
        chk_outputs = []
        for fidx, frame in enumerate(frames):
            fname = f"{work_dir}/qm_cluster{fidx+1:03d}.gjf"
            (cinput, chk) = self.gjf_from_frame(fname, route, frame)
            cluster_inputs.append(cinput)
            chk_outputs.append(chk)

        for ci in cluster_inputs:
            outfile = str(Path(ci).with_suffix(".out"))
            self.env_manager_.run_command(self.config_.G16_EXE, ["<", ci, ">", outfile])

        return (cluster_inputs, chk_outputs)
