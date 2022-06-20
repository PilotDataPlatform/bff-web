# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
class ContactUsForm:
    def __init__(self, event=None):
        if event:
            self._attribute_map = event
        else:
            self._attribute_map = {
                'email': '',  # by default success
                'category': '',  # empty when success
                'description': '',
                'name': '',
                'title': '',
                'attachments': [],
            }

    @property
    def to_dict(self):
        return self._attribute_map

    @property
    def email(self):
        return self._attribute_map['email']

    @email.setter
    def email(self, email):
        self._attribute_map['email'] = email

    @property
    def category(self):
        return self._attribute_map['category']

    @category.setter
    def category(self, category):
        self._attribute_map['category'] = category

    @property
    def description(self):
        return self._attribute_map['description']

    @description.setter
    def description(self, description):
        self._attribute_map['description'] = description


    @property
    def name(self):
        return self._attribute_map['name']

    @name.setter
    def name(self, name):
        self._attribute_map['name'] = name


    @property
    def title(self):
        return self._attribute_map['title']

    @title.setter
    def title(self, title):
        self._attribute_map['title'] = title

    @property
    def attachments(self):
        return self._attribute_map.get('attachments', [])

    @attachments.setter
    def attachments(self, attachments):
        self._attribute_map['attachments'] = attachments
