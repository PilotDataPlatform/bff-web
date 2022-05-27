import pytest
from uuid import uuid4
from config import ConfigClass

MOCK_FILE_DATA = {
    'archived': False,
    'container_code': 'test_project',
    'container_type': 'project',
    'created_time': '2021-05-10 19:43:55.382824',
    'extended': {
        'extra': {
            'attributes': {},
            'system_tags': [],
            'tags': []
        },
        'id': str(uuid4())
    },
    'id': str(uuid4()),
    'last_updated_time': '2021-05-10 19:43:55.383021',
    'name': 'jiang_folder_2',
    'owner': 'admin',
    'parent': str(uuid4()),
    'parent_path': 'test',
    'restore_path': None,
    'size': 0,
    'storage': {
        'id': str(uuid4()),
        'location_uri': None,
        'version': None
    },
    'type': 'folder',
    'zone': 1
}

MOCK_FILE_DATA_2 = {
    'archived': False,
    'container_code': 'test_project',
    'container_type': 'project',
    'created_time': '2021-05-10 19:43:55.382824',
    'extended': {
        'extra': {
            'attributes': {},
            'system_tags': [],
            'tags': []
        },
        'id': str(uuid4())
    },
    'id': str(uuid4()),
    'last_updated_time': '2021-05-10 19:43:55.383021',
    'name': 'new_file.txt',
    'owner': 'admin',
    'parent': str(uuid4()),
    'parent_path': 'test',
    'restore_path': None,
    'size': 0,
    'storage': {
        'id': str(uuid4()),
        'location_uri': None,
        'version': None
    },
    'type': 'file',
    'zone': 1
}

template_id = '3f73f4d4-82e7-4269-8d2e-3c8c678a6b05'

MOCK_TEMPLATE_DATA = {
    'id': template_id,
    'name': 'Template01',
    'project_code': 'test_project',
    'attributes': [
        {
            'name': 'attr1',
            'optional': True,
            'type': 'multiple_choice',
            'options': [
                'A',
                'B',
                'C'
            ]
        }
    ]
}


def test_list_templates_admin_200(test_client, requests_mocker, jwt_token_admin):
    mock_data = {'result': {'has_permission': 'True'}}
    requests_mocker.get(ConfigClass.AUTH_SERVICE + 'authorize', json=mock_data)

    mock_data = {
        'result': [
            MOCK_TEMPLATE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + 'template/', json=mock_data)

    params = {'project_code': 'test_project'}
    headers = {'Authorization': jwt_token_admin}
    response = test_client.get('v1/data/templates', query_string=params, headers=headers)
    assert response.status_code == 200


def test_create_new_templates_admin_200(test_client, requests_mocker, jwt_token_admin):
    mock_data = {'result': {'has_permission': 'True'}}
    requests_mocker.get(ConfigClass.AUTH_SERVICE + 'authorize', json=mock_data)

    mock_data = {
        'result': [
            MOCK_TEMPLATE_DATA
        ]
    }
    requests_mocker.post(ConfigClass.METADATA_SERVICE + 'template/', json=mock_data)

    headers = {'Authorization': jwt_token_admin}
    response = test_client.post('v1/data/templates', json=MOCK_TEMPLATE_DATA, headers=headers)
    assert response.status_code == 200


def test_get_template_by_id_admin_200(test_client, requests_mocker, jwt_token_admin):
    mock_data = {'result': {'has_permission': 'True'}}
    requests_mocker.get(ConfigClass.AUTH_SERVICE + 'authorize', json=mock_data)

    mock_data = {
        'result': [
            MOCK_TEMPLATE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'template/{template_id}/', json=mock_data)

    headers = {'Authorization': jwt_token_admin}
    response = test_client.get(f'v1/data/template/{template_id}', headers=headers)
    assert response.status_code == 200


def test_get_template_by_invalid_id_admin_404(test_client, requests_mocker, jwt_token_admin):
    invalid_id = '1234'
    mock_data = {'result': {'has_permission': 'True'}}
    requests_mocker.get(ConfigClass.AUTH_SERVICE + 'authorize', json=mock_data)

    mock_data = {
        'result': [
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'template/{invalid_id}/', json=mock_data)

    headers = {'Authorization': jwt_token_admin}
    response = test_client.get(f'v1/data/template/{invalid_id}', headers=headers)
    assert response.status_code == 404


def test_update_template_attributes_admin_200(test_client, requests_mocker, jwt_token_admin,
                                              has_permission_true):
    MOCK_TEMPLATE_UPDATE = MOCK_TEMPLATE_DATA.copy()
    MOCK_TEMPLATE_UPDATE['attributes'][0]['name'] = 'attr2'
    mock_data = {
        'result': [
            MOCK_TEMPLATE_UPDATE
        ]
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + 'template/', json=mock_data)

    headers = {'Authorization': jwt_token_admin}
    response = test_client.put(f'v1/data/template/{template_id}', json=MOCK_TEMPLATE_UPDATE, headers=headers)
    assert response.status_code == 200


def test_update_template_attributes_permission_denied_403(test_client, requests_mocker, jwt_token_contrib,
                                                          has_permission_false):
    MOCK_TEMPLATE_UPDATE = MOCK_TEMPLATE_DATA.copy()
    MOCK_TEMPLATE_UPDATE['attributes'][0]['name'] = 'attr2'
    mock_data = {
        'result': [
            MOCK_TEMPLATE_UPDATE
        ]
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + 'template/', json=mock_data)

    headers = {'Authorization': jwt_token_contrib}
    response = test_client.put(f'v1/data/template/{template_id}', json=MOCK_TEMPLATE_UPDATE, headers=headers)
    assert response.status_code == 403


def test_delete_template_by_id_admin_200(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    mock_data = {
        'result': [
        ]
    }
    requests_mocker.delete(ConfigClass.METADATA_SERVICE + f'template/?id={template_id}', json=mock_data)

    payload = {'project_code': 'test_project'}
    headers = {'Authorization': jwt_token_admin}
    response = test_client.delete(f'v1/data/template/{template_id}', json=payload, headers=headers)
    assert response.status_code == 200


def test_delete_template_by_id_permission_denied_403(test_client, jwt_token_contrib, has_permission_false):
    payload = {'project_code': 'test_project'}
    headers = {'Authorization': jwt_token_contrib}
    response = test_client.delete(f'v1/data/template/{template_id}', json=payload, headers=headers)
    assert response.status_code == 403


def test_update_template_attributes_of_file_admin_200(test_client, requests_mocker, jwt_token_admin,
                                                      has_permission_true):
    MOCK_FILE_DATA_ATTR = MOCK_FILE_DATA.copy()
    # mock get item by id
    mock_data = {
        'result': MOCK_FILE_DATA_ATTR
    }
    file_id = MOCK_FILE_DATA_ATTR['id']
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'item/{file_id}', json=mock_data)

    # mock update item attributes by id
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'B'}}
    mock_data = {
        'result': [
            MOCK_FILE_DATA_ATTR
        ]
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + f'item/?id={file_id}', json=mock_data)

    headers = {'Authorization': jwt_token_admin}
    response = test_client.put(f'v1/file/{file_id}/template', json={'attr1': 'B'}, headers=headers)
    assert response.status_code == 200


def test_update_template_attributes_of_file_permission_denied_contrib_403(test_client, requests_mocker,
                                                                          jwt_token_contrib):
    MOCK_FILE_DATA_ATTR = MOCK_FILE_DATA.copy()
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'C'}}
    # mock get item by id
    mock_data = {
        'result': MOCK_FILE_DATA_ATTR
    }
    file_id = MOCK_FILE_DATA_ATTR['id']
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'item/{file_id}', json=mock_data)

    headers = {'Authorization': jwt_token_contrib}
    response = test_client.put(f'v1/file/{file_id}/template', json={'attr1': 'B'}, headers=headers)
    assert response.status_code == 403


def test_update_template_attributes_of_file_permission_denied_admin_403(test_client, requests_mocker,
                                                                        jwt_token_admin, has_permission_false):
    MOCK_FILE_DATA_ATTR = MOCK_FILE_DATA.copy()
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'C'}}
    # mock get item by id
    mock_data = {
        'result': MOCK_FILE_DATA_ATTR
    }
    file_id = MOCK_FILE_DATA_ATTR['id']
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'item/{file_id}', json=mock_data)

    headers = {'Authorization': jwt_token_admin}
    response = test_client.put(f'v1/file/{file_id}/template', json={'attr1': 'B'}, headers=headers)
    assert response.status_code == 403


def test_import_template_admin_200(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    mock_data = {'result': {'has_permission': 'True'}}
    requests_mocker.get(ConfigClass.AUTH_SERVICE + 'authorize', json=mock_data)

    mock_data = {
        'result': [
            MOCK_TEMPLATE_DATA
        ]
    }
    requests_mocker.post(ConfigClass.METADATA_SERVICE + 'template/', json=mock_data)

    headers = {'Authorization': jwt_token_admin}
    response = test_client.post('v1/import/template', json=MOCK_TEMPLATE_DATA, headers=headers)
    assert response.status_code == 200


def test_export_template_admin_200(test_client, requests_mocker, jwt_token_admin):
    mock_data = {'result': {'has_permission': 'True'}}
    requests_mocker.get(ConfigClass.AUTH_SERVICE + 'authorize', json=mock_data)

    mock_data = {
        'result': [
            MOCK_TEMPLATE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'template/{template_id}/', json=mock_data)

    headers = {'Authorization': jwt_token_admin}
    params = {'template_id': template_id}
    response = test_client.get(f'v1/export/template', query_string=params, headers=headers)
    assert response.status_code == 200


def test_list_file_template_attributes_admin_200(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    MOCK_FILE_DATA_ATTR = MOCK_FILE_DATA.copy()
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    file_id = MOCK_FILE_DATA['id']

    # get item by id
    mock_data = {
        'result': MOCK_FILE_DATA_ATTR
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'item/{file_id}', json=mock_data)

    # get template
    mock_data = {
        'result': [
            MOCK_TEMPLATE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'template/{template_id}/', json=mock_data)

    headers = {'Authorization': jwt_token_admin}
    payload = {'geid_list': [file_id]}
    response = test_client.post(f'v1/file/template/query', json=payload, headers=headers)
    assert response.status_code == 200


def test_list_file_template_attributes_permission_denied_contrib_403(test_client, requests_mocker, jwt_token_contrib,
                                                                     has_permission_false):
    MOCK_FILE_DATA_ATTR = MOCK_FILE_DATA.copy()
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    file_id = MOCK_FILE_DATA['id']

    # get item by id
    mock_data = {
        'result': MOCK_FILE_DATA_ATTR
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'item/{file_id}', json=mock_data)

    headers = {'Authorization': jwt_token_contrib}
    payload = {'geid_list': [file_id]}
    response = test_client.post(f'v1/file/template/query', json=payload, headers=headers)
    assert response.status_code == 403


def test_list_file_template_attributes_template_not_found_contrib_404(test_client, requests_mocker, jwt_token_contrib,
                                                                      has_permission_true):
    MOCK_FILE_DATA_ATTR = MOCK_FILE_DATA.copy()
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    file_id = MOCK_FILE_DATA['id']

    # get item by id
    mock_data = {
        'result': MOCK_FILE_DATA_ATTR
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'item/{file_id}', json=mock_data)

    # get template
    mock_data = {}
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'template/{template_id}/', json=mock_data, status_code=404)

    headers = {'Authorization': jwt_token_contrib}
    payload = {'geid_list': [file_id]}
    response = test_client.post(f'v1/file/template/query', json=payload, headers=headers)
    assert response.status_code == 404


def test_attach_attributes_to_file_contrib_missing_attributes_field_400(test_client, requests_mocker,
                                                                        jwt_token_contrib):
    headers = {'Authorization': jwt_token_contrib}
    payload = {
        'item_ids': [MOCK_FILE_DATA['id']],
        'template_id': template_id,
        'project_code': MOCK_FILE_DATA['container_code'],
    }
    response = test_client.post(f'v1/file/attributes/attach', json=payload, headers=headers)
    assert response.status_code == 400


def test_attach_attributes_to_file_contrib_invalid_role_field_403(test_client, requests_mocker,
                                                                  jwt_token_contrib, has_invalid_project_role):
    headers = {'Authorization': jwt_token_contrib}
    payload = {
        'item_ids': [MOCK_FILE_DATA['id']],
        'template_id': template_id,
        'project_code': MOCK_FILE_DATA['container_code'],
        'attributes': {'attr1': 'A'}
    }
    response = test_client.post(f'v1/file/attributes/attach', json=payload, headers=headers)
    assert response.status_code == 403


def test_attach_attributes_to_folder_contrib_200(test_client, requests_mocker,
                                                 jwt_token_contrib, has_permission_true, has_project_contributor_role):
    # get item by id
    file_id = MOCK_FILE_DATA['id']
    mock_data = {
        'result': MOCK_FILE_DATA
    }

    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'item/{file_id}', json=mock_data)

    # update attributes for folder (bequeath)
    MOCK_FILE_DATA_ATTR = MOCK_FILE_DATA.copy()
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    mock_data = {
        'result': MOCK_FILE_DATA_ATTR
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + 'items/batch/bequeath/', json=mock_data)
    headers = {'Authorization': jwt_token_contrib}
    payload = {
        'item_ids': [MOCK_FILE_DATA['id']],
        'template_id': template_id,
        'project_code': MOCK_FILE_DATA['container_code'],
        'attributes': {'attr1': 'A'}
    }
    response = test_client.post(f'v1/file/attributes/attach', json=payload, headers=headers)
    assert response.status_code == 200


def test_attach_attributes_to_folder_failed_contrib_500(test_client, requests_mocker,
                                                         jwt_token_contrib, has_permission_true,
                                                         has_project_contributor_role):
    # get item by id
    file_id = MOCK_FILE_DATA['id']
    mock_data = {
        'result': MOCK_FILE_DATA
    }

    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'item/{file_id}', json=mock_data)

    # update attributes for folder (bequeath)
    MOCK_FILE_DATA_ATTR = MOCK_FILE_DATA.copy()
    MOCK_FILE_DATA_ATTR['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    mock_data = {}
    requests_mocker.put(ConfigClass.METADATA_SERVICE + 'items/batch/bequeath/', json=mock_data, status_code=500)
    headers = {'Authorization': jwt_token_contrib}
    payload = {
        'item_ids': [MOCK_FILE_DATA['id']],
        'template_id': template_id,
        'project_code': MOCK_FILE_DATA['container_code'],
        'attributes': {'attr1': 'A'}
    }
    response = test_client.post(f'v1/file/attributes/attach', json=payload, headers=headers)
    assert response.status_code == 500


def test_attach_attributes_to_file_and_folder_contrib_200(test_client, requests_mocker,
                                                          jwt_token_contrib, has_permission_true,
                                                          has_project_contributor_role):
    MOCK_FILE_DATA_ATTR_1 = MOCK_FILE_DATA.copy()
    MOCK_FILE_DATA_ATTR_2 = MOCK_FILE_DATA_2.copy()

    # get item by id
    file_id_1 = MOCK_FILE_DATA_ATTR_1['id']
    mock_data_folder = {
        'result': MOCK_FILE_DATA_ATTR_1
    }
    file_id_2 = MOCK_FILE_DATA_ATTR_2['id']
    mock_data_file = {
        'result': MOCK_FILE_DATA_ATTR_2
    }

    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'item/{file_id_1}', json=mock_data_folder)
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'item/{file_id_2}', json=mock_data_file)

    # update attributes for folder (bequeath)
    MOCK_FILE_DATA_ATTR_1['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    mock_data = {
        'result': MOCK_FILE_DATA_ATTR_1
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + 'items/batch/bequeath/', json=mock_data)

    # update attributes for file
    MOCK_FILE_DATA_ATTR_2['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    mock_data2 = {
        'result': [
            MOCK_FILE_DATA_ATTR_2
        ]
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + 'items/batch/', json=mock_data2)

    headers = {'Authorization': jwt_token_contrib}
    payload = {
        'item_ids': [MOCK_FILE_DATA['id'], MOCK_FILE_DATA_2['id']],
        'template_id': template_id,
        'project_code': MOCK_FILE_DATA['container_code'],
        'attributes': {'attr1': 'A'}
    }
    response = test_client.post(f'v1/file/attributes/attach', json=payload, headers=headers)
    assert response.status_code == 200


def test_attach_attributes_to_file_failed_contrib_500(test_client, requests_mocker,
                                                          jwt_token_contrib, has_permission_true,
                                                          has_project_contributor_role):
    MOCK_FILE_DATA_ATTR_1 = MOCK_FILE_DATA.copy()
    MOCK_FILE_DATA_ATTR_2 = MOCK_FILE_DATA_2.copy()

    # get item by id
    file_id_1 = MOCK_FILE_DATA_ATTR_1['id']
    mock_data_folder = {
        'result': MOCK_FILE_DATA_ATTR_1
    }
    file_id_2 = MOCK_FILE_DATA_ATTR_2['id']
    mock_data_file = {
        'result': MOCK_FILE_DATA_ATTR_2
    }

    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'item/{file_id_1}', json=mock_data_folder)
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f'item/{file_id_2}', json=mock_data_file)

    # update attributes for folder (bequeath)
    MOCK_FILE_DATA_ATTR_1['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    mock_data = {
        'result': MOCK_FILE_DATA_ATTR_1
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + 'items/batch/bequeath/', json=mock_data)

    # update attributes for file
    MOCK_FILE_DATA_ATTR_2['extended']['extra']['attributes'] = {template_id: {'attr1': 'A'}}
    mock_data2 = {}
    requests_mocker.put(ConfigClass.METADATA_SERVICE + 'items/batch/', json=mock_data2, status_code=500)

    headers = {'Authorization': jwt_token_contrib}
    payload = {
        'item_ids': [MOCK_FILE_DATA['id'], MOCK_FILE_DATA_2['id']],
        'template_id': template_id,
        'project_code': MOCK_FILE_DATA['container_code'],
        'attributes': {'attr1': 'A'}
    }
    response = test_client.post(f'v1/file/attributes/attach', json=payload, headers=headers)
    assert response.status_code == 500