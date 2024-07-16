from textual.widgets import TextArea

from pylspclient.lsp_pydantic_strcuts import Position, Range


class CodeView:
    textarea: TextArea | None = None
    def __init__(self, textarea: TextArea | None = None) -> None:
        self.textarea = textarea
        pass

    def key_down(self, down=True):
        if self.textarea is None:
            return
        begin = self.textarea.selection.start[0]
        # self.textarea.selection.start.
        self.textarea.select_line(begin+1 if down else begin-1)

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
            [' ', ',', '{', '-', '}', ';', '.', '(', ')', '/', '"'])
        while b-1 >= 0:
            if line[b-1] in ignore_set:
                break
            else:
                b = b-1

        while e+1 < len(line):
            if line[e+1] in ignore_set:
                break
            else:
                e += 1
        return line[b:e+1]

    def get_select(self) -> str:
        if self.textarea is None:
            return ""
        return self.textarea.selected_text
