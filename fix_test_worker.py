import re

with open("agent/tests/unit/test_worker.py", "r") as f:
    content = f.read()

mock_subprocess = """
@pytest.fixture(autouse=True)
def mock_subprocess_run(monkeypatch, tmp_path):
    import subprocess
    original_run = subprocess.run
    def _mock_run(cmd, *args, **kwargs):
        if "backtest.runner" in cmd:
            job_dir = cmd[-1]
            import os
            os.makedirs(os.path.join(job_dir, "artifacts"), exist_ok=True)
            with open(os.path.join(job_dir, "artifacts", "equity.csv"), "w") as f:
                f.write("Date,equity\\n2023-01-01,10000\\n2023-01-02,10100\\n")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="Mock success", stderr="")
        return original_run(cmd, *args, **kwargs)
    monkeypatch.setattr(subprocess, "run", _mock_run)

def test_run_backtest_job_success(monkeypatch, sample_payload, tmp_path):"""

content = content.replace("def test_run_backtest_job_success(monkeypatch, sample_payload, tmp_path):", mock_subprocess)

with open("agent/tests/unit/test_worker.py", "w") as f:
    f.write(content)
