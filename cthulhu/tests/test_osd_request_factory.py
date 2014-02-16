from django.utils.unittest import TestCase
from mock import MagicMock, patch


class CalamariConfig(type):
    def __new__(mcs, name, parents, dct):
        import os
        if os.environ.get("CALAMARI_CONFIG") is None:
            os.environ["CALAMARI_CONFIG"] = "/home/vagrant/calamari/dev/calamari.conf"

        return super(CalamariConfig, mcs).__new__(mcs, name, parents, dct)


class CalamariTestCase(TestCase):
    __metaclass__ = CalamariConfig

from cthulhu.manager.osd_request_factory import OsdRequestFactory
from cthulhu.manager.user_request import UserRequest


class TestOSDFactory(CalamariTestCase):

    salt_local_client = MagicMock(run_job=MagicMock())
    salt_local_client.return_value = salt_local_client
    salt_local_client.run_job.return_value = {'jid': 12345}

    def setUp(self):
        fake_cluster_monitor = MagicMock()
        attributes = {'name': 'I am a fake',
                      'fsid': 12345,
                      'get_sync_object.return_value': fake_cluster_monitor,
                      'osds_by_id': {0:{'up': True}, 1:{'up': False}}}
        fake_cluster_monitor.configure_mock(**attributes)


        self.osd_request_factory = OsdRequestFactory(fake_cluster_monitor)

    def testCreate(self):
        self.assertNotEqual(OsdRequestFactory(0), None, 'Test creating an OSDRequest')

    @patch('cthulhu.manager.user_request.LocalClient', salt_local_client)
    def testScrub(self):
        scrub = self.osd_request_factory.scrub(0)
        self.assertIsInstance(scrub, UserRequest, 'Testing Scrub')

        #import pdb; pdb.set_trace()
        scrub.submit(54321)
        self.salt_local_client.run_job.assert_called_with(54321, 'ceph.rados_commands', [12345, 'I am a fake', []])

    def testDeepScrub(self):
        deep_scrub = self.osd_request_factory.deep_scrub(0)
        self.assertIsInstance(deep_scrub, UserRequest, 'Failed to make a deep scrub request')

    def test_validate_scrub(self):
        self.assertTrue(self.osd_request_factory._validate_operation('scrub', 0))

    def test_validate_scrub_on_down_osd(self):
        self.assertFalse(self.osd_request_factory._validate_operation('scrub', 1))

    def test_validate_op_key_error(self):
        self.assertFalse(self.osd_request_factory._validate_operation('scrub', 2))