import tempfile

import pydantic
import pytest
import yaml

from monitor.serializers.settings import MonitorSettings, WebsiteSetting


def test_valid_yaml():
    test_data = {
        'db': {
            'period': 10,
            'max_batch_size': 100,
        },
        'websites': [
            {
                'url': 'https://foo.com/',
                'period': 10,
            },
            {
                'url': 'http://bar.com/',
                'period': 5.5,
                'regexp': 'bar',
            }
        ]
    }

    with tempfile.TemporaryFile(mode='w+') as temp_file:
        test_yaml = yaml.dump(data=test_data)
        temp_file.write(test_yaml)
        temp_file.seek(0)
        data = yaml.load(stream=temp_file, Loader=yaml.Loader)
        settings = MonitorSettings(**data)
        for i, website in enumerate(test_data['websites']):
            assert str(settings.websites[i].url) == website['url']
            assert settings.websites[i].period == float(website['period'])
            assert settings.websites[i].regexp == website.get('regexp', '')


@pytest.mark.parametrize('invalid_url', ('foo', '123'))
def test_invalid_url(invalid_url: str):
    data = {
        'url': invalid_url,
        'period': 10
    }
    with pytest.raises(pydantic.ValidationError):
        _ = WebsiteSetting(**data)


@pytest.mark.parametrize('invalid_period', (
        pytest.param(4, id='too_low'),
        pytest.param(301, id='too_high'),
))
def test_invalid_period(invalid_period: float):
    data = {
        'url': 'https://foo.com',
        'period': invalid_period
    }
    with pytest.raises(pydantic.ValidationError):
        _ = WebsiteSetting(**data)
