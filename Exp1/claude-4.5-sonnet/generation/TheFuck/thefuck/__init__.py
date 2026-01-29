"""TheFuck - Magnificent app which corrects your previous console command."""

__version__ = '3.32'

from thefuck.types import Command
from thefuck.corrector import get_corrected_commands

__all__ = ['Command', 'get_corrected_commands']