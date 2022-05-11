import uuid
from minio import Minio
from config import ConfigClass


class Minio_Client():
    '''
    Connect to MinIO
    '''
    def __init__(self):
        self.client = Minio(
            ConfigClass.MINIO_ENDPOINT,
            access_key=ConfigClass.MINIO_ACCESS_KEY,
            secret_key=ConfigClass.MINIO_SECRET_KEY,
            secure=ConfigClass.MINIO_HTTPS
        )



def create_admin_policy(project_code):
    template = '''
    {
        "Version": "2012-10-17",
        "Statement": [
            {
            "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
            "Effect": "Allow",
            "Resource": ["arn:aws:s3:::gr-%s", "arn:aws:s3:::core-%s"]
            },
            {
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Effect": "Allow",
            "Resource": ["arn:aws:s3:::gr-%s/*", "arn:aws:s3:::core-%s/*"]
            }
        ]
    }
    ''' % (project_code, project_code, project_code, project_code)

    template_name = str(uuid.uuid4())+".json"
    policy_file = open(template_name, "w")
    policy_file.write(template)
    policy_file.close()

    return template_name


def create_collaborator_policy(project_code):
    template = '''
    {
        "Version": "2012-10-17",
        "Statement": [
            {
            "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
            "Effect": "Allow",
            "Resource": ["arn:aws:s3:::gr-%s", "arn:aws:s3:::core-%s"]
            },
            {
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Effect": "Allow",
            "Resource": ["arn:aws:s3:::gr-%s/${jwt:preferred_username}/*", "arn:aws:s3:::core-%s/*"]
            }
        ]
    }
    ''' % (project_code, project_code, project_code, project_code)

    template_name = str(uuid.uuid4())+".json"
    policy_file = open(template_name, "w")
    policy_file.write(template)
    policy_file.close()

    return template_name


def create_contributor_policy(project_code):
    template = '''
    {
        "Version": "2012-10-17",
        "Statement": [
            {
            "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
            "Effect": "Allow",
            "Resource": ["arn:aws:s3:::gr-%s", "arn:aws:s3:::core-%s"]
            },
            {
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Effect": "Allow",
            "Resource": ["arn:aws:s3:::gr-%s/${jwt:preferred_username}/*", "arn:aws:s3:::core-%s/${jwt:preferred_username}/*"]
            }
        ]
    }
    ''' % (project_code, project_code, project_code, project_code)

    template_name = str(uuid.uuid4())+".json"
    policy_file = open(template_name, "w")
    policy_file.write(template)
    policy_file.close()

    return template_name
