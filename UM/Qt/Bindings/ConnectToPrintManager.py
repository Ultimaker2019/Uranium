# Copyright (c) 2019 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.
from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot
from typing import List, Mapping, Optional, TYPE_CHECKING

from UM.Logger import Logger

import subprocess
import os

class ConnectToPrintManager(QObject):
    def __init__(self) -> None:
        super().__init__()

    sub_process = None

    @pyqtSlot()
    def run(self):
        serch_path0 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../resources/run', 'USBprint2.exe'))
        command = [serch_path0]
        command += ['M2030']
        gcode_file_path = os.path.expanduser('~') + "\\AppData\\Local\\cura\\temp.gcode"
        command += [gcode_file_path]
        Logger.log("d", "Call subprocess: %s", command)
        if self.sub_process is None:
            self.sub_process = subprocess.Popen(command)
        sp = self.sub_process
        self.sub_process = subprocess.Popen(command)
        sp.terminate()
        return

def createConnectToPrintManager(engine: "QQmlEngine", script_engine: "QJSEngine") -> ConnectToPrintManager:
    return ConnectToPrintManager()

