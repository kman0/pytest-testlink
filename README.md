pytest-testlink [![Build Status](https://travis-ci.org/manojklm/pytest-testlink.svg?branch=master)](https://travis-ci.org/manojklm/pytest-testlink)
===============


Updates test results in test link.

Uses ini file with test case external id and test node id as mapping

    xmlrpc_url =http://[test link server]/testlink/lib/api/xmlrpc.php
    api_key =Testlink->My Settings->API interface->Generate Key
    project =Project name as in test link
    test_plan =Prefix $ to pick from environment variable.
    build_name =Prefix $ to pick from environment variable.

##pytest.ini configuration
    testlink_ini_file=testlink.ini

###Testlink file format (testlink.ini)
    ; ini file with testlink-conf section
    [testlink-conf]
    xmlrpc_url=http://[test link server]/testlink/lib/api/xmlrpc.php')
    api_key=aaaabbbbccccddddaaaabbbbccccdddd
    project=py-tl-Project
    test_plan=py-tl-Plan
    build_name=py-tl-Build
    exit_on_fail=optional [False] True errors on testlink failures'

    ;tl_custom_field=[pytest_node]unique custom_field')
    new_build=optional [False] True creates a new build')    
    ;tl_reference_test_plan=Test plan with all tests added.')
    
    ; ini file with testlink-maps section
    [testlink-maps]
    ;test case external-id=node-id(after parametrization)
    test-0=test_pytest_testlink.py::TestClass::test_dummy
    test-1=test_pytest_testlink.py::test_pass[0]
    test-2=test_pytest_testlink.py::test_pass[1]
    test-3=test_pytest_testlink.py::test_pass[2]

