import logging
from os import path
from subprocess import check_output, call

def get_dimensions(a_file):
    result = check_output([
        "convert",
        "-quiet",
        a_file,
        "-ping",
        "-format",
        '%[fx:w] %[fx:h]',
        "info:"
    ]).split(' ')

    return [int(result[0]), int(result[1])]

def get_height(a_file):
    return int(check_output([
        "convert",
        "-quiet",
        a_file,
        "-ping",
        "-format",
        '%[fx:h]',
        "info:"
    ]))

def get_width(a_file):
    return int(check_output([
        "convert",
        "-quiet",
        a_file,
        "-ping",
        "-format",
        '%[fx:w]',
        "info:"
    ]))

def generate_rectangles(tiles, width, grid_size):
    rects = []
    per_row = width // grid_size + 1

    for elem in tiles:
        idx = int(elem.split("_")[1].split(".")[0])
        row = idx // per_row
        col = idx % per_row

        rects.append("-draw")
        rects.append("rectangle " +
                     str(grid_size*col) + "," +
                     str(grid_size*row)  + "  " +
                     str(grid_size*(col+1)) + "," +
                     str(grid_size*(row+1)))

    return rects

def build_mask_files(config, which_lut, which_mask):
    call([
        "convert",
        "-quiet",
        "-type",
        "GrayScale",
        "-clut",
        config.NEW_MASK,
        which_lut,
        "-clamp",
        which_mask
    ])
    return

def prepare_land_mask(config):
    call([
        "convert",
        "-quiet",
        "-type",
        "GrayScale",
        config.WATER_MASK,
        config.CLOUD_MASK,
        "-compose",
        "add",
        "-composite",
        config.SNOW_MASK,
        "-compose",
        "minus_src",
        "-composite",
        "-blur",
        config.MASK_BLUR,
        "-crop",
        str(config.GRID_SIZE)+"x"+str(config.GRID_SIZE),
        path.join(config.SCRATCH_PATH, "land", "tile_%04d.png")
    ])

def prepare_cloud_mask(config):
    call([
        "convert",
        "-quiet",
        "-type",
        "GrayScale",
        config.CLOUD_MASK,
        "-blur",
        config.MASK_BLUR,
        "-crop",
        str(config.GRID_SIZE)+"x"+str(config.GRID_SIZE),
        path.join(config.SCRATCH_PATH, "cloud", "tile_%04d.png")
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

def draw_visualization(land, clouds, water, config):
    args = \
        ["convert", "-quiet", config.INPUT_FILE, "-strokewidth", "0"] \
        + ["-fill", "rgba(0,255,0,0.5)"] \
        + land \
        + ["-fill", "rgba(255,255,255,0.5)"] \
        + clouds \
        + ["-fill", "rgba(0,0,255,0.5)"] \
        + water \
        + ["-alpha", "remove"] \
        + ["-resize", "1000x1000", config.SCENE_NAME + "_tiles/output.png"]

    call(args)

def clamp_image(source, dest, config):
    logger = logging.getLogger(config.SCENE_NAME)

    band = dest.split("/")[1]
    lut = "clamp_lut_linear.pgm" if band != config.SATELLITE['blue'] else "clamp_lut_nonlinear.pgm"

    logger.info("Flattening negative values to zero")
    new_args = [
        "convert",
        "-quiet",
        "-type",
        "GrayScale",
        "-clut",
        source,
        lut,
        "-depth",
        "8",
        "-clamp",
        path.join(config.SCRATCH_PATH, "snow_mask.png"),
        "-compose",
        "lighten",
        "-composite",
        path.join(config.SCRATCH_PATH, "cloud_mask.png"),
        "-compose",
        "lighten",
        "-composite",
        dest + '.png'
    ]
    call(new_args)

def assemble_image(red, green, blue, config):
    logger = logging.getLogger(config.SCENE_NAME)

    logger.info("Generating simplified land/water masks")

    water_mask_args = [
        "convert",
        "-quiet",
        "-type",
        "GrayScale",
        config.WATER_MASK,
        "-blur",
        "5x2",
        "-white-threshold",
        "254",
        "-blur",
        "20x2",
        "-threshold",
        "254",
        path.join(config.SCRATCH_PATH, "water.png")
    ]

    land_mask_args = [
        "convert",
        "-quiet",
        "-type",
        "GrayScale",
        path.join(config.SCRATCH_PATH, "water.png"),
        "-negate",
        path.join(config.SCRATCH_PATH, "land.png")
    ]
    call(water_mask_args)
    call(land_mask_args)

    boost_args = [
        "./plm",
        "0,0,10,0,11,21,60,70,66,66,100,100",
        green,
        path.join(config.SCRATCH_PATH, "boost.png")
    ]

    logger.info("Generating boosted green channel")
    call(boost_args)

    mask_boost_args = [
        "convert",
        "-quiet",
        "-type",
        "GrayScale",
        path.join(config.SCRATCH_PATH, "boost.png"),
        path.join(config.SCRATCH_PATH, "water.png"),
        "-compose",
        "darken",
        "-composite",
        path.join(config.SCRATCH_PATH, "masked.png")
    ]
    logger.info("Masking boosted green channel")
    call(mask_boost_args)

    build_green_args = [
        "convert",
        "-quiet",
        "-type",
        "GrayScale",
        green,
        path.join(config.SCRATCH_PATH, "land.png"),
        "-compose",
        "darken",
        "-composite",
        path.join(config.SCRATCH_PATH, "masked.png"),
        "-compose",
        "add",
        "-composite",
        path.join(config.SCRATCH_PATH, "green_final.png")
    ]
    logger.info("Building final green channel")
    call(build_green_args)

    assemble_args = [
        "convert",
        "-quiet",
        red,
        path.join(config.SCRATCH_PATH, "green_final.png"),
        blue,
        "-set",
        "colorspace",
        "sRGB",
        "-depth",
        "8",
        "-combine",
        path.join(config.SCRATCH_PATH, "render.png")
    ]

    logger.info("Compositing red, green, and blue images")
    call(assemble_args)

def prepare_tiles(config):
    call([
        "convert",
        "-quiet",
        path.join(config.SCRATCH_PATH, "render.png"),
        "-crop",
        str(config.GRID_SIZE)+"x"+str(config.GRID_SIZE),
        path.join(config.SCRATCH_PATH, "scene", "tile_%04d.png")
    ])
