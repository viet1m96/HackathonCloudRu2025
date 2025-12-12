from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class CompanyFinancials(BaseModel):
    """Финансовые показатели компании из данных Checko API."""

    revenue: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Выручка компании по годам (ключ - год, значение - сумма)."
    )
    profit: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Чистая прибыль компании по годам (ключ - год, значение - сумма)."
    )


class LegalRisks(BaseModel):
    """Юридические риски компании (арбитраж, блокировка счетов)."""

    arbitration_cases: Optional[int] = Field(
        default=None,
        description="Количество арбитражных дел."
    )
    arbitration_amount: Optional[float] = Field(
        default=None,
        description="Общая сумма исков в арбитражных делах."
    )
    blocked_accounts: Optional[bool] = Field(
        default=None,
        description="Наличие заблокированных счетов."
    )


class CompanyProfile(BaseModel):
    """Полное досье юрлица из Checko API."""

    inn: str = Field(
        description="ИНН - Идентификационный номер налогоплательщика (10 цифр)."
    )
    ogrn: str = Field(
        description="ОГРН - Основной государственный регистрационный номер."
    )
    kpp: Optional[str] = Field(
        default=None,
        description="КПП - Код причины постановки на учет."
    )
    short_name: str = Field(
        description="Сокращенное название организации."
    )
    full_name: str = Field(
        description="Полное название организации."
    )
    address: Optional[str] = Field(
        default=None,
        description="Юридический адрес организации."
    )
    status: Dict[str, Any] = Field(
        description="Статус организации (действующее, ликвидировано и т.д.)."
    )
    ceo: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Руководители организации (ФИО, должность)."
    )
    founders: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Учредители/участники организации."
    )
    okved: Optional[str] = Field(
        default=None,
        description="Основной код ОКВЭД."
    )
    financials: Optional[CompanyFinancials] = Field(
        default=None,
        description="Финансовые показатели за прошлые периоды."
    )
    legal_risks: Optional[LegalRisks] = Field(
        default=None,
        description="Юридические риски (арбитраж, блокировка счетов)."
    )
    contacts: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Контактные данные (email, телефон, сайт)."
    )


class EntrepreneurProfile(BaseModel):
    """Досье индивидуального предпринимателя (ИП) из Checko API."""

    inn: str = Field(
        description="ИНН ИП - 12 цифр."
    )
    ogrnip: Optional[str] = Field(
        default=None,
        description="ОГРНИП - Основной государственный регистрационный номер ИП."
    )
    full_name: str = Field(
        description="Полное ФИО индивидуального предпринимателя."
    )
    status: Dict[str, Any] = Field(
        description="Статус ИП (действующий, прекращен)."
    )
    okved: Optional[List[str]] = Field(
        default=None,
        description="Виды деятельности (ОКВЭД) ИП."
    )


class SearchEntity(BaseModel):
    """Краткий результат поиска компании или ИП."""

    title: str = Field(
        description="Название организации или ФИО ИП."
    )
    inn: str = Field(
        description="ИНН организации или ИП."
    )
    ogrn: Optional[str] = Field(
        default=None,
        description="ОГРН юрлица или ОГРНИП для ИП."
    )
    region: Optional[str] = Field(
        default=None,
        description="Регион регистрации."
    )
