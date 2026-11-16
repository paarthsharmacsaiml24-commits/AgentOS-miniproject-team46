import re
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_DIRS = {
    ".git", "venv", "node_modules", "__pycache__",
    ".idea", ".vscode"
}
EXCLUDED_FILES = {
    ".env", "credentials.json", "token.json",
    "agent_memory.db"
}
ALLOWED_EXTENSIONS = {
    ".py", ".txt", ".md", ".json", ".csv"
}
class FileDataAgent:
    def get_files(self):
        files = []
        for path in PROJECT_ROOT.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(PROJECT_ROOT)
            if any(part in EXCLUDED_DIRS for part in relative.parts):
                continue
            if path.name.lower() in EXCLUDED_FILES:
                continue
            files.append(str(relative))
        return files[:200]
    def search_files(self, query):
        query = query.lower().strip()
        if not query:
            return []
        return [
            file for file in self.get_files()
            if query in Path(file).name.lower()
        ][:50]
    def search_content(self, query):
        if not query.strip():
            return []
        matches = []
        for relative in self.get_files():
            path = PROJECT_ROOT / relative
            if path.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue
            try:
                if path.stat().st_size > 1_000_000:
                    continue
                content = path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )
                if query.lower() in content.lower():
                    matches.append({
                        "file": relative,
                        "message": "Search term found in this file."
                    })
            except (OSError, UnicodeError):
                continue
        return matches[:50]
    def process(self, command):
        text = command.strip()
        lower = text.lower()
        if "search content" in lower or "search inside" in lower:
            query = re.sub(
                r"^.*?(?:search content for|search inside for|search inside)\s*",
                "",
                text,
                flags=re.IGNORECASE
            ).strip()
            return {
                "agent": "File/Data",
                "operation": "content_search",
                "results": self.search_content(query)
            }
        if "find file" in lower or "search file" in lower:
            query = re.sub(
                r"^.*?(?:find files? named|find files? called|find files? for|search files? for|search files? named|find file|search file)\s*",
                "",
                text,
                flags=re.IGNORECASE
            ).strip()
            return {
                "agent": "File/Data",
                "operation": "file_search",
                "results": self.search_files(query)
            }
        return {
            "agent": "File/Data",
            "operation": "list_files",
            "results": self.get_files()
        }
file_data_agent = FileDataAgent()