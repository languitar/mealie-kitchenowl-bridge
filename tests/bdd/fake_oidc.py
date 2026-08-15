"""A fake OIDC provider for BDD scenarios, stubbed via `requests_mock`.

Serves a real discovery document, JWKS, and signed `id_token`s (via
`joserfc`, the JOSE library Authlib itself uses internally) so the bridge's
actual Authlib login code - state/nonce handling, token exchange, signature
verification - runs end to end, rather than being mocked away.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlparse

from joserfc import jwt as jose_jwt
from joserfc.jwk import RSAKey

_KID = "fake-oidc-key"


@dataclass
class FakeOidcProvider:
    issuer: str
    client_id: str
    key: RSAKey = field(
        default_factory=lambda: RSAKey.generate_key(2048, parameters={"kid": _KID})
    )

    @property
    def discovery_url(self) -> str:
        return f"{self.issuer}/.well-known/openid-configuration"

    @property
    def authorization_endpoint(self) -> str:
        return f"{self.issuer}/authorize"

    @property
    def token_endpoint(self) -> str:
        return f"{self.issuer}/token"

    @property
    def jwks_uri(self) -> str:
        return f"{self.issuer}/jwks"

    def register(self, requests_mock) -> None:
        """Stub the discovery document and JWKS - stable for the whole test."""
        requests_mock.get(
            self.discovery_url,
            json={
                "issuer": self.issuer,
                "authorization_endpoint": self.authorization_endpoint,
                "token_endpoint": self.token_endpoint,
                "jwks_uri": self.jwks_uri,
                "response_types_supported": ["code"],
                "subject_types_supported": ["public"],
                "id_token_signing_alg_values_supported": ["RS256"],
            },
        )
        requests_mock.get(self.jwks_uri, json={"keys": [self.key.as_dict(private=False)]})

    def stub_successful_login(
        self,
        requests_mock,
        *,
        nonce: str,
        sub: str = "test-user",
        email: str = "test-user@example.com",
    ) -> None:
        """Stub the token endpoint to return a real, signed `id_token` for the given nonce."""
        now = int(time.time())
        claims = {
            "iss": self.issuer,
            "sub": sub,
            "aud": self.client_id,
            "exp": now + 300,
            "iat": now,
            "nonce": nonce,
            "email": email,
        }
        id_token = jose_jwt.encode({"alg": "RS256", "kid": _KID}, claims, self.key)
        requests_mock.post(
            self.token_endpoint,
            json={
                "access_token": "fake-access-token",  # noqa: S106 (test-only fake token)
                "token_type": "Bearer",
                "id_token": id_token,
                "expires_in": 300,
            },
        )


def parse_redirect_query(location: str) -> dict[str, str]:
    """Pull the query parameters (e.g. `state`, `nonce`) off a redirect's Location header."""
    query = parse_qs(urlparse(location).query)
    return {key: values[0] for key, values in query.items()}
