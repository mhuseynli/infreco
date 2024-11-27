import logging

def get_logger(name="core"):
    """
    Returns a centralized logger for the project.
    """
    return logging.getLogger(name)
