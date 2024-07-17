from history import history
from textual.suggester import SuggestFromList, SuggestionReady
from dircomplete import dir_complete_db
from commandline import convert_command_args,view_key,find_key
class input_suggestion(SuggestFromList):
    _history: history
    dircomplete: dir_complete_db

    async def _get_suggestion(self, requester, value: str) -> None:
        """Used by widgets to get completion suggestions.

        Note:
            When implementing custom suggesters, this method does not need to be
            overridden.

        Args:
            requester: The message target that requested a suggestion.
            value: The current value to complete.
        """

        args = convert_command_args(value)
        suggestion = None
        if suggestion is None:
            suggestion = self.complete_view(value, args)

        if suggestion != None:
            requester.post_message(SuggestionReady(value, suggestion))

        normalized_value = value if self.case_sensitive else value.casefold()
        if self.cache is None or normalized_value not in self.cache:
            suggestion = await self.get_suggestion(normalized_value)
            if self.cache is not None:
                self.cache[normalized_value] = suggestion
        else:
            suggestion = self.cache[normalized_value]

        if suggestion is None:
            suggestion = self.complete_path(value, args)
        if suggestion is None:
            ret = list(
                filter(lambda x: x.startswith(value), self._history._data))
            if len(ret) > 0:
                suggestion = ret[0]
        if suggestion is None:
            return
        requester.post_message(SuggestionReady(value, suggestion))

    def complete_view(self, value: str, args):
        view_name = ["code", "explore", "symbol", "history"]
        try:
            if value.startswith(view_key) == False:
                return None
            if len(args) == 2:
                for a in view_name:
                    if a.startswith(args[1]):
                        args[1] = a
                        return " ".join(args)

        except:
            pass
        return None

    def complete_path(self, value: str, args):
        try:
            # if self.root is None: return None
            if value.startswith(find_key) == False:
                return None
            if self.dircomplete != None:
                if len(args) == 2:
                    s = self.dircomplete.find(args[1])
                    if s != None:
                        part1 = value[0:value.find(args[1])]
                        return part1 + "/" + s

            # ret = find_dirs_os_walk(self.root, args[1])
            # if len(ret):
            # return ret[0]
        except Exception as e:
            print(e)
            pass
        return None
