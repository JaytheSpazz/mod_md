# test mod_md cleanups and sanitation

import json
import os
import pytest
import re
import socket
import ssl
import sys
import time

from datetime import datetime
from httplib import HTTPSConnection
from test_base import TestEnv
from test_base import HttpdConf
from test_base import CertUtil


def setup_module(module):
    print("setup_module    module:%s" % module.__name__)
    TestEnv.init()
    TestEnv.APACHE_CONF_SRC = "data/test_auto"
    TestEnv.check_acme()
    TestEnv.clear_store()
    TestEnv.install_test_conf();
    assert TestEnv.apache_start() == 0
    

def teardown_module(module):
    print("teardown_module module:%s" % module.__name__)
    assert TestEnv.apache_stop() == 0


class TestAuto:

    @classmethod
    def setup_class(cls):
        time.sleep(1)
        cls.dns_uniq = "%d.org" % time.time()
        cls.TMP_CONF = os.path.join(TestEnv.GEN_DIR, "auto.conf")


    def setup_method(self, method):
        print("setup_method: %s" % method.__name__)
        TestEnv.apache_err_reset();
        TestEnv.clear_store()
        TestEnv.install_test_conf();
        self.test_n = re.match("test_910_(.+)", method.__name__).group(1)
        self.test_domain =  ("%s-" % self.test_n) + TestAuto.dns_uniq

    def teardown_method(self, method):
        print("teardown_method: %s" % method.__name__)

    def test_910_01(self):
        domain = ("%s-" % self.test_n) + TestAuto.dns_uniq
        
        # generate a simple MD
        dnsList = [ domain ]
        conf = HttpdConf( TestAuto.TMP_CONF )
        conf.add_admin( "admin@not-forbidden.org" )
        conf.add_drive_mode( "manual" )
        conf.add_md( dnsList )
        conf.add_vhost( TestEnv.HTTPS_PORT, domain, aliasList=[], withSSL=True )
        conf.install()

        # create valid/invalid challenges subdirs
        challenges_dir = TestEnv.path_challenges()
        dirs_before = [ "aaa", "bbb", domain, "zzz" ]
        for name in dirs_before:
            os.makedirs(os.path.join( challenges_dir, name ))

        assert TestEnv.apache_restart() == 0

        # the one we use is still there
        assert os.path.isdir(os.path.join( challenges_dir, domain ))
        # and the others are gone
        missing_after = [ "aaa", "bbb", "zzz" ]
        for name in missing_after:
            assert not os.path.exists(os.path.join( challenges_dir, name ))

