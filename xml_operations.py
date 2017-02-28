from lxml import etree
from os import path

def parse_metadata(scene, xml_filename):
    print("Parsing XML metadata from {0}".format(xml_filename))

    result = { 'scene': scene }
    tree = etree.parse(xml_filename)
    nsmap = { "espa": tree.getroot().nsmap[None] }

    result['acquired_date'] = tree.xpath("espa:global_metadata/espa:acquisition_date", namespaces=nsmap)[0].text
    result['acquired_time'] = tree.xpath("espa:global_metadata/espa:scene_center_time", namespaces=nsmap)[0].text
    result['sensor_id'] = tree.xpath("espa:global_metadata/espa:instrument", namespaces=nsmap)[0].text
    result['earth_sun_distance'] = tree.xpath("espa:global_metadata/espa:earth_sun_distance", namespaces=nsmap)[0].text
    result['spacecraft'] = tree.xpath("espa:global_metadata/espa:satellite", namespaces=nsmap)[0].text
    result['sun_azimuth'] = tree.xpath("espa:global_metadata/espa:solar_angles", namespaces=nsmap)[0].get("azimuth")
    result['sun_zenith'] = tree.xpath("espa:global_metadata/espa:solar_angles", namespaces=nsmap)[0].get("zenith")
    result['utm_zone'] = tree.xpath(
        "espa:global_metadata/espa:projection_information/espa:utm_proj_params/espa:zone_code",
        namespaces=nsmap
    )[0].text

    corners=tree.xpath("espa:global_metadata/espa:projection_information/espa:corner_point", namespaces=nsmap)
    for corner in corners:
        result["corner_{0}".format(corner.get("location"))] = \
            "{0}, {1}".format( corner.get("x"), corner.get("y") )

    covers = tree.xpath("espa:bands/espa:band[@name='cfmask']/espa:percent_coverage/espa:cover", namespaces=nsmap)
    for cover in covers:
        if cover.get("type") == "cloud":
            result['cloud_cover'] = cover.text
        if cover.get("type") == "water":
            result['water_cover'] = cover.text

    return result
