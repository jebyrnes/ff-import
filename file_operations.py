from os import path, mkdir, listdir
import tempfile
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

def build_scratch(config):
    should_use_tempdir = config.WITHTEMPDIR

    if should_use_tempdir:
        config.SCRATCH_PATH = tempfile.mkdtemp(prefix='ff-import-')
        print("Using true scratch directory {0}".format(config.SCRATCH_PATH))

    scratch_path = config.SCRATCH_PATH
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

def maybe_clean_scratch(config):
    if config.WITHTEMPDIR:
        print("attempting to clean up scratch directory")
        rmtree(config.SCRATCH_PATH)
