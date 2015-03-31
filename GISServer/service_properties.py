"""
 service_extension.py
 Created on Sep 30, 2014

 Encapsulates ArcGIS for Server GIS service Extension properties and methods.

 @author: mschmidt

 SVN revision info:
 @version     $Revision: 219 $
 @updated_by: $Author: mschmidt $
 @date        $Date: 2014-07-24 12:19:40 -0400 (Thu, 24 Jul 2014) $
"""

import os
import json
import xml.etree.ElementTree as ET


class ServiceProperties(object):

    XML_ROOT = "Configurations/SVCConfiguration/Definition"

    def __init__(self, service_def):
        """
        :param service_def: Object that defines the service (json or sd draft file)
        """

        # Determine if service_def is coming from an sd draft file (XML)
        # or from ArcGIS for Server definition (JSON)
        if os.path.exists(service_def):
            tree = ET.parse(service_def)
            self._source = service_def
            self._raw_definition = tree
            self._definition_type = "XML"
        else:
            root = json.loads(service_def)
            self._source = service_def
            self._raw_definition = root
            self._definition_type = "JSON"

    def get_extension(self, extension_type):

        extension_def = None
        service_extension = None
        if self._definition_type == "XML":
            root = self._raw_definition.getroot()
            svc_exts = root.findall(self.XML_ROOT + "/Extensions/SVCExtension")
            for svc_ext in svc_exts:
                tn = svc_ext.find("TypeName")
                if tn.text.upper() == extension_type.upper():
                    extension_def = svc_ext
                    break
        else:
            svc_exts = self._raw_definition["extensions"]
            for svc_ext in svc_exts:
                tn = svc_ext["typeName"]
                if tn.upper() == extension_type.upper():
                    extension_def = svc_ext
                    break

        if extension_def is not None:
            service_extension = ServiceExtension(extension_def, self._definition_type)

        return service_extension

    def get_configuration_properties(self):

        if self._definition_type == "XML":
            root = self._raw_definition.getroot()
            property_def = root.find(self.XML_ROOT + "/ConfigurationProperties/PropertyArray")
        else:
            property_def = self._raw_definition

        config_properties = ServiceProperties(property_def, self._definition_type)

        return config_properties

    def get_new_extensions_definition(self):

        if self._definition_type == "XML":
            self.fix_sddraft_namespaces(self._raw_definition.getroot())

            file_name, file_ext = os.path.splitext(os.path.basename(self._source))
            new_draft = os.path.join(os.path.dirname(self._source), file_name + "_updated" + file_ext)

            try:
                if os.path.exists(new_draft):
                    os.remove(new_draft)
                self._raw_definition.write(new_draft)
                return new_draft
            except Exception as ex:
                raise Exception("Unable to update draft Service Definition file. {0}".format(ex.message))
        else:
            return self._raw_definition

    def set_operations_allowed(self, mapping, query, data):

        ops = []
        if mapping:
            ops.append("Map")
        if query:
            ops.append("Query")
        if data:
            ops.append("Data")
        ops_string = str(ops)

        if self._definition_type == "XML":
            ops_node = self._find_xml_node_by_key(
                self.XML_ROOT + "/Info/PropertyArray/PropertySetProperty",
                "WebCapabilities")
            ops_node.find("Value").text = ops_string
        else:
            self._raw_definition["capabilities"] = ops_string

    def min_instances(self, value):
        pass

    def max_instances(self, value):

        if self._definition_type == "XML":
            max_node = self._find_xml_node_by_key(self.XML_ROOT + "/Props/PropertyArray/PropertySetProperty",
                                                  "MaxInstances")
            max_node.find("Value") == str(value)
            pass
        else:
            self._raw_definition["maxInstancesPerNode"] = value

    def instances_per_container(self, value):
        pass

    def cluster_name(self, value):
        pass

    def max_wait_time(self, value):
        pass

    def max_startup_time(self, value):
        pass

    def max_idle_time(self, value):
        pass

    def max_usage_time(self, value):
        pass

    @staticmethod
    def fix_sddraft_namespaces(root):
        """
        Fixes namespaces for sddraft file after XML has been modified.
        :param root: root element in XML to be fixed
        """

        # Update namespaces - these get stripped out when parsed by ElementTree
        root.set("xmlns:xs", "http://www.w3.org/2001/XMLSchema")
        root.set("xmlns:typens", "http://www.esri.com/schemas/ArcGIS/10.1")

    def _find_xml_node_by_key(self, path, key):

        return_node = None
        root = self._raw_definition.getroot()
        node_list = root.findall(path)
        for node in node_list:
            if node.find("Key").text == key:
                return_node = node
                break

        return return_node

class ServiceExtension(object):

    def __init__(self, extension_def, definition_type):
        """
        :param extension_def: Definition of the extension
        :param definition_type: How definition is stored - XML or JSON
        """

        self._definition = extension_def
        self._definition_type = definition_type

    def set_property(self, property_name, property_value):

        if self._definition_type == "XML":
            node = self._definition.find(property_name)
            if not node is None:
                node.text = property_value
        else:
            self._definition[property_name] = property_value

    def get_property(self, property_name):

        value = None
        if self._definition_type == "XML":
            node = self._definition.find(property_name)
            if not node is None:
                value = node.text
        else:
            value = self._definition[property_name]

        return value


class ServiceProperty(object):

    def __init__(self, property_def, definition_type):
        """
        :param property_def: Definition of the extension
        :param definition_type: How definition is stored - XML or JSON
        """

        self._definition = property_def
        self._definition_type = definition_type

    def set_property(self, property_name, property_value):

        if self._definition_type == "XML":
            property_sets = self._definition.findall("PropertySetProperty")
            for property_set in property_sets:
                if property_set.find("Key").text == property_name:
                    property_set.find("Value").text = property_value
        else:
            self._definition[property_name] = property_value

    def get_property(self, property_name):

        value = None
        if self._definition_type == "XML":
            property_sets = self._definition.findall("PropertySetProperty")
            for property_set in property_sets:
                if property_set.find("Key").text == property_name:
                    value = property_set.find("Value").text
        else:
            value = self._definition[property_name]

        return value
