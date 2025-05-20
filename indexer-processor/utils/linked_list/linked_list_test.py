import unittest

from .linked_list import LinkedList
from .linked_list_node import LinkedListNode


class TestLinkedList(unittest.TestCase):
    def setUp(self):
        self.ll = LinkedList()

    def test_empty_list(self):
        self.assertEqual(self.ll._size, 0)
        self.assertIsNone(self.ll._head.next)

    def test_add_single(self):
        self.ll.add(10)
        self.assertEqual(self.ll._size, 1)
        node: LinkedListNode = self.ll._head.next # type: ignore
        self.assertIsNotNone(node)
        self.assertEqual(node.docId, 10)
        self.assertIsNone(node.next)

    def test_add_in_order(self):
        values = [5, 1, 3]
        for v in values:
            self.ll.add(v)
        # After insertion, list should be sorted: 1->3->5
        self.assertEqual(self.ll._size, 3)
        curr = self.ll._head.next
        sorted_vals = []
        while curr:
            sorted_vals.append(curr.docId)
            curr = curr.next
        self.assertEqual(sorted_vals, [1, 3, 5])

    def test_add_descending(self):
        for v in [10, 9, 8, 7]:
            self.ll.add(v)
        # Should end up 7,8,9,10
        expected = [7, 8, 9, 10]
        curr = self.ll._head.next
        result = []
        while curr:
            result.append(curr.docId)
            curr = curr.next
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
