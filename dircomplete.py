import os
def build_dirs(directory):
    files_found = {}
    for root, dirs, _, in os.walk(directory):
        aa = root.replace(directory, "").split("/")
        if len(aa) > 3:
            continue
        for file in dirs:
            key = os.path.join(root, file)
            files_found[key.replace(directory, "")] = True
            # files_found[file] = os.path.join(root, file)
    return files_found

class dir_complete_db:

    def __init__(self, root) -> None:
        self.root = root
        self.db = build_dirs(root)
        pass

    def find(self, pattern):
        try:
            if self.db[pattern]:
                return str(pattern)[1:]
        except:

            if pattern[-1] == "/":
                # pattern = pattern[:-1]
                # keys= list(filter(lambda x: os.path.dirname(x)==pattern,self.db.keys()))
                root = os.path.join(self.root, pattern[1:])
                keys = os.listdir(root)
                keys = list(
                    filter(lambda x: os.path.isdir(os.path.join(root, x)),
                           keys))
                keys = sorted(keys, key=lambda x: x)
                keys = list(set(list(map(lambda x: x[:2], keys))))
                keys = sorted(keys, key=lambda x: x)
                # return pattern + "|".join(keys[0:20])
                return pattern + "|".join(keys)
            else:
                keys = list(
                    filter(lambda x: x.startswith(pattern), self.db.keys()))
                keys = sorted(keys, key=lambda x: len(x))
                if len(keys):
                    return keys[0][1:]

        return None

def find_dirs_os_walk(directory, pattern):
    files_found = []
    for root, dirs, _, in os.walk(directory):
        for file in dirs:
            if file.startswith(pattern):
                files_found.append(os.path.join(root, file))
    return files_found

def find_files_os_walk(directory, file_extension):
    files_found = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.find(file_extension) > 0:
                files_found.append(os.path.join(root, file))
    return files_found
