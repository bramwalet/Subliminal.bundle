import logging

def registerLoggingHander(dependencies):
    plexHandler = PlexLoggerHandler()
    for dependency in dependencies:     
        Log.Debug("Registering LoggerHandler for dependency: %s" % dependency)   
        log = logging.getLogger(dependency)
        log.setLevel('DEBUG')
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