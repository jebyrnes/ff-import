from os import path, mkdir, listdir
from shutil import rmtree

def build_scratch(scratch_path):
    if(path.exists(scratch_path)):
        print("Removing existing tiles")
        rmtree(scratch_path)

    mkdir(scratch_path)
    mkdir(path.join(scratch_path,"land"))
    mkdir(path.join(scratch_path,"cloud"))
    mkdir(path.join(scratch_path,"scene"))

def get_files_by_extension(filepath, extension):
    accum = []

    files = listdir(filepath)

    for filename in files:
        if filename.endswith(extension):
            accum.append(filename)

    return accum
