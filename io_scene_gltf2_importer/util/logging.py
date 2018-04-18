import logging

class Log():
    def __init__(self, loglevel):
        self.logger = logging.getLogger('glTFImporter')
        hdlr = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(int(loglevel))

    def getLevels():
        levels = [
        (str(logging.CRITICAL), "Critical", "", logging.CRITICAL),
        (str(logging.ERROR), "Error", "", logging.ERROR),
        (str(logging.WARNING), "Warning", "", logging.WARNING),
        (str(logging.INFO), "Info", "", logging.INFO),
        (str(logging.NOTSET), "NotSet", "", logging.NOTSET)
        ]

        return levels

    def default():
        return str(logging.ERROR)
