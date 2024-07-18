from pathlib import Path
from typing import Literal
from textual.widgets import SelectionList, TextArea
from textual.message import Message

from event import log_message
from lspcpp import Body, from_file, to_file
from pylspclient.lsp_pydantic_strcuts import Location, Position, Range


class CodeSelection:
    range: Range
    text: str


class code_message_impl(Message):
    location: Location

    @staticmethod
    def get_code_message_impl(selection: CodeSelection, file: str):
        return code_message_impl(
            Location(uri=to_file(file), range=selection.range))

    def __init__(self, location: Location) -> None:
        super().__init__()
        self.location = location


class code_message_refer(Message):
    selection: CodeSelection
    file: str
    key: str

    def __init__(self, selection: CodeSelection, file: str):
        super().__init__()
        self.selection = selection
        self.file = file

    def location(self):
        return Location(uri=to_file(self.file), range=self.selection.range)


class code_message_decl(Message):
    location: Location

    def __init__(self, location: Location) -> None:
        super().__init__()
        self.location = location

    pass


class _code_area(TextArea):
    BINDINGS = [
        ("k", "key_up", "up"),
        ("j", "key_down", "down"),
        ("d", "go_declare", "Go to declare"),
        ("D", "go_impl", "Go to Define"),
        ("r", "refer", "Reference"),
    ]
    delegate: 'CodeView'

    def __init__(
        self,
        delegate: 'CodeView',
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
        super().__init__(
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
        self.delegate = delegate

    def action_refer(self) -> None:
        self.delegate.action_refer()

    def action_go_declare(self) -> None:
        self.delegate.action_go_declare()

    def action_go_impl(self) -> None:
        self.delegate.action_go_impl()


class CodeView:
    textarea: _code_area
    file: str

    def __init__(self) -> None:
        pass

    def action_go_impl(self) -> None:
        r = self.get_select_range()
        if r != None:
            self.textarea.post_message(
                code_message_impl.get_code_message_impl(r, self.file))
        pass

    def action_go_declare(self) -> None:
        selection = self.get_select_range()
        if selection != None:
            self.textarea.post_message(
                code_message_decl(
                    Location(range=selection.range, uri=to_file(self.file))))
        pass
        # r = self.get_select_range()
        # if r != None:
        #     self.textarea.post_message(code_message_decl(Location(uri=to_file(self.file),range=r))
        # pass

    def action_refer(self) -> None:
        r = self.get_select_range()
        if r != None:
            msg = code_message_refer(r, self.file)
            loc = msg.location()
            key1 = str(Body(loc)).replace("\n", "")
            key2 = self.get_select_wholeword()
            msg.key = key1 if len(key1) > len(key2) else key2 + \
                    " %s:%d" % (from_file(loc.uri), loc.range.start.line)
            self.textarea.post_message(msg)
        pass

    def loadfile(self, file):
        self.file = file
        from pathlib import Path
        code = self.textarea = _code_area(self,
                                          Path(file).read_text(),
                                          id="code-view",
                                          read_only=True)
        self.textarea = code
        self.set_language()

    def changefile(self, file):
        self.file = file
        TEXT = open(str(file), "r").read()
        self.textarea.load_text(TEXT)
        return

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

    def get_select_range(self) -> CodeSelection | None:
        if self.textarea is None:
            return None
        begin = self.textarea.selection.start
        end = self.textarea.selection.end
        r = Range(start=Position(line=begin[0], character=begin[1]),
                  end=Position(line=end[0], character=end[1]))
        s = CodeSelection()
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
