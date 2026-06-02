from unittest.mock import Mock

import app.data_selector as data_selector


def test_handler_processes_items_and_calls_aws_methods():
    # Prepare mocks
    mock_item = {
        'prediction_id': 'pred1',
        'timestamp': 'ts1',
        's3_path': 'inferences/2026/06/01/pred1.jpg',
        'confidence': '0.5',
        'is_labeled': 'False'
    }

    mock_dynamodb = Mock()
    mock_dynamodb.query.return_value = {'Items': [mock_item]}
    mock_dynamodb.update_item.return_value = {}

    mock_s3 = Mock()
    mock_s3.copy_object.return_value = {}

    # Inject mocks into the module
    data_selector.dynamodb = mock_dynamodb
    data_selector.s3 = mock_s3

    result = data_selector.handler({}, {})

    assert result['status'] == 'success'
    assert result['processed'] == 1

    # Verify AWS interactions
    mock_dynamodb.query.assert_called()
    mock_s3.copy_object.assert_called_once()
    mock_dynamodb.update_item.assert_called_once()
