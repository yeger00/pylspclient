import os

from common import where_is_bin


class planmuml_bin:
    def __init__(self) -> None:
        self.jarpath = os.path.join(os.path.dirname(
            __file__), "plantuml-1.2024.6.jar")
        self.java = where_is_bin("java")
        pass

    def conver(self, uml, ouput):
        if os.path.exists(self.jarpath) == False:
            raise Exception("Exception jar not found")
        if self.java is None or os.path.exists(self.java) == False:
            raise Exception("Exception java not found")
        os.system("%s -jar %s %s " % (self.java, self.jarpath, uml))
        os.system("%s -jar %s %s -utxt" % (self.java, self.jarpath, uml))


plamuml_jar = planmuml_bin()


def planuml_to_image(file, output):
    plamuml_jar.conver(file, output)
