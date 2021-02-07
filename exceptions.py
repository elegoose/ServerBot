class ServerNotFound(Exception):
    pass


class ServerAlreadyRunning(Exception):
    pass


class ServerNotYetImplemented(Exception):
    pass


class CantAccessRemoteServer(Exception):
    pass


class UnexpectedRunError(Exception):
    pass


class ServerIsNotRunning(Exception):
    pass


class CantClosePopulatedServer(Exception):
    pass


class NoMinecraftServerRunning(Exception):
    pass


class PlayerNotInGame(Exception):
    pass


class AlreadyRegistered(Exception):
    pass


class NoCoordinatesSaved(Exception):
    pass


class NotRegistered(Exception):
    pass


class NoCoordinatesWithThatName(Exception):
    pass


class NoDuplicateNamesAllowed(Exception):
    pass


class NoDuplicateCoordinatesAllowed(Exception):
    pass


class BadCoordinateFormat(Exception):
    pass


class MissingArgument(Exception):
    pass
