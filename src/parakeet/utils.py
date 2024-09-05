import logging
import discord

# Configure logging
logger = logging.getLogger(__name__)

def has_opt_in_role(user: discord.User, role_name: str) -> bool:
    """
    Checks if a user has the specified opt-in role.

    Parameters:
    - user: The user to check.
    - role_name: The name of the opt-in role.

    Returns:
    - True if the user has the opt-in role, False otherwise.
    """
    try:
        logger.debug(f"Checking if user {user.name} has opt-in role {role_name}")
        return any(role.name == role_name for role in user.roles)
    except Exception as e:
        logger.error(f"An error occurred while checking opt-in role: {e}", exc_info=True)
        return False