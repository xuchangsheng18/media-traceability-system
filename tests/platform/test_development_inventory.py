"""Keep static inventory evidence narrower than deployed or accepted behavior."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "development_inventory", ROOT / "scripts/generate_development_inventory.py"
)
assert SPEC is not None and SPEC.loader is not None
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


class InventoryExtractionTests(unittest.TestCase):
    def write(self, root, path, text):
        file = root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")

    def test_unincluded_decorated_file_is_not_registered_and_product_code_is_not_imported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                inventory.MAIN,
                "from .reads import router as reads\n"
                "raise RuntimeError('must never execute product code')\n"
                "def create_app():\n"
                "    app.include_router(reads, prefix='/api')\n",
            )
            self.write(
                root,
                "backend/business_app/reads.py",
                "raise RuntimeError('must never execute router code')\n"
                "router = APIRouter(prefix='/v1')\n"
                "@router.get('/assets', operation_id='listAssets')\n"
                "def list_assets(): pass\n",
            )
            self.write(
                root,
                "backend/business_app/unmounted.py",
                "router = APIRouter()\n@router.post('/fake', operation_id='fakeSuccess')\ndef fake_success(): pass\n",
            )
            routes, files = inventory.route_registrations(root)
            self.assertEqual(set(routes), {"listAssets"})
            self.assertEqual(files, ["backend/business_app/reads.py"])
            self.assertEqual(routes["listAssets"]["path"], "/api/v1/assets")
            self.assertEqual(routes["listAssets"]["python_function"], "list_assets")
            self.assertEqual(routes["listAssets"]["line"], 4)
            self.assertIn("NOT_RUNTIME_OR_ACCEPTANCE", routes["listAssets"]["evidence_kind"])

    def test_unresolvable_included_router_does_not_silently_disappear(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, inventory.MAIN, "def create_app():\n    app.include_router(make_router())\n")
            with self.assertRaisesRegex(ValueError, "Cannot statically resolve included"):
                inventory.route_registrations(root)

    def test_query_reference_and_operation_override_preserve_required_case_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = {
                "servers": [{"url": "/api/v1"}],
                "components": {
                    "parameters": {
                        "Case": {
                            "name": "case_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "uuid"},
                        }
                    }
                },
                "paths": {
                    "/assets": {
                        "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer", "maximum": 999}}],
                        "get": {
                            "operationId": "listAssets",
                            "parameters": [
                                {"$ref": "#/components/parameters/Case"},
                                {
                                    "name": "limit",
                                    "in": "query",
                                    "required": False,
                                    "schema": {"type": "integer", "maximum": 100},
                                },
                            ],
                            "responses": {"200": {"description": "ok"}},
                        },
                    }
                },
            }
            self.write(root, "api.yaml", yaml.safe_dump(document))
            operation = inventory.contract_operations(root, "api.yaml")["listAssets"]
            parameters = {item["name"]: item for item in operation["parameters"]}
            self.assertTrue(parameters["case_id"]["required"])
            self.assertEqual(parameters["case_id"]["schema"]["format"], "uuid")
            self.assertEqual(parameters["limit"]["schema"]["maximum"], 100)
            self.assertEqual(operation["path"], "/api/v1/assets")

    def test_external_or_cyclic_parameter_reference_requires_explicit_resolution(self):
        with self.assertRaisesRegex(ValueError, "Unsupported or cyclic"):
            inventory.local_reference({}, {"$ref": "other.yaml#/Case"})
        document = {"components": {"parameters": {"Case": {"$ref": "#/components/parameters/Case"}}}}
        with self.assertRaisesRegex(ValueError, "Unsupported or cyclic"):
            inventory.local_reference(document, {"$ref": "#/components/parameters/Case"})

    def test_sql_comments_strings_and_function_bodies_are_not_created_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "backend/business_migrations/0001_fixture.sql",
                "-- CREATE TABLE mt.comment_fake (id uuid);\n"
                "/* nested /* comment */ CREATE TABLE mt.block_fake(id uuid); */\n"
                "SELECT 'CREATE TABLE mt.string_fake(id uuid);';\n"
                "CREATE TABLE mt.real_table (id uuid);\n"
                "CREATE OR REPLACE FUNCTION mt.safe_read() RETURNS void AS $body$\n"
                "BEGIN RAISE NOTICE 'CREATE TABLE mt.body_fake(id uuid)'; END;\n"
                "$body$ LANGUAGE plpgsql;\n",
            )
            tables, functions, files = inventory.migration_objects(root)
            self.assertEqual(set(tables), {"real_table"})
            self.assertEqual(set(functions), {"safe_read"})
            self.assertEqual(tables["real_table"][0]["line"], 4)
            self.assertEqual(files, ["backend/business_migrations/0001_fixture.sql"])
            self.assertIn("NOT_TARGET_DATABASE_DEPLOYMENT", tables["real_table"][0]["evidence_kind"])

    def test_method_index_omits_defaults_and_does_not_invent_dynamic_or_nested_sql_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "backend/business_app/repository.py",
                "raise RuntimeError('must never import backend')\n"
                "class Repository:\n"
                "    def read(self, identifier, /, *, case_id, password='PRIVATE_DEFAULT_NEVER_EXPORT', **options):\n"
                '        """SELECT * FROM mt.audit_event is documentation only."""\n'
                "        ordinary = 'SELECT * FROM mt.upload_session'\n"
                "        # text('SELECT * FROM mt.users')\n"
                "        text(\"SELECT 'mt.users' AS note FROM mt.media_asset -- JOIN mt.roles\\n/* mt.permissions */\")\n"
                "        text(f'SELECT * FROM mt.{identifier}')\n"
                "        def child():\n"
                "            text('SELECT * FROM mt.audit_event')\n"
                "        return identifier\n",
            )
            methods, files = inventory.backend_method_sources(
                root, {"media_asset", "audit_event", "upload_session", "users", "roles", "permissions"}
            )
            self.assertEqual(files, ["backend/business_app/repository.py"])
            indexed = {item["qualified_name"]: item for item in methods}
            parent = indexed["business_app.repository.Repository.read"]
            self.assertEqual(parent["direct_literal_sql_tables"], ["media_asset"])
            self.assertTrue(parent["dynamic_or_indirect_sql_argument_present"])
            self.assertEqual(parent["parameter_names"]["positional_only"], ["self", "identifier"])
            self.assertEqual(parent["parameter_names"]["keyword_only"], ["case_id", "password"])
            self.assertEqual(parent["parameter_names"]["var_keyword"], "options")
            self.assertEqual(
                indexed["business_app.repository.Repository.read.child"]["direct_literal_sql_tables"], ["audit_event"]
            )
            self.assertNotIn("PRIVATE_DEFAULT_NEVER_EXPORT", json.dumps(methods))
            self.assertNotIn("SELECT", json.dumps(methods))


if __name__ == "__main__":
    unittest.main()
