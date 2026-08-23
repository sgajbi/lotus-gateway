from __future__ import annotations

import re
from importlib.metadata import PackageNotFoundError, version

MIN_HTTPX2_VERSION = (2, 12, 0)
_RELEASE_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:\.\d+)?$")


def parse_version(value: str) -> tuple[int, int, int]:
    match = _RELEASE_VERSION.fullmatch(value)
    if match is None:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())


def main() -> int:
    try:
        installed_version = version("httpx2")
    except PackageNotFoundError:
        print("TestClient dependency check failed: httpx2 is not installed.")
        return 1

    if parse_version(installed_version) < MIN_HTTPX2_VERSION:
        print(
            "TestClient dependency check failed: "
            f"httpx2>={'.'.join(map(str, MIN_HTTPX2_VERSION))} is required, "
            f"but {installed_version} is installed."
        )
        return 1

    try:
        import httpx2
    except Exception as error:
        print(
            "TestClient dependency check failed: importing httpx2 raised "
            f"{error.__class__.__name__}: {error}"
        )
        return 1

    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except Warning as warning:
            print(
                "TestClient dependency check failed: importing FastAPI TestClient emitted "
                f"{warning.__class__.__name__}: {warning}"
            )
            return 1
        except Exception as error:
            print(
                "TestClient dependency check failed: importing FastAPI TestClient raised "
                f"{error.__class__.__name__}: {error}"
            )
            return 1

    print(
        "TestClient dependency check passed: "
        f"httpx2={installed_version} ({httpx2.__name__}); no import warnings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
