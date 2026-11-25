from pathlib import Path
import shutil
import uuid

# Keep temporary state inside the workspace, including on managed Windows hosts.
TEST_TEMP = Path(__file__).resolve().parents[1] / "runtime" / "tests"
TEST_TEMP.mkdir(parents=True, exist_ok=True)


class WorkspaceTemporaryDirectory:
    """Avoid Python 3.14's user-only Windows ACL, which excludes sandbox tokens."""
    def __init__(self, **kwargs):
        self.path = TEST_TEMP / uuid.uuid4().hex
        self.path.mkdir(mode=0o777)
        self.name = str(self.path)

    def cleanup(self):
        target = self.path.resolve()
        if target.parent != TEST_TEMP.resolve() or self.path.is_symlink():
            raise ValueError("拒绝清理测试目录以外路径")
        if target.exists():
            shutil.rmtree(target)

    def __enter__(self):
        return self.name

    def __exit__(self, *args):
        self.cleanup()
