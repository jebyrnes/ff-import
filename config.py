from os import path

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
