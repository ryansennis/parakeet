import unittest
from unittest.mock import MagicMock
from src.parakeet.utils import has_opt_in_role

class UtilsTestCase(unittest.TestCase):
    def test_has_opt_in_role(self):
        # Create a mock user object
        user = MagicMock()
        user.name = "John"
        role1 = MagicMock()
        role1.name = "Role1"
        role2 = MagicMock()
        role2.name = "Role2"
        role3 = MagicMock()
        role3.name = "Role3"
        user.roles = [role1, role2, role3]

        # Test when the user has the opt-in role
        self.assertTrue(has_opt_in_role(user, "Role2"))

        # Test when the user does not have the opt-in role
        self.assertFalse(has_opt_in_role(user, "Role4"))

if __name__ == "__main__":
    unittest.main()
