from __future__ import division

from os import path
from sys import argv

import image_operations as img
from file_operations import build_output, build_scratch, get_files_by_extension, accept_tile, reject_tile
from csv_operations import write_rejects, write_manifest
from xml_operations import parse_metadata
from config import config

def usage():
    print("""
simple.py (Simple Image Pipeline)

python simple.py [--option] SCENE

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
    """)

def parse_options():
    rebuild = False

    for arg in argv:
        if(arg=="simple.py"):
            continue

        if(arg=="--help" or arg=="-?"):
            # do nothing, we'll fall through to usage
            noop = 0

        elif(arg=="--full"):
            config.REMOVE_NEGATIVE = True
            config.ASSEMBLE_IMAGE = True
            config.SLICE_IMAGE = True
            config.GENERATE_MASK_TILES = True
            config.REMOVE_LAND = True
            config.REMOVE_CLOUDS = True
            config.REJECT_TILES = True
            config.BUILD_MANIFEST = True

        elif(arg=="--remove-negative"):
            config.REMOVE_NEGATIVE = True
        elif(arg=="--assemble"):
            config.ASSEMBLE_IMAGE = True
        elif(arg=="--generate-tiles"):
            config.SLICE_IMAGE = True
        elif(arg=="--generate"):
            config.ASSEMBLE_IMAGE = True
            config.SLICE_IMAGE = True

        elif(arg=="--clean"):
            config.REBUILD = True

        elif(arg=="--sort-tiles"):
            config.GENERATE_MASK_TILES = True
            config.REMOVE_LAND = True
            config.REMOVE_CLOUDS = True
            config.REJECT_TILES = True
        elif(arg=="--generate-mask"):
            config.GENERATE_MASK_TILES = True
        elif(arg=="--remove-land"):
            config.REMOVE_LAND = True
        elif(arg=="--remove-clouds"):
            config.REMOVE_CLOUDS = True
        elif(arg=="--remove-all"):
            config.REMOVE_CLOUDS = True
            config.REMOVE_LAND = True
        elif(arg=="--visualize"):
            config.VISUALIZE_SORT = True
        elif(arg=="--reject"):
            config.REJECT_TILES = True
        elif(arg=="--manifest"):
            config.BUILD_MANIFEST = True

        elif(arg.startswith("--grid-size=")):
            config.GRID_SIZE = int(arg.split("=")[1])
        elif(arg.startswith("--source-dir=")):
            config.DATA_PATH = arg.split("=")[1]
        elif(arg.startswith("--land-threshhold=")):
            config.LAND_THRESHHOLD = int(arg.split("=")[1])
        elif(arg.startswith("--land-sensitivity=")):
            config.LAND_SENSITIVITY = int(arg.split("=")[1])
        elif(arg.startswith("--cloud-threshhold=")):
            config.CLOUD_THRESHHOLD = int(arg.split("=")[1])
        elif(arg.startswith("--cloud-sensitivity=")):
            config.CLOUD_SENSITIVITY = int(arg.split("=")[1])
        else:
            config.SCENE = arg

    config.LAND_MASK = path.join(config.DATA_PATH,config.SCENE,config.SCENE+"_sr_land_water_qa.tif")
    config.CLOUD_MASK = path.join(config.DATA_PATH,config.SCENE,config.SCENE+"_sr_cloud_qa.tif")
    config.SNOW_MASK = path.join(config.DATA_PATH,config.SCENE,config.SCENE+"_sr_snow_qa.tif")
    config.METADATA_SRC = path.join(config.DATA_PATH,config.SCENE,config.SCENE+".xml")
    config.INPUT_FILE = config.LAND_MASK

def generate_mask_tiles():
    print("Generating mask tiles of "+str(config.GRID_SIZE)+"x"+str(config.GRID_SIZE)+" pixels")

    print("Generating land mask tiles")
    img.prepare_land_mask(config)

    print("Generating cloud mask tiles")
    img.prepare_cloud_mask(config)

    generated_count = len(get_files_by_extension(path.join(config.SCRATCH_PATH, "land"), "png"))
    print("Generated " + str(generated_count) + " tiles")

def apply_rules(candidates, rejects, subdirectory, rules):
    accum = []

    print("Examining " + str(len(candidates)) + " tiles for " + subdirectory)
    for filename in candidates:
        done = False
        statistics = img.get_image_statistics(path.join(config.SCRATCH_PATH, subdirectory, filename))
        for rule in rules:
            if(not rule(*statistics)):
                rejects.append(filename)
                done = True
                break
        if(done):
            continue

        accum.append(filename)

    return accum

def index_to_location(filename, width, grid_size):
    per_row = width // grid_size + 1
    idx = int(filename.split("_")[1].split(".")[0])
    row = idx // per_row
    col = idx % per_row

    return [row, col]

def compute_tile_coords(row, col, config):
    scene_top = float(config.METADATA["scene_corner_UL_y"])
    scene_bottom = float(config.METADATA["scene_corner_LR_y"])
    scene_left = float(config.METADATA["scene_corner_UL_x"])
    scene_right = float(config.METADATA["scene_corner_LR_x"])

    scene_span_x = scene_right - scene_left
    scene_span_y = scene_bottom - scene_top

    left = ((col * config.GRID_SIZE) / config.width) * scene_span_x + scene_left
    top = ((row * config.GRID_SIZE) / config.height) * scene_span_y + scene_top

    return [left, top]

def build_dict_for_csv(filename, reason, config):
    [row, column] = index_to_location(filename, config.width, config.GRID_SIZE)
    [left, top] = compute_tile_coords(row, column, config)

    result = {
        'filename': filename,
        'reason': reason,
        'row': row,
        'column': column,
        'tile_UL_x': left,
        'tile_UL_y': top
    }

    result.update(config.METADATA)
    return result


def main():

    retained_tiles = []
    no_water = []
    too_cloudy = []

    parse_options()

    if(
        not config.GENERATE_MASK_TILES and
        not config.REJECT_TILES and
        not config.VISUALIZE_SORT and
        not config.ASSEMBLE_IMAGE and
        not config.SLICE_IMAGE and
        not config.REMOVE_NEGATIVE and
        not config.BUILD_MANIFEST and
        not config.REBUILD):
        usage()
        return

    if(
        (config.GENERATE_MASK_TILES or
        config.REJECT_TILES or
        config.VISUALIZE_SORT or
        config.ASSEMBLE_IMAGE or
        config.REMOVE_NEGATIVE or
        config.BUILD_MANIFEST or
        config.SLICE_IMAGE) and
        config.SCENE == ''):
        usage()
        return

    [config.width, config.height] = img.get_dimensions(config.INPUT_FILE)

    if(config.REBUILD):
        build_scratch(config.SCRATCH_PATH)

    print("Processing scene " + config.SCENE)

    if(config.BUILD_MANIFEST):
        metadata = parse_metadata(config.SCENE, config.METADATA_SRC)
        config.METADATA = metadata

    if(config.REMOVE_NEGATIVE):
        print("Processing source data to remove negative pixels")
        for suffix in ["band5.tif", "band4.tif", "band3.tif"]:
            filename = config.SCENE + "_sr_" + suffix
            print("Processing image " + filename)
            img.clamp_image(
                path.join(config.DATA_PATH, config.SCENE, filename),
                path.join(config.SCRATCH_PATH, suffix),
                config
            )

    if(config.ASSEMBLE_IMAGE):
        img.assemble_image(
            path.join(config.SCRATCH_PATH, "band5.tif"),
            path.join(config.SCRATCH_PATH, "band4.tif"),
            path.join(config.SCRATCH_PATH, "band3.tif"),
            config)
    else:
        print("Skipping scene generation")

    if(config.SLICE_IMAGE):
        print("Generating scene tiles of "+str(config.GRID_SIZE)+"x"+str(config.GRID_SIZE)+" pixels")
        img.prepare_tiles(config)
    else:
        print("Skipping scene tile generation")

    if(config.GENERATE_MASK_TILES):
        generate_mask_tiles()
    else:
        print("Skipping mask generation")

    if(config.REJECT_TILES or config.VISUALIZE_SORT):

        retained_tiles = get_files_by_extension(path.join(config.SCRATCH_PATH, "land"), "png")

        if(config.REMOVE_LAND):
            retained_tiles = apply_rules(
                retained_tiles, no_water, "land", [
                    lambda imin, imax, imean, idev: float(imax) > config.LAND_THRESHHOLD ,
                    lambda imin, imax, imean, idev: float(imean) > config.LAND_THRESHHOLD or float(idev) > config.LAND_SENSITIVITY ,
                ])
        else:
            print("Skipping land removal")

        if(config.REMOVE_CLOUDS):
            retained_tiles = apply_rules(
                retained_tiles, too_cloudy, "cloud", [
                    lambda imin, imax, imean, idev: float(imin) < config.CLOUD_THRESHHOLD ,
                    lambda imin, imax, imean, idev: float(imean) < config.CLOUD_THRESHHOLD or float(idev) > config.CLOUD_SENSITIVITY
                ])
        else:
            print("Skipping cloud removal")

    if(config.VISUALIZE_SORT):

        print(str(len(retained_tiles))+" tiles retained")
        print(str(len(no_water))+" tiles without water rejected")
        print(str(len(too_cloudy))+" tiles rejected for clouds")

        print("Generating tile visualization (output.png)")
        land = img.generate_rectangles(no_water, config.width, config.GRID_SIZE)
        clouds = img.generate_rectangles(too_cloudy, config.width, config.GRID_SIZE)
        water = img.generate_rectangles(retained_tiles, config.width, config.GRID_SIZE)
        img.draw_visualization(land, clouds, water, config.INPUT_FILE)

    if(config.REJECT_TILES):

        rejects = []
        accepts = []

        print("Building scene tile output directory")
        build_output(config.SCENE)

        print("Copying accepted tiles")
        for filename in retained_tiles:
            accept_tile(filename, config.SCRATCH_PATH, config.SCENE)
            accepts.append(build_dict_for_csv(filename, "Accepted", config))

        print("Copying rejected tiles")
        for filename in no_water:
            reject_tile(filename, config.SCRATCH_PATH, config.SCENE)
            rejects.append(build_dict_for_csv(filename, "No Water", config))

        for filename in too_cloudy:
            reject_tile(filename, config.SCRATCH_PATH, config.SCENE)
            rejects.append(build_dict_for_csv(filename, "Too Cloudy", config))

        print("Writing csv file")
        rejects = sorted(rejects, key=lambda k: k['filename'])
        write_rejects(path.join("{0}_tiles".format(config.SCENE), "rejected.csv"), rejects)

    if(config.BUILD_MANIFEST):
        write_manifest(path.join("{0}_tiles".format(config.SCENE),"accepted","manifest.csv"), accepts)

    print("Done")

if __name__ == "__main__":
    main()
