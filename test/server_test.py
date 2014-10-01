__author__ = 'mschmidt'

import unittest
import json
import GISServer.gis_server as gis_svr
import os

class ServerTest(unittest.TestCase):

    def setUp(self):
        self.gisserver = gis_svr.GISServer("nosat01", "geoadmin", "XXXXXX")

    def test_connect(self):
        print "Test token retrieval"
        token = self.gisserver._get_token(self.gisserver._admin_user, self.gisserver._admin_pwd)
        self.assertTrue(token is not None, "Could not get token from server")

    def test_bad_creds(self):
        print "Test bad creds"
        gis_server = gis_svr.GISServer("nosat01", "blah", "blah")
        token = gis_server._get_token(gis_server._admin_user, gis_server._admin_pwd)
        self.assertIsNone(token, "Credentials were good, expecting failure")

    def test_get_service_def(self):
        print "Test get service def"
        service_def = self.gisserver.get_service("SampleWorldCities", "", "MapServer")
        dataobj = json.loads(service_def)
        self.assertEqual(dataobj["serviceName"], "SampleWorldCities", "Wrong map service retrieved!")

    def test_create_confile(self):
        print "Create connection file"
        out_file = "C:/temp/test_confile.ags"
        self.gisserver.create_connection_file("C:/temp/test_confile.ags")
        self.assertTrue(os.path.exists("C:/temp/test_confile.ags"), "Connection file not created!")

        out_file = self.gisserver.create_connection_file()
        self.assertTrue(os.path.exists(out_file), "Connection file not created!")

    def test_service_exists(self):
        print "Test service exists"
        self.assertTrue(self.gisserver.service_exists("", "SampleWorldCities", "MapServer"),
                        "Map service does NOT exist")


if __name__ == "__main__":
    unittest.main()