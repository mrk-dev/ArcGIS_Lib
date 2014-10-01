__author__ = 'mschmidt'

import unittest
import GISServer.gis_service as agsservice
import GISServer.gis_server as ags


class ServiceTest(unittest.TestCase):

    def setUp(self):
        self.gissvr = ags.GISServer("nosat01", "geoadmin", "esri1600!")
        self.mapservice = agsservice.MAPService(self.gissvr, "", "test_map")
        self.featureservice = agsservice.FeatureService(self.gissvr, "", "test_featureService")
        self.geocoderservice = agsservice.GeoCoderService(self.gissvr, "", "test_geocoder")

    def test_b_publishfeatureservice(self):
        mxd_path = r"D:\Projects\Parks Canada\NIRS 2014\data\mxds\DFRP_GIS_Parcels.mxd"
        self.featureservice.mxd = mxd_path
        result = self.featureservice.publish()
        print result

        srv_exist = self.gissvr.service_exists("", "test_featureService", "FeatureServer")
        self.assertIs(srv_exist, False, "Service NOT published")

    def test_a_publishmap(self):
        mxd_path = r"D:\Projects\Parks Canada\NIRS 2014\data\mxds\DFRP_GIS_Parcels.mxd"
        self.mapservice.mxd = mxd_path
        result = self.mapservice.publish()
        print result

        srv_exist = self.gissvr.service_exists("", "test_map", "MapServer")
        self.assertIs(srv_exist, True, "Service NOT published")

    def test_c_publish_geocoder(self):
        locator_path = r"D:\Data\Spatial\ESRI\ArcLogistics\StreetData\NTNA2013_R1\Locators\CAN_StreetAddress.loc"
        self.geocoderservice.locator = locator_path
        result = self.geocoderservice.publish()
        print result

        srv_exist = self.gissvr.service_exists("", "test_geocoder", "GeocodeServer")
        self.assertIs(srv_exist, True, "Service NOT published")

    def test_z_delete_services(self):
        self.geocoderservice.delete()
        self.mapservice.delete()
        self.featureservice.delete()

        srvs_exist = self.gissvr.service_exists("", "test_map", "MapServer") | \
                     self.gissvr.service_exists("", "test_featureService", "FeatureServer") | \
                     self.gissvr.service_exists("", "test_geocoder", "GeocodeServer")
        self.assertIs(srvs_exist, False, "Service NOT deleted")

if __name__ == "__main__":
    unittest.main()