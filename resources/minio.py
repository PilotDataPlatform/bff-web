def get_admin_policy(project_code):
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
    return template


def get_collaborator_policy(project_code):
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
    return template


def get_contributor_policy(project_code):
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
    return template
