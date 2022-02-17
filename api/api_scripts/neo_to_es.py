from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from resources.decorator import check_role
from models.api_response import APIResponse, EAPIResponseCode
from services.logger_services.logger_factory_service import SrvLoggerFactory
from models.api_meta_class import MetaAPI
from config import ConfigClass
import json
import os
import requests
import time 
import datetime 
import math
from models.api_data_manifest import DataAttributeModel, DataManifestModel, TypeEnum, db
from ..api_data_manifest.utils import get_file_node
from api import module_api

_logger = SrvLoggerFactory('api_scripts').get_logger()

api_scripts = module_api.namespace('Script', description='Fetch data from neo4j and import to Elastic Search', path='/v1')


class APINeo4j2ESScript(metaclass=MetaAPI):
    def api_registry(self):
        api_scripts.add_resource(self.Neo4j2ES, '/scripts/neo4j-to-es')
    
    class Neo4j2ES(Resource):
        def get(self):
            neo4j_url = ConfigClass.NEO4J_SERVICE_V2 + 'nodes/query'

            body = {
                "page": 0,
                "page_size": 10,
                "partial": True,
                "order_by": "time_created",
                "order_type": "desc",
                "query": {
                    "labels": ["File"]
                }
            }

            neo4j_res = requests.post(neo4j_url, json=body)
            result = neo4j_res.json()

            neo4j_num = result['total']
            page_size = 100
            entities = result['result']

            pages = math.ceil(neo4j_num / page_size)

            es_entities = []

            for current_page in range(pages):
                body['page_size'] = 1000
                body['page'] = current_page

                neo4j_res = requests.post(neo4j_url, json=body)
                result = neo4j_res.json()

                entities = result['result']

                for item in entities:
                    if 'global_entity_id' not in item:
                        continue

                    labels = item['labels']
                    is_greenrom_raw = False
                    if 'Raw' in labels and 'Greenroom' in labels:
                        is_greenrom_raw = True

                    if 'manifest_id' in item and is_greenrom_raw:
                        manifest_id = item['manifest_id']
                        full_path = item['full_path']

                        attributes = []
                        manifest = db.session.query(DataManifestModel).get(manifest_id)
                        sql_attributes = db.session.query(DataAttributeModel).filter_by(manifest_id=manifest_id)
                        file_node = get_file_node(full_path)

                        for sql_attribute in sql_attributes:
                            attribute_value = file_node.get("attr_" + sql_attribute.name, "")

                            if sql_attribute.type.value == 'multiple_choice':
                                attribute_value = []
                                attribute_value.append(file_node.get("attr_" + sql_attribute.name, ""))

                            attributes.append({
                                "attribute_name": sql_attribute.name,
                                "name": manifest.name,
                                "value": attribute_value,
                            })

                        item['attributes'] = attributes

                    zone = "Greenroom"
                    file_type = "Raw"

                    path = os.path.normpath(item["path"])
                    path_parts = path.split(os.sep)

                    if len(path_parts) < 3:
                        continue
                    
                    project_code = item["project_code"]

                    time_created = datetime.datetime.strptime(item["time_created"], "%Y-%m-%dT%H:%M:%S") 
                    time_created_timestamp = datetime.datetime.timestamp(time_created)

                    time_lastmodified = datetime.datetime.strptime(item["time_lastmodified"], "%Y-%m-%dT%H:%M:%S") 
                    time_lastmodified_timestamp = datetime.datetime.timestamp(time_lastmodified) 

                    archived = False
                    tags = []
                    atlas_guid = ''
                    operator = item["uploader"]
                    process_pipeline = ""

                    if "archived" in item:
                        archived = item["archived"]
                    if "tags" in item:
                        tags = item["tags"]
                    if "guid" in item:
                        atlas_guid = item["guid"]
                    if "operator" in item:
                        operator = item["operator"]
                    if "process_pipeline" in item:
                        process_pipeline = item["process_pipeline"]

                    es_body = {
                        "global_entity_id": item["global_entity_id"],
                        "zone": zone,
                        "data_type": "File",
                        # "file_type": file_type,
                        "operator": operator,
                        "file_size": item["file_size"],
                        "tags": tags,
                        "archived": archived,
                        "path": item["path"],
                        "time_lastmodified": time_lastmodified_timestamp,
                        "process_pipeline": process_pipeline,
                        "uploader": item["uploader"],
                        "file_name": item["name"],
                        "time_created": time_created_timestamp,
                        "atlas_guid": atlas_guid,
                        "full_path": item["full_path"],
                        "dcm_id": item["dcm_id"],
                        "project_code": project_code,
                        "priority": 20
                    }

                    if "attributes" in item:
                        es_body["attributes"] = item["attributes"]

                    es_entities.append(es_body)

                    es_res = requests.post(ConfigClass.PROVENANCE_SERVICE + 'entity/file', json=es_body)
                    print(es_res.json())

            return es_entities
