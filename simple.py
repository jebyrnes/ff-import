from os import path
from sys import argv

import image_operations as img
from file_operations import build_scratch, get_files_by_extension

GRID_SIZE = 400
MASK_BLUR = "0x10"

CALI_SR = "LT50420362011199PAC01"
TASM_SR = "LT50900902005246ASA01"

SCENE = TASM_SR

SCRATCH_PATH = "scratch"
DATA_PATH = "temp"

LAND_MASK = path.join(DATA_PATH,SCENE,SCENE+"_sr_land_water_qa.tif")
CLOUD_MASK = path.join(DATA_PATH,SCENE,SCENE+"_sr_cloud_qa.tif")
SNOW_MASK = path.join(DATA_PATH,SCENE,SCENE+"_sr_snow_qa.tif")
INPUT_FILE = LAND_MASK

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

def remove_land(tiles, no_water):
    accum = []

    for filename in tiles:
        [minima, maxima, mean, stdev] = img.get_image_statistics(path.join(SCRATCH_PATH, "land", filename))

        if(float(maxima) < 10):
            no_water.append(filename)
            continue

        if(float(mean) < 10 and float(stdev) < 30):
            no_water.append(filename)
            continue

        accum.append(filename)

    return accum

def remove_clouds(tiles, too_cloudy):
    accum = []

    for filename in retained_tiles:
        [minima, maxima, mean, stdev] = img.get_image_statistics(path.join(SCRATCH_PATH, "cloud", filename))

        if(float(minima) > 10):
            too_cloudy.append(filename)
            continue

        if(float(mean) > 5 and float(stdev) < 80):
            too_cloudy.append(filename)
            continue

        accum.append(filename)

    return accum

def parse_options():
    global GENERATE_MASK_TILES, VISUALIZE_SORT, REJECT_TILES, REMOVE_LAND, REMOVE_CLOUDS
    for arg in argv:
        if(arg=="--generate-mask"):
            GENERATE_MASK_TILES = True
        if(arg=="--visualize"):
            VISUALIZE_SORT = True
        if(arg=="--reject"):
            REJECT_TILES = True
        if(arg=="--clean"):
            REMOVE_LAND = True
            REMOVE_CLOUDS = True
        if(arg=="--remove-land"):
            REMOVE_LAND = True
        if(arg=="--remove-clouds"):
            REMOVE_CLOUDS = True

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
            print("Examining " + str(len(retained_tiles)) + " tiles for water")
            result = remove_land(retained_tiles, no_water)
            print("Found " + str(len(result)) + " tiles with water or clouds to be retained (" + str(len(no_water)) + " tiles rejected)")
            retained_tiles = result
        else:
            print("Skipping land removal")

        if(REMOVE_CLOUDS):
            print("Examining " + str(len(retained_tiles)) + " tiles for clouds")
            result = remove_clouds(retained_tiles, too_cloudy)
            print("Found " + str(len(result)) + " tiles with few enough clouds to be retained (" + str(len(too_cloudy)) + " tiles rejected)")
            retained_tiles = result
        else:
            print("Skipping cloud removal")

    if(VISUALIZE_SORT):

        print("Generating visualization of retained tiles")

        width = img.get_width(INPUT_FILE)

        land = img.generate_rectangles(no_water, width, GRID_SIZE)
        clouds = img.generate_rectangles(too_cloudy, width, GRID_SIZE)
        water = img.generate_rectangles(retained_tiles, width, GRID_SIZE)

        img.draw_visualization(land, clouds, water, INPUT_FILE)

if __name__ == "__main__":
    main()
