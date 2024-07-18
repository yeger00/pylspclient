from typing import Literal
from textual.widgets import TextArea

from callinview import log_message
from pylspclient.lsp_pydantic_strcuts import Position, Range


class _code_area(TextArea):
    BINDINGS = [
        ("k", "key_up", "up"),
        ("j", "key_down", "down"),
        ("d", "go_declare", "Go to declare"),
        ("D", "go_impl", "Go to Define"),
        ("r", "refer", "Reference"),
    ]

    def __init__(
        self,
        text: str = "",
        language: str | None = None,
        theme: str = "monokai",
        soft_wrap: bool = False,
        tab_behavior: Literal["focus", "indent"] = "indent",
        read_only: bool = False,
        show_line_numbers: bool = True,
        max_checkpoints: int = 50,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        TextArea.__init__(
            self,
            text,
            language=language,
            theme=theme,
            soft_wrap=soft_wrap,
            tab_behavior=tab_behavior,
            read_only=read_only,
            show_line_numbers=show_line_numbers,
            max_checkpoints=max_checkpoints,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            tooltip=None,
        )


from pathlib import Path


class CodeView:
    textarea: _code_area

    def __init__(self) -> None:
        pass

    def loadfile(self, file):
        from pathlib import Path
        code = self._code_area = _code_area(Path(file).read_text(),
                                            id="code-view",
                                            read_only=True)
        self.textarea = code
        self.set_language()

    def set_language(self):
        from tree_sitter_languages import get_language
        try:
            cpp = get_language("cpp")
            cpp_highlight_query = (Path(__file__).parent /
                                   "queries/c/highlights.scm").read_text()
            code = self.textarea
            code.register_language(cpp, cpp_highlight_query)
            code.language = "cpp"
        except Exception as e:
            self.textarea.post_message(log_message(str(e)))
            pass

    def key_down(self, down=True):
        if self.textarea is None:
            return
        begin = self.textarea.selection.start[0]
        # self.textarea.selection.start.
        self.textarea.select_line(begin + 1 if down else begin - 1)

    def is_focused(self):
        if self.textarea is None:
            return False
        return self.textarea.screen.focused == self.textarea

    class Selection:
        range: Range
        text: str

    def get_select_range(self) -> Selection | None:
        if self.textarea is None:
            return None
        begin = self.textarea.selection.start
        end = self.textarea.selection.end
        r = Range(start=Position(line=begin[0], character=begin[1]),
                  end=Position(line=end[0], character=end[1]))
        s = CodeView.Selection()
        s.range = r
        s.text = self.textarea.selected_text
        return s

    def get_select_wholeword(self) -> str:
        r = self.get_select_range()
        if self.textarea is None:
            return ""
        if r is None:
            return ""
        linenum = r.range.start.line
        b = r.range.start.character
        e = r.range.end.character
        line = self.textarea.document.lines[linenum]
        ignore_set = set(
            [' ', ',', '{', '-', '}', ';', '.', '(', ')', '/', '"', ':', '&'])
        while b - 1 >= 0:
            if line[b - 1] in ignore_set:
                break
            else:
                b = b - 1

        while e + 1 < len(line):
            if line[e + 1] in ignore_set:
                break
            else:
                e += 1
        return line[b:e + 1]

    def get_select(self) -> str:
        if self.textarea is None:
            return ""
        return self.textarea.selected_text
