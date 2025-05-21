from .linked_list_node import LinkedListNode
import random
import math


class LinkedList:
    _head: LinkedListNode
    _size: int

    def __init__(self) -> None:
        self._head = LinkedListNode()
        self._size = 0

    def add(self, val: int) -> None:
        self._size += 1

        curr = self._head

        while curr and curr.skip and curr.skip.val < val:
            curr = curr.skip

        while curr and curr.next and curr.next.val < val:
            curr = curr.next

        node = LinkedListNode(val, curr.next)
        curr.next = node

        if random.random() > 0.05:
            self.build_skips()

    def index(self, val: int) -> int:
        curr = self._head.next
        idx = 0
        while curr:
            if curr.val == val:
                return idx
            curr = curr.next
            idx += 1
        return -1

    def build_skips(self) -> None:
        skip_interval = int(math.sqrt(self._size)) or 1
        curr = self._head.next
        nodes = []

        while curr:
            nodes.append(curr)
            curr = curr.next

        for i in range(len(nodes)):
            if i + skip_interval < len(nodes):
                nodes[i].skip = nodes[i + skip_interval]
            else:
                nodes[i].skip = None

    def __getstate__(self):
        """Serialize as a flat list of values."""
        values = []
        curr = self._head.next
        while curr:
            values.append(curr.val)
            curr = curr.next
        return {'_values': values}

    def __setstate__(self, state):
        """Rebuild the linked list from a list of values."""
        self.__init__()  # reinitialize
        for val in state['_values']:
            self.add(val)
