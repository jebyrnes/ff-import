def usage():
    print("""
simple.py (Simple Image Pipeline)

python simple.py [--option] SCENE

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
    --remove-all            Reject tiles that are only land or too cloudy
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

# NOTE:
# CALI_SR = "LT50420362011199PAC01"
# TASM_SR = "LT50900902005246ASA01"

def parse_options():
    rebuild = False

    for arg in argv:
        if(arg=="simple.py"):
            continue

        if(arg=="--help" or arg=="-?"):
            # do nothing, we'll fall through to usage
            noop = 0

        elif(arg=="--assemble"):
            config.ASSEMBLE_IMAGE = True
        elif(arg=="--generate-tiles"):
            config.ASSEMBLE_IMAGE = True
            config.SLICE_IMAGE = True

        elif(arg=="--clean"):
            config.REBUILD = True

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
        not config.REBUILD):
        usage()
        return

    if(
        (config.GENERATE_MASK_TILES or
        config.REJECT_TILES or
        config.VISUALIZE_SORT or
        config.ASSEMBLE_IMAGE or
        config.SLICE_IMAGE) and
        config.SCENE == ''):
        usage()
        return

    if(config.REBUILD):
        build_scratch(config.SCRATCH_PATH)

    print("Processing scene " + config.SCENE)

    if(config.ASSEMBLE_IMAGE):
        img.assemble_image(
            #TODO: all of these filenames are wrong :(
            path.join(config.DATA_PATH, config.SCENE, "rendered_5.tif"),
            path.join(config.DATA_PATH, config.SCENE, "rendered_4.tif"),
            path.join(config.DATA_PATH, config.SCENE, "rendered_3.tif"),
            config)
    else:
        print("Skipping scene generation")

    if(config.SLICE_IMAGE):
        print("Generating scene tiles of "+str(config.GRID_SIZE)+"x"+str(config.GRID_SIZE)+" pixels")
        img.prepare_tiles(config)

    if(config.GENERATE_MASK_TILES):
        generate_mask_tiles()

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

        width = img.get_width(config.INPUT_FILE)

        land = img.generate_rectangles(no_water, width, config.GRID_SIZE)
        clouds = img.generate_rectangles(too_cloudy, width, config.GRID_SIZE)
        water = img.generate_rectangles(retained_tiles, width, config.GRID_SIZE)

        img.draw_visualization(land, clouds, water, config.INPUT_FILE)

if __name__ == "__main__":
    main()
