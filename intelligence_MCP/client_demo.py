#!/usr/bin/env python3
"""
Demo client for the Business Intelligence MCP Server.

This script demonstrates how to use the MCP server tools to retrieve company information.
It simulates user queries: search for companies and get full profiles.
"""

import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

from src.api_client import CheckoApiClient


async def demo_business_intelligence():
    """Demonstrate business intelligence using the new API client."""

    checko_key = os.getenv("CHECKO_API_KEY")
    dadata_key = os.getenv("DADATA_API_KEY")

    if not checko_key and not dadata_key:
        print("Error: Neither CHECKO_API_KEY nor DADATA_API_KEY found in environment variables.")
        print("Please set at least one API key in a .env file.")
        return

    client = CheckoApiClient(checko_key=checko_key, dadata_key=dadata_key)

    try:
        print("Business Intelligence MCP Server Demo")
        print("Using Checko API primary, DaData as fallback\n")

        search_query = "Тюн ит"
        print(f"Searching for entities with query: '{search_query}'")
        print("="*60)

        entities = await client.search_entity(search_query, "org")
        if entities:
            print(f"Found {len(entities)} entities:")
            for i, entity in enumerate(entities[:6], 1):
                print(f"  {i}. {entity.title} (ИНН: {entity.inn})")
        else:
            print("No entities found")

        print("\n" + "="*60)

        target_inn = "7707083893"
        print(f"Getting full profile for company INN: {target_inn}")
        print("="*60)

        profile = await client.get_company_full_profile(target_inn)

        print("Company profile retrieved successfully!")
        print("\nCompany Details:")
        print(f"   INN: {profile.inn}")
        print(f"   ОГРН: {profile.ogrn}")
        print(f"   Short Name: {profile.short_name}")
        print(f"   Full Name: {profile.full_name}")
        print(f"   Address: {profile.address or 'N/A'}")
        print(f"   Status: {profile.status}")
        if profile.ceo:
            print(f"   CEO: {profile.ceo[0].get('ФИО', 'N/A') if profile.ceo else 'N/A'}")
        print(f"   ОКВЭД: {profile.okved or 'N/A'}")

        if profile.financials:
            print(f"   Financials: {profile.financials.revenue} revenue, {profile.financials.profit} profit")

        if profile.legal_risks:
            print(f"   Legal: {profile.legal_risks.arbitration_cases} arbitration cases")


        print("\nTool Response (JSON summary):")
        summary = {
            "inn": profile.inn,
            "short_name": profile.short_name,
            "status": profile.status,
            "financials": profile.financials.model_dump() if profile.financials else None,
            "legal_risks": profile.legal_risks.model_dump() if profile.legal_risks else None
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))

        print("\n" + "="*60)

        # Scenario 3: Search for entrepreneurs
        entrepreneur_search_query = "Клименков Сергей Викторович"
        print(f"Searching for entrepreneurs with query: '{entrepreneur_search_query}'")
        print("="*60)

        ent_entities = await client.search_entity(entrepreneur_search_query, "ent")
        if ent_entities:
            print(f"Found {len(ent_entities)} entrepreneurs:")
            for i, entity in enumerate(ent_entities[:3], 1):
                print(f"  {i}. {entity.title} (ИНН: {entity.inn})")
        else:
            print("No entrepreneurs found")

        print("\n" + "="*60)

        # Scenario 4: Get entrepreneur profile
        entrepreneur_inn = "691302447182"  # Example entrepreneur INN from search results
        print(f"Getting entrepreneur profile for INN: {entrepreneur_inn}")
        print("="*60)

        try:
            ent_profile = await client.get_entrepreneur_profile(entrepreneur_inn)
            print(" Entrepreneur profile retrieved successfully!")
            print("\n Entrepreneur Details:")
            print(f"   ИНН: {ent_profile.inn}")
            print(f"   ОГРНИП: {ent_profile.ogrnip}")
            print(f"   Full Name: {ent_profile.full_name}")
            print(f"   Status: {ent_profile.status}")
            print(f"   ОКВЭД: {ent_profile.okved}")

            # Show JSON response
            ent_summary = ent_profile.model_dump()
            print("\nTool Response (JSON summary):")
            print(json.dumps(ent_summary, indent=2, ensure_ascii=False))
        except Exception as e2:
            print(f"Entrepreneur profile error: {e2}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(demo_business_intelligence())
