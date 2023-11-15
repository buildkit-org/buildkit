class SingletonMeta(type):
    _instances: dict[type, object] = {}

    def __call__(cls: type, *args: tuple, **kwargs: dict) -> object:
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance

        return cls._instances[cls]
