"""Protect noarch resource and publication declarations without scientific imports."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SDK_SHA = "2d32048457c6d37093ae509f5626d00a5cda121b"
SUITE = Path(os.environ.get("ELASTNETMT_SUITE_ROOT", ROOT / ".molsyssuite"))
PLAN = "devtools/conda-build/release_plan.example.toml"
RESOURCES = "devtools/conda-build/resources.toml"


class TestDistributionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=SUITE, text=True
        ).strip()
        if head != SDK_SHA:
            raise AssertionError("Use the reviewed immutable distribution SDK")
        subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=SUITE, check=True)
        if subprocess.check_output(
            ["git", "status", "--porcelain", "--", "devtools"],
            cwd=SUITE,
            text=True,
        ).strip():
            raise AssertionError("Shared distribution tools are modified")
        sys.path.insert(0, str(SUITE))
        from devtools.scripts import noarch_conda, verify_installed_matrix

        if not Path(noarch_conda.__file__).resolve().is_relative_to(SUITE.resolve()):
            raise AssertionError("Tests resolved another editable SDK namespace")
        cls.noarch = noarch_conda
        cls.matrix = verify_installed_matrix

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="elastnetmt-contract-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in (
            "pyproject.toml",
            ".github",
            "devtools/conda-build",
            "elastnetmt",
            "molsysviewer_elastnetmt",
        ):
            source, target = ROOT / name, self.root / name
            if source.is_dir():
                shutil.copytree(
                    source,
                    target,
                    ignore=shutil.ignore_patterns("__pycache__"),
                )
            else:
                shutil.copy2(source, target)
        self.plan, self.inventory = self.noarch.inspect_recipe(
            self.root, PLAN, RESOURCES
        )

    def payload(self):
        version = self.plan["version"]
        content = {
            name: b"# synthetic payload\n" for name in self.inventory["required_paths"]
        }
        content[self.inventory["version_file"]] = (
            f'__version__ = "{version}"\n'.encode()
        )
        content["info/index.json"] = json.dumps(
            {
                "name": "elastnetmt",
                "version": version,
                "build": "py_2",
                "build_number": 2,
                "subdir": "noarch",
                "depends": self.inventory["expected_run"],
            }
        ).encode()
        content["info/link.json"] = b'{"noarch": {"type": "python"}}'
        content[f"site-packages/elastnetmt-{version}.dist-info/METADATA"] = (
            f"Name: elastnetmt\nVersion: {version}\n".encode()
        )
        return content

    def archive(self, entries):
        path = self.root / "elastnetmt-0.0.0-py_2.tar.bz2"
        with tarfile.open(path, "w:bz2") as archive:
            for name, content in entries.items():
                member = tarfile.TarInfo(name)
                member.size = len(content)
                archive.addfile(member, io.BytesIO(content))
        return path

    def test_resources_cover_both_complete_distribution_roots(self):
        tracked = subprocess.check_output(
            ["git", "ls-files", "--", "elastnetmt", "molsysviewer_elastnetmt"],
            cwd=ROOT,
            text=True,
        ).splitlines()
        expected = {"site-packages/" + name for name in tracked}
        expected.add("site-packages/elastnetmt/_version.py")
        self.assertEqual(set(self.inventory["required_paths"]), expected)
        self.assertIn("site-packages/elastnetmt/_private/smonitor/catalog.py", expected)
        self.assertIn("site-packages/molsysviewer_elastnetmt/runtime.py", expected)

    def test_complete_synthetic_archive_passes_shared_inspection(self):
        result = self.noarch.inspect_artifact(
            self.archive(self.payload()), self.plan, self.inventory
        )
        self.assertEqual(result["filename"], "elastnetmt-0.0.0-py_2.tar.bz2")

    def test_missing_private_or_addon_runtime_resource_fails(self):
        for missing in (
            "site-packages/elastnetmt/_private/smonitor/catalog.py",
            "site-packages/molsysviewer_elastnetmt/runtime.py",
        ):
            with self.subTest(missing=missing):
                entries = self.payload()
                del entries[missing]
                with self.assertRaisesRegex(ValueError, "required artifact resource"):
                    self.noarch.inspect_artifact(
                        self.archive(entries), self.plan, self.inventory
                    )

    def test_stale_embedded_version_fails(self):
        entries = self.payload()
        entries[self.inventory["version_file"]] = b'__version__ = "0.1.0"\n'
        with self.assertRaisesRegex(ValueError, "embedded Python version"):
            self.noarch.inspect_artifact(
                self.archive(entries), self.plan, self.inventory
            )

    def test_missing_required_recipe_dependency_fails(self):
        recipe = self.root / "devtools/conda-build/meta.yaml"
        recipe.write_text(recipe.read_text().replace("    - depdigest\n", ""))
        with self.assertRaisesRegex(ValueError, "depdigest"):
            self.noarch.inspect_recipe(self.root, PLAN, RESOURCES)

    def test_installed_descriptor_preserves_eight_cells_and_postscience_check(self):
        descriptor = self.noarch.promotion_descriptor(
            self.root, self.plan, self.inventory, "a" * 64
        )
        profile = json.loads(descriptor["profile"])
        self.assertEqual(len(self.matrix.expected_jobs(profile)), 9)
        self.assertEqual(
            profile["required_steps"],
            [
                "Install exact artifact",
                "Validate installed files",
                "Run installed tests",
                "Recheck installed provenance after scientific tests",
            ],
        )
        self.assertEqual(profile["platforms"], ["linux-64", "osx-arm64"])
        self.assertEqual(profile["python_versions"], ["3.11", "3.12", "3.13", "3.14"])
        self.assertEqual(self.inventory["installed_tests"]["paths"], ["tests"])

    def test_example_cannot_authorize_an_actual_candidate(self):
        self.assertFalse(
            (self.root / "devtools/conda-build/release_plan.toml").exists()
        )
        with self.assertRaises((OSError, ValueError)):
            self.noarch.inspect_recipe(
                self.root, "devtools/conda-build/release_plan.toml", RESOURCES
            )

    def test_full_gate_profile_names_every_applicable_existing_workflow(self):
        required = self.plan["required_workflows"]
        self.assertEqual(set(required), set(self.plan["gate_jobs"]))
        self.assertEqual(sum(len(jobs) for jobs in self.plan["gate_jobs"].values()), 12)
        science = self.plan["gate_jobs"][".github/workflows/CI.yaml"]
        expected = {
            f"Test on {os_name}, Python {python}"
            for os_name in ("ubuntu-latest", "macos-15")
            for python in ("3.11", "3.12", "3.13", "3.14")
        }
        self.assertTrue(expected <= set(science))
        self.assertTrue(all("Run tests" in science[name] for name in expected))
        ci = yaml.load(
            (ROOT / ".github/workflows/CI.yaml").read_text(), Loader=yaml.BaseLoader
        )
        admin_steps = {step.get("name") for step in ci["jobs"]["governance"]["steps"]}
        self.assertTrue(set(science["Reporting governance"]) <= admin_steps)

    def test_recovery_and_promotion_bind_original_file_with_separate_workflow_sha(self):
        path = ROOT / ".github/workflows/promote_conda_package.yaml"
        workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
        inputs = workflow["jobs"]["promote"]["with"]
        self.assertEqual(inputs["candidate_sha"], "${{ inputs.candidate_sha }}")
        self.assertEqual(inputs["sha256"], "${{ inputs.sha256 }}")
        self.assertEqual(
            inputs["qualification_sha"],
            "${{ inputs.qualification_sha || inputs.candidate_sha }}",
        )
        for filename in (
            "build_and_upload_conda_packages.yaml",
            "test_installed_conda_package.yaml",
            "promote_conda_package.yaml",
            "conda_publication_governance.yaml",
        ):
            data = yaml.load(
                (ROOT / ".github/workflows" / filename).read_text(),
                Loader=yaml.BaseLoader,
            )
            self.assertTrue(
                all(
                    job["uses"].endswith("@" + SDK_SHA) for job in data["jobs"].values()
                )
            )


if __name__ == "__main__":
    unittest.main()
