config = type('Config', (object,), {
    'GRID_SIZE': 400,
    'MASK_BLUR': "0x10",
    'SCRATCH_PATH': "scratch",
    'DATA_PATH': "temp",
    'LAND_THRESHHOLD': 10,
    'LAND_SENSITIVITY': 30,
    'CLOUD_THRESHHOLD': 10,
    'CLOUD_SENSITIVITY': 80
})()
