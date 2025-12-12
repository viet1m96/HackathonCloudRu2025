import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastmcp import FastMCP

from api_client import CheckoApiClient
from models import SearchEntity, CompanyProfile, EntrepreneurProfile

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

_client: Optional[CheckoApiClient] = None


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Управление жизненным циклом: инициализация при старте, и очистка при выходе."""
    global _client
    checko_key = os.getenv("CHECKO_API_KEY")
    dadata_key = os.getenv("DADATA_API_KEY")

    if not checko_key and not dadata_key:
        logger.warning("No API keys found! Functionality will be limited.")

    logger.info("Initializing CheckoApiClient...")
    _client = CheckoApiClient(checko_key=checko_key, dadata_key=dadata_key)

    yield

    logger.info("Closing CheckoApiClient...")
    if _client:
        await _client.close()


app = FastMCP(
    name="Business Intelligence MCP Server",
    lifespan=lifespan
)


def get_client() -> CheckoApiClient:
    """Helper to ensure client is initialized."""
    if _client is None:
        raise RuntimeError("Client not initialized. Server startup failed?")
    return _client


@app.tool()
async def search_entity(query: str, obj: str) -> str:
    """
    Search for companies and entrepreneurs by name or INN. "obj" must be "org" for organisations and "ent" for entrepreneurs.
    """
    try:
        client = get_client()
        entities = await client.search_entity(query.strip(), obj)
        return [entity.model_dump() for entity in entities] if entities else []
    except Exception as e:
        logger.error(f"Error searching for '{query}': {e}")
        return f"{{\"error\": \"{str(e)}\"}}"


@app.tool()
async def get_company_full_profile(inn: str) -> str:
    """
    Get full business intelligence profile of a company by INN.
    """
    try:
        client = get_client()
        profile = await client.get_company_full_profile(inn.strip())
        return profile.model_dump_json(indent=2)
    except Exception as e:
        logger.error(f"Error getting company profile for INN '{inn}': {e}")
        return f"{{\"error\": \"{str(e)}\"}}"


@app.tool()
async def get_entrepreneur_profile(inn: str) -> str:
    """
    Get profile of an individual entrepreneur (ИП) by INN.
    """
    try:
        client = get_client()
        profile = await client.get_entrepreneur_profile(inn.strip())
        return profile.model_dump_json(indent=2)
    except Exception as e:
        logger.error(f"Error getting entrepreneur profile for INN '{inn}': {e}")
        return f"{{\"error\": \"{str(e)}\"}}"


if __name__ == "__main__":
    app.run()