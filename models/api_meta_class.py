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
class MetaAPI(type):
    def __new__(cls, name: str, bases, namespace, **kwargs):
        if not name.startswith('API'):
            raise TypeError('[Fatal] Invalid API Statement: class name should start with "API"', name)
        if 'api_registry' not in namespace:
            raise TypeError('[Fatal] Invalid API Statement: Function api_registry Not Found ', name)
        return super().__new__(cls, name, bases, namespace, **kwargs)