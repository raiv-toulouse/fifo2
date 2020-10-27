from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
import os
import shutil
from pathlib import Path
import subprocess
import json

class DialogEdit(QDialog):
    def __init__(self,file):
        super().__init__()
        loadUi('edit.ui',self)
        self.file = file
        self.zoneEdition.setPlainText(file.read_text())
        self.accepted.connect(self.sauverFichier)

    def sauverFichier(self):
        f = open(self.file,"w")
        f.write(self.zoneEdition.toPlainText())
        f.close()

class QuartusWidget(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('main.ui',self)
        # Gestionnaires d'évenements
        self.btnWorkingDirectory.clicked.connect(self.selectWorkingDirectory)
        self.cbProject.activated[str].connect(self.selectProject)
        self.cbSchema.activated[str].connect(self.selectSchema)
        self.btnPathQuartus.clicked.connect(self.selectQuartus)
        self.btnEdit.clicked.connect(self.edit_user_v)
        self.btnGenerateProjectFile.clicked.connect(self.generateProjectFile)
        self.btnGenerateBitstream.clicked.connect(self.genereBitstream)
        self.btnQuartusPgmw.clicked.connect(self.runQuartusPgmw)
        self.btn_all_actions.clicked.connect(self.all_actions)
        # Init with config.json file if present
        config_path = Path('config.json')
        if config_path.exists():
            with open(config_path, "r") as config_file:
                config_data = json.load(config_file)
                print(config_data)
                # Update the GUI
                self.workingDirectory = config_data["working_dir"]
                self.project = config_data["project"]
                self.schema = config_data["schema"]
                self.pathQuartus = Path(config_data["path_quartus"])
                self.lblWorkingDirectory.setText(self.workingDirectory)
                self.lblProject.setText(self.project)
                self.lblSchema.setText(self.schema)
                self.lblQuartus.setText(str(self.pathQuartus))
                self.btnEdit.setEnabled(True)
                self.btn_all_actions.setEnabled(True)
        self.home = os.getcwd()

    def selectWorkingDirectory(self):
        self.workingDirectory = QFileDialog.getExistingDirectory(self, "Open Directory",".",QFileDialog.ShowDirsOnly)
        self.lblWorkingDirectory.setText(self.workingDirectory)
        # Récupération des projets présents dans ce working directory
        lstProjects = next(os.walk(self.workingDirectory))[1]
        self.cbProject.clear()
        for project in lstProjects:
            self.cbProject.addItem(project)
        self.cbProject.setEnabled(True)

    def selectProject(self,txt):
        self.project = txt
        self.lblProject.setText(txt)
        self.cbSchema.setEnabled(True)
        # Màj de la liste des schémas
        pathWD = Path(self.workingDirectory)
        lstSchemas = next(os.walk(pathWD / self.project))[1]
        self.cbSchema.clear()
        for schema in lstSchemas:
            self.cbSchema.addItem(schema)
        self.cbSchema.setEnabled(True)

    def selectSchema(self,txt):
        self.schema = txt
        self.lblSchema.setText(txt)
        self.btnPathQuartus.setEnabled(True)

    def selectQuartus(self):
        self.pathQuartus = Path(QFileDialog.getOpenFileName(self, "Select path for Quartus", ".", "quartus_sh.exe")[0])
        self.lblQuartus.setText(str(self.pathQuartus))
        # write the config file
        config = {"working_dir" : self.workingDirectory,
                  "project" : self.project,
                  "schema" : self.schema,
                  "path_quartus" : str(self.pathQuartus)}
        with open("config.json", "w") as config_file:
            json.dump(config, config_file)
        self.btnEdit.setEnabled(True)
        self.btn_all_actions.setEnabled(True)

    def edit_user_v(self):
        os.chdir(self.home)
        self.edit = DialogEdit(Path(self.workingDirectory) / self.project / "quartusProject" / "user.v")
        self.edit.exec_()
        self.btnGenerateProjectFile.setEnabled(True)

    def generateProjectFile(self):
        racine = Path(self.workingDirectory) / self.project
        os.chdir(racine)
        # Création de la liste des fichiers VHD
        lstVhdFiles = []
        for dirpath, dirs, files in os.walk(self.schema):
            for filename in files:
                fname = os.path.join(dirpath,filename)
                if fname.endswith('.vhd'):
                    lstVhdFiles.append(fname)
                    print(fname)
        # On recopie le template
        racine = Path(self.workingDirectory) / self.project
        nomFichProjet = racine / "quartusProject" / "MKRVIDOR4000.qsf"
        shutil.copy(racine / "quartusProject/MKRVIDOR4000.qsf.template",nomFichProjet)
        # On s'en sert pour mettre à jour le fichier du projet
        fich = open(nomFichProjet,"a")
        for fichVhd in lstVhdFiles:
            fich.write("set_global_assignment -name VHDL_FILE ..\\"+fichVhd+'\n')
        fich.close()
        self.btnGenerateBitstream.setEnabled(True)

    def genereBitstream(self):
        #os.chdir(Path(self.PathQuartus[0]).parent)
        os.chdir(Path(self.workingDirectory))
        #print (Path(self.PathQuartus[0]).parent / "quartus_sh.exe")
        result = subprocess.run([self.pathQuartus, '--flow compile MKRVIDOR4000.qpf'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.afficherOutEtErr(result)
        self.btnQuartusPgmw.setEnabled(True)

    def runQuartusPgmw(self):
        path_quartus_pgmw = self.pathQuartus.parent / 'quartus_pgmw.exe'
        print(path_quartus_pgmw)
        result = subprocess.run([path_quartus_pgmw], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.afficherOutEtErr(result)

    def afficherOutEtErr(self,result):
        ch = self.txtOutput.toPlainText()
        ch += result.stdout.decode('utf-8') + '\n'
        ch += result.stderr.decode('utf-8')
        self.txtOutput.setPlainText(ch)

    def all_actions(self):
        self.edit_user_v()
        self.generateProjectFile()
        self.genereBitstream()
        self.runQuartusPgmw()

#
# Main program
#
app = QApplication([])
monQuartusWidget = QuartusWidget()
monQuartusWidget.show()
app.exec_()