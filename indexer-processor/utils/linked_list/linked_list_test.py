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
        node = self.ll._head.next
        self.assertIsNotNone(node)
        if node is None:
            return

        self.assertEqual(node.val, 10)
        self.assertIsNone(node.next)

    def test_add_in_order(self):
        values = [5, 1, 3]
        for v in values:
            self.ll.add(v)

        self.assertEqual(self.ll._size, 3)
        curr = self.ll._head.next
        sorted_vals = []
        while curr:
            sorted_vals.append(curr.val)
            curr = curr.next
        self.assertEqual(sorted_vals, [1, 3, 5])

    def test_add_descending(self) -> None:
        for v in [10, 9, 8, 7]:
            self.ll.add(v)

        expected = [7, 8, 9, 10]
        curr = self.ll._head.next
        result = []
        while curr:
            result.append(curr.val)
            curr = curr.next
        self.assertEqual(result, expected)

    def test_index_empty(self) -> None:
        res = self.ll.index(420)
        self.assertEqual(res, -1)

    def test_index(self):
        vs = [10, 2, 8, 15]

        for v in vs:
            self.ll.add(v)

        self.assertEqual(self.ll.index(2), 0)
        self.assertEqual(self.ll.index(8), 1)
        self.assertEqual(self.ll.index(10), 2)
        self.assertEqual(self.ll.index(15),3)


if __name__ == '__main__':
    unittest.main()
