"""Read-only private identity inventory; no account, role or adoption mutation."""

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from uuid import UUID


def _imports() -> None:
    root = Path(__file__).resolve().parents[1]
    for path in (str(root), str(root / "backend")):
        if path not in sys.path:
            sys.path.insert(0, path)


def run(private_configuration: Path, output: Path) -> dict[str, Any]:
    _imports()
    from business_app.db import Database
    from business_app.permissions.generation_manifest import _read_private, _unique
    from business_app.task_creation_identity_inventory import IdentityInventoryRequest, observe_identity_inventory

    from scripts.task_creation_adoption import _output_path, _save_prepared

    _output_path(output)
    value = json.loads(_read_private(private_configuration).decode("utf8"), object_pairs_hook=_unique)
    fields = {"database_dsn", "issuer", "subject", "user_id", "org_id", "case_id"}
    if type(value) is not dict or set(value) != fields or any(type(item) is not str for item in value.values()):
        raise ValueError("TASK_IDENTITY_INVENTORY_INVALID")
    if not value["database_dsn"] or len(value["database_dsn"].encode("utf8")) > 8192:
        raise ValueError("TASK_IDENTITY_INVENTORY_INVALID")
    identifiers = {key: UUID(value[key]) for key in ("user_id", "org_id", "case_id")}
    if any(str(identifier) != value[key] for key, identifier in identifiers.items()):
        raise ValueError("TASK_IDENTITY_INVENTORY_INVALID")
    request = IdentityInventoryRequest(issuer=value["issuer"], subject=value["subject"], **identifiers)
    database = Database(value["database_dsn"])
    try:
        observed = observe_identity_inventory(database, request)
    finally:
        database.close()
    _save_prepared(output, [("identity-directory-observation.json", observed.canonical_bytes)])
    return dict(
        status=observed.as_dict()["status"],
        private_output_written=True,
        observation_sha256=observed.sha256,
        database_written=False,
        external_authentication_verified=False,
        adoption_authorized=False,
    )


def main(argv: Sequence[str] | None = None) -> int:
    _imports()
    from scripts.task_creation_adoption import SafeParser

    parser = SafeParser(description=__doc__)
    try:
        parser.add_argument("--private-configuration", required=True, type=Path)
        parser.add_argument("--output", required=True, type=Path)
        args = parser.parse_args(argv)
        result = run(args.private_configuration, args.output)
    except Exception:
        print(
            json.dumps(
                dict(
                    status="TASK_IDENTITY_INVENTORY_BLOCKED_OR_UNAVAILABLE",
                    private_output_written=False,
                    database_written=False,
                    adoption_authorized=False,
                )
            )
        )
        return 1
    print(json.dumps(result))
    return 0 if result["status"] == "IDENTITY_MEMBERSHIP_OBSERVED_NOT_ADOPTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
