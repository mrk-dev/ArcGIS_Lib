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


class ServiceExtension(object):

    def __init__(self, service_def, extension_type):
        """
        :param service_def: Object that defines the service (json or sd draft file)
        :param extension_type: Name of the extension to be retrieved
        """

        # Determine if service_def is coming from an sd draft file (XML)
        # or from ArcGIS for Server definition (JSON)
        if os.path.exists(service_def):
            tree = ET.parse(service_def)
            root = tree.getroot()
            svc_exts = root.findall("Configurations/SVCConfiguration/Definition/Extensions/SVCExtension")
            extension_node = None
            for svc_ext in svc_exts:
                tn = svc_ext.find("TypeName")
                if tn.text.upper() == extension_type.upper():
                    extension_node = svc_ext
                    break

            self._root = tree
            self._definition = extension_node
            self._definition_type = "XML"
        else:
            root = json.loads(service_def)
            svc_exts = root["extensions"]
            extension_node = None
            for svc_ext in svc_exts:
                tn = svc_ext["typeName"]
                if tn.upper() == extension_type.upper():
                    extension_node = svc_ext
                    break

            self._root = root
            self._definition = extension_node
            self._definition_type = "JSON"

        self._extension_type = extension_type

    def set_property(self, property_name, property_value):

        if self._definition_type == "XML":
            node = self._definition.find(property_name)
            if not node is None:
                node.text = property_value
        else:
            self._definition[property_name] = property_value

    def root(self):
        return self._root