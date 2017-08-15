#!/usr/bin/env python

import unittest, re

import ds1054z

HOST = ''

class DS1054zTest(unittest.TestCase):

    def setUp(self):
        self.scope = ds1054z.DS1054Z(HOST)

    def tearDown(self):
        del self.scope

    def test_idn(self):
        regex = re.compile('RIGOL TECHNOLOGIES,DS\d+Z,[a-zA-Z0-9]+,\d{2}.\d{2}.\d{2}.*')
        self.assertTrue( regex.match( self.scope.idn ) )

    def test_display_hide_channels(self):
        self.scope.display_channel(1, False)
        self.scope.display_channel(2, False)
        self.scope.display_channel(3, False)
        self.scope.display_channel(4, False)
        self.scope.display_channel('MATH', False)
        dc = self.scope.displayed_channels
        self.assertEqual(dc, [])

        self.scope.display_channel(4, True)
        self.scope.display_channel('MATH', True)
        dc = self.scope.displayed_channels
        self.assertEqual(dc, ['CHAN4', 'MATH'])

        self.scope.display_only_channel(1)
        dc = self.scope.displayed_channels
        self.assertEqual(dc, ['CHAN1'])
 
    def test_set_mdepth(self):
        self.scope.display_only_channel(1)
        self.scope.write(':TRIGger:MODE EDGE')
        self.scope.write(':TRIGger:EDGe:SOURce CHAN1')
        self.scope.run()

        for value in (12e3, 120e3, 1.2e6, 12e6):
            self.scope.memory_depth = value
            self.assertEqual(self.scope.memory_depth, int(value))

    def test_get_screenshot(self):
        from PIL import Image
        import io
        img_data = self.scope.display_data
        im = Image.open(io.BytesIO(img_data))

    def test_nbytes_displayed(self):
        self.scope.display_only_channel(1)
        self.scope.single()
        self.scope.tforce()

        displayed_data = self.scope.get_waveform_bytes(1, mode='NORMal')
        self.assertEqual(len(displayed_data), 1200)

    def test_nbytes_full(self):
        self.scope.display_only_channel(1)
        self.scope.write(':TRIGger:MODE EDGE')
        self.scope.write(':TRIGger:EDGe:SOURce CHAN1')

        #for mdepth in (120e3, 12e6):
        for mdepth in (12e3, 120e3):

            self.scope.run()
            self.scope.memory_depth = mdepth
            self.scope.single()
            self.scope.tforce()

            self.assertEqual(self.scope.memory_depth, int(mdepth))

            full_data = self.scope.get_waveform_bytes(1, mode='RAW')
            self.assertEqual(len(full_data), int(mdepth))


def main():
    global HOST
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    args = parser.parse_args()
    HOST = args.host
    # call the test
    suite = unittest.TestSuite()
    suite.addTest(DS1054zTest('test_idn'))
    suite.addTest(DS1054zTest('test_display_hide_channels'))
    suite.addTest(DS1054zTest('test_set_mdepth'))
    suite.addTest(DS1054zTest('test_get_screenshot'))
    suite.addTest(DS1054zTest('test_nbytes_displayed'))
    suite.addTest(DS1054zTest('test_nbytes_full'))
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()
