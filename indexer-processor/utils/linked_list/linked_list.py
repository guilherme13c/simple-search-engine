from . import linked_list_node


class LinkedList:
    _head: linked_list_node.LinkedListNode
    _size: int

    def __init__(self):
        self._head = linked_list_node.LinkedListNode()
        self._size = 0

    def add(self, val: int):
        self._size += 1

        curr = self._head

        while curr and curr.next and curr.next.val < val:
            curr = curr.next

        node = linked_list_node.LinkedListNode(val, curr.next)
        curr.next = node

    def index(self, val: int) -> int:
        curr = self._head.next
        idx = 0
        while curr:
            if curr.val == val:
                return idx
            curr = curr.next
            idx += 1
        return -1
