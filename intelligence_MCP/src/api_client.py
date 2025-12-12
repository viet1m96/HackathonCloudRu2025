import logging
from typing import Any, Dict, List, Optional

import httpx
from pydantic import ValidationError

from models import (
    CompanyProfile,
    EntrepreneurProfile,
    SearchEntity,
    CompanyFinancials,
    LegalRisks,
)

logger = logging.getLogger(__name__)


class CheckoApiClient:
    """Asynchronous API client for retrieving company and entrepreneur information from Checko.ru or DaData as fallback."""

    def __init__(self, checko_key: str | None = None, dadata_key: str | None = None):
        self.checko_key = checko_key
        self.dadata_key = dadata_key
        self.checko_base = "https://api.checko.ru/v2"
        self.dadata_base = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _extract_company_financials(self, fin_data: Dict[str, Any]) -> Optional[CompanyFinancials]:
        from .models import CompanyFinancials
        if not fin_data:
            return None
        return CompanyFinancials(
            revenue=fin_data.get('Выручка'),
            profit=fin_data.get('Прибыль')
        )

    def _extract_company_legal_risks(self, data: Dict[str, Any]) -> Optional[LegalRisks]:
        from .models import LegalRisks
        arb = data.get('Арбитраж')
        bloc = data.get('Блокировка')
        if not arb and not bloc:
            return None
        return LegalRisks(
            arbitration_cases=arb.get('Количество') if arb else None,
            arbitration_amount=arb.get('Суммы') if arb else None,
            blocked_accounts=bloc
        )

    async def _request_checko(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Checko API."""
        if not self.checko_key:
            raise ValueError("Checko API key required")
        url = f"{self.checko_base}{endpoint}"
        params = params.copy()
        params['key'] = self.checko_key
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def _request_dadata(self, inn: str) -> Dict[str, Any]:
        """Make request to DaData API for company by INN."""
        if not self.dadata_key:
            raise ValueError("DaData API key required")
        headers = {"Authorization": f"Token {self.dadata_key}"}
        payload = {"query": inn}
        response = await self.client.post(self.dadata_base, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        suggestions = data.get("suggestions", [])
        if not suggestions:
            raise ValueError(f"No company found for INN {inn}")
        return {"data": suggestions[0].get("data", {})}

    async def search_entity(self, query: str, obj: str) -> List[SearchEntity]:
        """Search for companies and entrepreneurs by name or INN."""
        try:
            params = {"query": query, "obj": obj, "by": "name"}
            data = await self._request_checko("/search", params)
            results = data.get('data', {}).get('Записи', [])
        except Exception as e:
            logger.warning(f"Checko search failed: {e}. Trying DaData.")
            if query.isdigit() and len(query) in [10, 12]:
                try:
                    dadata_data = await self._request_dadata(query)
                    d_data = dadata_data["data"]
                    results = [{
                        "НаимСокр": d_data.get("name", {}).get("short_with_opf"),
                        "НаимПолн": d_data.get("name", {}).get("full_with_opf"),
                        "ФИО": d_data.get("name", {}).get("full_with_opf"),
                        "ИНН": query,
                        "ОГРН": d_data.get("ogrn"),
                        "ОГРНИП": d_data.get("ogrn"),
                        "РегионКод": d_data.get("address", {}).get("data", {}).get("region_iso_code") or "Unknown"
                    }]
                except Exception as e2:
                    logger.warning(f"DaData fallback failed: {e2}")
                    results = []
            else:
                results = []

        entities = []
        for item in results:
            try:
                if obj == "ent":
                    title = item.get('ФИО') or item.get('НаимПолн')
                    ogrn = item.get('ОГРНИП') or item.get('ОГРН')
                else:
                    title = item.get('НаимСокр') or item.get('НаимПолн')
                    ogrn = item.get('ОГРН')

                inn = item.get('ИНН')
                region = item.get('РегионКод')

                if not title or not inn:
                    continue

                entity = SearchEntity(title=title, inn=inn, ogrn=ogrn, region=region)
                entities.append(entity)
            except ValidationError as e:
                logger.warning(f"Invalid search result data: {e}")
        return entities

    async def get_company_full_profile(self, inn: str) -> CompanyProfile:
        """Get full company profile by INN."""
        try:
            data = await self._request_checko("/company", {"inn": inn})
            d = data.get('data', data)
            profile = CompanyProfile(
                inn=inn,
                ogrn=d.get('ogrn') or d.get('ОГРН'),
                kpp=d.get('kpp'),
                short_name=d.get('short_name') or (d.get('Наим', {}).get('Сокр')) or "Unknown",
                full_name=d.get('full_name') or (d.get('Наим', {}).get('Полн')) or "Unknown",
                address=d.get('address') or (d.get('ЮрАдрес', {}).get('АдресРФ')),
                status=d.get('status') or d.get('Статус') or {},
                ceo=d.get('ceo') or d.get('Руковод'),
                founders=d.get('founders') or (d.get('Учред') if isinstance(d.get('Учред'), list) else None),
                okved=d.get('okved') or (d.get('ОКВЭД', {}).get('Код') if isinstance(d.get('ОКВЭД'), dict) else d.get('ОКВЭД') or "Unknown"),
                financials=self._extract_company_financials(d.get('ФинПоказ', {})),
                legal_risks=self._extract_company_legal_risks(d),
                contacts=d.get('contacts') or d.get('Контакты'),
            )
        except Exception as e:
            logger.warning(f"Checko company request failed: {e}. Trying DaData.")
            try:
                dadata_data = await self._request_dadata(inn)
                ddata = dadata_data["data"]
                profile = CompanyProfile(
                    inn=inn,
                    ogrn=ddata.get("ogrn"),
                    kpp=ddata.get("kpp"),
                    short_name=ddata.get("name", {}).get("short_with_opf", ""),
                    full_name=ddata.get("name", {}).get("full_with_opf", ""),
                    address=ddata.get("address", {}).get("value"),
                    status={"status": ddata.get("state", {}).get("status", "Unknown")},
                    ceo=[{"name": ddata.get("management", {}).get("name", "")}] if ddata.get("management", {}).get("name") else None,
                    okved=ddata.get("okved"),
                    financials=None,
                    legal_risks=None,
                    contacts=None,
                    founders=None,
                )
            except Exception as e2:
                logger.error(f"Fallback failed: {e2}")
                raise ValueError("Unable to retrieve company data")

        return profile

    async def get_entrepreneur_profile(self, inn: str) -> EntrepreneurProfile:
        """Get entrepreneur profile by INN. No DaData fallback as it doesn't support entrepreneurs."""
        data = await self._request_checko("/entrepreneur", {"inn": inn})
        try:
            d = data.get('data', data)
            profile = EntrepreneurProfile(
                inn=inn,
                ogrnip=d.get('ogrnip') or d.get('ОГРНИП'),
                full_name=d.get('full_name') or d.get('ФИО'),
                status=d.get('status') or d.get('Статус'),
                okved=d.get('okved') or d.get('ВидДеят'),
            )
            return profile
        except ValidationError as e:
            logger.error(f"Validation error for entrepreneur profile: {e}")
            raise ValueError("Invalid entrepreneur data")
