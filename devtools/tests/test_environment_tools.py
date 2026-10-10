"""Protect generation, Python restrictions and Conda failure propagation."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "devtools"))
import broadcast_requirements as broadcast  # noqa: E402 — owner tool path above
import conda_environment as environments  # noqa: E402 — owner tool path above


class TestEnvironmentTools(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="elastnetmt-environment-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in (
            "pyproject.toml",
            "devtools/requirements.yaml",
            "devtools/dependency_routes.toml",
            "devtools/conda-envs",
            "devtools/conda-build",
            "devtools/requirements",
        ):
            source, target = ROOT / name, self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(
                    source, target, ignore=shutil.ignore_patterns("__pycache__")
                )
            else:
                shutil.copy2(source, target)
        self.path = self.root / "devtools/conda-envs/production_env.yaml"

    def selected(self, minor="3.14", path=None):
        return environments.selected_environment(
            path or self.path, minor, root=self.root
        )

    def test_generation_preserves_jinja_recipe_specialized_environments_and_source_bytes(
        self,
    ):
        protected = [
            self.root / "devtools/conda-build/meta.noarch.yaml.txt",
            *self.root.glob("devtools/requirements/*.txt"),
            *(
                self.root / "devtools/conda-envs" / name
                for name in (
                    "importable_env.yaml",
                    "test_env_py313.yaml",
                    "test_env_py314.yaml",
                )
            ),
        ]
        before = {path: path.read_bytes() for path in protected}
        broadcast.generate(self.root)
        broadcast.generate(self.root, check=True)
        self.assertEqual(before, {path: path.read_bytes() for path in protected})
        documents = broadcast.environment_documents(self.root)
        for name in ("production", "development", "docs"):
            dependencies = yaml.safe_load(
                documents[f"devtools/conda-envs/{name}_env.yaml"]
            )["dependencies"]
            for requirement in (
                "numpy",
                "smonitor",
                "argdigest",
                "depdigest",
                "lindelint",
            ):
                self.assertIn(requirement, dependencies)
        test = yaml.safe_load(documents["devtools/conda-envs/test_env.yaml"])[
            "dependencies"
        ]
        self.assertIn("pyunitwizard", test)  # Reviewed public bootstrap overlay.
        self.assertIn("numpy", test)
        for source in ("lindelint", "smonitor", "argdigest", "depdigest"):
            self.assertNotIn(source, test)

    def test_check_mode_rejects_drift_without_writing(self):
        self.path.write_text(self.path.read_text().replace("- depdigest\n", ""))
        before = {
            path: path.read_bytes()
            for path in self.root.glob("devtools/conda-envs/*.yaml")
        }
        with self.assertRaisesRegex(ValueError, "Generated environments differ"):
            broadcast.generate(self.root, check=True)
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_late_invalid_tool_group_fails_before_any_output_is_written(self):
        groups = self.root / "devtools/requirements.yaml"
        groups.write_text(groups.read_text().replace("- conda-build", "- python=3.7"))
        before = {
            path: path.read_bytes()
            for path in self.root.glob("devtools/conda-envs/*.yaml")
        }
        with self.assertRaisesRegex(ValueError, "Metadata/source context owns"):
            broadcast.generate(self.root)
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_changed_metadata_floor_is_propagated_to_generated_consumers(self):
        project = self.root / "pyproject.toml"
        project.write_text(project.read_text().replace('"numpy"', '"numpy>=2.1,<3"'))
        documents = broadcast.environment_documents(self.root)
        for name in ("production", "development", "docs", "test"):
            self.assertIn(
                "- numpy>=2.1,<3\n", documents[f"devtools/conda-envs/{name}_env.yaml"]
            )

    def test_shared_range_proof_rejects_unsupported_partial_and_specialized_minors(
        self,
    ):
        for minor in ("3.10", "3.15", "3.14.7", "3.14;echo", "None"):
            with self.subTest(minor=minor), self.assertRaises(ValueError):
                self.selected(minor)
        specialized = self.root / "devtools/conda-envs/test_env_py314.yaml"
        with self.assertRaises(ValueError):
            self.selected("3.13", specialized)
        older = self.root / "devtools/conda-envs/test_env.yaml"
        with self.assertRaisesRegex(ValueError, "fixed-source environment"):
            self.selected("3.14", older)
        self.selected("3.11", older)
        self.selected("3.12", older)

    def test_existing_patch_bounds_cannot_be_widened_to_an_entire_minor(self):
        for selector in (
            "python >=3.14.2,<3.15",
            "python >=3.14,<3.14.8",
            "python=3.14=custom_0",
        ):
            self.path.write_text("dependencies:\n- " + selector + "\n- numpy\n")
            with self.subTest(selector=selector), self.assertRaises(ValueError):
                self.selected()

    def test_missing_dependencies_duplicates_and_invalid_entries_are_rejected(self):
        for text in (
            "[]",
            "dependencies: null",
            "dependencies: []",
            "dependencies: [python, python=3.14]",
            "dependencies: [23]",
            "dependencies: [{pip: invalid}]",
        ):
            self.path.write_text(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.selected()

    def test_selection_preserves_non_python_constraints_and_does_not_edit_manifest(
        self,
    ):
        self.path.write_text(
            "name: other\nprefix: /other\nchannels: [uibcdf, conda-forge]\ndependencies:\n- python >=3.11,<3.15\n- numpy >=2.1,<3\n- pip:\n  - provider==1.2\n"
        )
        before = self.path.read_bytes()
        selected = self.selected()
        self.assertEqual(
            selected["dependencies"],
            ["python>=3.14,<3.15", "numpy >=2.1,<3", {"pip": ["provider==1.2"]}],
        )
        self.assertNotIn("name", selected)
        self.assertNotIn("prefix", selected)
        self.assertEqual(before, self.path.read_bytes())

    def test_create_uses_argument_vector_strict_priority_and_cleans_up_on_failure(self):
        captured = []
        before = self.path.read_bytes()

        def fail(command, **kwargs):
            self.assertEqual(
                command[:5],
                ["/manager with spaces", "env", "create", "--name", "elastnetmt@3.14"],
            )
            self.assertTrue(kwargs["check"])
            self.assertNotIn("shell", kwargs)
            self.assertEqual(kwargs["env"]["CONDA_CHANNEL_PRIORITY"], "strict")
            manifest = Path(command[command.index("--file") + 1])
            self.assertIn(
                "python>=3.14,<3.15",
                yaml.safe_load(manifest.read_text())["dependencies"],
            )
            captured.append(manifest)
            raise subprocess.CalledProcessError(7, command)

        with (
            patch.object(environments, "manager", return_value="/manager with spaces"),
            patch.object(
                environments, "subprocess", SimpleNamespace(run=Mock(side_effect=fail))
            ),
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                environments.apply_environment(
                    self.path, "3.14", name="elastnetmt@3.14", root=self.root
                )
        self.assertFalse(captured[0].exists())
        self.assertEqual(before, self.path.read_bytes())

    def test_update_targets_verified_active_prefix_and_propagates_failure(self):
        prefix = self.root / "active prefix"
        (prefix / "conda-meta").mkdir(parents=True)
        with (
            patch.object(environments, "manager", return_value="/conda"),
            patch.object(
                environments,
                "subprocess",
                SimpleNamespace(
                    run=Mock(side_effect=subprocess.CalledProcessError(8, "conda"))
                ),
            ) as runner,
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                environments.apply_environment(
                    self.path, "3.14", prefix=prefix, root=self.root
                )
        arguments = runner.run.call_args.args[0]
        self.assertEqual(
            arguments[:5], ["/conda", "env", "update", "--prefix", str(prefix)]
        )
        self.assertEqual(arguments[-1], "--prune")
        self.assertFalse(Path(arguments[arguments.index("--file") + 1]).exists())

    def test_invalid_target_fails_before_calling_manager(self):
        for kwargs in (
            {"name": "name;echo"},
            {"name": "-option"},
            {"prefix": self.root},
            {},
        ):
            with (
                self.subTest(kwargs=kwargs),
                patch.object(environments, "manager") as manager,
            ):
                with self.assertRaises(ValueError):
                    environments.apply_environment(
                        self.path, "3.14", root=self.root, **kwargs
                    )
                manager.assert_not_called()

    def test_mamba_alone_is_valid_and_invalid_explicit_path_is_rejected(self):
        with (
            patch.dict(os.environ, {"MAMBA_EXE": "/custom/mamba"}, clear=True),
            patch.object(
                environments.shutil,
                "which",
                side_effect=lambda name: (
                    "/custom/mamba" if name == "/custom/mamba" else None
                ),
            ),
        ):
            self.assertEqual(environments.manager(), "/custom/mamba")
        with (
            patch.dict(os.environ, {"CONDA_EXE": "/missing"}, clear=True),
            patch.object(environments.shutil, "which", return_value=None),
            self.assertRaises(ValueError),
        ):
            environments.manager()

    def test_cli_imports_have_no_argument_parsing_or_environment_mutation(self):
        for name in ("create_conda_env", "update_conda_env"):
            specification = importlib.util.spec_from_file_location(
                name, ROOT / f"devtools/conda-envs/{name}.py"
            )
            module = importlib.util.module_from_spec(specification)
            with (
                patch(
                    "argparse.ArgumentParser.parse_args",
                    side_effect=AssertionError("import parsed CLI"),
                ),
                patch.object(
                    environments,
                    "apply_environment",
                    side_effect=AssertionError("import changed environment"),
                ),
            ):
                specification.loader.exec_module(module)

    def test_cli_returns_failure_from_manager_instead_of_success(self):
        specification = importlib.util.spec_from_file_location(
            "create_cli", ROOT / "devtools/conda-envs/create_conda_env.py"
        )
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        with (
            patch.object(sys, "argv", ["create", "-n", "test", str(self.path)]),
            patch.object(
                module,
                "apply_environment",
                side_effect=subprocess.CalledProcessError(7, "conda"),
            ),
        ):
            self.assertEqual(module.main(), 1)


if __name__ == "__main__":
    unittest.main()
