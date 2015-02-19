# -*- coding: utf-8 -*-
"""
testlink-python
***************

"""

from __future__ import print_function
from collections import defaultdict
import sys

if sys.version_info[0] < 3:
    import ConfigParser as configparser

    configparser.ConfigParser = configparser.SafeConfigParser
else:
    import configparser

import os
import time
import testlink
from path import Path
import pytest
from testlink import TestLinkError


PLUGIN_NAME = "pytest_testlink"


class TLINK:
    # globals
    enabled = True
    exit_on_fail = False

    ini = configparser.ConfigParser()
    ini_required_keys = ['xmlrpc_url', 'api_key', 'project', 'test_plan', 'build_name']
    ini_optional = ['new_build', 'reference_test_plan', 'custom_field']
    nodes = defaultdict(list)
    maps = {}
    conf = {}

    rpc = testlink.TestlinkAPIClient


    def __str__(self):
        return PLUGIN_NAME

    def __repr__(self):
        return PLUGIN_NAME

    @classmethod
    def disable_or_exit(cls, err_msg):
        print('testlink: disabled! %s' % err_msg)
        cls.enabled = False
        if cls.exit_on_fail:
            raise TestLinkError(err_msg)


########################################################################################################################
# ini file processing
########################################################################################################################
def load_testlink_file(file_path):
    if not file_path.isfile():
        print("ERROR: testlink_file not found!")
        TLINK.disable_or_exit('FileNotFoundError: testlink_file: %s' % file_path)
    if not TLINK.enabled:
        return

    # read ini file
    TLINK.ini.read(file_path)

    # load testlink-conf section
    if 'testlink-conf' in TLINK.ini.sections():
        TLINK.conf = TLINK.ini['testlink-conf']
    else:
        TLINK.disable_or_exit('section "testlink-conf" not found in ini file: %s' % file_path)

    # load testlink-maps section
    if 'testlink-maps' in TLINK.ini.sections():
        TLINK.maps = TLINK.ini['testlink-maps']
    else:
        print('section "testlink-maps" not found in ini file: %s' % file_path)


def load_conf_section():
    def process_config_env_value(key):
        if TLINK.conf[key].strip().startswith('$'):
            return os.environ[TLINK.conf[key][1:]]
        else:
            return TLINK.conf[key]

    missing_tl_keys = {k for k in TLINK.ini_required_keys if k not in TLINK.conf}
    if missing_tl_keys:
        TLINK.disable_or_exit('Missing testlink ini keys: %s' % missing_tl_keys)
    else:
        temp_dict = {}
        for conf_key, conf_val in TLINK.conf.items():
            temp_dict[conf_key] = process_config_env_value(conf_key)
        for k, v in temp_dict.items():
            TLINK.conf[k] = v


def load_maps_section():
    node_dict = defaultdict(list)
    for key, val in TLINK.maps.items():
        node_dict[val].append(key)
    duplicates = [x for x in node_dict if len(node_dict[x]) != 1]
    if duplicates:
        TLINK.disable_or_exit('Duplicate node ids in testlink maps: %s' % duplicates)
        return
    # construct the nodes dict
    TLINK.nodes = {v: k for k, v in TLINK.maps.items()}


########################################################################################################################
# test link section
########################################################################################################################

def init_testlink():
    """Test link initialization"""
    if not TLINK.enabled:
        return
    # connect to test link
    TLINK.rpc = testlink.TestlinkAPIClient(server_url=TLINK.conf['xmlrpc_url'], devKey=TLINK.conf['api_key'])

    # assert test project exists
    _test_project = TLINK.rpc.getTestProjectByName(TLINK.conf['project'])
    if not _test_project:
        TLINK.disable_or_exit('Invalid tl_project name. Unable to find project')
        return

    # type convert from list for older testlink instances
    _test_project = _test_project[0] if isinstance(_test_project, list) else _test_project

    # get project id and prefix
    TLINK.project_id = _test_project['id']
    TLINK.project_prefix = _test_project['prefix']

    # list of test plans
    plans = {plan['id']: plan for plan in TLINK.rpc.getProjectTestPlans(TLINK.project_id)}

    # create test plan if required
    plan_name = [tp for tp in TLINK.rpc.getProjectTestPlans(TLINK.project_id) if tp['name'] == TLINK.conf['test_plan']]
    if not plan_name:
        TLINK.rpc.createTestPlan(TLINK.conf['test_plan'], TLINK.conf['project'])
        plan_name = [tp for tp in TLINK.rpc.getProjectTestPlans(TLINK.project_id) if
                     tp['name'] == TLINK.conf['test_plan']]
    TLINK.test_plan_id = plan_name[0]['id']

    # create test build if required
    TLINK.test_build = [tb for tb in TLINK.rpc.getBuildsForTestPlan(TLINK.test_plan_id)
                        if tb['name'] == TLINK.conf['build_name']]
    if not TLINK.test_build:
        TLINK.rpc.createBuild(int(TLINK.test_plan_id), TLINK.conf['build_name'],
                              'Automated test. Created by mf_testlink plugin.')
        TLINK.test_build = [tb for tb in TLINK.rpc.getBuildsForTestPlan(TLINK.test_plan_id)
                            if tb['name'] == TLINK.conf['build_name']]
    TLINK.test_build_id = TLINK.test_build[0]['id']
    print(TLINK.test_build_id)


########################################################################################################################
# py test hooks
########################################################################################################################
def pytest_addoption(parser):
    """Add all the required ini and command line options here"""
    parser.addoption(
        '--no-testlink', action="store_false", dest="testlink", default=True,
        help="disable pytest-testlink"
    )
    parser.addoption(
        '--testlink-exit-on-error', action="store_true", dest="testlink_exit_on_fail", default=False,
        help="exit on any test link plugin related errors/exceptions"
    )
    parser.addini('testlink_file', 'Location of testlink configuration ini file.')


def pytest_configure(config):
    if not config.option.testlink:
        TLINK.enabled = False
        return
    if 'testlink_file' not in config.inicfg:
        TLINK.enabled = False
        return

    if config.option.testlink_exit_on_fail:
        TLINK.exit_on_fail = True

    # load testlink-conf section
    load_testlink_file(Path(config.inicfg['testlink_file']))
    if not TLINK.enabled:
        return

    load_conf_section()
    if not TLINK.enabled:
        return

    load_maps_section()
    if not TLINK.nodes:
        TLINK.disable_or_exit("No nodes found!")
        return

    init_testlink()


def pytest_report_header(config, startdir):
    if not config.option.testlink:
        print('testlink: disabled by --no-testlink')
    elif 'testlink_file' in config.inicfg:
        print('testlink: %s' % config.inicfg['testlink_file'])
    else:
        print('testlink: "testlink_file" key was not found in [pytest] section')

    if config.option.testlink_exit_on_fail:
        print('testlink: exit on failure enabled!')


def pytest_runtest_logreport(report):
    if not TLINK.enabled:
        return

    status = ''
    if report.passed:
        # ignore setup/teardown
        if report.when == "call":
            status = 'p'
    elif report.failed:
        status = 'f'
    elif report.skipped:
        status = 'b'
    if status:
        try:
            if report.nodeid not in TLINK.nodes:
                print('testlink: WARN: ext-id not found: %s' % report.nodeid)
                return
            TLINK.rpc.reportTCResult(testplanid=TLINK.test_plan_id,
                                     buildid=TLINK.test_build_id,
                                     status=status,
                                     testcaseexternalid=TLINK.nodes[report.nodeid])
        except TestLinkError as exc:
            print('testlink: WARN: Unable to update result: %s' % report.nodeid)
            print('testlink: Check if the test case is not linked to test plan!')
            print(exc)
