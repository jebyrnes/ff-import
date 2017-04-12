import logging
from os import path, mkdir, listdir
from shutil import rmtree, copy
import tempfile

def accept_tile(filename, config):
    copy(
        path.join(config.SCRATCH_PATH, "scene", filename),
        path.join("{0}_tiles".format(config.SCENE), "accepted", filename)
    )

def reject_tile(filename, config):
    copy(
        path.join(config.SCRATCH_PATH, "scene", filename),
        path.join("{0}_tiles".format(config.SCENE), "rejected", filename)
    )

def build_output(scene_name):
    logger = logging.getLogger(scene_name)
    target = "{0}_tiles".format(scene_name)

    if(path.exists(target)):
        logger.info("Removing existing output tiles")
        rmtree(target)

    logger.info("Building output subdirectories")
    mkdir(target)
    mkdir(path.join(target,"accepted"))
    mkdir(path.join(target,"rejected"))

def build_scratch(config):
    logger = logging.getLogger(config.SCENE)

    should_use_tempdir = config.WITHTEMPDIR

    if should_use_tempdir:
        config.SCRATCH_PATH = tempfile.mkdtemp(prefix='ff-import-')
        logger.info("Using true scratch directory {0}".format(config.SCRATCH_PATH))

    scratch_path = config.SCRATCH_PATH
    if(not config.WITHTEMPDIR and path.exists(scratch_path)):
        logger.info("Removing existing scratch tiles")
        rmtree(scratch_path)
        mkdir(scratch_path)

    logger.info("Building scratch tile directories")
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
    logger = logging.getLogger(config.SCENE)
    if config.WITHTEMPDIR:
        logger.info("attempting to clean up scratch directory")
        rmtree(config.SCRATCH_PATH)
