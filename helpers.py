import os
import platform
from shutil import copyfile


class FileExtensions:
    @staticmethod
    def removeFile(filePath: str):
        if os.path.isfile(filePath):
            os.remove(filePath)
        else:
            raise FileNotFoundError('Couldn\'t find a file')

    @staticmethod
    def moveFileFromTo(filePathFrom: str, filePathTo: str):
        if os.path.isfile(filePathFrom):
            copyfile(filePathFrom, filePathTo)
            # os.popen(f'cp {filePathFrom} {filePathTo}')
        else:
            raise FileNotFoundError('Couldn\'t find a file')


class OSExtensions:
    @staticmethod
    def isWindows():
        return platform.system() == 'Windows'
