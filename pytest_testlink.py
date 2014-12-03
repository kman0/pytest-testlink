# -*- coding: utf-8 -*-
"""
testlink-python
***************

"""

from __future__ import print_function
from collections import defaultdict
import configparser

import os
import sys
import time
import testlink
from path import Path
import pytest


class TestLink:
    # todo: move class up to module
    plugin_name = "pytest_testlink"
    tl_ini_required_keys = ['tl_url', 'tl_api_key', 'tl_project', 'tl_test_plan', 'tl_build_name']

    node_id_lookup = {}
    ext_id_lookup = {}

    automated_tests = {}
    automated_tests_ref = {}
    pytest_node_ids = {}
    duplicate_pytest_nodes = set()

    def __str__(self):
        return self.plugin_name

    def __repr__(self):
        return self.plugin_name

    @staticmethod
    def get_automated_tests_for_test_plan():
        return TestLink.get_automated_tests([TestLink.test_plan_id])

    @classmethod
    def get_automated_tests(cls, test_plans_list):
        return_dict = {}
        for _tp in test_plans_list:
            _tmp_tests = cls._tl.getTestCasesForTestPlan(_tp, execution='2', active='1')
            if _tmp_tests:
                return_dict.update({key: val for key, val in _tmp_tests.items()})
        return return_dict

    @classmethod
    def lookup_pytest_node(cls, pytest_node):
        """

        :param pytest_node:
        :return:
        """
        return cls.pytest_node_ids[pytest_node]

EXT_ID_MAP = {

}

NODE_ID_MAP = {
    'test-3': 'stest_pytest_testlink.py::test_pass[2]'
}


def init_testlink(config):
    """Test link initialization"""
    missing_tl_keys = {k for k in TestLink.tl_ini_required_keys if k not in config.inicfg}
    if missing_tl_keys:
        print('ERROR: Missing testlink ini keys: %s' % missing_tl_keys)
        print('WARNING: %s plugin will be disabled!' % TestLink.plugin_name)
        return None

    def process_config_env_value(key):
        if config.inicfg[key].strip().startswith('$'):
            return os.environ[config.inicfg[key][1:]]
        else:
            return config.inicfg[key]

    def process_config_default_value(key, default):
        if key in config.inicfg:
            return config.inicfg[key]
        else:
            return default

    TestLink.testlink_url = config.inicfg['tl_url']
    TestLink.dev_api_key = config.inicfg['tl_api_key']
    TestLink.project_name = config.inicfg['tl_project']

    TestLink.plan_name = process_config_env_value('tl_test_plan')
    TestLink.build_name = process_config_env_value('tl_build_name')
    TestLink.plan_ref = process_config_default_value('tl_reference_test_plan', None)
    TestLink.custom_field_name = process_config_default_value('tl_custom_field', 'pytest_node')


def connect_and_assert_testlink_args():

    # connect to test link
    _tl = testlink.TestlinkAPIClient(server_url=TestLink.testlink_url, devKey=TestLink.dev_api_key)
    TestLink._tl = _tl


def load_tl_maps_from_testlink():
    pass


def load_tl_maps_from_ini(ini_path):
    if not ini_path.isfile():
        raise FileNotFoundError('ini file: %s' % ini_path)
    con = configparser.ConfigParser(allow_no_value=True)
    con.read(ini_path)
    if 'testlink-maps' not in con.sections():
        raise KeyError('testlink-maps section not found in ini file: %s ' % ini_path.abspath())
    _errors = []
    for k, v in con['testlink-maps'].items():
        if k.strip() not in NODE_MAP:
            NODE_MAP[k.strip()] = v.strip()
        elif v.strip() == NODE_MAP[k.strip()]:
            continue
        else:
            _errors.append('Mismatch - \n\tnode id from testlink: %s' % NODE_MAP[k.strip()] +
                           '\n\tnode id from ini file: %s' % v.strip())
    if _errors:
        print('\n'.join(_errors))
        raise KeyError('Errors/Duplicates while loading keys from maps file')
        # print(TL_NODE_MAP)


########################################################################################################################
# py test hooks
########################################################################################################################


def pytest_addoption(parser):
    """Add all the required ini and command line options here"""
    parser.addini('tl_url', 'http://[test link server]/testlink/lib/api/xmlrpc.php')
    parser.addini('tl_api_key', 'Testlink->My Settings->API interface->Generate Key')
    parser.addini('tl_project', 'Project name in test link')
    parser.addini('tl_test_plan', 'Prefix $ to pick from environment variable.')
    parser.addini('tl_build_name', 'Prefix $ to pick from environment variable.')
    parser.addini('tl_custom_field', '[pytest_node]unique custom_field')

    parser.addini('tl_reference_test_plan', 'Test plan with all tests added.')
    parser.addini('tl_fail_hard', 'optional [False] True errors on testlink failures')
    parser.addini('tl_new_build', 'optional [False] True creates a new build')


def pytest_configure(config):

    global NODE_MAP
    NODE_MAP = {}
    init_testlink(config)
    load_tl_maps_from_testlink()
    if 'tl_map_file' in config.inicfg:
        load_tl_maps_from_ini(Path(config.inicfg['tl_map_file']))


def pytest_runtest_logreport(report):
    print(report.nodeid)
    if report.nodeid in NODE_MAP:
        print()

