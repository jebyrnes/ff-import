def usage():
    print("""
simple.py (Simple Image Pipeline)

This script is used to process satellite imagery from LANDSAT 4, 5, 7, and 8
into subjects for Floating Forests. This includes sorting out tiles that only
contain land or contain too many clouds, as well as compositing the different
bands together into an RGB image and boosting certain parts of the green
channel to aid in kelp-spotting.

    --clean                 Recreate scratch directory

    --assemble              Perform color adjustment and build color output
    --generate-tiles        Build color tiles of scene

    --generate-mask         Regenerate mask tiles
    --remove-land           Reject tiles that are only land
    --remove-clouds         Reject tiles that are too cloudy
    --reject                Sort tiles into accepted and directed folders
    --visualize             Show which tiles would be rejected

    --grid-size=XXX         Set custom tile size

    --source-dir=MY_PATH    Load scenes from a specified directory

    --land-threshhold=XX    Configure land detection
    --land-sensitivity=XX

    --cloud-threshhold=XX   Configure cloud detection
    --cloud-sensitivity=XX
    """)

from os import path
from sys import argv

import image_operations as img
from file_operations import build_scratch, get_files_by_extension
from config import config

GENERATE_MASK_TILES = False
REJECT_TILES = False
VISUALIZE_SORT = False
REMOVE_LAND = False
REMOVE_CLOUDS = False
ASSEMBLE_IMAGE = False
SLICE_IMAGE = False

# CALI_SR = "LT50420362011199PAC01"
# TASM_SR = "LT50900902005246ASA01"

retained_tiles = []
no_water = []
too_cloudy = []

def generate_mask_tiles():
    print("Generating mask tiles of "+str(config.GRID_SIZE)+"x"+str(config.GRID_SIZE)+" pixels")

    print("Generating land mask tiles")
    img.prepare_land_mask(LAND_MASK, CLOUD_MASK, SNOW_MASK, config)

    print("Generating cloud mask tiles")
    img.prepare_cloud_mask(CLOUD_MASK, config)

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

def parse_options():
    global GENERATE_MASK_TILES, VISUALIZE_SORT, REJECT_TILES, REMOVE_LAND, REMOVE_CLOUDS, ASSEMBLE_IMAGE, SLICE_IMAGE
    global SCENE, LAND_MASK, CLOUD_MASK, SNOW_MASK, INPUT_FILE
    rebuild = False

    for arg in argv:
        if(arg=="--help" or arg=="-?"):
            # do nothing, we'll fall through to usage
            noop = 0

        elif(arg=="--assemble"):
            ASSEMBLE_IMAGE = True
        elif(arg=="--generate-tiles"):
            ASSEMBLE_IMAGE = True
            SLICE_IMAGE = True

        elif(arg=="--clean"):
            rebuild = True

        elif(arg=="--generate-mask"):
            GENERATE_MASK_TILES = True
        elif(arg=="--remove-land"):
            REMOVE_LAND = True
        elif(arg=="--remove-clouds"):
            REMOVE_CLOUDS = True
        elif(arg=="--visualize"):
            VISUALIZE_SORT = True
        elif(arg=="--reject"):
            REJECT_TILES = True

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
            SCENE = arg

    if(rebuild):
        build_scratch(config.SCRATCH_PATH)

    LAND_MASK = path.join(config.DATA_PATH,SCENE,SCENE+"_sr_land_water_qa.tif")
    CLOUD_MASK = path.join(config.DATA_PATH,SCENE,SCENE+"_sr_cloud_qa.tif")
    SNOW_MASK = path.join(config.DATA_PATH,SCENE,SCENE+"_sr_snow_qa.tif")
    INPUT_FILE = LAND_MASK

def main():
    global retained_tiles, no_water, too_cloudy

    parse_options()

    if(not GENERATE_MASK_TILES and not REJECT_TILES and not VISUALIZE_SORT and not ASSEMBLE_IMAGE and not SLICE_IMAGE):
        usage()
        return

    print("Processing scene " + SCENE)

    if(ASSEMBLE_IMAGE):
        img.assemble_image(
            #TODO: all of these filenames are wrong :(
            path.join(config.DATA_PATH, SCENE, "rendered_5.tif"),
            path.join(config.DATA_PATH, SCENE, "rendered_4.tif"),
            path.join(config.DATA_PATH, SCENE, "rendered_3.tif"),
            config,
            LAND_MASK)
    else:
        print("Skipping scene generation")

    if(SLICE_IMAGE):
        print("Generating rendered tiles")
        img.prepare_tiles(config)

    if(GENERATE_MASK_TILES):
        print("Generating tiles")
        generate_mask_tiles()
    else:
        print("Skipping mask tile generation")

    if(REJECT_TILES or VISUALIZE_SORT):

        retained_tiles = get_files_by_extension(path.join(config.SCRATCH_PATH, "land"), "png")

        if(REMOVE_LAND):
            retained_tiles = apply_rules(
                retained_tiles, no_water, "land", [
                    lambda imin, imax, imean, idev: float(imax) > config.LAND_THRESHHOLD ,
                    lambda imin, imax, imean, idev: float(imean) > config.LAND_THRESHHOLD or float(idev) > config.LAND_SENSITIVITY ,
                ])
        else:
            print("Skipping land removal")

        if(REMOVE_CLOUDS):
            retained_tiles = apply_rules(
                retained_tiles, too_cloudy, "cloud", [
                    lambda imin, imax, imean, idev: float(imin) < config.CLOUD_THRESHHOLD ,
                    lambda imin, imax, imean, idev: float(imean) < config.CLOUD_THRESHHOLD or float(idev) > config.CLOUD_SENSITIVITY
                ])
        else:
            print("Skipping cloud removal")

    if(VISUALIZE_SORT):

        print(str(len(retained_tiles))+" tiles retained")
        print(str(len(no_water))+" tiles without water rejected")
        print(str(len(too_cloudy))+" tiles rejected for clouds")

        print("Generating tile visualization")

        width = img.get_width(INPUT_FILE)

        land = img.generate_rectangles(no_water, width, config.GRID_SIZE)
        clouds = img.generate_rectangles(too_cloudy, width, config.GRID_SIZE)
        water = img.generate_rectangles(retained_tiles, width, config.GRID_SIZE)

        img.draw_visualization(land, clouds, water, INPUT_FILE)

if __name__ == "__main__":
    main()
