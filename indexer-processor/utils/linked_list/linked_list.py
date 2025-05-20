from . import linked_list_node


class LinkedList:
    _head: linked_list_node.LinkedListNode
    _size: int

    def __init__(self):
        self._head = linked_list_node.LinkedListNode()
        self._size = 0

    def add(self, docId: int):
        self._size += 1

        curr = self._head

        while curr.next and curr.next.docId < docId:
            curr = curr.next

        node = linked_list_node.LinkedListNode(docId, curr.next)
        curr.next = node
