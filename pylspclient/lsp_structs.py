import enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, List

def to_type(o, new_type):
    '''
    Helper function that receives an object or a dict and convert it to a new given type.

    :param object|dict o: The object to convert
    :param Type new_type: The type to convert to.
    '''
    if new_type == type(o):
        return o
    else:
        return new_type(**o)


class Position(BaseModel):
    """
    Constructs a new Position instance.

    :param int line: Line position in a document (zero-based).
    :param int character: Character offset on a line in a document (zero-based).
    """
    line: int
    character: int


class Range(BaseModel):
    """
    Constructs a new Range instance.

    :param Position start: The range's start position.
    :param Position end: The range's end position.
    """
    start: Any
    end: Any
    def __init__(self, **data):
        data["start"] = to_type(data["start"], Range)
        data["end"] = to_type(data["end"], Range)
        super().__init__(**data)


class Location(BaseModel):
    """
    Represents a location inside a resource, such as a line inside a text file.
    """
    uri: str
    range: Any
    def __init__(self, **data):
        """
        Constructs a new Location instance.

        :param str uri: Resource file.
        :param Range range: The range inside the file
        """
        data["range"] = to_type(data["range"], Range)
        super().__init__(**data)


class LocationLink(BaseModel):
    """
    Represents a link between a source and a target location.
    """
    originSelectionRange: Any
    targetUri: str
    targetRange: Any
    targetSelectionRange: Any

    def __init__(self, **data):
        """
        Constructs a new LocationLink instance.

        :param Range originSelectionRange: Span of the origin of this link.
            Used as the underlined span for mouse interaction. Defaults to the word range at the mouse position.
        :param str targetUri: The target resource identifier of this link.
        :param Range targetRange: The full target range of this link. If the target for example is a symbol then target 
            range is the range enclosing this symbol not including leading/trailing whitespace but everything else
            like comments. This information is typically used to highlight the range in the editor.
        :param Range targetSelectionRange: The range that should be selected and revealed when this link is being followed, 
            e.g the name of a function. Must be contained by the the `targetRange`. See also `DocumentSymbol#range`
        """
        data["originSelectionRange"] = to_type(data["originSelectionRange"], Range)
        data["targetRange"] = to_type(data["targetRange"], Range)
        data["targetSelectionRange"] = to_type(data["targetSelectionRange"], Range)
        super().__init__(**data)


class Diagnostic(BaseModel):
    """
    Constructs a new Diagnostic instance.
    :param Range range: The range at which the message applies.Resource file.
    :param int severity: The diagnostic's severity. Can be omitted. If omitted it is up to the
                            client to interpret diagnostics as error, warning, info or hint.
    :param str code: The diagnostic's code, which might appear in the user interface.
    :param str source: A human-readable string describing the source of this
                        diagnostic, e.g. 'typescript' or 'super lint'.
    :param str message: The diagnostic's message.
    :param list relatedInformation: An array of related diagnostic information, e.g. when symbol-names within   
                                    a scope collide all definitions can be marked via this property.
    """
    range: Range
    severity: int
    code: str
    source: str
    message: str
    relatedInformation: list


class DiagnosticSeverity(object):
    Error: int = 1
    Warning: int = 2 # TODO: warning is known in python
    Information: int = 3
    Hint: int = 4


class DiagnosticRelatedInformation(BaseModel):
    """
    Constructs a new Diagnostic instance.
    :param Location location: The location of this related diagnostic information.
    :param str message: The message of this related diagnostic information.
    """
    location: Location
    message: str


class Command(BaseModel):
    """
    Constructs a new Diagnostic instance.
    :param str title: Title of the command, like `save`.
    :param str command: The identifier of the actual command handler.
    :param list arguments: Arguments that the command handler should be invoked with.
    """
    title: str
    command: str
    arguments: list


class TextDocumentItem(BaseModel):
    """
    An item to transfer a text document from the client to the server.
    Constructs a new Diagnostic instance.
    
    :param DocumentUri uri: Title of the command, like `save`.
    :param str languageId: The identifier of the actual command handler.
    :param int version: Arguments that the command handler should be invoked with.
    :param str text: Arguments that the command handler should be invoked with.
    """
    uri: str
    languageId: str
    version: int
    text: str


class TextDocumentIdentifier(BaseModel):
    """
    Text documents are identified using a URI. On the protocol level, URIs are passed as strings. 
    Constructs a new TextDocumentIdentifier instance.

    :param DocumentUri uri: The text document's URI.       
    """
    uri: str


class VersionedTextDocumentIdentifier(TextDocumentIdentifier):
    """
    An identifier to denote a specific version of a text document.
    """
    def __init__(self, version, uri):
        """
        Constructs a new TextDocumentIdentifier instance.
        
        :param DocumentUri uri: The text document's URI.
        :param int version: The version number of this document. If a versioned 
            text document identifier is sent from the server to the client and 
            the file is not open in the editor (the server has not received an 
            open notification before) the server can send `null` to indicate 
            that the version is known and the content on disk is the truth (as 
            speced with document content ownership).
        The version number of a document will increase after each change, including
        undo/redo. The number doesn't need to be consecutive.
        """
        self.version = version
        super(VersionedTextDocumentIdentifier, self).__init__(uri=uri)


class TextDocumentContentChangeEvent(BaseModel):
    """
    An event describing a change to a text document. If range and rangeLength are omitted
    the new text is considered to be the full content of the document.
    Constructs a new TextDocumentContentChangeEvent instance.

    :param Range range: The range of the document that changed.
    :param int rangeLength: The length of the range that got replaced.
    :param str text: The new text of the range/document.
    """
    range: Range
    rangeLength: int
    text: str


class TextDocumentPositionParams(BaseModel):
    """
    A parameter literal used in requests to pass a text document and a position inside that document.
    Constructs a new TextDocumentPositionParams instance.

    :param TextDocumentIdentifier textDocument: The text document.
    :param Position position: The position inside the text document.
    """
    textDocument: TextDocumentIdentifier
    Position: Position


class LANGUAGE_IDENTIFIER(object):
    BAT: str="bat"
    BIBTEX: str="bibtex"
    CLOJURE: str="clojure"
    COFFESCRIPT: str="coffeescript"
    C: str="c"
    CPP: str="cpp"
    CSHARP: str="csharp"
    CSS: str="css"
    DIFF: str="diff"
    DOCKERFILE: str="dockerfile"
    FSHARP: str="fsharp"
    GIT_COMMIT: str="git-commit"
    GIT_REBASE: str="git-rebase"
    GO: str="go"
    GROOVY: str="groovy"
    HANDLEBARS: str="handlebars"
    HTML: str="html"
    INI: str="ini"
    JAVA: str="java"
    JAVASCRIPT: str="javascript"
    JSON: str="json"
    LATEX: str="latex"
    LESS: str="less"
    LUA: str="lua"
    MAKEFILE: str="makefile"
    MARKDOWN: str="markdown"
    OBJECTIVE_C: str="objective-c"
    OBJECTIVE_CPP: str="objective-cpp"
    Perl: str="perl"
    PHP: str="php"
    POWERSHELL: str="powershell"
    PUG: str="jade"
    PYTHON: str="python"
    R: str="r"
    RAZOR: str="razor"
    RUBY: str="ruby"
    RUST: str="rust"
    SASS: str="sass"
    SCSS: str="scss"
    ShaderLab: str="shaderlab"
    SHELL_SCRIPT: str="shellscript"
    SQL: str="sql"
    SWIFT: str="swift"
    TYPE_SCRIPT: str="typescript"
    TEX: str="tex"
    VB: str="vb"
    XML: str="xml"
    XSL: str="xsl"
    YAML: str="yaml"


class SymbolKind(enum.Enum):
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


class SymbolInformation(BaseModel):
    """
    Represents information about programming constructs like variables, classes, interfaces etc.
    Constructs a new SymbolInformation instance.

    :param str name: The name of this symbol.
    :param int kind: The kind of this symbol.
    :param bool Location: The location of this symbol. The location's range is used by a tool
                            to reveal the location in the editor. If the symbol is selected in the
                            tool the range's start information is used to position the cursor. So
                            the range usually spans more then the actual symbol's name and does
                            normally include things like visibility modifiers.

                            The range doesn't have to denote a node range in the sense of a abstract
                            syntax tree. It can therefore not be used to re-construct a hierarchy of
                            the symbols.
    :param str containerName: The name of the symbol containing this symbol. This information is for
                                user interface purposes (e.g. to render a qualifier in the user interface
                                if necessary). It can't be used to re-infer a hierarchy for the document
                                symbols.
    :param bool deprecated: Indicates if this symbol is deprecated.
    """
    name: str
    kind: Any
    location: Any
    containerName: Optional[str] = None
    deprecated: Optional[bool] = False
    def __init__(self, **data):
        data["location"] = to_type(data["location"], Location)
        data["kind"] = SymbolKind(data["kind"])        
        super().__init__(**data)


class ParameterInformation(BaseModel):
    """
    Represents a parameter of a callable-signature. A parameter can
    have a label and a doc-comment.
            Constructs a new ParameterInformation instance.

    :param str label: The label of this parameter. Will be shown in the UI.
    :param str documentation: The human-readable doc-comment of this parameter. Will be shown in the UI but can be omitted.
    """
    label: str
    documentation: str


class SignatureInformation(BaseModel):
    """
    Represents the signature of something callable. A signature
    can have a label, like a function-name, a doc-comment, and
    a set of parameters.
    Constructs a new SignatureInformation instance.

    :param str label: The label of this signature. Will be shown in the UI.
    :param str documentation: The human-readable doc-comment of this signature. Will be shown in the UI but can be omitted.
    :param ParameterInformation[] parameters: The parameters of this signature.
    """
    label: str
    documentation: Optional[str] = ''
    parameters: List[Any] = []
    def __init__(self, **data):
        data["parameters"] = [to_type(parameter, ParameterInformation) for parameter in data["parameters"]]
        super().__init__(**data)


class SignatureHelp(BaseModel):
    """
    Signature help represents the signature of something
    callable. There can be multiple signature but only one
    active and only one active parameter.
    Constructs a new SignatureHelp instance.

    :param SignatureInformation[] signatures: One or more signatures.
    :param int activeSignature:
    :param int activeParameter:
    """
    activeSignature: Optional[int] = 0
    activeParameter: Optional[int] = 0
    signatures: List[Any]
    def __init__(self, **data):
        data["signatures"] = [to_type(signature, SignatureInformation) for signature in data["signatures"]]


class CompletionTriggerKind(object):
    Invoked: int = 1
    TriggerCharacter: int = 2
    TriggerForIncompleteCompletions: int = 3

class CompletionContext(BaseModel):
    """
    Contains additional information about the context in which a completion request is triggered.
    Constructs a new CompletionContext instance.

    :param CompletionTriggerKind triggerKind: How the completion was triggered.
    :param str triggerCharacter: The trigger character (a single character) that has trigger code complete.
                                    Is undefined if `triggerKind !== CompletionTriggerKind.TriggerCharacter`
    """
    model_config = ConfigDict(extra='allow')
    triggerKind: int
    def __init__(self, **data):
        for k in data.keys():
            if k == "triggerCharacter":
                curr_val = data.get(k)
                # if value for triggerCharacter is None or non string
                # then ensure attribute doesnt exist in the object
                if curr_val is None and not isinstance(curr_val, str):
                    data.pop(k)
            elif k not in self.__class__.model_fields.keys():
                data.pop(k)
        super().__init__(**data)


class TextEdit(BaseModel):
    """
    A textual edit applicable to a text document.
    :param Range range: The range of the text document to be manipulated. To insert
                        text into a document create a range where start === end.
    :param str newText: The string to be inserted. For delete operations use an empty string.
    """
    range: Range
    newText: str

class InsertTextFormat(object):
    PlainText: int = 1
    Snippet: int = 2

class CompletionItem(BaseModel):
    label: str
    kind: Optional[int] = None
    detail: Optional[str] = None
    documentation: Optional[str] = None
    deprecated: Optional[bool] = None
    preselect: Optional[bool] = None
    sortText: Optional[str] = None
    filterText: Optional[str] = None
    insertText: Optional[str] = None
    insertTextFormat: Optional[int] = None
    textEdit: Optional[TextEdit] = None
    additionalTextEdits: Optional[TextEdit] = None
    commitCharacters: Optional[str] = None
    command: Optional[Command] = None
    data: Optional[Any] = None
    score: float = 0.0


class CompletionItemKind(enum.Enum):
    Text = 1
    Method = 2
    Function = 3
    Constructor = 4
    Field = 5
    Variable = 6
    Class = 7
    Interface = 8
    Module = 9
    Property = 10
    Unit = 11
    Value = 12
    Enum = 13
    Keyword = 14
    Snippet = 15
    Color = 16
    File = 17
    Reference = 18
    Folder = 19
    EnumMember = 20
    Constant = 21
    Struct = 22
    Event = 23
    Operator = 24
    TypeParameter = 25


class CompletionList(BaseModel):
    """
    Represents a collection of [completion items](#CompletionItem) to be presented in the editor.
    Constructs a new CompletionContext instance.
    :param bool isIncomplete: This list it not complete. Further typing should result in recomputing this list.
    :param CompletionItem items: The completion items.
    """
    isIncomplete: bool
    items: List[Any]
    def __init__(self, **data):
        data["items"] = [to_type(it, CompletionItem) for it in data["items"]]
        super().__init__(**data)


class ErrorCodes(enum.Enum):
    # Defined by JSON RPC
    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603
    serverErrorStart = -32099
    serverErrorEnd = -32000
    ServerNotInitialized = -32002
    UnknownErrorCode = -32001

    # Defined by the protocol.
    RequestCancelled = -32800
    ContentModified = -32801

class ResponseError(Exception):
    def __init__(self, code, message, data = None):
        self.code = code
        self.message = message
        if data:
            self.data = data
