from os import listdir, path, mkdir
from shutil import rmtree
from sys import argv
from subprocess import check_output, call

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

retained_tiles = []
no_water = []
too_cloudy = []

def compute_width(input_file):
    return int(check_output([
        "convert",
        "-quiet",
        input_file,
        "-ping",
        "-format",
        '"%[fx:w]"',
        "info:"
    ]).strip('""'))

def generate_rectangles(tiles, width):
    rects = []
    per_row = width // GRID_SIZE + 1

    for elem in tiles:
        idx = int(elem.split("_")[1].split(".")[0])
        row = idx // per_row
        col = idx % per_row

        rects.append("-draw")
        rects.append("rectangle " + str(GRID_SIZE*col) + "," + str(GRID_SIZE*row)  + "  " + str(GRID_SIZE*(col+1)) + "," + str(GRID_SIZE*(row+1)))

    return rects

def usage():
    print("USAGE")
    print("To regenerate mask tiles, use --generate-mask")
    print("To show which tiles would be rejected, use --visualize")
    print("To sort tiles into reject and accept, use --reject")

def build_scratch(scratch_path):
    if(path.exists(scratch_path)):
        print("Removing existing tiles")
        rmtree(scratch_path)
        
    mkdir(scratch_path)
    mkdir(path.join(scratch_path,"land"))
    mkdir(path.join(scratch_path,"cloud"))

for arg in argv:
    if(arg=="--generate-mask"):
        GENERATE_MASK_TILES = True
    if(arg=="--visualize"):
        VISUALIZE_SORT = True
    if(arg=="--reject"):
        REJECT_TILES = True

if(not GENERATE_MASK_TILES and not REJECT_TILES and not VISUALIZE_SORT):
    usage()

print("Processing scene " + SCENE)

if(GENERATE_MASK_TILES):

    print("Generating tiles")

    build_scratch(SCRATCH_PATH)

    print("Generating mask tiles of "+str(GRID_SIZE)+"x"+str(GRID_SIZE)+" pixels")

    print("Generating land mask tiles")
    call([
        "convert",
        "-quiet",
        LAND_MASK,
        CLOUD_MASK,
        "-compose",
        "add",
        "-composite",
        SNOW_MASK,
        "-compose",
        "minus_src",
        "-composite",
        "-blur",
        MASK_BLUR,
        "-crop",
        str(GRID_SIZE)+"x"+str(GRID_SIZE),
        path.join(SCRATCH_PATH,"land","tile_%04d.png")
    ])

    print("Generating cloud mask tiles")
    call([
        "convert",
        "-quiet",
        CLOUD_MASK,
        "-blur",
        MASK_BLUR,
        "-crop",
        str(GRID_SIZE)+"x"+str(GRID_SIZE),
        path.join(SCRATCH_PATH,"cloud","tile_%04d.png")
    ])

    generated_count = len(listdir(path.join(SCRATCH_PATH,"land")))
    print("Generated " + str(generated_count) + " tiles")
else:
    print("Skipping mask tile generation")

if(REJECT_TILES or VISUALIZE_SORT):
    files = listdir(path.join(SCRATCH_PATH,"land"))

    for filename in files:
        if filename.endswith("png"):
            retained_tiles.append(filename)

    count_files = len(retained_tiles)
    print("Examining " + str(count_files) + " tiles for water")

    accum = []

    for filename in retained_tiles:
        [minima, maxima, mean, stdev] = check_output([
            "convert",
            "-quiet",
            path.join(SCRATCH_PATH,"land",filename),
            "-format",
            "\"%[fx:100*minima] %[fx:100*maxima] %[fx:100*mean] %[fx:100*standard_deviation]\"",
            "info:"
        ]).strip('"').split(" ")

        if(float(maxima) < 10):
            no_water.append(filename)
            continue

        if(float(mean) < 10 and float(stdev) < 30):
            no_water.append(filename)
            continue

        accum.append(filename)

    retained_tiles = accum
    print("Found " + str(len(retained_tiles)) + " tiles with water or clouds to be retained (" + str(count_files-len(retained_tiles)) + " tiles rejected)")

    accum = []
    count_files = len(retained_tiles)
    print("Examining " + str(count_files) + " tiles for clouds")

    for filename in retained_tiles:
        [minima, maxima, mean, stdev] = check_output([
            "convert",
            "-quiet",
            path.join(SCRATCH_PATH,"cloud",filename),
            "-format",
            "\"%[fx:100*minima] %[fx:100*maxima] %[fx:100*mean] %[fx:100*standard_deviation]\"",
            "info:"
        ]).strip('"').split(" ")

        if(float(minima) > 10):
            too_cloudy.append(filename)
            continue

        if(float(mean) > 5 and float(stdev) < 80):
            too_cloudy.append(filename)
            continue

        accum.append(filename)

    retained_tiles = accum
    print("Found " + str(len(retained_tiles)) + " tiles with few enough clouds to be retained (" + str(count_files-len(retained_tiles)) + " tiles rejected)")

if(VISUALIZE_SORT):
    print("Generating visualization of retained tiles")

    width = compute_width(INPUT_FILE)

    land = generate_rectangles(no_water, width)
    clouds = generate_rectangles(too_cloudy, width)
    water = generate_rectangles(retained_tiles, width)

    args = \
        ["convert", "-quiet", INPUT_FILE, "-strokewidth", "0"] \
        + ["-fill", "rgba(0,255,0,0.5)"] \
        + land \
        + ["-fill", "rgba(255,255,255,0.5)"] \
        + clouds \
        + ["-fill", "rgba(0,0,255,0.5)"] \
        + water \
        + ["-alpha", "remove"] \
        + ["-resize", "1000x1000", "output.png"]

    call(args)
