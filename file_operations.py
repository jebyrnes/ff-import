from os import path, mkdir, listdir
from shutil import rmtree, copy

def accept_tile(filename, scratch_path):
    copy(
        path.join(scratch_path, "scene", filename),
        path.join("tiles", "accepted", filename)
    )

def reject_tile(filename, scratch_path):
    copy(
        path.join(scratch_path, "scene", filename),
        path.join("tiles", "rejected", filename)
    )

def build_output():
    if(path.exists("tiles")):
        print("Removing existing output tiles")
        rmtree("tiles")

    mkdir("tiles")
    mkdir(path.join("tiles","accepted"))
    mkdir(path.join("tiles","rejected"))

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
