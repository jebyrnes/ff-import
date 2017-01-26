from os import path
from sys import argv

import image_operations as img
from file_operations import build_scratch, get_files_by_extension
from config import *

GENERATE_MASK_TILES = False
REJECT_TILES = False
VISUALIZE_SORT = False
REMOVE_LAND = False
REMOVE_CLOUDS = False

retained_tiles = []
no_water = []
too_cloudy = []

def usage():
    print("USAGE")
    print("To regenerate mask tiles, use --generate-mask")
    print("To reject tiles that are only land, use --remove-land")
    print("To reject tiles that are too cloudy, use --remove-clouds")
    print("To reject both land and cloud tiles, use --clean")
    print("To sort tiles into reject and accept, use --reject")
    print("To show which tiles would be rejected, use --visualize")

def generate_tiles():
    print("Generating mask tiles of "+str(GRID_SIZE)+"x"+str(GRID_SIZE)+" pixels")

    print("Generating land mask tiles")
    img.prepare_land_mask(LAND_MASK, CLOUD_MASK, SNOW_MASK, MASK_BLUR, GRID_SIZE, SCRATCH_PATH)

    print("Generating cloud mask tiles")
    img.prepare_cloud_mask(CLOUD_MASK, MASK_BLUR, GRID_SIZE, SCRATCH_PATH)

    generated_count = len(get_files_by_extension(path.join(SCRATCH_PATH, "land"), "png"))
    print("Generated " + str(generated_count) + " tiles")

def apply_rules(candidates, rejects, subdirectory, rules):
    accum = []

    print("Examining " + str(len(candidates)) + " tiles for " + subdirectory)
    for filename in candidates:
        done = False
        statistics = img.get_image_statistics(path.join(SCRATCH_PATH, subdirectory, filename))
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
    global GENERATE_MASK_TILES, VISUALIZE_SORT, REJECT_TILES, REMOVE_LAND, REMOVE_CLOUDS
    global SCENE, LAND_MASK, CLOUD_MASK, SNOW_MASK, INPUT_FILE
    for arg in argv:
        if(arg=="--generate-mask"):
            GENERATE_MASK_TILES = True
        elif(arg=="--visualize"):
            VISUALIZE_SORT = True
        elif(arg=="--reject"):
            REJECT_TILES = True
        elif(arg=="--clean"):
            REMOVE_LAND = True
            REMOVE_CLOUDS = True
        elif(arg=="--remove-land"):
            REMOVE_LAND = True
        elif(arg=="--remove-clouds"):
            REMOVE_CLOUDS = True
        else:
            SCENE = arg

    LAND_MASK = path.join(DATA_PATH,SCENE,SCENE+"_sr_land_water_qa.tif")
    CLOUD_MASK = path.join(DATA_PATH,SCENE,SCENE+"_sr_cloud_qa.tif")
    SNOW_MASK = path.join(DATA_PATH,SCENE,SCENE+"_sr_snow_qa.tif")
    INPUT_FILE = LAND_MASK

def main():
    global retained_tiles, no_water, too_cloudy

    parse_options()

    if(not GENERATE_MASK_TILES and not REJECT_TILES and not VISUALIZE_SORT):
        usage()
    else:
        print("Processing scene " + SCENE)

    if(GENERATE_MASK_TILES):
        print("Generating tiles")
        build_scratch(SCRATCH_PATH)
        generate_tiles()
    else:
        print("Skipping mask tile generation")

    if(REJECT_TILES or VISUALIZE_SORT):

        retained_tiles = get_files_by_extension(path.join(SCRATCH_PATH, "land"), "png")

        if(REMOVE_LAND):
            retained_tiles = apply_rules(
                retained_tiles, no_water, "land", [
                    lambda imin, imax, imean, idev: float(imax) > 10 ,
                    lambda imin, imax, imean, idev: float(imean) > 10 or float(idev) > 30 ,
                ])
        else:
            print("Skipping land removal")

        if(REMOVE_CLOUDS):
            retained_tiles = apply_rules(
                retained_tiles, too_cloudy, "cloud", [
                    lambda imin, imax, imean, idev: float(imin) < 10 ,
                    lambda imin, imax, imean, idev: float(imean) < 5 or float(idev) > 80
                ])
        else:
            print("Skipping cloud removal")

    if(VISUALIZE_SORT):

        print(str(len(retained_tiles))+" tiles retained")
        print(str(len(no_water))+" tiles without water rejected")
        print(str(len(too_cloudy))+" tiles rejected for clouds")

        print("Generating tile visualization")

        width = img.get_width(INPUT_FILE)

        land = img.generate_rectangles(no_water, width, GRID_SIZE)
        clouds = img.generate_rectangles(too_cloudy, width, GRID_SIZE)
        water = img.generate_rectangles(retained_tiles, width, GRID_SIZE)

        img.draw_visualization(land, clouds, water, INPUT_FILE)

if __name__ == "__main__":
    main()
