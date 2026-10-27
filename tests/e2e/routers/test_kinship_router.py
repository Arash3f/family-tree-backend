import pytest
from family_tree_api_client import Client
from family_tree_api_client.api.kinship.label_kinship_chain_kinship_label_post import (
    asyncio_detailed as label_chain,
)
from family_tree_api_client.models.kinship_label_request import KinshipLabelRequest
from family_tree_api_client.models.kinship_label_response import KinshipLabelResponse
from family_tree_api_client.models.kinship_step import KinshipStep
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_anyone_can_name_a_chain_without_signing_in(client: Client):
    response = await label_chain(
        client=client,
        body=KinshipLabelRequest(
            steps=[KinshipStep.FATHER, KinshipStep.BROTHER, KinshipStep.SON]
        ),
    )

    assert response.status_code == 200, response.content
    assert isinstance(response.parsed, KinshipLabelResponse)
    assert response.parsed.label_fa == "پسرعمو"
    assert response.parsed.label_en == "paternal uncle's son"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "steps",
    [[], ["father"] * 9, ["cousin"]],
    ids=["empty", "too-long", "unknown-step"],
)
async def test_malformed_chains_are_rejected(asgi_transport: ASGITransport, steps):
    async with AsyncClient(
        transport=asgi_transport, base_url="http://testserver"
    ) as http:
        response = await http.post("/kinship/label", json={"steps": steps})

    assert response.status_code == 422
