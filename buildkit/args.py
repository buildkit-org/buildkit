from typing import Any, Optional


class Args:
    def __init__(self):
        self.__args = {}

    def __repr__(self) -> str:
        return self.__args.__repr__()

    def __getattr__(self, name: str) -> Any:
        args = super().__getattribute__("_Args__args")
        if name in args:
            return args[name]
        else:
            return super().__getattribute__(name)

    def bind(self, args: Optional[list["Arg"]] = None):
        if args is None:
            return

        names = [n for a in args for n in (a.name, a.shortName)]
        self.__args = {k: v for k, v in self.__args.items() if k in names}

        for arg in args:
            if arg.shortName in self.__args:
                self.__args[arg.name] = self.__args[arg.shortName]
                del self.__args[arg.shortName]

            if arg.name not in self.__args:
                if arg.default is not None:
                    self.__args[arg.name] = arg.default
                elif not arg.optional:
                    raise ValueError(f"Argument {arg.name} is required")
                elif arg.optional:
                    self.__args[arg.name] = None

            val = self.__args[arg.name]
            if val is not None and arg.type in (int, float, bool, str):
                self.__args[arg.name] = arg.type(val)
            elif val is not None and arg.type is list:
                if "," in val:
                    self.__args[arg.name] = val.split(",")
                else:
                    raise ValueError("List arguments must be comma separated")

    @classmethod
    def parse(cls, args: list[str]) -> "Args":
        def is_flag(arg: str):
            return arg.startswith("--") or arg.startswith("-")

        def dash_count(arg: str):
            return 2 if arg.startswith("--") else 1

        pFlag = None
        self = Args()

        for arg in args:
            if is_flag(arg):
                n = dash_count(arg)
                arg = arg[n:]

                if n == 1 and len(arg) > 1:
                    any(map(lambda f: self._Args__args.update({f: True}), arg))
                    continue

                if pFlag is not None:
                    self._Args__args.update[pFlag] = True
                    pFlag = arg
                else:
                    pFlag = arg
            else:
                if pFlag is None:
                    raise ValueError(f"Invalid argument: {arg}")
                else:
                    self._Args__args[pFlag] = arg
                    pFlag = None

        if pFlag is not None:
            self._Args__args[pFlag] = True

        if "v" in self.__args:
            self.__args["verbose"] = True
            del self.__args["v"]

        return self
