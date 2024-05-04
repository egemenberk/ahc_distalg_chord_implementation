from adhoccomputing.GenericModel import GenericModel
from enum import Enum
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes, GenericMessageHeader, GenericMessagePayload, GenericMessage
import queue
import asyncio
from component_registry import ComponentRegistry
from adhoccomputing.Generics import *
from adhoccomputing.Experimentation.Topology import Topology


SYSTEM_SIZE_BITS = 3


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
        return f'FingerTableEntry(start={self.start}, node={self.node.node_id})'

    def __str__(self):
        return f'FingerTableEntry: {self.start}, Node: {self.node.node_id}'


class FingerTable:
    def __init__(self, node):
        self.node = node
        self.entries = [FingerTableEntry((node.node_id + 2**i) % 2**SYSTEM_SIZE_BITS, node) for i in range(SYSTEM_SIZE_BITS)]

    def __repr__(self):
        entries_repr = ', '.join(repr(entry) for entry in self.entries)
        return f'FingerTable(node={self.node.node_id}, entries=[{entries_repr}])'

    def __str__(self):
        entries_str = '\n'.join(str(entry) for entry in self.entries)
        return f'FingerTable:\nNode: {self.node.node_id}\nEntries:\n{entries_str}'

    def update(self, i, s):
        self.entries[i].node = s


def between(_id: int, left: int, right: int, inclusive_left=False, inclusive_right=True) -> bool:
    """
    Check if _id lies between left and right in a circular ring.
    """
    ring_sz = 2 ** SYSTEM_SIZE_BITS
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
    # This is a simple implementation of the Chord protocol
    # The Chord protocol is a distributed lookup protocol that provides a way to locate a node in a network of nodes given its key.

    def __init__(self, componentname, componentinstancenumber, context=None, configuration_parameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configuration_parameters, num_worker_threads, topology)

        self.eventhandlers["msgfrompeer"] = self.on_message_from_peer

        self.find_successor_result_queue = queue.Queue()
        self.find_predecessor_result_queue = queue.Queue()
        self.find_closest_preceding_finger_result_queue = queue.Queue()

        self.predecessor = self
        self.node_id = componentinstancenumber
        self.registry = ComponentRegistry()
        self.finger_table = FingerTable(self)

    def __repr__(self):
        return f'ChordComponent(componentname={self.componentname}, componentinstancenumber={self.componentinstancenumber}, node_id={self.node_id})'

    def on_message_from_peer(self, eventobj: Event):
        chord_message = eventobj.eventcontent
        hdr = chord_message.header
        payload = chord_message.payload

        if hdr.messagetype == ApplicationLayerMessageTypes.FIND_SUCCESSOR_REQ:
            successor = self._find_successor(payload)
            # send response back to requestor
            resp = GenericMessage(ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.FIND_SUCCESSOR_RESP, self.componentinstancenumber, hdr.messagefrom), successor)
            self.send_peer(Event(self, EventTypes.MFRP, resp))

        elif hdr.messagetype == ApplicationLayerMessageTypes.FIND_SUCCESSOR_RESP:
            print("Putting result in find_successor_result_queue")
            self.find_successor_result_queue.put_nowait(payload)
            print("EXCXJITS")

        elif hdr.messagetype == ApplicationLayerMessageTypes.FIND_PREDECESSOR_REQ:
            predecessor = self._find_predecessor(payload)
            resp = GenericMessage(ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.FIND_PREDECESSOR_RESP, self.componentinstancenumber, hdr.messagefrom), predecessor)
            self.send_peer(Event(self, EventTypes.MFRP, resp))

        elif hdr.messagetype == ApplicationLayerMessageTypes.FIND_PREDECESSOR_RESP:
            print("Putting result in find_predecessor_result_queue")
            self.find_predecessor_result_queue.put_nowait(payload)

        elif hdr.messagetype == ApplicationLayerMessageTypes.FIND_CLOSEST_PRECEDING_FINGER_REQ:
            closest_finger = self._closest_preceding_finger(payload)
            resp = GenericMessage(ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.FIND_CLOSEST_PRECEDING_FINGER_RESP, self.componentinstancenumber, hdr.messagefrom), closest_finger)
            self.send_peer(Event(self, EventTypes.MFRP, resp))

        elif hdr.messagetype == ApplicationLayerMessageTypes.FIND_CLOSEST_PRECEDING_FINGER_RESP:
            self.find_closest_preceding_finger_result_queue.put(payload)

    def successor(self):
        return self.finger_table.entries[0].node

    def create_remote_event(self, message_type: ApplicationLayerMessageTypes, queue, node_id):
        other_node = self.registry.get_arbitrary_component(self.componentname, self.componentinstancenumber)
        req = GenericMessage(ApplicationLayerMessageHeader(message_type, self.componentinstancenumber, other_node), node_id)
        self.send_peer(Event(self, EventTypes.MFRP, req))
        return queue.get()

    def find_successor(self, node_id):
        return self.create_remote_event(ApplicationLayerMessageTypes.FIND_SUCCESSOR_REQ, self.find_successor_result_queue, node_id)

    def find_predecessor(self, node_id):
        return self.create_remote_event(ApplicationLayerMessageTypes.FIND_PREDECESSOR_REQ, self.find_predecessor_result_queue, node_id)

    def closest_preceding_finger(self, node_id):
        return self.create_remote_event(ApplicationLayerMessageTypes.FIND_CLOSEST_PRECEDING_FINGER_REQ, self.find_closest_preceding_finger_result_queue, node_id)

    def _find_successor(self, node_id):
        if self.node_id == self.successor().node_id:
            return self
        else:
            predecessor = self._find_predecessor(node_id)
            return predecessor.successor()

    def _find_predecessor(self, node_id):
        other_node = self
        while not between(node_id, other_node.node_id, other_node.successor().node_id, inclusive_left=False, inclusive_right=True):
            """
            if node_id == other_node.node_id:
                return other_node.predecessor
            if node_id == other_node.successor().node_id:
                return other_node
            """
            other_node = other_node._closest_preceding_finger(node_id)
        return other_node

    def _closest_preceding_finger(self, node_id):
        for i in range(SYSTEM_SIZE_BITS - 1, -1, -1):
            #if self.node_id < self.finger_table.entries[i].node.node_id < node_id:
            if between(self.finger_table.entries[i].node.node_id, self.node_id, node_id, inclusive_left=False, inclusive_right=False):
                return self.finger_table.entries[i].node
        return self

    def init_finger_table(self):
        succ_node = self.find_successor(self.finger_table.entries[0].start)
        print(f"FOUND SUCCESSOR: {succ_node.node_id}")
        self.finger_table.update(0, succ_node)

        self.registry.add_component(self)
        successor = self.successor()
        self.predecessor = successor.predecessor
        successor.predecessor = self
        succ_node.finger_table.entries[0].node = self
        for i in range(SYSTEM_SIZE_BITS-1):
            #if self.node_id <= self.finger_table.entries[i+1].start < self.finger_table.entries[i].node.node_id:
            if between(self.finger_table.entries[i+1].start, self.node_id, self.finger_table.entries[i].node.node_id, inclusive_left=True, inclusive_right=False):
                self.finger_table.entries[i+1].node = self.finger_table.entries[i].node
            else:
                node = self.find_successor(self.finger_table.entries[i+1].start)
                self.finger_table.update(i+1, node)
        import ipdb; ipdb.set_trace()

    def join(self):
        # We assume that there is already at least one node in the network
        if not self.registry.components:
            # If there are no components in the registry, add this component to the registry
            # Init the finger table for the Single node in the network
            for i in range(SYSTEM_SIZE_BITS):
                self.finger_table.entries[i].node = self
            self.predecessor = self
            self.registry.add_component(self)
        else:
            self.predecessor = None
            self.init_finger_table()
            self.update_other_nodes()
            #self.stabilize()
            #self.fix_fingers()

    def update_other_nodes(self):
        node = self.registry.get_arbitrary_component(self.componentname, self.componentinstancenumber)
        for i in range(SYSTEM_SIZE_BITS):
            p = node.find_predecessor((node.node_id - 2**i) % 2**SYSTEM_SIZE_BITS)
            p.update_finger_table(node, i)

    def update_finger_table(self, s, i):
        #if self.node_id <= s.node_id < self.finger_table.entries[i].node.node_id:
        if between(s.node_id, self.node_id, self.finger_table.entries[i].node.node_id, inclusive_left=True, inclusive_right=False):
            self.finger_table.update(i, s)
            p = self.predecessor
            p.update_finger_table(s, i)

    def fix_fingers(self):
        for node in self.registry.components.values():
            for i in range(SYSTEM_SIZE_BITS):
                node.finger_table.update(i, node._find_successor(node.finger_table.entries[i].start))

    def stabilize(self):
        x = self.successor().predecessor
        if self.node_id < x.node_id < self.successor().node_id:
            self.finger_table.entries[0].node = x
        self.successor().notify(self)

    def notify(self, other_node):
        if self.predecessor is None or between(other_node.node_id, self.predecessor.node_id, self.node_id, inclusive_left=False, inclusive_right=False):
            self.predecessor = other_node

class Node(GenericModel):
    def on_init(self, eventobj: Event):
        pass

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        # SUBCOMPONENTS
        self.N = ChordComponent("N", 0)
        self.B = ChordComponent("B", 1)

        self.components.append(self.N)
        self.components.append(self.B)

        #self.N.connect_me_to_component(self.B)

        self.N.P(self.B)
        self.B.P(self.N)

        self.N.join()
        print("N IS ADDED")
        self.B.join()
        import ipdb; ipdb.set_trace()


def main():
    setAHCLogLevel(DEBUG)
    topo = Topology();
    topo.construct_single_node(Node, 0)
    topo.start()
    time.sleep(1)
    topo.exit()

if __name__ == "__main__":
    main()
