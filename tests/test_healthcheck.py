from httpx import AsyncClient


async def test_health(async_client: AsyncClient):
    response = await async_client.get("/healthcheck")

    assert response.status_code == 200
