"""
 web_service.py
 Created on Sep 19, 2014

 Encapsulates a web service and its functions.

 @author: mschmidt

 SVN revision info:
 @version     $Revision: 219 $
 @updated_by: $Author: mschmidt $
 @date        $Date: 2014-07-24 12:19:40 -0400 (Thu, 24 Jul 2014) $
"""

import urllib
import httplib
import json


class WebService(object):

    def __init__(self, server_name, web_site, port):
        self._server_name = server_name
        self._web_site = web_site
        self._web_port = port

    @property
    def server_name(self):
        return self._server_name

    @property
    def web_site(self):
        return self._web_site

    @property
    def web_port(self):
        return self._web_port

    def make_request(self, request, request_params, user, password):
        token = self._get_token(user, password)

        if token == "":
            raise Exception("Could not generate a token with the username and password provided.")

        service_url = "/{0}/admin/{1}".format(self._web_site, request)
        if request_params is None or request_params == "":
            request_params = {}
        request_params.update({"token": token, "f": "json"})
        params = urllib.urlencode(request_params)
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

        # Connect to service and get its current JSON definition
        http_conn = httplib.HTTPConnection(self.server_name, self.web_port)
        http_conn.request("POST", service_url, params, headers)

        # Read response
        response = http_conn.getresponse()
        if response.status != 200:
            http_conn.close()
            print "Request failed"
            return
        else:
            data = response.read()

        # Check that data returned is not an error object
        if not self.assert_json_success(data):
            print "Error when making request. " + str(data)
        else:
            print "Request was successful."

        http_conn.close()

        return data

    def _get_token(self, user, password):
        # Get token from http://server[:port]/arcgis/admin/generateToken
        token_url = "/{0}/admin/generateToken".format(self.web_site)

        params = urllib.urlencode({"username": user,
                                   "password": password,
                                   "client": "requestip",
                                   "f": "json"})
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}

        # Connect to URL and post parameters
        http_conn = httplib.HTTPConnection(self.server_name, self.web_port)
        http_conn.request("POST", token_url, params, headers)

        # Read Response
        response = http_conn.getresponse()
        if response.status != 200:
            http_conn.close()
            print "Error while fetching tokens form admin URL. Please check the URL and try again."
            return
        else:
            data = response.read()
            http_conn.close()

            # Check that data returned is not an error object
            if not self.assert_json_success(data):
                return

            # Extract the token from it
            token = json.loads(data)
            return token["token"]

    @staticmethod
    def assert_json_success(data):
        obj = json.loads(data)
        if "status" in obj and obj["status"] == "error":
            print "Error: JSON object returns an error. {0}".format(str(obj))
            return False
        else:
            return True