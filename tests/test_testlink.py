# -*- coding: utf-8 -*-
from __future__ import print_function

pytest_plugins = "pytester"


import os
import sys
import time

import pytest
from pytest_testlink import TLINK


DEMO_XMLRPC = "http://demo.testlink.org/latest/lib/api/xmlrpc/v1/xmlrpc.php"
DEMO_APIKEY = "583e35fa07bd59e81048640f5cee1897"


def init_ini(testdir):
    testdir.tmpdir.ensure("pytest.ini").write("""[pytest]
testlink_file=testlink.ini""")


def init_pass(testdir):
    testdir.makepyfile("""
    import pytest
    def test_pass(): assert 1
    """)


def init_tests(testdir):
    testdir.makepyfile("""
    import pytest
    def test_1(): assert 1
    def test_2(): assert 0
    def test_3(): pytest.skip()
    @pytest.mark.xfail
    def test_4(): assert 0
    @pytest.mark.xfail
    def test_5(): assert 1
    """)

def init_testlink(testdir):
    testdir.tmpdir.ensure("testlink.ini").write("""
[testlink-conf]
xmlrpc_url=""" + DEMO_XMLRPC + """
api_key=""" + DEMO_APIKEY + """
project=TS
test_plan=Automation
build_name=1

[testlink-maps]
ts-1=tests/test_testlink.py::test_1
ts-2=tests/test_testlink.py::test_2
ts-3=tests/test_testlink.py::test_3
ts-4=tests/test_testlink.py::test_4
ts-5=tests/test_testlink.py::test_5
"""
    )



# # Tests
def test_no_testlink(testdir):
    init_pass(testdir)
    result = testdir.runpytest('--no-testlink', testdir.tmpdir)
    assert result.ret == 0
    result.stdout.fnmatch_lines_random("*testlink: disabled by --no-testlink*")


def test_no_configure_print(testdir):
    init_pass(testdir)
    result = testdir.runpytest(testdir.tmpdir)
    assert result.ret == 0
    result.stdout.fnmatch_lines_random(r'*testlink: "testlink_file" key was not found in [pytest? section*')


def test_testlink_file_not_found(testdir):
    init_ini(testdir)
    init_pass(testdir)

    result = testdir.runpytest(testdir.tmpdir)
    assert result.ret == 0
    result.stdout.fnmatch_lines_random("*FileNotFoundError: testlink_file: testlink.ini*")
    result.stdout.fnmatch_lines_random("*1 passed*")

    result = testdir.runpytest('--testlink-exit-on-error', testdir.tmpdir)
    # result.stdout.fnmatch_lines_random("*testlink: exit on failure enabled!*")
    assert result.ret == 3
    result.stderr.fnmatch_lines_random("*FileNotFoundError: testlink_file: testlink.ini*")
    result.stderr.fnmatch_lines_random("*INTERNALERROR*")


def test_testlink_conf_section_not_found(testdir):
    init_ini(testdir)
    init_pass(testdir)
    testdir.tmpdir.ensure("testlink.ini").write("""[pytest]""")

    result = testdir.runpytest(testdir.tmpdir)
    assert result.ret == 0
    result.stdout.fnmatch_lines_random("*1 passed*")
    result.stdout.fnmatch_lines_random('*section "testlink-conf" not found in ini file: testlink.ini*')

    result = testdir.runpytest('--testlink-exit-on-error', testdir.tmpdir)
    # result.stdout.fnmatch_lines_random("*testlink: exit on failure enabled!*")
    assert result.ret == 3
    result.stderr.fnmatch_lines_random('*section "testlink-conf" not found in ini file: testlink.ini*')
    result.stderr.fnmatch_lines_random("*INTERNALERROR*")


def test_testlink_maps_section_not_found(testdir):
    init_ini(testdir)
    init_pass(testdir)
    testdir.tmpdir.ensure("testlink.ini").write("""[testlink-conf]""")

    result = testdir.runpytest(testdir.tmpdir)
    assert result.ret == 0
    result.stdout.fnmatch_lines_random("*1 passed*")
    result.stdout.fnmatch_lines_random('*section "testlink-maps" not found in ini file: testlink.ini*')


@pytest.mark.parametrize(argnames="data",
                         argvalues=TLINK.ini_required_keys)
def test_testlink_missing_key(testdir, data):
    init_ini(testdir)
    init_pass(testdir)
    keys = set(TLINK.ini_required_keys)
    keys.remove(data)
    testdir.tmpdir.ensure("testlink.ini").write("""[testlink-conf]\n%s""" % ('\n'.join(k+"=dummy" for k in keys)))
    print(open("testlink.ini").read())
    result = testdir.runpytest(testdir.tmpdir)
    assert result.ret == 0
    result.stdout.fnmatch_lines_random("*Missing testlink ini keys: {'%s'}*" % data)

    result = testdir.runpytest('--testlink-exit-on-error', testdir.tmpdir)
    assert result.ret == 3
    result.stderr.fnmatch_lines_random("*INTERNALERROR*")
    result.stderr.fnmatch_lines_random("*Missing testlink ini keys: {'%s'}*" % data)


def test_ini_map_one_test(testdir):
    init_ini(testdir)
    init_pass(testdir)
    testdir.tmpdir.ensure("testlink.ini").write("""[testlink-conf]\n%s""" %
                                                ('\n'.join(k+"=dummy" for k in TLINK.ini_required_keys)) +
                                                """\n[testlink-maps]
                                                test-1=tests/test_testlink.py::test_ini_map
                                                """)
    result = testdir.runpytest(testdir.tmpdir)
    assert result.ret == 0
    result.stdout.fnmatch_lines_random("*1 passed*")


def test_ini_map_duplicate_keys(testdir):
    init_ini(testdir)
    init_pass(testdir)
    testdir.tmpdir.ensure("testlink.ini").write("""[testlink-conf]\n%s""" %
                                                ('\n'.join(k+"=dummy" for k in TLINK.ini_required_keys)) +
                                                """\n[testlink-maps]
                                                test-1=tests/test_testlink.py::test_ini_map
                                                test-1=tests/test_testlink.py::test_ini_map
                                                """)
    result = testdir.runpytest(testdir.tmpdir)
    assert result.ret == 3
    result.stderr.fnmatch_lines_random("*configparser.DuplicateOptionError*")
    result.stderr.fnmatch_lines_random("*option 'test-1' in section 'testlink-maps' already exists*")


def test_ini_map_duplicate_nodes(testdir):
    init_ini(testdir)
    init_pass(testdir)
    testdir.tmpdir.ensure("testlink.ini").write("""[testlink-conf]\n%s""" %
                                                ('\n'.join(k+"=dummy" for k in TLINK.ini_required_keys)) +
                                                """\n[testlink-maps]
                                                test-1=tests/test_testlink.py::test_ini_map
                                                test-2=tests/test_testlink.py::test_ini_map
                                                """)
    result = testdir.runpytest(testdir.tmpdir)
    assert result.ret == 0
    result.stdout.fnmatch_lines_random("*Duplicate node ids in testlink maps: ['tests/test_testlink.py::test_ini_map'*")

    result = testdir.runpytest('--testlink-exit-on-error', testdir.tmpdir)
    assert result.ret == 3
    result.stderr.fnmatch_lines_random("*INTERNALERROR*")
    result.stderr.fnmatch_lines_random("*Duplicate node ids in testlink maps:*")


def test_ini_map_no_nodes(testdir):
    init_ini(testdir)
    init_pass(testdir)
    testdir.tmpdir.ensure("testlink.ini").write("""[testlink-conf]\n%s""" %
                                                ('\n'.join(k+"=dummy" for k in TLINK.ini_required_keys)) +
                                                """\n[testlink-maps]""")
    result = testdir.runpytest(testdir.tmpdir)
    assert result.ret == 0
    result.stdout.fnmatch_lines_random("*No nodes found*")

    result = testdir.runpytest('--testlink-exit-on-error', testdir.tmpdir)
    assert result.ret == 3
    result.stderr.fnmatch_lines_random("*INTERNALERROR*")
    result.stderr.fnmatch_lines_random("*No nodes found!*")


def test_1(testdir):
    init_ini(testdir)


def test_2():
    assert 0

def test_3():
    pytest.skip()

@pytest.mark.xfail
def test_4():
    assert 0

@pytest.mark.xfail
def test_5():
    assert 1

