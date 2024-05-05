from adhoccomputing.GenericModel import GenericModel
import matplotlib.pyplot as plt
from queue import Queue, Empty
from component_registry import ComponentRegistry
from adhoccomputing.Generics import *
from adhoccomputing.Experimentation.Topology import Topology

total_nodes = 50
SYSTEM_SIZE_BITS = 7

class ApplicationLayerMessageTypes(Enum):
    FIND_SUCCESSOR_REQ = "FIND_SUCCESSOR_REQ"
    FIND_SUCCESSOR_RESP = "FIND_SUCCESSOR_RESP"
    FIND_PREDECESSOR_REQ = "FIND_PREDECESSOR_REQ"
    FIND_PREDECESSOR_RESP = "FIND_PREDECESSOR_RESP"
    FIND_CLOSEST_PRECEDING_FINGER_REQ = "FIND_CLOSEST_PRECEDING_FINGER_REQ"
    FIND_CLOSEST_PRECEDING_FINGER_RESP = "FIND_CLOSEST_PRECEDING_FINGER_RESP"


class ApplicationLayerMessageHeader(GenericMessageHeader):
    def __init__(self, messagetype, source, destination):
        super().__init__(messagetype, source, destination)


class NotifyPayload:
    def __init__(self, node):
        self.node = node


class FingerTableEntry:
    def __init__(self, start, node):
        self.start = start
        self.node = node

    def __repr__(self):
        return f"FingerTableEntry(start={self.start}, node={self.node.node_id})"

    def __str__(self):
        return f"FingerTableEntry: {self.start}, Node: {self.node.node_id}"


class FingerTable:
    def __init__(self, node):
        self.node = node
        self.entries = [
            FingerTableEntry((node.node_id + 2**i) % 2**SYSTEM_SIZE_BITS, node)
            for i in range(SYSTEM_SIZE_BITS)
        ]

    def __repr__(self):
        entries_repr = ", ".join(repr(entry) for entry in self.entries)
        return f"FingerTable(node={self.node.node_id}, entries=[{entries_repr}])"

    def __str__(self):
        entries_str = "\n".join(str(entry) for entry in self.entries)
        return f"FingerTable:\nNode: {self.node.node_id}\nEntries:\n{entries_str}"

    def update(self, i, s):
        self.entries[i].node = s


def between(_id: int, left: int, right: int, inclusive_left=False, inclusive_right=True) -> bool:
    """
    This code is taken from https://github.com/melzareix/chord-dht/blob/master/src/chord/helpers.py#L33-L46
    Check if _id lies between left and right in a circular ring.
    """
    ring_sz = 2**SYSTEM_SIZE_BITS
    if left != right:
        if inclusive_left:
            left = (left - 1 + ring_sz) % ring_sz
        if inclusive_right:
            right = (right + 1) % ring_sz
    if left < right:
        return left < _id < right
    else:
        return (_id > max(left, right)) or (_id < min(left, right))


class ChordComponent(GenericModel):
    """
    ChordComponent is a component that implements the Chord protocol.
    The Chord protocol is a distributed lookup protocol that provides a way to locate a node in a network of nodes given its key.
    This component is responsible for maintaining the finger table and the successor and predecessor pointers.
    The use of ahc components is different from its purpose since the ahc is hierarchical
    on the other hand there is no hierarchy in the Chord protocol which made it little bit hard to implement the Chord protocol using ahc.

    There are queues for each type of message that is sent to the peer.
    The queues are used to get the response from the peer.
    When the response is received, the response is put in the queue.
    The response is then retrieved from the queue and returned to the caller.

    The nodes in the network are identified by their node_id and joins the network by calling the join() method.
    """

    def __init__(
        self,
        componentname,
        componentinstancenumber,
        context=None,
        configuration_parameters=None,
        num_worker_threads=1,
        topology=None,
    ):
        super().__init__(
            componentname,
            componentinstancenumber,
            context,
            configuration_parameters,
            num_worker_threads,
            topology,
        )

        self.eventhandlers["msgfrompeer"] = self.on_message_from_peer

        self.find_successor_result_queue = Queue()
        self.find_predecessor_result_queue = Queue()
        self.find_closest_preceding_finger_result_queue = Queue()

        self.predecessor = None
        self.node_id = componentinstancenumber
        self.registry = ComponentRegistry()
        self.finger_table = FingerTable(self)
        self.keys = set()

    def __repr__(self):
        return f"ChordComponent(componentname={self.componentname}, componentinstancenumber={self.componentinstancenumber}, node_id={self.node_id})"

    def on_message_from_peer(self, eventobj: Event):
        chord_message = eventobj.eventcontent
        hdr = chord_message.header
        payload = chord_message.payload

        # Check if the message is for this node
        if hdr.messageto != self:
            return

        if hdr.messagetype == ApplicationLayerMessageTypes.FIND_SUCCESSOR_REQ:
            successor = self._find_successor(payload)
            resp = GenericMessage(
                ApplicationLayerMessageHeader(
                    ApplicationLayerMessageTypes.FIND_SUCCESSOR_RESP,
                    self.componentinstancenumber,
                    hdr.messagefrom,
                ),
                successor,
            )
            self.send_peer(Event(self, EventTypes.MFRP, resp))

        elif hdr.messagetype == ApplicationLayerMessageTypes.FIND_SUCCESSOR_RESP:
            self.find_successor_result_queue.put_nowait(payload)

        elif hdr.messagetype == ApplicationLayerMessageTypes.FIND_PREDECESSOR_REQ:
            predecessor = self._find_predecessor(payload)
            resp = GenericMessage(
                ApplicationLayerMessageHeader(
                    ApplicationLayerMessageTypes.FIND_PREDECESSOR_RESP,
                    self.componentinstancenumber,
                    hdr.messagefrom,
                ),
                predecessor,
            )
            self.send_peer(Event(self, EventTypes.MFRP, resp))

        elif hdr.messagetype == ApplicationLayerMessageTypes.FIND_PREDECESSOR_RESP:
            self.find_predecessor_result_queue.put_nowait(payload)

        elif hdr.messagetype == ApplicationLayerMessageTypes.FIND_CLOSEST_PRECEDING_FINGER_REQ:
            closest_finger = self._closest_preceding_finger(payload)
            resp = GenericMessage(
                ApplicationLayerMessageHeader(
                    ApplicationLayerMessageTypes.FIND_CLOSEST_PRECEDING_FINGER_RESP,
                    self.componentinstancenumber,
                    hdr.messagefrom,
                ),
                closest_finger,
            )
            self.send_peer(Event(self, EventTypes.MFRP, resp))

        elif hdr.messagetype == ApplicationLayerMessageTypes.FIND_CLOSEST_PRECEDING_FINGER_RESP:
            self.find_closest_preceding_finger_result_queue.put(payload)

    def successor(self):
        return self.finger_table.entries[0].node

    def inner_queue_handler(self, queue):
        return queue.get()

    def create_remote_event(self, message_type: ApplicationLayerMessageTypes, queue, node_id):
        #import ipdb; ipdb.set_trace()
        other_node = self.registry.get_arbitrary_component(
            self.componentname, self.componentinstancenumber
        )
        if other_node == self:
            if message_type == ApplicationLayerMessageTypes.FIND_SUCCESSOR_REQ:
                return self._find_successor(node_id)
            elif message_type == ApplicationLayerMessageTypes.FIND_PREDECESSOR_REQ:
                return self._find_predecessor(node_id)
            elif message_type == ApplicationLayerMessageTypes.FIND_CLOSEST_PRECEDING_FINGER_REQ:
                return self._closest_preceding_finger(node_id)
        req = GenericMessage(
            ApplicationLayerMessageHeader(message_type, self, other_node),
            node_id,
        )
        self.send_peer(Event(self, EventTypes.MFRP, req))
        try:
            return queue.get(timeout=0.1)  # Add timeout here
        except Empty:    # handle exception here
            return None

    def find_successor(self, node_id):
        return self.create_remote_event(
            ApplicationLayerMessageTypes.FIND_SUCCESSOR_REQ,
            self.find_successor_result_queue,
            node_id,
        )

    def find_predecessor(self, node_id):
        return self.create_remote_event(
            ApplicationLayerMessageTypes.FIND_PREDECESSOR_REQ,
            self.find_predecessor_result_queue,
            node_id,
        )

    def closest_preceding_finger(self, node_id):
        return self.create_remote_event(
            ApplicationLayerMessageTypes.FIND_CLOSEST_PRECEDING_FINGER_REQ,
            self.find_closest_preceding_finger_result_queue,
            node_id,
        )

    def _find_successor(self, node_id):
        self.registry.find_successor += 1
        if self.node_id == self.successor().node_id or self.node_id == self.predecessor.node_id:
            return self
        else:
            predecessor = self._find_predecessor(node_id)
            return predecessor.successor()

    def _find_predecessor(self, node_id):
        self.registry.find_predecessor += 1
        other_node = self
        while not between(
            node_id,
            other_node.node_id,
            other_node.successor().node_id,
            inclusive_left=False,
            inclusive_right=True,
        ):
            other_node = other_node._closest_preceding_finger(node_id)
        return other_node

    def _closest_preceding_finger(self, node_id):
        self.registry.closest_preceding_finger += 1
        for i in range(SYSTEM_SIZE_BITS - 1, -1, -1):
            if between(
                self.finger_table.entries[i].node.node_id,
                self.node_id,
                node_id,
                inclusive_left=False,
                inclusive_right=False,
            ):
                return self.finger_table.entries[i].node
        return self

    def init_finger_table(self):
        succ_node = self.find_successor(self.finger_table.entries[0].start)
        self.finger_table.update(0, succ_node)

        self.registry.add_component(self)
        self.predecessor = succ_node.predecessor
        succ_node.predecessor = self
        self.predecessor.finger_table.update(0, self)
        # succ_node.finger_table.entries[0].node = self
        for i in range(SYSTEM_SIZE_BITS - 1):
            if between(
                self.finger_table.entries[i + 1].start,
                self.node_id,
                self.finger_table.entries[i].node.node_id,
                inclusive_left=True,
                inclusive_right=False,
            ):
                self.finger_table.entries[i + 1].node = self.finger_table.entries[i].node
            else:
                node = self.find_successor(self.finger_table.entries[i + 1].start)
                self.finger_table.update(i + 1, node)

    def make_peer(self, node):
        self.P(node)
        node.P(self)

    def join(self):
        if not self.registry.components:
            # If there are no components in the registry, add this component to the registry
            # Init the finger table for the Single node in the network
            for i in range(SYSTEM_SIZE_BITS):
                self.finger_table.entries[i].node = self
            self.predecessor = self
            self.registry.add_component(self)
        else:
            # Connect the new node as peer to the every other node in the network
            for node in self.registry.components.values():
                self.make_peer(node)
            self.predecessor = None
            self.init_finger_table()
            self.update_other_nodes()
            self.stabilize()
            self.fix_fingers()

    def update_other_nodes(self):
        node = self.registry.get_arbitrary_component(
            self.componentname, self.componentinstancenumber
        )
        for i in range(SYSTEM_SIZE_BITS):
            p = node.find_predecessor((node.node_id - 2**i) % 2**SYSTEM_SIZE_BITS)
            p.update_finger_table(node, i)

    def update_finger_table(self, s, i):
        if between(
            s.node_id,
            self.node_id,
            self.finger_table.entries[i].node.node_id,
            inclusive_left=True,
            inclusive_right=False,
        ):
            self.finger_table.update(i, s)
            p = self.predecessor
            p.update_finger_table(s, i)

    def fix_fingers(self):
        for node in self.registry.components.values():
            for i in range(SYSTEM_SIZE_BITS):
                node.finger_table.update(
                    i, node.find_successor(node.finger_table.entries[i].start)
                )

    def stabilize(self):
        x = self.successor().predecessor
        if between(
            x.node_id,
            self.node_id,
            self.successor().node_id,
            inclusive_left=False,
            inclusive_right=False,
        ):
            self.finger_table.entries[0].node = x
        self.successor().notify(self)

    def notify(self, other_node):
        if self.predecessor is None or between(
            other_node.node_id,
            self.predecessor.node_id,
            self.node_id,
            inclusive_left=False,
            inclusive_right=False,
        ):
            self.predecessor = other_node

    def put(self, key):
        """
        Stores a key in the distributed hash table.
        The key is stored in the node that is responsible for the key.
        """
        node = self.find_successor(key)
        node.keys.add(key)

    def get(self, key):
        """
        The method finds the node that is responsible for the key and returns the key if it is stored in the node.
        """
        node = self.find_successor(key)
        if key in node.keys:
            return key
        else:
            return None


class Node(GenericModel):
    def on_init(self, eventobj: Event):
        pass

    def __init__(
        self,
        componentname,
        componentinstancenumber,
        context=None,
        configurationparameters=None,
        num_worker_threads=5,
        topology=None,
    ):
        super().__init__(
            componentname,
            componentinstancenumber,
            context,
            configurationparameters,
            num_worker_threads,
            topology,
        )
        # SUBCOMPONENTS
        network = {}
        for i in range(2**SYSTEM_SIZE_BITS-1):
            node_id = i
            node = ChordComponent(componentname="Node", componentinstancenumber=node_id)
            network[node_id] = node
            self.components.append(node)

        for node in network.values():
            node.join()
            print(f"Node {node.node_id} has joined")

        keys = [i for i in range(2**SYSTEM_SIZE_BITS)]
        path_lengths = []
        for key in keys:
            node.put(key)
        for key in keys:
            node.registry.find_successor = 0
            node.registry.find_predecessor = 0
            node.registry.closest_preceding_finger = 0
            node.find_successor(key)
            path_lengths.append(node.registry.find_successor + node.registry.find_predecessor + node.registry.closest_preceding_finger)
        plt.hist(path_lengths, density=True, bins=SYSTEM_SIZE_BITS)  # 'auto' will automatically determine the number of bins
        plt.title("Histogram of Path Lengths")
        plt.xlabel("Path Length")
        plt.ylabel("Frequency")
        plt.show()
        pass


def main():
    setAHCLogLevel(ERROR)
    topo = Topology()
    topo.construct_single_node(Node, 0)
    topo.start()
    time.sleep(1)
    topo.exit()


if __name__ == "__main__":
    main()