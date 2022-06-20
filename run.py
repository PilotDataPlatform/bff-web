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
from app import create_app
from common import LoggerFactory
import multiprocessing

flaskapp = create_app()
main_logger = LoggerFactory('main').get_logger()

# add to https
# trigger cicd ####

if __name__ == '__main__':
    main_logger.info('Start Flask App')
    main_logger.info('CPU Core: ' + str(multiprocessing.cpu_count()))
    flaskapp.run(debug=True)
