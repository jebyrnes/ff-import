from os import path
from subprocess import check_output, call
from wand.image import Image
from wand_extensions import StatisticsImage

def get_width(file):
    with Image(filename=file) as img:
        return img.width

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
    with Image(filename=image) as img:
        return StatisticsImage(img).my_statistics()

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
        "0,0,50,50,50,0,100,0",
        source,
        path.join(config.SCRATCH_PATH, "clamp.tif")
    ]

    print("Flattening negative values to zero")
    call(plm_args)

    print("Adjusting brightness")
    convert_args = [
        "convert",
        path.join(config.SCRATCH_PATH, "clamp.tif"),
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
        "0,0,4,0,5,24,13,28,14,14,100,100",
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
