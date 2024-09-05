import sys
import unittest
from unittest.mock import MagicMock

# Add the src directory to the Python path
sys.path.insert(0, './src')

from parakeet.utils import has_opt_in_role

class TestHasOptInRole(unittest.TestCase):

    def setUp(self):
        """
        Set up the test environment by creating mock objects and assigning them to instance variables.

        Mock objects created:
        - self.user: A MagicMock object representing a user.
        - self.role1: A MagicMock object representing a role.
        - self.role2: A MagicMock object representing another role.

        The names of the roles are set as follows:
        - self.role1.name = "role1"
        - self.role2.name = "role2"

        The user's roles are set as a list containing self.role1 and self.role2.

        This method is executed before each test case in the test suite.
        """
        self.user = MagicMock()
        self.role1 = MagicMock()
        self.role2 = MagicMock()
        self.role1.name = "role1"
        self.role2.name = "role2"
        self.user.roles = [self.role1, self.role2]

    def test_user_has_role(self):
        """
        Test case to verify if a user has a specific role.

        This test asserts that the function `has_opt_in_role` returns True when the user has the specified role.

        Parameters:
        - self: The test case instance.

        Returns:
        - None
        """
        self.assertTrue(has_opt_in_role(self.user, "role1"))

    def test_user_does_not_have_role(self):
        """
        Test case to verify that the user does not have a specific role.

        This test asserts that the function `has_opt_in_role` returns False when
        checking if the user has the role "role3".

        """
        self.assertFalse(has_opt_in_role(self.user, "role3"))

    def test_exception_handling(self):
        """
        Test case for exception handling.

        This test verifies that an exception is raised when the user's roles are set to None.
        It checks if the function has_opt_in_role correctly handles the exception and returns False.

        """
        self.user.roles = None  # This will cause an exception in the function
        self.assertFalse(has_opt_in_role(self.user, "role1"))

if __name__ == '__main__':
    unittest.main()