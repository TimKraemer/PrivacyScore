# Copyright (C) 2017 PrivacyScore Contributors
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import sys

from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

from privacyscore.backend.models import RawScanResult


class Command(BaseCommand):
    help = 'Cleans up old raw data and removes raw data from filesystem not known to db.'

    def handle(self, *args, **options):
        """Handle command."""
        # remove raw data db entries older than configured max allowed
        outdated = RawScanResult.objects.filter(
            scan__start__lte=timezone.now() - settings.RAW_DATA_DELETE_AFTER)
        deleted = outdated.delete()[0]
        self.stdout.write('Deleted {} database entries'.format(deleted))

        # find files from file system unknown to db
        known_files = [v['file_name'] for v in RawScanResult.objects.filter(
            file_name__isnull=False).values('file_name')]

        deleted = 0
        for file in os.listdir(settings.RAW_DATA_DIR):
            if file not in known_files:
                os.remove(os.path.join(
                    settings.RAW_DATA_DIR, file))
                deleted += 1
        print('Deleted {} files from file system'.format(deleted))

        # find files from db unknown to filesystem
        known_files = os.listdir(settings.RAW_DATA_DIR)
        to_delete = []
        for elem in RawScanResult.objects.filter(
                file_name__isnull=False).values('id', 'file_name'):
            if elem['file_name'] not in known_files:
                to_delete.append(elem['id'])
        deleted = RawScanResult.objects.filter(id__in=to_delete).delete()[0]
        print('Deleted {} db entries unknown in filesystem.'.format(deleted))
