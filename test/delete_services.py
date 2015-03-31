__author__ = 'mschmidt'

import unittest
import GISServer.gis_server as ags
import GISServer.gis_service as svc


class ServiceTest(unittest.TestCase):

    def setUp(self):
        self.gissvr = ags.GISServer("nosat01", "geoadmin", "esri1600!")
        self.mapservice = svc.MAPService(self.gissvr, "", "test_map")
        self.featureservice = svc.FeatureService(self.gissvr, "", "test_featureService")
        self.geocoderservice = svc.GeoCoderService(self.gissvr, "", "test_geocoder")

    def test_z_delete_services(self):
        self.geocoderservice.delete()
        self.mapservice.delete()
        self.featureservice.delete()

        srvs_exist = self.gissvr.service_exists("", "test_map", "MapServer") | \
                     self.gissvr.service_exists("", "test_featureService", "FeatureServer") | \
                     self.gissvr.service_exists("", "test_geocoder", "GeocodeServer")
        self.assertIs(srvs_exist, False, "Service NOT deleted")
