from unittest import TestCase, main as unittest_main

from recipe_search import unicode_to_ascii


class UnicodToASCIITest(TestCase):
    
    def test_unicode_to_ascii(self):
        return_value = unicode_to_ascii(text='niçoise')
        expected_value = 'nicoise'
        self.assertEqual(expected_value, return_value)


if __name__ == '__main__':
    unittest_main()
