from flask import current_app


def print_loaded_config(app):
    with open('loaded_config.txt', 'w') as config:
        for key, value in app.config.items():
            print(f'{key} = {value}', file=config)


def log_message(user, action, message, level="info"):
    """
    Generic logger function to handle different log levels.

    Args:
        user: The user object (can be None for anonymous users).
        action: The action being logged.
        message: The log message.
        level: The log level ("info", "warning", "error").
    """
    logger = current_app.logger
    user_info = "Anonymous" if user is None else f"{user.username} ({user.id})"
    log_message = f"{user_info}; {action}; {message}"

    if level == "info":
        logger.info(log_message, stacklevel=3)
    elif level == "warning":
        logger.warning(log_message, stacklevel=3)
    elif level == "error":
        logger.error(log_message, stacklevel=3)
    else:
        raise ValueError(f"Invalid log level: {level}")


def log_info(user, action, message):
    log_message(user, action, message, level="info")


def log_warning(user, action, message):
    log_message(user, action, message, level="warning")


def log_error(user, action, message):
    log_message(user, action, message, level="error")
