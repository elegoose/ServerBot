class ServerNotFound(Exception):
    pass


class ServerAlreadyRunning(Exception):
    pass


class ServerNotYetImplemented(Exception):
    pass


class CouldntAccessRemoteServer(Exception):
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

class NoCoordinateNameChosen(Exception):
    pass

class NoCoordinatesWithThatName(Exception):
    pass

class WrongAnswer(Exception):
    pass