import logging


def registerLoggingHander(dependencies, level="ERROR"):
    plexHandler = PlexLoggerHandler()
    for dependency in dependencies:
        Log.Debug("Registering LoggerHandler for dependency: %s" % dependency)
        log = logging.getLogger(dependency)
        # remove previous plex logging handlers
        # fixme: this is not the most elegant solution...
        for handler in log.handlers:
            if isinstance(handler, PlexLoggerHandler):
                log.removeHandler(handler)

        log.setLevel(level)
        log.addHandler(plexHandler)


class PlexLoggerHandler(logging.StreamHandler):
    def __init__(self, level=0):
        super(PlexLoggerHandler, self).__init__(level)

    def getFormattedString(self, record):
        return record.name + ": " + record.getMessage()

    def emit(self, record):
        if record.levelno == logging.DEBUG:
            Log.Debug(self.getFormattedString(record))
        elif record.levelno == logging.INFO:
            Log.Info(self.getFormattedString(record))
        elif record.levelno == logging.WARNING:
            Log.Warn(self.getFormattedString(record))
        elif record.levelno == logging.ERROR:
            Log.Error(self.getFormattedString(record))
        elif record.levelno == logging.CRITICAL:
            Log.Critical(self.getFormattedString(record))
        elif record.levelno == logging.FATAL:
            Log.Exception(self.getFormattedString(record))
        else:
            Log.Error("UNKNOWN LEVEL: %s", record.getMessage())


console_handler = logging.StreamHandler()
console_formatter = Framework.core.LogFormatter('%(asctime)-15s - %(name)-32s (%(thread)x) :  %(levelname)s (%(module)s:%(lineno)d) - %(message)s')
console_handler.setFormatter(console_formatter)
