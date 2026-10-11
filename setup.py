"""Include the single-source installer resources in built wheels."""

from pathlib import Path
import shutil
from setuptools import setup
from setuptools.command.build_py import build_py


class Build(build_py):
    def run(self):
        super().run()
        root = Path(__file__).parent
        bundle = Path(self.build_lib) / "aek" / "bundle"
        for name in ["src", "scripts", "skills", "templates"]:
            shutil.copytree(
                root / name,
                bundle / name,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.egg-info", "bundle"
                ),
            )


setup(cmdclass={"build_py": Build})
