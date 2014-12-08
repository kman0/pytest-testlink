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
    assert result.ret == 3
    result.stderr.fnmatch_lines_random("*FileNotFoundError: testlink_file: testlink.ini*")

