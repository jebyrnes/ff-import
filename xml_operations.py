from lxml import etree
from os import path

def get_field_text(tree, path):
    nsmap = { "espa": tree.getroot().nsmap[None] }
    node = tree.xpath(path, namespaces=nsmap)
    if len(node) > 0:
        return node[0].text
    else:
        return ''

def parse_metadata(scene, xml_filename):
    print("Parsing XML metadata from {0}".format(xml_filename))

    result = { '!scene': scene }

    tree = etree.parse(xml_filename)
    nsmap = { "espa": tree.getroot().nsmap[None] }

    result['acquired_date'] = get_field_text(tree, "espa:global_metadata/espa:acquisition_date")
    result['acquired_time'] = get_field_text(tree, "espa:global_metadata/espa:scene_center_time")
    result['sensor_id'] = get_field_text(tree, "espa:global_metadata/espa:instrument")
    result['spacecraft'] = get_field_text(tree, 'espa:global_metadata/espa:satellite')

    esd = tree.xpath("espa:global_metadata/espa:earth_sun_distance", namespaces=nsmap)
    if len(esd) > 0:
        result['!earth_sun_distance'] = esd[0].text
    result['!sun_azimuth'] = tree.xpath("espa:global_metadata/espa:solar_angles", namespaces=nsmap)[0].get("azimuth")
    result['!sun_zenith'] = tree.xpath("espa:global_metadata/espa:solar_angles", namespaces=nsmap)[0].get("zenith")
    covers = tree.xpath("espa:bands/espa:band[@name='cfmask']/espa:percent_coverage/espa:cover", namespaces=nsmap)
    for cover in covers:
        if cover.get("type") == "cloud":
            result['!cloud_cover'] = cover.text
        if cover.get("type") == "water":
            result['!water_cover'] = cover.text

    result['#utm_zone'] = tree.xpath(
        "espa:global_metadata/espa:projection_information/espa:utm_proj_params/espa:zone_code",
        namespaces=nsmap
    )[0].text

    corners=tree.xpath("espa:global_metadata/espa:projection_information/espa:corner_point", namespaces=nsmap)
    for corner in corners:
        result["#scene_corner_{0}_x".format(corner.get("location"))] = corner.get("x")
        result["#scene_corner_{0}_y".format(corner.get("location"))] = corner.get("y")


    return result
