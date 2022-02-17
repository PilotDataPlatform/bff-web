from app import create_app
from services.logger_services.logger_factory_service import SrvLoggerFactory
import multiprocessing

flaskapp = create_app()
main_logger = SrvLoggerFactory('main').get_logger()

# add to https
# trigger cicd ####

if __name__ == '__main__':
    main_logger.info('Start Flask App')
    main_logger.info('CPU Core: ' + str(multiprocessing.cpu_count()))
    flaskapp.run(debug=True)
