__author__ = 'mschmidt'

import unittest
import GISServer.gis_service as agsservice
import GISServer.gis_server as ags


class ServiceTest(unittest.TestCase):

    def setUp(self):
        self.gissvr = ags.GISServer("nosat01", "geoadmin", "XXXXXX")
        self.service = agsservice.GeoProcessingService(self.gissvr, None, "test_gps",
                                                       r"D:\temp\test.tbx",
                                                       "Script")

    def test_publishgp(self):
        self.service.add_parameter("Name", "Mark")

        result = self.service.publish()
        print result

        srv_def = self.gissvr.service_exists("", "Script", "GPServer")
        self.assertIs(srv_def, False, "Service NOT published")

if __name__ == "__main__":
    unittest.main()