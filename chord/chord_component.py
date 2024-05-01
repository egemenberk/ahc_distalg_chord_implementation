from adhoccomputing.GenericModel import GenericModel
from enum import Enum
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes, GenericMessageHeader, GenericMessagePayload, GenericMessage
from component_registry import ComponentRegistry
from adhoccomputing.Generics import *
from adhoccomputing.Experimentation.Topology import Topology


SYSTEM_SIZE_BITS = 3


class ApplicationLayerMessageTypes(Enum):
    FIND_SUCCESSOR = "FIND_SUCCESSOR"
    FIND_PREDECESSOR = "FIND_PREDECESSOR"
    FIND_CLOSEST_PRECEDING_FINGER = "FIND_CLOSEST_PRECEDING_FINGER"


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


class ChordComponent(GenericModel):
    # This is a simple implementation of the Chord protocol
    # The Chord protocol is a distributed lookup protocol that provides a way to locate a node in a network of nodes given its key.

    def __init__(self, componentname, componentinstancenumber, context=None, configuration_parameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configuration_parameters, num_worker_threads, topology)

        self.eventhandlers["messagefrombottom"] = self.on_message_received
        self.eventhandlers["messagefromtop"] = self.on_message_received
        self.eventhandlers["messagefrompeer"] = self.on_message_received

        self.predecessor = self
        self.node_id = componentinstancenumber
        self.registry = ComponentRegistry()
        self.finger_table = FingerTable(self)

    def __repr__(self):
        return f'ChordComponent(componentname={self.componentname}, componentinstancenumber={self.componentinstancenumber}, node_id={self.node_id})'

    def on_message_received(self, eventobj: Event):
        # This is a message from the successor node
        chord_message = eventobj.eventcontent
        hdr = chord_message.header

        if hdr.messagetype == ApplicationLayerMessageTypes.FIND_SUCCESSOR:
            id = chord_message.payload.node
            result = self._find_successor(id)

        elif hdr.messagetype == ApplicationLayerMessageTypes.FIND_PREDECESSOR:
            result = self.find_predecessor(chord_message)

        if eventobj.fromchannel == ConnectorTypes.PEER:
            self.send_peer(Event(self, EventTypes.MFRB, chord_message))

    def successor(self):
        return self.finger_table.entries[0].node

    def find_successor(self, node_id):

        """
        if len(self.registry.components) <= 2:
            for node in self.registry.components.values():
                if node.node_id > node_id:
                    return node
        other_node = self.find_predecessor(node_id)
        return other_node.successor()
        """
        sorted_components = sorted(self.registry.components.values(), key=lambda x: x.node_id)
        for node in sorted_components:
            if node_id < node.node_id:
                print(f"find_successor: Node: {node_id} Successor: {node.node_id}")
                return node
        print(f"find_successor: Node: {node_id} Successor: {sorted_components[0].node_id}")
        return sorted_components[0]

    def stabilize(self):
        x = self.successor().predecessor
        if self.node_id < x.node_id < self.successor().node_id:
            self.finger_table.entries[0].node = x
        self.successor().notify(self)

    def notify(self, other_node):
        if self.predecessor is None or self.predecessor.node_id < other_node.node_id < self.node_id:
            self.predecessor = other_node

    def find_predecessor(self, node_id):
        """
        other_node = self
        while not (other_node.node_id < node_id <= other_node.successor().node_id):
            other_node = other_node.closest_preceding_finger(node_id)
        return other_node
        """
        sorted_components = sorted(self.registry.components.values(), key=lambda x: x.node_id, reverse=True)
        for node in sorted_components:
            if node_id > node.node_id:
                print(f"find_predecessor: Node: {node_id} Predecessor: {node.node_id}")
                return node
        print(f"find_predecessor: Node: {node_id} Predecessor: {sorted_components[0].node_id}")
        return sorted_components[0]

    def closest_preceding_finger(self, node_id):
        for i in range(SYSTEM_SIZE_BITS - 1, -1, -1):
            if self.node_id < self.finger_table.entries[i].node.node_id < node_id:
                return self.finger_table.entries[i].node
        return self

    def init_finger_table(self):
        #other_node = self.registry.get_arbitrary_component(self.componentname, self.componentinstancenumber)
        # TODO make other_node call over the network
        node = self.find_successor(self.finger_table.entries[0].start)
        self.finger_table.update(0, node)
        successor = self.successor()
        self.predecessor = successor.predecessor
        successor.predecessor = self
        #self.predecessor.finger_table.entries[0].node = self
        for i in range(SYSTEM_SIZE_BITS-1):
            if self.node_id <= self.finger_table.entries[i+1].start <= self.finger_table.entries[i].node.node_id:
                self.finger_table.entries[i+1].node = self.finger_table.entries[i].node
            else:
                node = self.find_successor(self.finger_table.entries[i+1].start)
                self.finger_table.update(i+1, node)

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
            #other_node = self.registry.get_arbitrary_component(self.componentname, self.componentinstancenumber)
            self.predecessor = None
            self.finger_table.entries[0].node = self.find_successor(self.node_id)

            self.registry.add_component(self)
            self.predecessor = self.successor().predecessor
            self.init_finger_table()
            self.update_other_nodes()
            self.stabilize()
            self.fix_fingers()

    def update_other_nodes(self):
        for i in range(SYSTEM_SIZE_BITS):
            p = self.find_predecessor((self.node_id - 2**i) % 2**SYSTEM_SIZE_BITS)
            p.update_finger_table(self, i)

    def update_finger_table(self, s, i):
        if self.node_id <= s.node_id < self.finger_table.entries[i].node.node_id:
            self.finger_table.update(i, s)
            p = self.predecessor
            p.update_finger_table(s, i)

    def fix_fingers(self):
        for node in self.registry.components.values():
            for i in range(SYSTEM_SIZE_BITS):
                node.finger_table.update(i, node.find_successor(node.finger_table.entries[i].start - 1))

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
