import os
def ensureDirExist(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)