from adhoccomputing.GenericModel import GenericModel
from enum import Enum
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes, GenericMessageHeader, GenericMessagePayload, GenericMessage
from component_registry import ComponentRegistry


SYSTEM_SIZE_BITS = 10


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


class FingerTable:
    def __init__(self, node):
        self.node = node
        self.entries = [FingerTableEntry(node.node_id + 2**i, node) for i in range(SYSTEM_SIZE_BITS)]

    def update(self, i, s):
        self.entries[i].node = s

    def find_successor(self, id):
        for i in range(SYSTEM_SIZE_BITS-1, 0, -1):
            if self.entries[i].node.node_id < id < self.entries[i+1].node.node_id:
                return self.entries[i].node
        return self.node


class ChordComponent(GenericModel):
    # This is a simple implementation of the Chord protocol
    # The Chord protocol is a distributed lookup protocol that provides a way to locate a node in a network of nodes given its key.

    def __init__(self, component_name, component_instance_number, context=None, configuration_parameters=None, num_worker_threads=1, topology=None):
        super().__init__(component_name, component_instance_number, context, configuration_parameters, num_worker_threads, topology)

        self.eventhandlers["messagefrombottom"] = self.on_message_received
        self.eventhandlers["messagefromtop"] = self.on_message_received
        self.eventhandlers["messagefrompeer"] = self.on_message_received

        self.join(None)  # Join an existing network or create a new one if None.
        self.registry = ComponentRegistry()
        self.registry.add_component(self)

    def on_init(self, eventobj: Event):
        self.node_id = self.componentinstancenumber
        self.finger_table = FingerTable(self)

    def on_message_received(self, eventobj: Event):
        # This is a message from the successor node
        chord_message = eventobj.eventcontent
        hdr = chord_message.header

        if hdr.messagetype == ApplicationLayerMessageTypes.FIND_SUCCESSOR:
            result = self.find_successor(chord_message)

        elif hdr.messagetype == ApplicationLayerMessageTypes.FIND_PREDECESSOR:
            result = self.find_predecessor(chord_message)

        # TODO Create a message with result and send below
        if eventobj.fromchannel == ConnectorTypes.PEER:
            self.send_up(Event(self, EventTypes.MFRB, chord_message))
        elif eventobj.fromchannel == ConnectorTypes.DOWN:
            self.send_up(Event(self, EventTypes.MFRP, chord_message))
        elif eventobj.fromchannel == ConnectorTypes.UP:
            self.send_down(Event(self, EventTypes.MFRT, chord_message))

    def successor(self):
        return self.finger_table.entries[0].node

    def find_successor(self, chord_message):
        # TODO
        pass

    def join(self, other_node):
        if other_node:
            self.init_finger_table(other_node)
            self.update_other_nodes()
        else:
            for i in range(len(self.finger_table.entries)):
                self.finger_table.entries[i].node = self
            self.connect_me_to_component(ConnectorTypes.PEER, other_node)

    def init_finger_table(self, other_node):
        # TODO make other_node call over the network
        self.finger_table[0] = other_node.find_successor(self.finger_table[0].start)
        successor = self.successor()
        predecessor = successor.predecessor
        successor.predecessor = self
        for i in range(SYSTEM_SIZE_BITS-1):
            if self.finger_table.entries[i+1].start <= self.node_id < self.finger_table.entries[i+1].node.node_id:
                self.finger_table.entries[i+1] = self.finger_table.entries[i]
            elif self.finger_table.entries[i+1].node.node_id < self.finger_table.entries[i+1].start:
                self.finger_table.entries[i+1] = self.finger_table.entries[i]
            else:
                self.finger_table.entries[i+1] = other_node.find_successor(self.finger_table.entries[i+1].start)

    def update_other_nodes(self):
        for i in range(SYSTEM_SIZE_BITS):
            p = self.find_predecessor(self.node_id - 2**i)
            # Send a notify message to p to make it update its finger table
            hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.NOTIFY, self.componentinstancenumber, p)
            notify_msg = GenericMessage(hdr, NotifyPayload(self.node_id))
            self.send_down(Event(self, EventTypes.MFRT, notify_msg))

    def find_predecessor(self, id):
        other_node = self
        while id <= other_node.node_id or id > other_node.node_id.successor.node_id:
            # TODO Make other_node call over the network
            # TODO Use ComponentRegistry to get the other_node
            other_node = other_node.closest_preceding_finger(id)
        return other_node

    def closest_preceding_finger(self, id):
        for i in range(SYSTEM_SIZE_BITS-1, 0, -1):
            if self.node_id < self.finger_table.entries[i].node.node_id < id:
                return self.finger_table[i]
        return self.node_id
