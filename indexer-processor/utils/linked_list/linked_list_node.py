class LinkedListNode:
    val: int
    next: 'LinkedListNode | None'

    def __init__(self, val: int = -1, next: 'LinkedListNode | None' = None) -> None:
        self.val = val
        self.next = next
