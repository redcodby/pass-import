# -*- encoding: utf-8 -*-
# pass import - Passwords importer swiss army knife
# Copyright (C) 2017-2020 Alexandre PUJOL <alexandre@pujol.io>.
#

import json

from yaml import parse

from pass_import.core import register_managers
from pass_import.formats.csv import CSV
from pass_import.formats.json import JSON


class BitwardenCSV(CSV):
    """Importer for Bitwarden in CSV format."""
    name = 'bitwarden'
    url = 'https://bitwarden.com'
    hexport = 'Tools> Export Vault> File Format: .csv'
    himport = 'pass import bitwarden file.csv'
    keys = {
        'title': 'name',
        'password': 'login_password',
        'login': 'login_username',
        'url': 'login_uri',
        'comments': 'notes',
        'group': 'folder',
        'otpauth': 'login_totp',
    }


class BitwardenJSON(JSON):
    """Importer for Bitwarden in JSON format."""
    name = 'bitwarden'
    default = False
    url = 'https://bitwarden.com'
    hexport = 'Tools> Export Vault> File Format: .json'
    himport = 'pass import bitwarden file.json'
    ignore = {'login', 'id', 'folderId', 'collectionIds', 'organizationId', 'type', 'favorite'}
    nesting_keys = {'card', 'identity'}
    keys = {
        'title': 'name',
        'password': 'password',
        'login': 'username',
        'url': 'uris',
        'otpauth': 'totp',
        'comments': 'notes',
    }
    json_header = {
        'folders': [{
            'id': str,
            'name': str
        }],
        'items': [{
            'id': str,
            'folderId': str,
            'type': int,
            'name': str,
            'favorite': bool,
        }],
    }

    def _sortgroup(self, folders):
        for entry in self.data:
            groupid = entry.get('group', '')
            entry['group'] = folders.get(groupid, '')

    def parse(self):
        """Parse Bitwarden JSON file."""
        jsons = json.loads(self.file.read())
        keys = self.invkeys()
        folders = dict()
        for item in jsons.get('folders', {}):
            key = item.get('id', '')
            folders[key] = item.get('name', '')

        for item in jsons.get('items', {}):
            entry = dict()
            entry['group'] = item.get('folderId', '')
            logins = item.get('login', {})
            item.update(logins)
            for key, value in item.items():
                if key in self.ignore:
                    continue

                if key == 'fields':
                    self.parse_custom_fields(entry, value)
                elif key in self.nesting_keys:
                    self.parse_nested(entry, value)
                else:
                    entry[keys.get(key, key)] = value

            entry['url'] = entry.get('url', [{}])[0].get('uri', '')  # TODO: vivlim handle multiple urls
            self.data.append(entry)
        self._sortgroup(folders)

    def parse_nested(self, destination_entry, nesting_source):
        for key, value in nesting_source.items():
            destination_entry[key] = value

    def parse_custom_fields(self, destination_entry, custom_fields):
        for field in custom_fields:
            destination_entry[field['name']] = field['value']

register_managers(BitwardenCSV, BitwardenJSON)
