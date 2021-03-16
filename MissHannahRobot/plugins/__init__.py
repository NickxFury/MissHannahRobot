from MissHannahRobot import LOAD, LOGGER, NO_LOAD


def __list_all_plugins():
    import glob
    from os.path import basename, dirname, isfile

    # This generates a list of plugins in this folder for the * in __main__ to work.
    mod_paths = glob.glob(dirname(__file__) + "/*.py")
    all_plugins = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]

    if LOAD or NO_LOAD:
        to_load = LOAD
        if to_load:
            if not all(
                any(mod == module_name for module_name in all_plugins)
                for mod in to_load
            ):
                LOGGER.error("Invalid loadorder names. Quitting.")
                quit(1)

            all_plugins = sorted(set(all_plugins) - set(to_load))
            to_load = list(all_plugins) + to_load

        else:
            to_load = all_plugins

        if NO_LOAD:
            LOGGER.info("Not loading: {}".format(NO_LOAD))
            return [item for item in to_load if item not in NO_LOAD]

        return to_load

    return all_plugins


ALL_MODULES = __list_all_plugins()
LOGGER.info("Modules to load: %s", str(ALL_MODULES))
__all__ = ALL_MODULES + ["ALL_MODULES"]
