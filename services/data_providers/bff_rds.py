from config import ConfigClass
from psycopg2 import pool
from models.service_meta_class import MetaService
from services.logger_services.logger_factory_service import SrvLoggerFactory

provider_rds_pool_cache = None

class SrvRDSSingleton(metaclass=MetaService):
    def __init__(self):
        global provider_rds_pool_cache
        if provider_rds_pool_cache:
            self.pool = provider_rds_pool_cache
        else:
            provider_rds_pool_cache = rds_connection_pool_factory()
            self.pool = provider_rds_pool_cache

    def simple_query(self, query, sql_params={}, iffetch=True, iffetchone=False):
        '''
        Simple Query Executor, Singleton Pool Version, Not Close Connection, But Will End Transaction Right After the Execution, Close Cursor
        ## default fetch all results [()]
        ## No Record Returns []
        '''
        conn = self.pool.getconn()
        res = postgre_simple_querier(conn, query, sql_params, iffetch, iffetchone)
        self.pool.putconn(conn)
        return res
    def close(self):
        global provider_rds_pool_cache
        self.pool.closeall()
        provider_rds_pool_cache = None

def rds_connection_pool_factory():
    _logger = SrvLoggerFactory('SrvRDSSingleton').get_logger()
    my_host = ConfigClass.RDS_HOST
    my_port = ConfigClass.RDS_PORT
    my_dbname = ConfigClass.RDS_DBNAME
    my_user = ConfigClass.RDS_USER
    my_pass = ConfigClass.RDS_PWD
    try:
        my_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            user=my_user,
            password=my_pass,
            host=my_host,
            port=my_port,
            database=my_dbname
        )
        _logger.info('Initiated RDS Pool')
        return my_pool
    except Exception as e:
        _logger.critical("Error when initiating RDS pool: " + str(e))
        raise

def postgre_simple_querier(conn, query, sql_params, iffetch=True, iffetchone=False ):
    '''
    Simple Query Executor, Not Close Connection, But Will End Transaction Right After the Execution, Close Cursor
    ## default fetch all results [()]
    ## No Record Returns []
    '''
    _logger = SrvLoggerFactory('SrvRDSSingleton').get_logger()
    cursor = conn.cursor()
    try:
        fetched = []
        cursor.execute(query, sql_params)
        if iffetch:
            fetched = cursor.fetchone() if iffetchone else cursor.fetchall()
        conn.commit()
        cursor.close()
        return fetched
    except Exception as e:
        conn.rollback()
        cursor.close()
        _logger.error('[POSGRE_SIMPLE_QUERY]: ' + 'Failed' + query)
        _logger.error('[POSGRE_SIMPLE_QUERY]: Robacked------' + str(e))
        raise
