from . import deprecated_properties, load_code_from_file


def define_env(env):
    load_code_from_file.define_env(env)
    deprecated_properties.define_env(env)
