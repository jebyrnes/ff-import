from os import path
from subprocess import check_output, call

def get_dimensions(file):
    with Image(filename=file) as img:
        return [img.width, img.height]

def get_height(file):
    with Image(filename=file) as img:
        return img.height

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

def prepare_land_mask(config):
    call([
        "convert",
        "-quiet",
        config.LAND_MASK,
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
        path.join(config.SCRATCH_PATH,"land","tile_%04d.png")
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

def clamp_image(source, dest, config):
    plm_args = [
        "./plm",
        "0,0,50,100,50,0,100,0",
        source,
        path.join(config.SCRATCH_PATH, "clamp.tif")
    ]

    print("Flattening negative values to zero")
    call(plm_args)

    print("Adjusting brightness")
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
    boost_args = [
        "./plm",
        "0,0,8,8,8,14,13,23,13,13,100,100",
        green,
        path.join(config.SCRATCH_PATH, "boost.tif")
    ]

    print("Generating boosted green channel")
    call(boost_args)

    adjust_args = [
        "convert",
        "-quiet",
        config.LAND_MASK,
        "-blur",
        config.MASK_BLUR,
        config.LAND_MASK,
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

    print("Adjusting boosted green channel")
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
        path.join(config.SCRATCH_PATH,"render.tif")
    ]

    print("Compositing red, green, and blue images")
    call(assemble_args)

def prepare_tiles(config):
    call([
        "convert",
        "-quiet",
        path.join(config.SCRATCH_PATH,"render.tif"),
        "-crop",
        str(config.GRID_SIZE)+"x"+str(config.GRID_SIZE),
        path.join(config.SCRATCH_PATH,"scene","tile_%04d.png")
    ])
