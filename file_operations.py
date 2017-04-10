from os import path, mkdir, listdir
from shutil import rmtree, copy

def accept_tile(filename, scratch_path, scene_name):
    copy(
        path.join(scratch_path, "scene", filename),
        path.join("{0}_tiles".format(scene_name), "accepted", filename)
    )

def reject_tile(filename, scratch_path, scene_name):
    copy(
        path.join(scratch_path, "scene", filename),
        path.join("{0}_tiles".format(scene_name), "rejected", filename)
    )

def build_output(scene_name):
    target = "{0}_tiles".format(scene_name)
    if(path.exists(target)):
        print("Removing existing output tiles")
        rmtree(target)

    mkdir(target)
    mkdir(path.join(target,"accepted"))
    mkdir(path.join(target,"rejected"))

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
