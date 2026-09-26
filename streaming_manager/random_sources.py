from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

RANDOM_ORG_API_URL = "https://api.random.org/json-rpc/4/invoke"
RANDOM_ORG_MAX_INTEGER = 1_000_000_000


class RandomOrgError(RuntimeError):
    pass


@dataclass(slots=True)
class RandomDraw:
    value: int
    method: str
    serial_number: int | None = None
    ticket_id: str | None = None
    random_object: dict[str, Any] | None = None
    signature: str | None = None
    verified: bool | None = None
    requests_left: int | None = None
    bits_left: int | None = None

    def metadata(self) -> dict[str, Any]:
        return {
            "rng_method": self.method,
            "rng_value": int(self.value),
            "rng_serial_number": self.serial_number,
            "rng_ticket_id": self.ticket_id,
            "rng_random_json": (
                json.dumps(
                    self.random_object,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                if self.random_object is not None
                else None
            ),
            "rng_signature": self.signature,
            "rng_verified": (
                1 if self.verified is True else 0 if self.verified is False else None
            ),
        }

    def verification_url(self) -> str | None:
        if not self.random_object or not self.signature:
            return None
        raw = json.dumps(
            self.random_object,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        encoded = base64.b64encode(raw).decode("ascii")
        return "https://api.random.org/signatures/form?" + urllib.parse.urlencode(
            {
                "format": "json",
                "random": encoded,
                "signature": self.signature,
            }
        )


class RandomOrgClient:
    def __init__(self, api_key: str, timeout: float = 12.0):
        self.api_key = str(api_key or "").strip()
        self.timeout = float(timeout)
        if not self.api_key:
            raise RandomOrgError(
                "API key RANDOM.ORG не задан. Сохраните его во вкладке «Настройки»."
            )

    def _rpc(self, method: str, params: dict[str, Any]) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }
        request = urllib.request.Request(
            RANDOM_ORG_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "StreamingManager-RandomOrg",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = str(exc)
            raise RandomOrgError(
                f"RANDOM.ORG вернул HTTP {exc.code}: {detail}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RandomOrgError(
                f"Не удалось подключиться к RANDOM.ORG: {exc}"
            ) from exc

        try:
            decoded = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RandomOrgError("RANDOM.ORG вернул некорректный JSON.") from exc
        if decoded.get("error") is not None:
            error = decoded.get("error") or {}
            message = error.get("message") or str(error)
            code = error.get("code")
            suffix = f" (код {code})" if code is not None else ""
            raise RandomOrgError(f"RANDOM.ORG: {message}{suffix}")
        if "result" not in decoded:
            raise RandomOrgError("RANDOM.ORG не вернул result.")
        return decoded["result"]

    def get_usage(self) -> dict[str, Any]:
        return dict(self._rpc("getUsage", {"apiKey": self.api_key}))

    def create_ticket(self) -> dict[str, Any]:
        result = self._rpc(
            "createTickets",
            {
                "apiKey": self.api_key,
                "n": 1,
                "showResult": True,
            },
        )
        if not isinstance(result, list) or not result:
            raise RandomOrgError("RANDOM.ORG не вернул созданный билет.")
        ticket = dict(result[0])
        if not ticket.get("ticketId"):
            raise RandomOrgError("RANDOM.ORG вернул билет без ticketId.")
        return ticket

    def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        return dict(self._rpc("getTicket", {"ticketId": str(ticket_id)}))

    def verify_signed_result(self, result: dict[str, Any]) -> bool:
        random_object = result.get("random")
        signature = result.get("signature")
        if not random_object or not signature:
            return False
        response = self._rpc(
            "verifySignature",
            {"random": random_object, "signature": signature},
        )
        return bool((response or {}).get("authenticity"))

    @staticmethod
    def _draw_from_result(
        result: dict[str, Any],
        method: str,
        ticket_id: str | None,
        verified: bool | None,
    ) -> RandomDraw:
        random_object = result.get("random") or {}
        data = random_object.get("data") or []
        if not data:
            raise RandomOrgError("RANDOM.ORG не вернул случайное число.")
        try:
            value = int(data[0])
        except (TypeError, ValueError) as exc:
            raise RandomOrgError("RANDOM.ORG вернул неподдерживаемое число.") from exc
        ticket_data = random_object.get("ticketData") or {}
        effective_ticket = ticket_id or ticket_data.get("ticketId")
        return RandomDraw(
            value=value,
            method=method,
            serial_number=(
                int(random_object["serialNumber"])
                if random_object.get("serialNumber") is not None
                else None
            ),
            ticket_id=effective_ticket,
            random_object=dict(random_object) if random_object else None,
            signature=result.get("signature"),
            verified=verified,
            requests_left=(
                int(result["requestsLeft"])
                if result.get("requestsLeft") is not None
                else None
            ),
            bits_left=(
                int(result["bitsLeft"])
                if result.get("bitsLeft") is not None
                else None
            ),
        )

    def draw_below(
        self,
        upper: int,
        *,
        signed: bool = False,
        ticket_id: str | None = None,
        user_data: dict[str, Any] | None = None,
    ) -> RandomDraw:
        upper = int(upper)
        if upper <= 0:
            raise ValueError("Диапазон случайного числа должен быть больше нуля.")
        if upper - 1 > RANDOM_ORG_MAX_INTEGER:
            raise RandomOrgError(
                "Суммарный вес слишком велик для Integer API RANDOM.ORG: "
                "поддерживается диапазон до 1 000 000 001 значения."
            )
        if signed and not ticket_id:
            raise RandomOrgError("Для Random.org+ отсутствует билет.")

        # Если сервер уже успел использовать билет, но клиент не получил ответ,
        # showResult=true позволяет восстановить ровно тот же Signed result.
        if signed and ticket_id:
            ticket = self.get_ticket(ticket_id)
            existing = ticket.get("result")
            if ticket.get("usedTime") and existing:
                verified = self.verify_signed_result(existing)
                if not verified:
                    raise RandomOrgError(
                        "Восстановленный результат RANDOM.ORG не прошёл проверку подписи."
                    )
                return self._draw_from_result(
                    existing,
                    "random_org_plus",
                    ticket_id,
                    verified,
                )

        method = "generateSignedIntegers" if signed else "generateIntegers"
        params: dict[str, Any] = {
            "apiKey": self.api_key,
            "n": 1,
            "min": 0,
            "max": upper - 1,
            "replacement": True,
            "base": 10,
        }
        if signed:
            params["ticketId"] = ticket_id
            params["userData"] = user_data

        result = dict(self._rpc(method, params))
        verified: bool | None = None
        if signed:
            verified = self.verify_signed_result(result)
            if not verified:
                raise RandomOrgError(
                    "Подпись ответа RANDOM.ORG не прошла проверку."
                )
        return self._draw_from_result(
            result,
            "random_org_plus" if signed else "random_org",
            ticket_id,
            verified,
        )
