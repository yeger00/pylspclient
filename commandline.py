def convert_command_args(value):
    args = list(filter(lambda x: len(x) > 0, value.split(" ")))
    return args

find_key = "find "
view_key = "view "
clear_key = "clear"
input_command_options = [
    "history", "symbol", "open", "find", "refer", "callin", "ctrl-c", "copy",
    "save", "log", "quit", "grep", "view", "clear"
]
