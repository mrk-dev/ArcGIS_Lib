"""
 service.py
 Created on Sep 16, 2014

 Encapsulates ArcGIS for Server GIS service properties and methods.

 @author: mschmidt

 SVN revision info:
 @version     $Revision: 219 $
 @updated_by: $Author: mschmidt $
 @date        $Date: 2014-07-24 12:19:40 -0400 (Thu, 24 Jul 2014) $
"""

#TODO: add abiltites to edit properties of a service (may need class specific methods)
#Todo: complete Image Service


import arcpy
import os
import tempfile
import json
import web_service
import collections
import xml.etree.ElementTree as ET
import service_properties

# Default Geocoding Service properties
DEFAULT_MAX_CANDIDATES = 500
DEFAULT_MAX_BATCH_SIZE = 1000
DEFAULT_SUGGESTED_BATCH_SIZE = 1000

# Default Service settings
DEFAULT_MAX_RECORDS = 1000
DEFAULT_MIN_INSTANCES = 1
DEFAULT_MAX_INSTANCES = 2
DEFAULT_MAX_USAGE_TIME = 600
DEFAULT_MAX_WAIT_TIME = 60
DEFAULT_MAX_IDLE_TIME = 1800


class GISService(web_service.WebService):
    """Base class for all ArcGIS Service types."""

    def __init__(self, gis_server, folder_name, service_name, service_type):
        """
        :param gis_server: ArcGIS Server object (see GISServer class)
        :param folder_name: name of folder where service will be published ("" for root)
        :param service_name: name to be given to service
        :param service_type: type of service ("MapService", "GPService", ...)
        """
        self._gis_server = gis_server
        web_service.WebService.__init__(self, self.gis_server.server_name,
                                        self.gis_server.web_site, self.gis_server.web_port)
        self._service_name = service_name
        self._service_type = service_type
        self._folder_name = folder_name
        self._summary = ""
        self._tags = ""
        self._analysis_results = ""

        self._min_instances = DEFAULT_MIN_INSTANCES
        self._max_instances = DEFAULT_MAX_INSTANCES

    @property
    def service_name(self):
        return self._service_name

    @property
    def service_type(self):
        return self._service_type

    @property
    def gis_server(self):
        return self._gis_server

    @property
    def folder_name(self):
        return self._folder_name

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, summary_text):
        self._summary = summary_text

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, tags_list):
        self._tags = tags_list

    @property
    def min_instances(self):
        return self._min_instances

    @min_instances.setter
    def min_instances(self, value):
        value = 1 if value < 1 else value
        value = self.max_instances if value > self.max_instances else value
        self._min_instances = value

    @property
    def max_instances(self):
        return self._max_instances

    @max_instances.setter
    def max_instances(self, value):
        value = 1 if value < 1 else value
        value = self.min_instances if value < self._min_instances else value
        self._max_instances = value

    @property
    def analysis_results(self):
        return self._analysis_results

    def get_defn(self):
        request = "services/{0}.{1}".format(self.service_name, self.service_type)
        data = self.make_request(request, "", self.gis_server._admin_user, self.gis_server._admin_pwd)
        obj = json.loads(data)
        return obj

    def stop(self):
        request = "services/{0}.{1}/stop".format(self.service_name, self.service_type)
        data = self.make_request(request, "", self.gis_server._admin_user, self.gis_server._admin_pwd)
        obj = json.loads(data)
        return obj

    def start(self):
        request = "services/{0}.{1}/start".format(self.service_name, self.service_type)
        data = self.make_request(request, "", self.gis_server._admin_user, self.gis_server._admin_pwd)
        obj = json.loads(data)
        return obj

    def delete(self):
        request = "services/{0}.{1}/delete".format(self.service_name, self.service_type)
        data = self.make_request(request, "", self.gis_server._admin_user, self.gis_server._admin_pwd)
        obj = json.loads(data)
        return obj


class MAPService(GISService):
    """Encapsulates a Map Service"""

    def __init__(self, gis_server, folder_name, service_name, mxd=None):
        """
        :param gis_server: ArcGIS Server object (see GISServer class)
        :param folder_name: name of folder where map service will be published ("" for root)
        :param service_name: name to be given to the service
        :param mxd: full path to mxd file defining map service (optional)
        """
        GISService.__init__(self, gis_server, folder_name, service_name, "MapServer")
        self._mxd = mxd
        self._mobile_enabled = False
        self._mapping = True
        self._query = True
        self._data = True

    @property
    def mxd(self):
        return self._mxd

    @mxd.setter
    def mxd(self, mxd):
        self._mxd = mxd

    @property
    def mobile_enabled(self):
        return self._mobile_enabled

    @mobile_enabled.setter
    def mobile_enabled(self, value):
        self._mobile_enabled = value if type(value) == bool else False

    def set_capabilities(self, mapping, query, data):
        self._mapping = mapping
        self._query = query
        self._data = data

    def publish(self):

        map_doc = arcpy.mapping.MapDocument(self.mxd)
        temp_dir = tempfile.gettempdir()
        sd_draft = os.path.join(temp_dir, self.service_name + ".sddraft")
        sd_final = os.path.join(temp_dir, self.service_name + ".sd")
        ags_con = self.gis_server.create_connection_file()

        # Create draft service - save to location at sd_draft
        arcpy.mapping.CreateMapSDDraft(map_doc,
                                       sd_draft,
                                       self.service_name,
                                       "FROM_CONNECTION_FILE",
                                       ags_con,
                                       folder_name=self.folder_name,
                                       summary=self.summary,
                                       tags=self.tags)

        # Analyze the draft service
        analysis = arcpy.mapping.AnalyzeForSD(sd_draft)

        # Build return string of results
        res_str = ""
        for key in ("messages", "warnings", "errors"):
            res_str += "----{0}----".format(key.upper())
            vals = analysis[key]
            for ((message, code), layerlist) in vals.iteritems():
                res_str += "\n\t{0}\t(CODE {1}".format(message, code)
                res_str += "\n\t\tapplies to:"
                for layer in layerlist:
                    res_str += "\n{0}\t".format(layer.name)
                res_str += "\n"
            res_str += "\n"
        self._analysis_results = res_str

        # Make any modifications to service capabilities as per settings
        service_props = service_properties.ServiceProperties(sd_draft)
        if self.mobile_enabled:
            mobile_ext = service_props.get_extension("MobileServer")
            mobile_ext.set_property("Enabled", "true")

        if not self._mapping and self._query and self._data:
            service_props.set_operations_allowed(self._mapping, self._query, self._data)

        if self.min_instances != DEFAULT_MIN_INSTANCES:
            service_props.min_instances(self.min_instances)

        if self.max_instances != DEFAULT_MAX_INSTANCES:
            service_props.max_instances(self.max_instances)

        sd_draft = service_props.get_new_extensions_definition()

        # Stage and upload the draft file to the server when no errors found
        if not analysis["errors"]:
            try:
                arcpy.StageService_server(sd_draft, sd_final)

                # Upload to the server
                arcpy.UploadServiceDefinition_server(sd_final, ags_con)
            except Exception as ex:
                raise Exception("Unable to publish Map service. {0}".format(ex.message))
        else:
            raise Exception("Error while creating draft Map service. {0}".format(analysis["errors"]))

        # Clean up - Delete ags connection file
        try:
            os.remove(ags_con)
            os.remove(sd_final)
        except Exception as ex:
            print "Unable to clean up. {0}".format(ex.message)

        return res_str


class FeatureService(MAPService):
    """Encapsulates a Feature Service"""

    def publish(self):
        map_doc = arcpy.mapping.MapDocument(self.mxd)
        temp_dir = tempfile.gettempdir()
        sd_draft = os.path.join(temp_dir, self.service_name + ".sddraft")
        sd_final = os.path.join(temp_dir, self.service_name + ".sd")
        ags_con = self.gis_server.create_connection_file()

        # Create draft service - save to location at sd_draft
        arcpy.mapping.CreateMapSDDraft(map_doc,
                                       sd_draft,
                                       self.service_name,
                                       "FROM_CONNECTION_FILE",
                                       ags_con,
                                       folder_name=self.folder_name,
                                       summary=self.summary,
                                       tags=self.tags)

        # Set the Feature Service extension to True
        service_extensions = service_properties.ServiceProperties(sd_draft)
        feature_ext = service_extensions.get_extension("FeatureServer")
        feature_ext.set_property("Enabled", "true")
        sd_draft = service_extensions.get_new_extensions_definition()

        # Analyze the draft service
        analysis = arcpy.mapping.AnalyzeForSD(sd_draft)

        # Build return string of results
        res_str = ""
        for key in ("messages", "warnings", "errors"):
            res_str += "----{0}----".format(key.upper())
            values = analysis[key]
            for ((message, code), layer_list) in values.iteritems():
                res_str += "\n\t{0}\t(CODE {1}".format(message, code)
                res_str += "\n\t\tapplies to:"
                for layer in layer_list:
                    res_str += "\n{0}\t".format(layer.name)
                res_str += "\n"
            res_str += "\n"
            self._analysis_results = res_str

        # Stage and upload the draft file to the server when no errors found
        if not analysis["errors"]:
            try:
                arcpy.StageService_server(sd_draft, sd_final)

                # Upload to the server
                arcpy.UploadServiceDefinition_server(sd_final, ags_con)
            except Exception as ex:
                raise Exception("Unable to publish Feature Service. {0}\n{1}".format(ex.message, res_str))

        # Clean up
        try:
            os.remove(ags_con)
            os.remove(sd_final)
        except Exception as ex:
            print "Unable to clean up. {0}".format(ex.message)


class GeoProcessingService(GISService):
    """Encapsulates a Geoprocessing Service"""

    def __init__(self, gis_server, folder_name, service_name, toolbox_file, tool_name):
        """
        :param gis_server: ArcGIS Server object (see GISServer class)
        :param folder_name: name of folder where service will be published ("" for root)
        :param service_name: name to be give the service (no spaces)
        :param toolbox_file: full path to toolbox where tool to be published resides
        :param tool_name: name of tool in toolbox
        """

        GISService.__init__(self, gis_server, folder_name, service_name, "GPServer")
        self._toolbox = toolbox_file
        self._toolbox_alias = os.path.splitext(os.path.basename(toolbox_file))[0]
        self._tool_name = tool_name
        self._parameters = collections.OrderedDict()
        self._is_asynchronous = True
        self._use_result_layer = False
        self._show_messages = "NONE"
        self._max_records = DEFAULT_MAX_RECORDS
        self._min_instances = DEFAULT_MIN_INSTANCES
        self._max_instances = DEFAULT_MAX_INSTANCES
        self._max_usage_time = DEFAULT_MAX_USAGE_TIME
        self._max_wait_time = DEFAULT_MAX_WAIT_TIME
        self._max_idle_time = DEFAULT_MAX_IDLE_TIME

    @property
    def toolbox_file(self):
        """
        :return: (String) full path to toolbox file
        """
        return self._toolbox

    @property
    def toolbox_alias(self):
        return self._toolbox_alias

    @property
    def tool_name(self):
        return self._tool_name

    @property
    def is_asynchronous(self):
        return self._is_asynchronous

    @is_asynchronous.setter
    def is_asynchronous(self, value):
        # Allowed values True, False
        if value not in [True, False]:
            value = False
        self._is_asynchronous = value

    @property
    def use_result_layer(self):
        return self._use_result_layer

    @use_result_layer.setter
    def use_result_layer(self, value):
        # Allowed values True, False
        if value not in [True, False]:
            value = False
        self._use_result_layer = value

    @property
    def show_messages(self):
        return self._show_messages

    @show_messages.setter
    def show_messages(self, value):
        # Allowed values "NONE", "ERROR", "WARNING", "INFO"
        if value.upper() not in ["NONE", "ERROR", "WARNING", "INFO"]:
            value = "NONE"
        self._show_messages = value.upper()

    def add_parameter(self, name, value):
        self._parameters[name] = value

    def remove_parameter(self, name):
        if name in self._parameters.keys():
            del(self._parameters[name])

    def publish(self):
        # Notes:
        #   1. Currently assumes that all data sources used as parameters
        #      are registered with the server.

        temp_dir = tempfile.gettempdir()
        sd_draft = os.path.join(temp_dir, self.service_name + ".sddraft")
        sd_final = os.path.join(temp_dir, self.service_name + ".sd")
        ags_con = self.gis_server.create_connection_file()

        # Create parameter string
        params = ""
        for key, item in self._parameters.iteritems():
            if isinstance(item, basestring):
                value = "'{0}'".format(item)
            elif isinstance(item, object):
                value = "self._parameters['{0}']".format(key)
            else:
                value = item
            params += "{0}, ".format(value)

        # strip off last comma and space from parameters
        params = params.rstrip(", ")

        # Create execution string
        tool_exe = "arcpy.{0}.{1}({2})".format(self.toolbox_alias, self.tool_name, params)

        # Import toolbox and verify tool exists in it
        module = arcpy.ImportToolbox(self.toolbox_file, self.toolbox_alias)
        if self.tool_name not in module.__all__:
            raise Exception("Tool {0} not found in toolbox {1}".format(self.tool_name, self.toolbox_file))

        # Run the tool and save the result
        execution = "ASYNCHRONOUS" if self.is_asynchronous else "SYNCHRONOUS"
        try:
            result = eval(tool_exe)
        except Exception as e:
            raise Exception("Failed to execute tool. {0}".format(e.message))

        try:
            arcpy.CreateGPSDDraft(result, sd_draft, self.service_name,
                                  "FROM_CONNECTION_FILE", ags_con,
                                  False, self.folder_name,
                                  self.summary, self.tags,
                                  execution,
                                  self.use_result_layer,
                                  self.show_messages,
                                  self._max_records,
                                  self._min_instances,
                                  self._max_instances,
                                  self._max_usage_time,
                                  self._max_wait_time,
                                  self._max_idle_time)
        except Exception as ex:
            raise Exception("Unable to create Geoprocessing service draft. {0}".format(ex.message))

        analysis = arcpy.mapping.AnalyzeForSD(sd_draft)

        if not analysis["errors"]:
            try:
                # Execute Stage Service
                arcpy.StageService_server(sd_draft, sd_final)
                # Execute Upload Service Definition
                arcpy.UploadServiceDefinition_server(sd_final, ags_con)
            except Exception as ex:
                raise Exception("Unable to publish Geoprocessing service. {0}".format(ex.message))
        else:
            raise Exception("Error while creating draft Geoprocessing service. {0}".format(analysis["errors"]))

        # Clean up
        try:
            os.remove(ags_con)
            os.remove(sd_final)
        except Exception as ex:
            print "Unable to clean up. {0}".format(ex.message)


class GeoCoderService(GISService):
    """Encapsulates a Geocoding Service"""

    def __init__(self, gis_server, folder_name, service_name, locator_path=None):
        """
        :param gis_server: ArcGIS Server object (see GISServer class)
        :param folder_name: name of folder where service will be published ("" for root)
        :param service_name: name to be give the service (no spaces)
        :param locator_path: path to locator (file or geodatabase)
        """
        GISService.__init__(self, gis_server, folder_name, service_name, "GeocodeServer")
        self._locator = locator_path
        self._max_candidates = DEFAULT_MAX_CANDIDATES
        self._max_batch_size = DEFAULT_MAX_BATCH_SIZE
        self._suggested_batch_size = DEFAULT_SUGGESTED_BATCH_SIZE
        self._supports_geocode = True
        self._supports_reverse_geocode = True

    @property
    def locator(self):
        return self._locator

    @locator.setter
    def locator(self, value):
        self._locator = value

    @property
    def max_candidates(self):
        return self._max_candidates

    @max_candidates.setter
    def max_candidates(self, value):
        self._max_candidates = DEFAULT_MAX_CANDIDATES
        if str(value).isnumeric():
            if int(value) > 0:
                self._max_candidates = int(value)

    @property
    def max_batch_size(self):
        return self._max_batch_size

    @max_batch_size.setter
    def max_batch_size(self, value):
        self._max_batch_size = DEFAULT_MAX_BATCH_SIZE
        if str(value).isnumeric():
            if int(value) > 0:
                self._max_batch_size = int(value)

    @property
    def suggested_batch_size(self):
        return self._suggested_batch_size

    @suggested_batch_size.setter
    def suggested_batch_size(self, value):
        self._max_batch_size = DEFAULT_MAX_BATCH_SIZE
        if str(value).isnumeric():
            if int(value) > 0:
                self._max_batch_size = int(value)

    @property
    def supports_geocode(self):
        return self._supports_geocode

    @supports_geocode.setter
    def supports_geocode(self, value):
        self._supports_geocode = value if type(value) == bool else False

    @property
    def supports_reverse_geocode(self):
        return self._supports_revese_geocode

    @supports_reverse_geocode.setter
    def supports_geocode(self, value):
        self._supports_reverse_geocode = value if type(value) == bool else False

    def _supported_operations(self):
        supported_ops = []
        if self._supports_geocode:
            supported_ops.append("GEOCODE")
        if self._supports_reverse_geocode:
            supported_ops.append("REVERSE_GEOCODE")

        # Must have at least one supported operation
        if len(supported_ops) == 0:
            supported_ops.append("GEOCODE")

        as_string = str(supported_ops)
        return as_string

    def publish(self):
        temp_dir = tempfile.gettempdir()
        sd_draft = os.path.join(temp_dir, self.service_name + ".sddraft")
        sd_final = os.path.join(temp_dir, self.service_name + ".sd")
        ags_con = self.gis_server.create_connection_file()

        # Create draft service - save to location at sd_draft
        supported_operations = self._supported_operations()
        analysis = arcpy.CreateGeocodeSDDraft(self.locator, sd_draft, self.service_name,
                                              "FROM_CONNECTION_FILE",
                                              ags_con,
                                              folder_name=self.folder_name,
                                              summary=self.summary,
                                              tags=self.tags,
                                              max_result_size=self.max_candidates,
                                              max_batch_size=self.max_batch_size,
                                              suggested_batch_size=self.suggested_batch_size,
                                              supported_operations=supported_operations)

        if not analysis["errors"]:
            try:
                # Stage the Service
                arcpy.StageService_server(sd_draft, sd_final)

                # Upload the Service
                arcpy.UploadServiceDefinition_server(sd_final, ags_con)
            except Exception as e:
                raise Exception("Unable to publish Geocoder service. {0}".format(e.message))
        else:
            raise Exception("Error while creating Geocoder draft service. {0}".format(analysis["errors"]))

        # Clean up
        try:
            os.remove(ags_con)
            os.remove(sd_final)
        except Exception as ex:
            print "Unable to clean up. {0}".format(ex.message)


class ImageService(GISService):
    """Encapsulates an Image Service"""

    def __init__(self, gis_server, folder_name, service_name, raster=None):
        """
        :param gis_server:
        :param folder_name:
        :param service_name:
        """
        GISService.__init__(gis_server, folder_name, service_name, "ImageServer")
        self._raster = raster

    @property
    def raster(self):
        return self._raster

    @raster.setter
    def raster(self, value):
        self._raster = value

    def publish(self):
        temp_dir = tempfile.gettempdir()
        sd_draft = os.path.join(temp_dir, self.service_name + ".sddraft")
        sd_final = os.path.join(temp_dir, self.service_name + ".sd")
        ags_con = self.gis_server.create_connection_file()

        try:
            arcpy.CreateImageSDDraft(self.raster, sd_draft, self.service_name,
                                     "FROM_CONECTION_FILE",
                                     ags_con,
                                     self.folder_name)
        except Exception as ex:
            raise Exception("Unable to create Image service draft. {0}".format(ex.message))

        analysis = arcpy.mapping.AnalyzeForSD(sd_draft)

        if not analysis["errors"]:
            try:
                # Stage the Service
                arcpy.StageService_server(sd_draft, sd_final)

                # Upload the Service
                arcpy.UploadServiceDefinition_server(sd_final, ags_con)
            except Exception as ex:
                raise Exception("Unable to publish Image service. {0}".format(ex.message))
        else:
            raise Exception("Error while creating draft Image service. {0}".format(analysis["errors"]))

        # Clean up
        try:
            os.remove(ags_con)
            os.remove(sd_final)
        except Exception as ex:
            print "Unable to clean up. {0}".format(ex.message)

