from typing import Optional, List
from enum import Enum, IntEnum
from pydantic import BaseModel, HttpUrl


class LanguageIdentifier(str, Enum):
    BAT="bat"
    BIBTEX="bibtex"
    CLOJURE="clojure"
    COFFESCRIPT="coffeescript"
    C="c"
    CPP="cpp"
    CSHARP="csharp"
    CSS="css"
    DIFF="diff"
    DOCKERFILE="dockerfile"
    FSHARP="fsharp"
    GIT_COMMIT="git-commit"
    GIT_REBASE="git-rebase"
    GO="go"
    GROOVY="groovy"
    HANDLEBARS="handlebars"
    HTML="html"
    INI="ini"
    JAVA="java"
    JAVASCRIPT="javascript"
    JSON="json"
    LATEX="latex"
    LESS="less"
    LUA="lua"
    MAKEFILE="makefile"
    MARKDOWN="markdown"
    OBJECTIVE_C="objective-c"
    OBJECTIVE_CPP="objective-cpp"
    Perl="perl"
    PHP="php"
    POWERSHELL="powershell"
    PUG="jade"
    PYTHON="python"
    R="r"
    RAZOR="razor"
    RUBY="ruby"
    RUST="rust"
    SASS="sass"
    SCSS="scss"
    ShaderLab="shaderlab"
    SHELL_SCRIPT="shellscript"
    SQL="sql"
    SWIFT="swift"
    TYPE_SCRIPT="typescript"
    TEX="tex"
    VB="vb"
    XML="xml"
    XSL="xsl"
    YAML="yaml"

class TextDocumentItem(BaseModel):
    """
    Represents a text document.

    Attributes:
        uri: The text document's URI.
        languageId: The text document's language identifier.
        version: The version number of this document. It will increase after each change, including undo/redo.
        text: The content of the opened text document.
    """
    uri: str
    languageId: LanguageIdentifier
    version: int
    text: str

class TextDocumentIdentifier(BaseModel):
    """
    Identifies a text document using its URI.
    """
    uri: str

class Position(BaseModel):
    """Represents a position in a text document."""
    line: int
    character: int

class Range(BaseModel):
    """Defines a range in a text document."""
    start: Position
    end: Position

class Location(BaseModel):
    """Represents a location inside a resource, such as a line inside a text file."""
    uri: str
    range: Range

class SymbolKind(IntEnum):
    """Represents various symbol kinds like File, Module, Namespace, Package, Class, Method, etc."""
    File = 1
    Module = 2
    Namespace = 3
    Package = 4
    Class = 5
    Method = 6
    Property = 7
    Field = 8
    Constructor = 9
    Enum = 10
    Interface = 11
    Function = 12
    Variable = 13
    Constant = 14
    String = 15
    Number = 16
    Boolean = 17
    Array = 18
    Object = 19
    Key = 20
    Null = 21
    EnumMember = 22
    Struct = 23
    Event = 24
    Operator = 25
    TypeParameter = 26

class SymbolTag(Enum):
    """Represents additional information about the symbol."""
    # Define the symbol tags as per your specification, for example:
    Deprecated = 1

class DocumentSymbol(BaseModel):
    """
    Represents information about programming constructs like variables, classes, interfaces etc.
    """
    name: str
    detail: Optional[str] = None
    kind: SymbolKind
    tags: Optional[List[SymbolTag]] = None
    deprecated: Optional[bool] = None
    range: Range
    selectionRange: Range
    children: Optional[List['DocumentSymbol']] = None

class SymbolInformation(BaseModel):
    """
    Represents information about programming constructs like variables, classes, interfaces, etc.
    """
    name: str
    kind: SymbolKind
    deprecated: Optional[bool] = None
    location: Location
    containerName: Optional[str] = None

class TextDocumentPositionParams(BaseModel):
    """
    A base class including the text document identifier and a position within that document.
    """
    textDocument: TextDocumentIdentifier
    position: Position

class ReferenceContext(BaseModel):
    """
    Additional information about the context of a reference request.
    """
    includeDeclaration: bool  # Whether to include the declaration of the symbol being referenced

class ReferenceParams(TextDocumentPositionParams):
    """
    Parameters for a Reference Request in the Language Server Protocol.
    """
    context: ReferenceContext
    workDoneToken: Optional[str] = None  # Optional; used for progress reporting
    partialResultToken: Optional[str] = None  # Optional; used for partial results

class LocationLink(BaseModel):
    originSelectionRange: Optional[Range]
    targetUri: HttpUrl
    targetRange: Range
    targetSelectionRange: Range
