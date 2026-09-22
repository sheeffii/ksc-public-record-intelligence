"""Provider-neutral structured generation for citation-first research.

Providers receive only the whitelisted retrieval snapshots. Source text is
delimited as untrusted data and can never supply system instructions.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderSource:
    id: str
    category: str
    ref: str
    citation: str
    text: str


@dataclass(frozen=True)
class ProviderClaim:
    kind: str
    text: str
    content_type: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class ProviderRequest:
    question: str
    system_prompt: str
    sources: tuple[ProviderSource, ...]
    temperature: float


@dataclass(frozen=True)
class ProviderResponse:
    claims: tuple[ProviderClaim, ...]
    input_tokens: int | None = None
    output_tokens: int | None = None
    raw: dict[str, Any] | None = None


class AiProvider(Protocol):
    name: str
    model: str

    def generate(self, request: ProviderRequest) -> ProviderResponse: ...


class ProviderError(RuntimeError):
    pass


_KIND_BY_CATEGORY = {
    "court_finding": "court",
    "witness_testimony": "testimony",
    "spo_argument": "spo",
    "defence_argument": "defence",
    "document_exhibit": "evidence",
    "court_response": "court_response",
    "human_note": "human_note",
}
_KIND_ORDER = {
    "court": 0,
    "evidence": 1,
    "testimony": 2,
    "spo": 3,
    "defence": 4,
    "court_response": 5,
    "human_note": 6,
}
SAFE_ANALYSIS_TEXT = (
    "The available record indicates that the retrieved, source-labelled passages "
    "address the question. The controlled corpus does not establish anything beyond "
    "those passages."
)


class DeterministicExtractiveProvider:
    """Offline quality-gate provider: quotes retrieved text and adds no record fact."""

    name = "deterministic"
    model = "citation-first-extractive-v1"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        first_by_kind: dict[str, ProviderSource] = {}
        for source in request.sources:
            kind = _KIND_BY_CATEGORY.get(source.category)
            if kind is not None and kind not in first_by_kind:
                first_by_kind[kind] = source
        claims = [
            ProviderClaim(
                kind=kind,
                text=source.text,
                content_type="verbatim_quote",
                source_ids=(source.id,),
            )
            for kind, source in sorted(first_by_kind.items(), key=lambda item: _KIND_ORDER[item[0]])
        ]
        claims.append(
            ProviderClaim(
                kind="ai",
                text=SAFE_ANALYSIS_TEXT,
                content_type="ai_analysis",
                source_ids=tuple(source.id for source in request.sources),
            )
        )
        return ProviderResponse(claims=tuple(claims), raw={"mode": "deterministic_extractive"})


def _parse_structured(content: str, raw: dict[str, Any], usage: dict[str, Any]) -> ProviderResponse:
    try:
        payload = json.loads(content)
        claims = tuple(
            ProviderClaim(
                kind=str(item["kind"]),
                text=str(item["text"]),
                content_type=str(item["content_type"]),
                source_ids=tuple(str(value) for value in item["source_ids"]),
            )
            for item in payload["claims"]
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ProviderError("provider returned invalid structured output") from exc
    return ProviderResponse(
        claims=claims,
        input_tokens=_optional_int(usage.get("prompt_tokens") or usage.get("input_tokens")),
        output_tokens=_optional_int(usage.get("completion_tokens") or usage.get("output_tokens")),
        raw=raw,
    )


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) and value >= 0 else None


class _HttpJsonProvider:
    name: str

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        model: str,
        timeout: float = 30,
        max_output_tokens: int = 1600,
        max_retries: int = 1,
    ) -> None:
        if not endpoint or not api_key or not model:
            raise ProviderError(f"{self.name} provider is not fully configured")
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_output_tokens = max_output_tokens
        self.max_retries = max_retries

    def _post(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        request = urllib.request.Request(  # noqa: S310 - configured provider endpoint
            self.endpoint,
            data=json.dumps(payload).encode(),
            headers={"content-type": "application/json", **headers},
            method="POST",
        )
        last_error: Exception | None = None
        for _ in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(  # noqa: S310 - allowlisted by production settings
                    request, timeout=self.timeout
                ) as response:
                    body = json.loads(response.read())
                break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
        else:
            raise ProviderError(f"{self.name} provider request failed") from last_error
        if not isinstance(body, dict):
            raise ProviderError(f"{self.name} provider returned a non-object response")
        return body


def _untrusted_context(sources: tuple[ProviderSource, ...]) -> str:
    return json.dumps(
        [
            {
                "source_id": source.id,
                "category": source.category,
                "ref": source.ref,
                "citation": source.citation,
                "untrusted_source_text": source.text,
            }
            for source in sources
        ],
        ensure_ascii=False,
    )


class OpenAiCompatibleProvider(_HttpJsonProvider):
    name = "openai_compatible"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        body = self._post(
            {
                "model": self.model,
                "temperature": request.temperature,
                "max_tokens": self.max_output_tokens,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": request.system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "question": request.question,
                                "sources": _untrusted_context(request.sources),
                            }
                        ),
                    },
                ],
            },
            {"authorization": f"Bearer {self.api_key}"},
        )
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("OpenAI-compatible response has no message content") from exc
        return _parse_structured(str(content), body, body.get("usage", {}))


class AnthropicCompatibleProvider(_HttpJsonProvider):
    name = "anthropic_compatible"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        body = self._post(
            {
                "model": self.model,
                "temperature": request.temperature,
                "max_tokens": self.max_output_tokens,
                "system": request.system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "question": request.question,
                                "sources": _untrusted_context(request.sources),
                            }
                        ),
                    }
                ],
            },
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
        )
        try:
            content = body["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Anthropic-compatible response has no text content") from exc
        return _parse_structured(str(content), body, body.get("usage", {}))
