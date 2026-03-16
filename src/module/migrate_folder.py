from shutil import move
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import Parameter


class MigrateFolder:
    def __init__(
        self,
        parameter: "Parameter",
    ):
        self.ROOT = parameter.ROOT
        self.root = parameter.root
        self.folder = parameter.folder_name

    def compatible(self):
        for i in (
            "Music",
            "Data",
            "Live",
        ):
            if (old := self.ROOT.parent.joinpath(i)).exists() and not (
                new_ := self.ROOT.joinpath(i)
            ).exists():
                try:
                    move(old, new_)
                except Exception as e:
                    # 忽略文件占用错误
                    pass
        if self.ROOT != self.root:
            return
        if (old := self.ROOT.parent.joinpath(self.folder)).exists() and not (
            new_ := self.ROOT.joinpath(self.folder)
        ).exists():
            try:
                move(old, new_)
            except Exception as e:
                # 忽略文件占用错误
                pass
        folders = self.ROOT.parent.iterdir()
        for i in folders:
            if not i.is_dir():
                continue
            if len(i.name) > 10 and i.name[1:3] == "ID":
                try:
                    move(i, self.ROOT.joinpath(i.name))
                except Exception as e:
                    # 忽略文件占用错误
                    pass
