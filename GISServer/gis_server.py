"""
 gis_server.py
 Created on Sep 16, 2014

 Encapsulates ArcGIS for Server GIS server properties and methods.

 @author: mschmidt

 SVN revision info:
 @version     $Revision: 219 $
 @updated_by: $Author: mschmidt $
 @date        $Date: 2014-07-24 12:19:40 -0400 (Thu, 24 Jul 2014) $
"""

import arcpy
import json
import tempfile
import datetime
import os
import gis_service
import web_service


class GISServer(web_service.WebService):
    """Encapsulates admin properties and methods for ArcGIS for Server"""

    def __init__(self, server, admin_user, admin_pwd, website="arcgis", port=6080):

        web_service.WebService.__init__(self, server, website, port)
        self._server = server
        self._website = website
        self._port = port
        self._admin_user = admin_user
        self._admin_pwd = admin_pwd
        self._init = True

    @property
    def server_name(self):
        return self._server

    @property
    def web_site(self):
        return self._website

    @property
    def web_port(self):
        return self._port

    @property
    def server_url(self):
        if self.web_port is not None:
            url = "http://{0}:{1}/{2}".format(self.server_name, self.web_port, self.web_site)
        else:
            url = "http://{0}/{1}".format(self.server_name, self.web_site)
        return url

    def get_service(self, folder_name, service_name):
        return gis_service.GISService(self, folder_name, service_name)

    def service_exists(self, folder_name, service_name, service_type):
        params = {"folderName": folder_name,
                  "serviceName": service_name,
                  "type": service_type}

        data = self.make_request("services/exists", params, self._admin_user, self._admin_pwd)
        obj = json.loads(data)

        return obj["exists"]

    def create_service(self):
        pass

    def update_service(self):
        pass

    def export_site(self, file_location=None):
        if file_location is None:
            params = {}
        else:
            params = {"location": file_location}

        data = self.make_request("exportSite", params, self._admin_user, self._admin_pwd)
        obj = json.loads(data)

        return obj

    def import_site(self, file_location):
        params = {"location": file_location}

        data = self.make_request("importSite", params, self._admin_user, self._admin_pwd)
        obj = json.loads(data)

        return obj

    def delete_site(self):
        params = {}

        data = self.make_request("deleteSite", params, self._admin_user, self._admin_pwd)
        obj = json.loads(data)

        return obj

    def join_site(self, admin_url, admin_user=None, admin_password=None):
        admin_user = self._admin_user if admin_user is None else admin_user
        admin_password = self._admin_pwd if admin_password is None else admin_password

        params = {"adminURL": admin_url, "username": admin_user, "password": admin_password}

        data = self.make_request("joinSite", params, self._admin_user, self._admin_pwd)
        obj = json.loads(data)

        return obj

    def create_connection_file(self, outfile=None):

        if outfile is None:
            out_dir = tempfile.gettempdir()
            tstamp = datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S")
            out_name = "{0}-{1}.ags".format(self.server_name, tstamp)
        else:
            out_dir = os.path.dirname(outfile)
            out_name = os.path.basename(outfile)

        staging_dir = tempfile.mkdtemp(dir=out_dir)

        arcpy.mapping.CreateGISServerConnectionFile("ADMINISTER_GIS_SERVICES",
                                                    out_dir,
                                                    out_name,
                                                    self.server_url + "/admin",
                                                    "ARCGIS_SERVER",
                                                    False,
                                                    staging_dir,
                                                    self._admin_user,
                                                    self._admin_pwd,
                                                    "SAVE_USERNAME")

        return os.path.join(out_dir, out_name)



