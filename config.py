config = type('Config', (object,), {
    'GRID_SIZE': 400,
    'MASK_BLUR': "0x10",
    'SCRATCH_PATH': "scratch",
    'DATA_PATH': "temp",
    'LAND_THRESHHOLD': 10,
    'LAND_SENSITIVITY': 30,
    'CLOUD_THRESHHOLD': 10,
    'CLOUD_SENSITIVITY': 80,

    'SCENE': '',
    'GENERATE_MASK_TILES': False,
    'REJECT_TILES': False,
    'VISUALIZE_SORT': False,
    'REMOVE_LAND': False,
    'REMOVE_CLOUDS': False,
    'ASSEMBLE_IMAGE': False,
    'SLICE_IMAGE': False,
    'REBUILD': False
})()
