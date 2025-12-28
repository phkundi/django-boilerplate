"""
Colored logging formatter for better console output during development.
"""

import logging
import sys


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log levels and improves readability.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
        "BOLD": "\033[1m",  # Bold
        "DIM": "\033[2m",  # Dim
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Check if we're outputting to a terminal that supports colors
        self.use_colors = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()

    def format(self, record):
        if not self.use_colors:
            # Fall back to standard formatting if colors aren't supported
            return super().format(record)

        # Get the original formatted message
        log_message = super().format(record)

        # Get color for the log level
        level_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        bold = self.COLORS["BOLD"]
        dim = self.COLORS["DIM"]

        # Format different parts with colors
        # Extract components from the formatted message
        parts = log_message.split("] ", 2)
        if len(parts) >= 3:
            timestamp = parts[0] + "]"
            level_and_location = parts[1] + "]"
            message = parts[2]

            # Color the level name within the level_and_location part
            level_name = record.levelname
            colored_level = f"{level_color}{bold}{level_name}{reset}"
            level_and_location = level_and_location.replace(level_name, colored_level)

            # Format the final message
            formatted_message = (
                f"{dim}{timestamp}{reset} "
                f"{level_and_location} "
                f"{level_color}{message}{reset}"
            )
        else:
            # Fallback if parsing fails
            formatted_message = f"{level_color}{log_message}{reset}"

        return formatted_message


class DevelopmentFormatter(ColoredFormatter):
    """
    Enhanced formatter for development with more detailed information.
    """

    def format(self, record):
        if not self.use_colors:
            return super().format(record)

        # Add more context in development
        reset = self.COLORS["RESET"]
        dim = self.COLORS["DIM"]
        level_color = self.COLORS.get(record.levelname, reset)
        bold = self.COLORS["BOLD"]

        # Create a more detailed format
        timestamp = self.formatTime(record, "%H:%M:%S")

        formatted_message = (
            f"{dim}[{timestamp}]{reset} "
            f"{level_color}{bold}{record.levelname:<8}{reset} "
            f"{dim}{record.name}:{record.lineno}{reset} "
            f"{level_color}{record.getMessage()}{reset}"
        )

        # Add exception info if present
        if record.exc_info:
            formatted_message += f"\n{self.formatException(record.exc_info)}"

        return formatted_message
