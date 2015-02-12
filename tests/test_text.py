import unittest

from ppsay.text import *

class TestText(unittest.TestCase):
    def test_is_sublist_single(self):
        self.assertEqual(list(is_sublist([1,2], [1,2,3])), [(0,2)])
        self.assertEqual(list(is_sublist([1,3], [1,2,3])), [])
        self.assertEqual(list(is_sublist([], [1,2,3])), [])
        self.assertEqual(list(is_sublist([1,2,3,4], [1,2,3])), [])
    
    def test_is_sublist_multiple(self):
        self.assertEqual(list(is_sublist([1,2], [1,2,3,1,2])), [(0,2),(3,5)])

    def test_range_overlap(self):
        true_overlaps = [((0,1), (0,1)), # same
                         ((0,4), (1,2)), # middle
                         ((1,4), (3,4)), # upper
                         ((1,4), (1,2)), # lower
                         ((0,4), (3,5)), # disjoint upper
                         ((0,4), (-1,1)), # disjoint lower
                        ]

        for a, b in true_overlaps:
            self.assertTrue(range_overlap(a, b))
            self.assertTrue(range_overlap(b, a))

        false_overlaps = [((0,1), (2,3)), # far
                          ((0,1), (1,2)), # touching
                         ]
        
        for a, b in false_overlaps:
            self.assertFalse(range_overlap(a, b))
            self.assertFalse(range_overlap(b, a))

    def test_get_tokens(self):
        pairs = [("Hello world", ["Hello", "world"], [(0,5), (6,11)]),
                 ("Hello, world", ["Hello", "world"], [(0,5), (7,12)]),
                ]

        for text, tokens, spans in pairs:
            tokens_out, spans_out = get_tokens(text)

            self.assertEqual(tokens_out, tokens)
            self.assertEqual(spans_out, spans)
        

if __name__ == '__main__':
    unittest.main()
