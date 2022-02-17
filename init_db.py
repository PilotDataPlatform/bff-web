from app import create_app, db
from config import ConfigClass
#from models.api_data_manifest import DataManifestModel, DataAttributeModel
from models.api_resource_request import ResourceRequest

app = create_app()
with app.app_context():
    #DataManifestModel.__table__.create(db.session.bind)
    #DataAttributeModel.__table__.create(db.session.bind)
    ResourceRequest.__table__.create(db.session.bind)
    print("SUCCESS")

