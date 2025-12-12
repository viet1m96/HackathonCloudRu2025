import os
import sys
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


from src.api_client import CheckoApiClient
from src.models import CompanyProfile, EntrepreneurProfile, SearchEntity

class TestCheckoApiClient:

    @pytest_asyncio.fixture
    async def client(self):
        api_client = CheckoApiClient(checko_key="dummy", dadata_key="dummy")
        yield api_client
        await api_client.close()

    @pytest.mark.asyncio
    async def test_search_entity_checko_success(self, client):
        mock_data = {
            "data": {"Записи": [{"НаимСокр": "ООО РОМАШКА", "ИНН": "7700000000", "ОГРН": "123", "РегионКод": "77"}]}
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_data
        mock_resp.raise_for_status.return_value = None

        with patch.object(client.client, 'get', return_value=mock_resp):
            results = await client.search_entity("Ромашка", "org")
            assert len(results) == 1
            assert results[0].title == "ООО РОМАШКА"

    @pytest.mark.asyncio
    async def test_get_company_full_profile_success(self, client):
        mock_data = {
            "data": {
                "ИНН": "7700000000", "ОГРН": "123",
                "Наим": {"Сокр": "ООО ТЕСТ", "Полн": "ООО ТЕСТ ПОЛНОЕ"},
                "Статус": {"Наим": "Действует"},
                "ЮрАдрес": {"АдресРФ": "Адрес"},
                "Руковод": [{"ФИО": "Иванов И.И."}],
                "ФинПоказ": {"Выручка": {"2022": 100}},
                "Арбитраж": {"Количество": 0}, "Блокировка": False
            }
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_data
        mock_resp.raise_for_status.return_value = None

        with patch.object(client.client, 'get', return_value=mock_resp):
            profile = await client.get_company_full_profile("7700000000")
            assert profile.inn == "7700000000"
            assert profile.financials.revenue == {"2022": 100}

    @pytest.mark.asyncio
    async def test_get_entrepreneur_profile_success(self, client):
        mock_data = {
            "data": {
                "ФИО": "ИВАНОВ ИВАН",
                "ИНН": "123456789012",
                "ОГРНИП": "320000",
                "Статус": {"Наим": "Действующий"},
                "ВидДеят": ["62.01"]
            }
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_data
        mock_resp.raise_for_status.return_value = None

        with patch.object(client.client, 'get', return_value=mock_resp):
            profile = await client.get_entrepreneur_profile("123456789012")
            assert profile.inn == "123456789012"
            assert profile.status == {"Наим": "Действующий"}

    @pytest.mark.asyncio
    async def test_fallback_to_dadata(self, client):
        mock_dadata = {
            "suggestions": [{
                "data": {
                    "name": {"short_with_opf": "ООО ЗАПАСНОЙ", "full_with_opf": "ООО ЗАПАСНОЙ"},
                    "ogrn": "111",
                    "address": {"data": {"region_iso_code": "77"}}
                }
            }]
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_dadata
        mock_resp.raise_for_status.return_value = None

        with patch.object(client.client, 'get', side_effect=Exception("Error")):
            with patch.object(client.client, 'post', return_value=mock_resp) as mock_post:
                results = await client.search_entity("7777777777", "org")

                assert len(results) == 1
                assert results[0].title == "ООО ЗАПАСНОЙ"
                assert results[0].inn == "7777777777"
                mock_post.assert_called_once()


class TestModels:
    def test_basic_model(self):
        ent = SearchEntity(title="T", inn="1")
        assert ent.inn == "1"