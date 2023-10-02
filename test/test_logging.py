import unittest


class MyTestCase(unittest.TestCase):
    def test_something(self):
        from zenlog import log
        log.debug('A debug message')
        log.info('An info message')
        log.warning('A warning')
        log.error('An error message')
        log.critical('A critical error message')
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
