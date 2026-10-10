"""Administrative guards exercise the actual shared source/context preflight."""

from __future__ import annotations

import json
import shutil
import unittest

from devtools.tests import test_distribution_contract as fixtures


class TestSourceRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.TestDistributionContract.setUpClass.__func__(cls)
        from devtools.scripts import dependency_routes

        cls.routes = dependency_routes

    def setUp(self):
        fixtures.TestDistributionContract.setUp(self)
        # Historical fixtures belong to archive guards, not current routes.
        for name in ("meta.yaml", "resources.toml", "release_plan.example.toml"):
            (self.root / "devtools/conda-build" / name).unlink()
        (self.root / "elastnetmt/model/old_anm.py").unlink()
        shutil.copy2(fixtures.ROOT / "pyproject.toml", self.root / "pyproject.toml")
        for name in [
            "devtools/conda-envs",
            "devtools/requirements",
            "devtools/dependency_routes.toml",
        ]:
            source, target = fixtures.ROOT / name, self.root / name
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
        for name in ("meta.yaml", "release_plan.example.toml"):
            shutil.copy2(
                fixtures.ROOT / "devtools/conda-build" / name,
                self.root / "devtools/conda-build" / name,
            )

    def audit(self, **kwargs):
        return self.routes.audit(self.root, **kwargs)

    def test_all_current_routes_thirteen_pins_and_seven_contexts_are_classified(self):
        result = self.audit()
        self.assertEqual(result["schema"], "molsyssuite.dependency-routes@3")
        self.assertEqual(len(result["routes"]), 18)
        self.assertEqual(len(result["source_routes"]), 13)
        self.assertEqual(len(result["contexts"]), 7)
        self.assertEqual(result["qualification"], "declared-only")
        self.assertNotIn("installed_sources", result)

    def test_native_recipe_audit_does_not_claim_native_or_release_qualification(self):
        route = next(
            route
            for route in self.audit()["routes"]
            if route["kind"] == "native-abi3-dependencies"
        )
        self.assertEqual(route["abi3_minimum"], "3.11")
        self.assertEqual(route["artifact_subdirs"], ["linux-64", "osx-arm64"])
        self.assertEqual(route["python_versions"], ["3.11", "3.12", "3.13", "3.14"])
        self.assertEqual(route["qualification"], "declared-only")
        self.assertFalse(route["native_bytes_verified"])
        self.assertEqual(
            set(route["input_sha256"]),
            {
                "pyproject.toml",
                "devtools/conda-build/meta.yaml",
                "devtools/conda-build/release_plan.example.toml",
            },
        )
        self.assertFalse(
            (fixtures.ROOT / "devtools/conda-build/release_plan.toml").exists()
        )

    def test_native_recipe_cannot_hide_python_abi_or_runtime_drift(self):
        path = self.root / "devtools/conda-build/meta.yaml"
        original = path.read_text()
        for old, new in (
            ("python-abi3 3.11.*", "python-abi3 3.12.*"),
            ("    - depdigest\n", ""),
            ("    - python >=3.11,<3.15", "    - python >=3.11"),
            (
                "python_version_independent: true",
                "python_version_independent: true\n  noarch: python",
            ),
        ):
            with self.subTest(new=new):
                path.write_text(original.replace(old, new))
                with self.assertRaises(ValueError):
                    self.audit()

    def test_missing_public_runtime_dependency_cannot_hide_behind_source_ci(self):
        path = self.root / "devtools/conda-envs/production_env.yaml"
        path.write_text(path.read_text().replace("- depdigest\n", ""))
        with self.assertRaisesRegex(ValueError, "production_env.yaml.*depdigest"):
            self.audit()

    def test_changed_git_input_requires_reinspection(self):
        path = self.root / "devtools/requirements/controlled_suite_dependencies.txt"
        path.write_text(
            path.read_text().replace("3825c741ee08d2cb0b6c2398337f368a6875dd96", "main")
        )
        with self.assertRaisesRegex(ValueError, "source input changed"):
            self.audit()

    def test_unreviewed_scientific_workflow_change_is_rejected(self):
        path = self.root / ".github/workflows/CI.yaml"
        path.write_text(
            path.read_text().replace("3bcfaf4d50df6c84ebd14505790ed5221543e5de", "main")
        )
        with self.assertRaisesRegex(ValueError, "reviewed workflow changed"):
            self.audit()

    def test_wrong_source_pin_and_overlay_are_rejected(self):
        path = self.root / "devtools/dependency_routes.toml"
        original = path.read_text()
        for changed in [
            original.replace("3825c741ee08d2cb0b6c2398337f368a6875dd96", "a" * 40),
            original.replace('overlays = ["pyunitwizard"]', "overlays = []"),
        ]:
            path.write_text(changed)
            with self.subTest(changed=changed[:30]), self.assertRaises(ValueError):
                self.audit()

    def test_actual_primary_editables_cannot_be_mistaken_for_selected_git_pins(self):
        class Distribution:
            version = "1.0.0"

            def read_text(self, name):
                return json.dumps(
                    {"url": "file:///unrelated/source", "dir_info": {"editable": True}}
                )

        with self.assertRaisesRegex(ValueError, "reviewed root Git"):
            self.audit(
                context="ci-3.14",
                check_installed=True,
                python_version="3.14.7",
                distribution_for=lambda name: Distribution(),
            )

    def test_exact_candidate_science_jobs_require_executed_installed_preflight(self):
        for name, steps in self.plan["gate_jobs"][".github/workflows/CI.yaml"].items():
            if name.startswith("Test on "):
                self.assertIn(
                    "Check dependency routes and installed Git context", steps
                )
        data = fixtures.yaml.safe_load(
            (fixtures.ROOT / ".github/workflows/CI.yaml").read_text()
        )
        steps = data["jobs"]["test-linux"]["steps"]
        self.assertEqual(steps, data["jobs"]["test-macos"]["steps"])
        names = [s.get("name") for s in steps]
        self.assertLess(
            names.index("Check dependency routes and installed Git context"),
            names.index("Run tests"),
        )
        run = next(
            s["run"]
            for s in steps
            if s.get("name") == "Install isolated dependency-check tools"
        )
        self.assertIn("--target .molsyssuite-tools", run)


if __name__ == "__main__":
    unittest.main()
