from os import path
from subprocess import check_output, call

def get_width(file):
    return int(check_output([
        "convert",
        "-quiet",
        file,
        "-ping",
        "-format",
        '"%[fx:w]"',
        "info:"
    ]).strip('""'))

def generate_rectangles(tiles, width, grid_size):
    rects = []
    per_row = width // grid_size + 1

    for elem in tiles:
        idx = int(elem.split("_")[1].split(".")[0])
        row = idx // per_row
        col = idx % per_row

        rects.append("-draw")
        rects.append("rectangle " + str(grid_size*col) + "," + str(grid_size*row)  + "  " + str(grid_size*(col+1)) + "," + str(grid_size*(row+1)))

    return rects

def prepare_land_mask(land, cloud, snow, config):
    call([
        "convert",
        "-quiet",
        land,
        cloud,
        "-compose",
        "add",
        "-composite",
        snow,
        "-compose",
        "minus_src",
        "-composite",
        "-blur",
        config.MASK_BLUR,
        "-crop",
        str(config.GRID_SIZE)+"x"+str(config.GRID_SIZE),
        path.join(config.SCRATCH_PATH,"land","tile_%04d.png")
    ])

def prepare_cloud_mask(cloud, config):
    call([
        "convert",
        "-quiet",
        cloud,
        "-blur",
        config.MASK_BLUR,
        "-crop",
        str(config.GRID_SIZE)+"x"+str(config.GRID_SIZE),
        path.join(config.SCRATCH_PATH,"cloud","tile_%04d.png")
    ])

def get_image_statistics(image):
    return check_output([
        "convert",
        "-quiet",
        image,
        "-format",
        "\"%[fx:100*minima] %[fx:100*maxima] %[fx:100*mean] %[fx:100*standard_deviation]\"",
        "info:"
    ]).strip('"').split(" ")

def draw_visualization(land, clouds, water, input):
    args = \
        ["convert", "-quiet", input, "-strokewidth", "0"] \
        + ["-fill", "rgba(0,255,0,0.5)"] \
        + land \
        + ["-fill", "rgba(255,255,255,0.5)"] \
        + clouds \
        + ["-fill", "rgba(0,0,255,0.5)"] \
        + water \
        + ["-alpha", "remove"] \
        + ["-resize", "1000x1000", "output.png"]

    call(args)
