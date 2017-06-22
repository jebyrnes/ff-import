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

def draw_visualization(land, clouds, water, input_file):
    args = \
        ["convert", "-quiet", input_file, "-strokewidth", "0"] \
        + ["-fill", "rgba(0,255,0,0.5)"] \
        + land \
        + ["-fill", "rgba(255,255,255,0.5)"] \
        + clouds \
        + ["-fill", "rgba(0,0,255,0.5)"] \
        + water \
        + ["-alpha", "remove"] \
        + ["-resize", "1000x1000", "output.png"]

    call(args)

def clamp_image(source, dest, config):
    logger = logging.getLogger(config.SCENE_NAME)
    plm_args = [
        "./plm",
        "0,0,50,100,50,0,100,0",
        source,
        path.join(config.SCRATCH_PATH, "clamp.tif")
    ]

    logger.info("Flattening negative values to zero")
    call(plm_args)

    logger.info("Adjusting brightness")
    convert_args = [
        "convert",
        path.join(config.SCRATCH_PATH, "clamp.tif"),
        "-depth",
        "8",
        "-contrast-stretch",
        "1x1%",
        "-alpha",
        "remove",
        dest
    ]

    call(convert_args)

def assemble_image(red, green, blue, config):
    logger = logging.getLogger(config.SCENE_NAME)
    boost_args = [
        "./plm",
        "0,0,8,8,8,14,13,23,13,13,100,100",
        green,
        path.join(config.SCRATCH_PATH, "boost.tif")
    ]

    logger.info("Generating boosted green channel")
    call(boost_args)

    adjust_args = [
        "convert",
        "-quiet",
        config.WATER_MASK,
        "-blur",
        config.MASK_BLUR,
        config.WATER_MASK,
        "-compose",
        "darken",
        "-composite",
        path.join(config.SCRATCH_PATH, "boost.tif"),
        "-compose",
        "darken",
        "-composite",
        green,
        "-compose",
        "lighten",
        "-composite",
        path.join(config.SCRATCH_PATH, "adjust.tif")
    ]

    logger.info("Adjusting boosted green channel")
    call(adjust_args)


    assemble_args = [
        "convert",
        "-quiet",
        red,
        path.join(config.SCRATCH_PATH, "adjust.tif"),
        # green,
        blue,
        "-set",
        "colorspace",
        "RGB",
        "-combine",
        path.join(config.SCRATCH_PATH, "render.tif")
    ]

    logger.info("Compositing red, green, and blue images")
    call(assemble_args)

def prepare_tiles(config):
    call([
        "convert",
        "-quiet",
        path.join(config.SCRATCH_PATH, "render.tif"),
        "-crop",
        str(config.GRID_SIZE)+"x"+str(config.GRID_SIZE),
        path.join(config.SCRATCH_PATH, "scene", "tile_%04d.png")
    ])
