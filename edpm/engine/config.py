# config_namespace.py

class ConfigNamespace:
    """
    Class that behaves like both an object and a dictionary.
    Example usage:
        cfg = ConfigNamespace(app_name="myapp", version="1.2.3")
        print(cfg.app_name)
        print(cfg["version"])
        cfg["repo"] = "https://example.com"
        print(cfg.repo)
    """

    def __init__(self, **kwargs):
        # Store all kwargs in __dict__
        self.__dict__.update(kwargs)

    def __repr__(self):
        keys = sorted(self.__dict__)
        items = (f"{k}={v}" for k,v in self.__dict__.items())
        return f"{type(self).__name__}({', '.join(items)})"

    def __eq__(self, other):
        if not isinstance(other, ConfigNamespace):
            return False
        return self.__dict__ == other.__dict__

    # Let config["key"] behave like config.key
    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __contains__(self, key):
        return key in self.__dict__

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def update(self, other):
        """Merge fields from another ConfigNamespace or dict into this one."""
        if isinstance(other, ConfigNamespace):
            self.__dict__.update(other.__dict__)
        elif isinstance(other, dict):
            self.__dict__.update(other)
        else:
            raise TypeError("update() requires dict or ConfigNamespace")

    def keys(self):
        return self.__dict__.keys()

    def items(self):
        return self.__dict__.items()

    def values(self):
        return self.__dict__.values()

    def pop(self, key, default=None):
        return self.__dict__.pop(key, default)
