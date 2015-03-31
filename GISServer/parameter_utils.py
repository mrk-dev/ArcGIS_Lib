"""
 parameter_utils.py
 Created on Mar 31, 2015

 Provides helper functions for ArcToolbox parameters

 @author: mschmidt
"""

import arcpy


def create_feature_set(points, shape_type, spatialref_wkid):
    """
    Creates a feature set from a points.

    :param points: either a coordinate pair as a Python list or a Python list of coordinate pairs
    :param shape_type: either "POINT", "POLYLINE" or "POLYGON"
    :param spatialref_wkid: numeric id of the wkid of the spatial reference
    :return: a feature set object

    Notes: It's assumed that the input points are in the same units/spatial reference as defined
    by the wkid.
    """

    arcpy.env.overwriteOutput = True
    input_spatial_ref = arcpy.SpatialReference(spatialref_wkid)

    feature_class = arcpy.CreateFeatureclass_management("in_memory", "tempfc", shape_type.upper(),
                                                        spatial_reference=input_spatial_ref)

    if shape_type.upper() == "POLYGON":
        feature = arcpy.Polygon(arcpy.Array([arcpy.Point(*coords) for coords in points]))
    elif shape_type.upper == "POLYLINE":
        feature = arcpy.Polyline(arcpy.Array([arcpy.Point(*coords) for coords in points]))
    else:
        pnt = arcpy.Point(points[0], points[1])
        feature = arcpy.PointGeometry(pnt)

    with arcpy.da.InsertCursor(feature_class, ["SHAPE@"]) as cursor:
        cursor.insertRow([feature])

    feature_set = arcpy.FeatureSet()
    feature_set.load(feature_class)

    return feature_set


def create_polygon(point_list):
    # Create a Polygon object based on the array of points


    return feature


def create_line(point_list):