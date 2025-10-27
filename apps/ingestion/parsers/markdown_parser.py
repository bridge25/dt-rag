from typing import Optional
import re
from .base import BaseParser, ParserError


class MarkdownParser(BaseParser):
    def parse(self, file_content: bytes, file_name: Optional[str] = None) -> str:
        try:
            text = file_content.decode("utf-8", errors="ignore")

            parsed_text = self._parse_markdown(text)

            parsed_text = parsed_text.strip()

            if not parsed_text:
                raise ParserError("Markdown parsing resulted in empty content")

            return parsed_text
        except Exception as e:
            if isinstance(e, ParserError):
                raise
            raise ParserError(f"Markdown parsing failed: {str(e)}")

    def _parse_markdown(self, text: str) -> str:
        lines = text.split("\n")
        parsed_lines = []

        in_code_block = False

        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                parsed_lines.append(line)
                continue

            processed_line = line

            if re.match(r"^\s*[-\*_]{3,}\s*$", processed_line):
                continue

            if re.match(r"^\s*\|.*\|.*\|\s*$", processed_line):
                if re.match(r"^\s*\|[\s\-:|]+\|\s*$", processed_line):
                    continue
                processed_line = re.sub(r"^\s*\|", "", processed_line)
                processed_line = re.sub(r"\|\s*$", "", processed_line)
                processed_line = re.sub(r"\|", " ", processed_line)

            processed_line = re.sub(r"^#{1,6}\s+", "", processed_line)

            processed_line = re.sub(r"\*\*(.+?)\*\*", r"\1", processed_line)
            processed_line = re.sub(r"__(.+?)__", r"\1", processed_line)

            processed_line = re.sub(r"\*(.+?)\*", r"\1", processed_line)
            processed_line = re.sub(r"_(.+?)_", r"\1", processed_line)

            processed_line = re.sub(r"~~(.+?)~~", r"\1", processed_line)

            processed_line = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", processed_line)

            processed_line = re.sub(r"!\[.*?\]\(.+?\)", "", processed_line)

            processed_line = re.sub(r"^[\*\-\+]\s+\[[ xX]\]\s+", "", processed_line)

            processed_line = re.sub(r"^[\*\-\+]\s+", "", processed_line)

            processed_line = re.sub(r"^\d+\.\s+", "", processed_line)

            processed_line = re.sub(r"^>\s+", "", processed_line)

            processed_line = re.sub(r"`(.+?)`", r"\1", processed_line)

            if processed_line.strip():
                parsed_lines.append(processed_line)

        return "\n".join(parsed_lines)

    def supports_format(self, file_format: str) -> bool:
        return file_format.lower() in ["md", "markdown"]
