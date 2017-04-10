from pyproj import Proj

def compute_lat_lon(x, y, utm_zone):
    p = Proj(proj='utm',zone=utm_zone,ellps='WGS84')
    lat, lon = p(x,y,inverse=True)
    return [lat, lon]

def compute_tile_coords(row, col, width, height, config):
    scene_top = float(config.METADATA["#scene_corner_UL_y"])
    scene_bottom = float(config.METADATA["#scene_corner_LR_y"])
    scene_left = float(config.METADATA["#scene_corner_UL_x"])
    scene_right = float(config.METADATA["#scene_corner_LR_x"])

    scene_span_x = scene_right - scene_left
    scene_span_y = scene_bottom - scene_top

    left = ((col * config.GRID_SIZE) / config.width) * scene_span_x + scene_left
    top = ((row * config.GRID_SIZE) / config.height) * scene_span_y + scene_top
    right = left + (width / config.width) * scene_span_x
    bottom = top + (height / config.height) * scene_span_y

    return [left, top, right, bottom]
