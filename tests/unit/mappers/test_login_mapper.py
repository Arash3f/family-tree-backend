from app.application.dto.auth_dto import LoginMapper


def test_login_mapper_to_response():
    access_token = "access_token_example"
    refresh_token = "refresh_token_example"

    dto = LoginMapper.to_response(access_token, refresh_token)

    assert dto.access_token == access_token
    assert dto.refresh_token == refresh_token
