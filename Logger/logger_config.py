import logging
import os

def setup_logger():
    """Creates a simple logger that logs messages to a file."""
    log_file = "app.log"

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,  
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8",
    )

    return logging.getLogger()

# Initialize logger
logger = setup_logger()

# Example usage
logger.info("This is an info message.")
logger.error("This is an error message.")
