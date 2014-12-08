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
    maps = []
    conf = []


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
    missing_tl_keys = {k for k in TLINK.ini_required_keys if k not in TLINK.conf}
    if missing_tl_keys:
        TLINK.disable_or_exit('Missing testlink ini keys: %s' % missing_tl_keys)


def load_maps_section():
    node_dict = defaultdict(list)
    for key, val in TLINK.maps.items():
        node_dict[val].append(key)
    duplicates = [x for x in node_dict if len(x) > 1]
    if duplicates:
        TLINK.disable_or_exit('Duplicate node ids in testlink maps: %s' % duplicates)


########################################################################################################################
# test link section
########################################################################################################################

def init_testlink(config):
    """Test link initialization"""

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

    TLINK.testlink_url = config.inicfg['tl_url']
    TLINK.dev_api_key = config.inicfg['tl_api_key']
    TLINK.project_name = config.inicfg['tl_project']

    TLINK.plan_name = process_config_env_value('tl_test_plan')
    TLINK.build_name = process_config_env_value('tl_build_name')
    TLINK.plan_ref = process_config_default_value('tl_reference_test_plan', None)
    TLINK.custom_field_name = process_config_default_value('tl_custom_field', 'pytest_node')


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
    if not TLINK.enabled:
        return


    # global NODE_MAP
    # NODE_MAP = {}
    # init_testlink(config)
    # load_tl_maps_from_testlink()
    # if 'tl_map_file' in config.inicfg:
    #     load_tl_maps_from_ini(Path(config.inicfg['tl_map_file']))


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
    print('Starting testlink processor for node: %s' % report.nodeid)
