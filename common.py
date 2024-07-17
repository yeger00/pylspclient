from pylspclient.lsp_pydantic_strcuts import Location, Position, SymbolInformation


import subprocess

def where_is_bin(clangd):
    try:
        result = subprocess.run(['/usr/bin/whereis', clangd], capture_output=True, text=True, check=True)
        ret = result.stdout.split('\n')[0]
        s = ret[ret.find("/"):]
        s = s[:s.find(" ")]
        return s
    except subprocess.CalledProcessError:
        return None


def from_file(path: str) -> str:
    return path.replace("file://", "").replace("file:", "")


def to_file(path: str) -> str:
    if path.startswith("file://"):
        return path
    return f"file://{path}"

def range_before(before: Position, after: Position):
    if before.line < after.line:
        return True
    elif before.line == after.line:
        return before.character <= after.character
    else:
        return False


def SubLine(begin, end, lines:list[str])->list[str]:
    subline = lines[begin.line:end.line+1]
    if begin.line == end.line:
        e =  end.character+1 if end.character >-1 else -1 
        subline[0] = subline[0][begin.character:e]
    else:
        subline[0] = subline[0][begin.character:]
        e =  end.character+1 if end.character >-1 else -1 
        subline[-1] = subline[-1][:e]
    return subline


class Body:
    subline: list[str] = []
    location: Location

    def __init__(self, location: Location) -> None:
        self.data = ""
        self.location = location
        range = location.range
        begin = range.start
        end = range.end
        with open(from_file(location.uri), "r") as fp:
            lines = fp.readlines()
            subline = SubLine(begin, end, lines)
            self.subline = subline

    def __str__(self) -> str:
        return "\n".join(self.subline)
    
def location_to_filename(loc:Location):
    import os
    filename = os.path.basename(from_file(loc.uri))
    return "%s:%d" % (filename, loc.range.start.line)