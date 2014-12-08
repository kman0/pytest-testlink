# -*- coding: utf-8 -*-
from __future__ import print_function

pytest_plugins = "pytester"


import os
import sys
import time

import pytest
from pytest_testlink import TLINK

def init_ini(testdir):
    testdir.tmpdir.ensure("pytest.ini").write("""[pytest]
testlink_file=testlink.ini""")


def init_pass(testdir):
    testdir.makepyfile("""
    import pytest
    def test_pass(): assert 1
    """)


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