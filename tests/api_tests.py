#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# (C) 2014 tchvatal@suse.cz, openSUSE.org
# Distribute under GPLv2 or later

import os
import contextlib
import unittest
import httpretty
# mock is part of python3.3
try:
    import unittest.mock
except ImportError:
    import mock

import oscs
import osc

class TestApiCalls(unittest.TestCase):
    """
    Tests for various api calls to ensure we return expected content
    """

    def _get_fixtures_dir(self):
        """
        Return path for fixtures
        """
        return os.path.join(os.getcwd(), 'tests/fixtures')

    def _register_pretty_url_get(self, url, filename):
        """
        Register specified url with specific filename in fixtures
        :param url: url address to "open"
        :param filename: name of the fixtures file
        """

        response = open(os.path.join(self._get_fixtures_dir(), filename), 'r')
        content = response.read()
        response.close()

        httpretty.register_uri(httpretty.GET,
                               url,
                               body=content)

    def setUp(self):
        """
        Initialize the configuration so the osc is happy
        """

        oscrc = os.path.join(self._get_fixtures_dir(), 'oscrc')
        osc.core.conf.get_config(override_conffile=oscrc,
                                 override_no_keyring=True,
                                 override_no_gnome_keyring=True)
        os.environ['OSC_CONFIG'] = oscrc

    @httpretty.activate
    def test_ring_packages(self):
        """
        Validate the creation of the rings.
        """

        # our content in the XML files
        ring_packages = {'AGGR-antlr': 'openSUSE:Factory:MainDesktops',
                         'Botan': 'openSUSE:Factory:DVD',
                         'DirectFB': 'openSUSE:Factory:Core',
                         'zlib': 'openSUSE:Factory:Build'}

        # Initiate the pretty overrides
        self._register_pretty_url_get('http://localhost/source/openSUSE:Factory:Build',
                                      'build-project.xml')
        self._register_pretty_url_get('http://localhost/source/openSUSE:Factory:Core',
                                      'core-project.xml')
        self._register_pretty_url_get('http://localhost/source/openSUSE:Factory:MainDesktops',
                                      'maindesktops-project.xml')
        self._register_pretty_url_get('http://localhost/source/openSUSE:Factory:DVD',
                                      'dvd-project.xml')

        # Create the api object
        api = oscs.StagingApi('http://localhost')
        self.assertEqual(ring_packages,
                         api.ring_packages)


    @httpretty.activate
    def test_list_projects(self):
        """
        List projects and their content
        """
        prjlist = [
            'openSUSE:Factory:Staging:A',
            'openSUSE:Factory:Staging:B',
            'openSUSE:Factory:Staging:C',
            'openSUSE:Factory:Staging:D'
        ]


        # Initiate the pretty overrides
        self._register_pretty_url_get('http://localhost/search/project/id?match=starts-with(@name,\'openSUSE:Factory:Staging:\')',
                                      'staging-project-list.xml')

        # Initiate the api with mocked rings
        with mock_generate_ring_packages():
            api = oscs.StagingApi('http://localhost')

        # Compare the results
        self.assertEqual(prjlist,
                        api.get_staging_projects())

    @httpretty.activate
    def test_open_requests(self):
        """
        List projects and their content
        """
        requests = [
        ]


        # Initiate the pretty overrides
        self._register_pretty_url_get('http://localhost/search/request?match=state/@name=\'review\'+and+review[@by_group=\'factory-staging\'+and+@state=\'new\']',
                                      'open-requests.xml')

        # Initiate the api with mocked rings
        with mock_generate_ring_packages():
            api = oscs.StagingApi('http://localhost')

        # get the open requests
        requests = api.get_open_requests()
        count = len(requests)

        # Compare the results, we only care now that we got 2 of them not the content
        self.assertEqual(2, count)


# Here place all mockable functions
@contextlib.contextmanager
def mock_generate_ring_packages():
    with mock.patch('oscs.StagingApi._generate_ring_packages', return_value={'AGGR-antlr': 'openSUSE:Factory:MainDesktops',
                         'Botan': 'openSUSE:Factory:DVD',
                         'DirectFB': 'openSUSE:Factory:Core',
                         'zlib': 'openSUSE:Factory:Build'}):
        yield
