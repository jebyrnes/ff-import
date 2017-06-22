from os import path
from sys import argv
import logging

import image_operations as img
from csv_operations import write_rejects, write_manifest

from file_operations import (
    build_output, scratch_exists,
    build_scratch, get_files_by_extension, accept_tile, reject_tile,
    maybe_clean_scratch, find_scene_name)
from gis_operations import compute_coordinate_metadata
from xml_operations import parse_metadata
from config import config

logging.basicConfig(
    format='[ff-import %(name)s] %(levelname)s %(asctime)-15s %(message)s'
)


def usage():
    print """
simple.py (Simple Image Pipeline)

python simple.py [--option] SCENE_DIR

This script is used to process satellite imagery from LANDSAT 4, 5, 7, and 8
into subjects for Floating Forests. This includes sorting out tiles that only
contain land or contain too many clouds, as well as compositing the different
bands together into an RGB image and boosting certain parts of the green
channel to aid in kelp-spotting.

    --full                  Run full pipeline

    --clean                 Recreate scratch directory

    --generate              Perform all scene tile generation tasks
    --assemble              Perform color adjustment and build color output
    --generate-tiles        Build color tiles of scene

    --remove-negative       Remove negative pixels from data that happens
                            to contain 16-bit signed values

    --sort-tiles            Perform all tile sorting tasks
    --generate-mask         Regenerate mask tiles
    --remove-land           Reject tiles that are only land
    --remove-clouds         Reject tiles that are too cloudy
    --remove-all            Reject tiles that are only land or too cloudy
    --reject                Sort tiles into accepted and rejected folders

    --visualize             Show which tiles would be rejected

    --manifest              Build a manifest file for Panoptes subject upload

    --grid-size=XXX         Set custom tile size

    --source-dir=MY_PATH    Load scenes from a specified directory

    --land-threshhold=XX    Configure land detection
    --land-sensitivity=XX

    --cloud-threshhold=XX   Configure cloud detection
    --cloud-sensitivity=XX
    """


def parse_options():
    # note that logger is undefined when this method is active
    for arg in argv:
        if arg == "simple.py":
            continue

        if arg == "--help" or arg == "-?":
            # do nothing, we'll fall through to usage
            () #noqa

        elif arg == "--full":
            config.WITHTEMPDIR = True
            config.REBUILD = True
            config.REMOVE_NEGATIVE = True
            config.ASSEMBLE_IMAGE = True
            config.SLICE_IMAGE = True
            config.GENERATE_MASK_TILES = True
            config.REMOVE_LAND = True
            config.REMOVE_CLOUDS = True
            config.REJECT_TILES = True
            config.BUILD_MANIFEST = True

        elif arg == "--remove-negative":
            config.REMOVE_NEGATIVE = True
        elif arg == "--assemble":
            config.ASSEMBLE_IMAGE = True
        elif arg == "--generate-tiles":
            config.SLICE_IMAGE = True
        elif arg == "--generate":
            config.ASSEMBLE_IMAGE = True
            config.SLICE_IMAGE = True

        elif arg == "--clean":
            config.REBUILD = True

        elif arg == "--sort-tiles":
            config.GENERATE_MASK_TILES = True
            config.REMOVE_LAND = True
            config.REMOVE_CLOUDS = True
            config.REJECT_TILES = True
        elif arg == "--generate-mask":
            config.GENERATE_MASK_TILES = True
        elif arg == "--remove-land":
            config.REMOVE_LAND = True
        elif arg == "--remove-clouds":
            config.REMOVE_CLOUDS = True
        elif arg == "--remove-all":
            config.REMOVE_CLOUDS = True
            config.REMOVE_LAND = True
        elif arg == "--visualize":
            config.VISUALIZE_SORT = True
        elif arg == "--reject":
            config.REJECT_TILES = True
        elif arg == "--manifest":
            config.BUILD_MANIFEST = True

        elif arg.startswith("--grid-size="):
            config.GRID_SIZE = int(arg.split("=")[1])
        elif arg.startswith("--land-threshhold="):
            config.LAND_THRESHHOLD = int(arg.split("=")[1])
        elif arg.startswith("--land-sensitivity="):
            config.LAND_SENSITIVITY = int(arg.split("=")[1])
        elif arg.startswith("--cloud-threshhold="):
            config.CLOUD_THRESHHOLD = int(arg.split("=")[1])
        elif arg.startswith("--cloud-sensitivity="):
            config.CLOUD_SENSITIVITY = int(arg.split("=")[1])
        else:
            config.SCENE_DIR = arg

    config.DO_LUT = True

    config.SCENE_NAME = find_scene_name(config)
    config.NEW_MASK = path.join(config.SCENE_DIR, config.SCENE_NAME + "_pixel_qa.tif")
    config.RED_CHANNEL = path.join(config.SCENE_DIR, config.SCENE_NAME + "_sr_band3.tif")
    config.GREEN_CHANNEL = path.join(config.SCENE_DIR, config.SCENE_NAME + "_sr_band4.tif")
    config.BLUE_CHANNEL = path.join(config.SCENE_DIR, config.SCENE_NAME + "_sr_band1.tif")
    config.METADATA_SRC = path.join(config.SCENE_DIR, config.SCENE_NAME + ".xml")
    config.INPUT_FILE = config.NEW_MASK

def generate_mask_tiles():
    logger = logging.getLogger(config.SCENE_NAME)
    logger.info(
        "Generating mask tiles of " + str(config.GRID_SIZE) +
        "x" + str(config.GRID_SIZE) + " pixels")

    logger.info("Generating land mask tiles")
    img.prepare_land_mask(config)

    logger.info("Generating cloud mask tiles")
    img.prepare_cloud_mask(config)

    generated_count = len(get_files_by_extension(path.join(config.SCRATCH_PATH, "land"), "png"))
    logger.info("Generated " + str(generated_count) + " tiles")

def apply_rules(candidates, rejects, subdirectory, rules):
    accum = []
    logger = logging.getLogger(config.SCENE_NAME)

    logger.info("Examining " + str(len(candidates)) + " tiles for " + subdirectory)
    for filename in candidates:
        done = False
        statistics = img.get_image_statistics(path.join(
            config.SCRATCH_PATH,
            subdirectory,
            filename))
        for rule in rules:
            if not rule(*statistics):
                rejects.append(filename)
                done = True
                break
        if done:
            continue

        accum.append(filename)

    return accum

def index_to_location(filename, width, grid_size):
    per_row = width // grid_size + 1
    idx = int(filename.split("_")[1].split(".")[0])
    row = idx // per_row
    col = idx % per_row

    return [row, col]

def build_dict_for_csv(filename, reason, config):
    [width, height] = img.get_dimensions(path.join(config.SCRATCH_PATH, "scene", filename))
    [row, column] = index_to_location(filename, config.width, config.GRID_SIZE)

    my_dict = {
        '#filename': filename,
        '#reason': reason,
        '#row': row,
        '#column': column,
        '#width': width,
        '#height': height,
    }

    coordinate_metadata = compute_coordinate_metadata(row, column, width, height, config)

    my_dict.update(coordinate_metadata)
    my_dict.update(config.METADATA)
    return my_dict


def main():

    retained_tiles = []
    no_water = []
    too_cloudy = []

    parse_options()

    if  (not config.GENERATE_MASK_TILES and
         not config.REJECT_TILES and
         not config.VISUALIZE_SORT and
         not config.ASSEMBLE_IMAGE and
         not config.SLICE_IMAGE and
         not config.REMOVE_NEGATIVE and
         not config.BUILD_MANIFEST and
         not config.DO_LUT and
         not config.REBUILD):
        usage()
        return

    if ((config.GENERATE_MASK_TILES or
         config.REJECT_TILES or
         config.VISUALIZE_SORT or
         config.ASSEMBLE_IMAGE or
         config.REMOVE_NEGATIVE or
         config.BUILD_MANIFEST or
         config.SLICE_IMAGE) and
            config.SCENE_DIR == ''):
        usage()
        return

    logger = logging.getLogger(config.SCENE_NAME)
    logger.setLevel(logging.INFO)
    logger.info("Processing start")

    accepts = []
    rejects = []

    [config.width, config.height] = img.get_dimensions(config.INPUT_FILE)

    if config.REBUILD or not scratch_exists(config):
        build_scratch(config)

    if config.BUILD_MANIFEST:
        metadata = parse_metadata(config.SCENE_DIR, config.METADATA_SRC)
        config.METADATA = metadata

    if config.DO_LUT:
        logger.info("Building water mask")
        config.WATER_MASK = path.join(config.SCRATCH_PATH, "water_mask.png")
        img.build_mask_files(config, "water_lut.pgm", config.WATER_MASK)
        logger.info("Building cloud mask")
        config.CLOUD_MASK = path.join(config.SCRATCH_PATH, "cloud_mask.png")
        img.build_mask_files(config, "cloud_lut.pgm", config.CLOUD_MASK)
        logger.info("Building snow mask")
        config.SNOW_MASK = path.join(config.SCRATCH_PATH, "snow_mask.png")
        img.build_mask_files(config, "snow_lut.pgm", config.SNOW_MASK)
        config.INPUT_FILE = config.WATER_MASK

    if config.REMOVE_NEGATIVE:
        logger.info("Processing source data to remove negative pixels")
        for suffix in ["band3.tif", "band4.tif", "band1.tif"]:
            filename = config.SCENE_NAME + "_sr_" + suffix
            logger.info("Processing image " + filename)
            img.clamp_image(
                path.join(config.SCENE_DIR, filename),
                path.join(config.SCRATCH_PATH, suffix),
                config
            )
        config.RED_CHANNEL = path.join(config.SCRATCH_PATH, "band3.tif")
        config.GREEN_CHANNEL = path.join(config.SCRATCH_PATH, "band4.tif")
        config.BLUE_CHANNEL = path.join(config.SCRATCH_PATH, "band1.tif")

    if config.ASSEMBLE_IMAGE:
        img.assemble_image(
            path.join(config.RED_CHANNEL),
            path.join(config.GREEN_CHANNEL),
            path.join(config.BLUE_CHANNEL),
            config)
    else:
        logger.info("Skipping scene generation")

    if config.SLICE_IMAGE:
        logger.info(
            "Generating scene tiles of " +
            str(config.GRID_SIZE) + "x" +
            str(config.GRID_SIZE)+" pixels")
        img.prepare_tiles(config)
    else:
        logger.info("Skipping scene tile generation")

    if config.GENERATE_MASK_TILES:
        generate_mask_tiles()
    else:
        logger.info("Skipping mask generation")

    if config.REJECT_TILES or config.VISUALIZE_SORT:

        retained_tiles = get_files_by_extension(path.join(config.SCRATCH_PATH, "land"), "png")

        if config.REMOVE_LAND:
            retained_tiles = apply_rules(
                retained_tiles, no_water, "land", [
                    lambda imin, imax, imean, idev: float(imax) > config.LAND_THRESHHOLD,
                    lambda imin, imax, imean, idev: (
                        float(imean) > config.LAND_THRESHHOLD or
                        float(idev) > config.LAND_SENSITIVITY
                    )
                ])
        else:
            logger.info("Skipping land removal")

        if config.REMOVE_CLOUDS:
            retained_tiles = apply_rules(
                retained_tiles, too_cloudy, "cloud", [
                    lambda imin, imax, imean, idev: float(imin) < config.CLOUD_THRESHHOLD,
                    lambda imin, imax, imean, idev: (
                        float(imean) < config.CLOUD_THRESHHOLD or
                        float(idev) > config.CLOUD_SENSITIVITY
                    )
                ])
        else:
            logger.info("Skipping cloud removal")

    if config.VISUALIZE_SORT:
        logger.info(str(len(retained_tiles))+" tiles retained")
        logger.info(str(len(no_water))+" tiles without water rejected")
        logger.info(str(len(too_cloudy))+" tiles rejected for clouds")

        logger.info("Generating tile visualization (output.png)")
        land = img.generate_rectangles(no_water, config.width, config.GRID_SIZE)
        clouds = img.generate_rectangles(too_cloudy, config.width, config.GRID_SIZE)
        water = img.generate_rectangles(retained_tiles, config.width, config.GRID_SIZE)
        img.draw_visualization(land, clouds, water, config.INPUT_FILE)

    if config.REJECT_TILES:
        logger.info("Building scene tile output directory")
        build_output(config.SCENE_NAME)

        logger.info("Copying accepted tiles")
        for filename in retained_tiles:
            accept_tile(filename, config)
            accepts.append(build_dict_for_csv(filename, "Accepted", config))

        logger.info("Copying rejected tiles")
        for filename in no_water:
            reject_tile(filename, config)
            rejects.append(build_dict_for_csv(filename, "No Water", config))

        for filename in too_cloudy:
            reject_tile(filename, config)
            rejects.append(build_dict_for_csv(filename, "Too Cloudy", config))

        logger.info("Writing csv file")
        rejects = sorted(rejects, key=lambda k: k['#filename'])
        write_rejects(
            path.join("{0}_tiles".format(config.SCENE_NAME), "rejected", "rejected.csv"),
            rejects)

    if config.BUILD_MANIFEST:
        logger.info("Writing manifest")
        write_manifest(
            path.join("{0}_tiles".format(config.SCENE_NAME), "accepted", "manifest.csv"),
            accepts)

    maybe_clean_scratch(config)

    logger.info("Processing finished")

if __name__ == "__main__":
    main()
