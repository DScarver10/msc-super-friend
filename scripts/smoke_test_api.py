from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> None:
    url = "http://localhost:8000/ask"
    payload = {"question": "What is DHA policy?"}
    data = json.dumps(payload).encode("utf-8")

    req = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print("Status:", resp.status)
            print("Response:", body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print("Status:", exc.code)
        print("Response:", body)
    except URLError as exc:
        print("Request failed:", exc.reason)


if __name__ == "__main__":
    main()
