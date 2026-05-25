import subprocess
import logging

class GitUtility:
    """에이전트 작업을 위한 Git 자동화 유틸리티."""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.logger = logging.getLogger("GitUtility")

    def run_git(self, args: list) -> str:
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git error: {e.stderr}")
            return f"Error: {e.stderr.strip()}"
        except Exception as e:
            return f"Error: {str(e)}"

    def commit_changes(self, message: str) -> str:
        self.run_git(["add", "."])
        return self.run_git(["commit", "-m", message])

    def get_status(self) -> str:
        return self.run_git(["status", "--short"])
