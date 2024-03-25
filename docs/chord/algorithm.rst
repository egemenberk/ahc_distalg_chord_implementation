.. include:: substitutions.rst

|chord|
=========================================



Background and Related Work
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Domain Name System (DNS) [Mockapetris1988]_ as a traditional name and location service that provides host name to IP address mapping.
In contrast to DNS, Chord offers a decentralized approach to mapping keys onto nodes, eliminating the need for special servers.
By storing key/value pairs at mapped nodes, Chord demonstrates versatility in implementing key/value functionality efficiently in peer-to-peer networks.

The Freenet peer-to-peer storage system [Clarke1999]_ [Clarke2000]_ operates as a decentralized and symmetric peer-to-peer storage system that adapts dynamically to node arrivals and departures.
Unlike Chord, Freenet does not assign specific servers responsibility for documents; instead, it relies on cached copies for lookups.
This approach allows Freenet to offer a degree of anonymity but may result in challenges related to document retrieval and retrieval costs.

The Ohaha system [Ohaha]_, utilizes a consistent hashing-like algorithm for mapping documents to nodes and employs Freenet-style query routing.
While this system shares similarities with Freenet, it may inherit some of the limitations associated with Freenet's approach to data lookup.
Ohaha's use of consistent hashing and query routing reflects its design choices in balancing anonymity and lookup efficiency in peer-to-peer storage systems.

The Globe system [Globe2000]_ features a wide-area location service that maps object identifiers to the locations of moving objects.
By structuring the Internet as a hierarchy of geographical, topological, or administrative domains,
Globe constructs a static global search tree akin to DNS. This hierarchical approach to data location management in Globe showcases a different perspective on decentralized data lookup strategies in large-scale networks

Distributed Algorithm: |chord|
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Chord is a fundamental algorithm in distributed systems, offering a scalable peer-to-peer lookup service for internet applications.
    These features enable efficient routing of requests, supporting tasks such as load balancing, data replication, and resource location.
    In this section, we explore the Chord algorithm, elaborating on its design, implementation details, and its features and benefits.

    **Chord Lookup Algorithm:**

    Proposed in a research paper by Ion Stoica, Robert Morris, David Karger, Frans Kaashoek, and Hari Balakrishnan, :ref:`the Chord Algorithm <ChordLookupAlgorithm>` [Chord]_ offers a practical and scalable solution for network searches. It operates by implementing a distributed hash table where keys are stored in the network nodes, allowing any node to efficiently route a search query for a key to the node responsible for that key. This algorithm is robust and able to cope with changes in the network, with nodes joining and leaving without disrupting the service. Here are the main procedures involved in this algorithm:

    1. **Initialization of System:** All nodes and keys in the system are assigned m-bit identifiers through consistent hashing. Each node maintains a routing table with m entries.

    2. **Node Joining:** A joining node, N, is assigned a place on the hash ring corresponding to its m-bit identifier. Any keys previously owned by N's successor are reassigned to N.

    3. **Routing/Searching:** To locate a node with an identifier closest to a given key, K, the predecessor of K is found first. From the predecessor, the successor holding K can be identified easily.

    4. **Node Departure/Key Reassignment:** If a node departs from the network, all its keys are reassigned to its immediate successor.

    5. **System Stabilization:** The network regularly updates to reflect joinings/leavings of nodes in order to maintain the network structure.

    6. **Finger Table Routing:** Each node N keeps a finger table with up to m entries, where each entry points to the successor of node (N + 2^i). This table is used in expediting the search process within the network.

An example distributed algorithm for broadcasting on an undirected graph is presented in  :ref:`Algorithm <ChordLookupAlgorithm>`.

.. _ChordLookupAlgorithm:

.. code-block:: RST
    :linenos:
    :caption: Chord Algorithm.
    

    - Initialization (Ring and Finger Table)
      For each node n in the system:
        n.id = hashFunction(n) // Assign an m-bit identifier to each node using a hash function
        n.fingerTable = new Table(m) // Initialize an empty finger table with m entries for each node

    - Node Joins (A new node n joins the system)
      n.id = hashFunction(n)
      n.successor = findSuccessor(n) // Find its position and successor in the ring
      transferKeysTo(n, n.successor) // Transfer necessary keys from successor to new node

    - Routing (Find node v responsible for key k)
      v = findSuccessor(k) // Determine the successor of k, which is considered the responsible node

    - Node Leaves (A node n leaves the system)
      transferKeysTo(n, n.successor) // Transfer all keys from departing node to its successor

    - Stabilization (run periodically to update finger tables and successor lists)
      For each node n in the system:
        updateFingerTable(n) // Update its own finger table
        updateSuccessorList(n) // Update its successor list

    Function findSuccessor(id):
      n = closestPrecedingNode(id)
      return n.successor

    Function closestPrecedingNode(id):
      for i = m down to 1 do
        if(finger[i].node is between n and id)
          return finger[i].node
      return n


Do not forget to explain the algorithm line by line in the text.

Example
~~~~~~~~

    1. **File Sharing Systems:** In peer-to-peer file sharing systems like BitTorrent, the Chord algorithm can facilitate efficient file lookup and downloads. Each file is treated as a key, and the peers that have this file are collectively considered as the value for this key. Therefore, any peer that wants to download a file only needs to perform a lookup for the file's key in the network.

    2. **Distributed Databases and Key-Value Stores:** Chord can be crucial in implementing distributed hash tables (DHTs) which form the backbone of distributed databases and large-scale key-value stores. It helps in efficiently locating the server node where a particular row or key-value pair is stored.

    3. **Content Distribution Networks (CDNs):** Chord can be used to effectively manage resources in a CDN. Resources could be replicated across multiple nodes, and the CDN uses Chord to identify which system node (server) a particular content request should be routed to.

    4. **Internet of Things (IoT):** With increasing numbers of IoT devices, managing resources efficiently is a challenge. Chord helps in such situations by providing efficient lookup services, facilitating load balancing, and managing the vast network of devices.

    5. **Networking Services:** Due to its scalable and resilient features, Chord can help provide a decentralized Domain Name System (DNS), enabling the routing of web requests without relying on a central authority.

    6. **Load Balancing:** In large distributed systems, managing the load across nodes is a challenge. The Chord algorithm can help distribute the load evenly across all nodes by using consistent hashing, thereby preventing any single node from being overwhelmed by requests.


Correctness
~~~~~~~~~~~

    The Chord :ref:`Algorithm <ChordLookupAlgorithm>` uses several mechanisms to maintain the correctness and function effectively in a dynamic, peer-to-peer network setting.

    1. **Identifier Assignment:** During the initialization, each node ``n`` and key ``k`` in the system is assigned a unique m-bit identifier using consistent hashing function. This is denoted as

    ``n.id = hash(n)`` and ``k.id = hash(k)``.

    This not only ensures uniqueness, but also approximately equal load distribution across all nodes due to the properties of the hash function.

    2. **Node Joining & Leaving:** When a new node ``n`` joins or an existing node leaves, Chord ensures that all keys are correctly assigned to their successor nodes. This is done by assigning the keys in the interval ``(p.id, n.id]`` to node ``n``, where ``p`` is the predecessor of ``n``. This preserves the correctness of key-to-node mapping in the network.

    3. **Lookup Operation:** The lookup operation in the Chord network is always correct if it correctly returns the successor of a key ``k``. The time complexity of the lookup operation is ``O(log(N))``, where ``N`` is the number of nodes in the network.

    4. **Fault-Tolerance:** If a node ``n`` fails, all keys of the failed node are reassigned to ``n``'s successor, preserving the integrity of the network and the correctness of the algorithm.

    5. **Stabilization:** The periodic running of the stabilization protocol ensures that the ``O(log(N))`` finger table entries (where ``N`` is the total number of nodes) are correct at any node and that any newly joined node becomes fully situated within the network.

    6. **Data Availability:** Chord also ensures correctness in the face of node failures by keeping copies of a key on ``r`` consecutive nodes counterclockwise from the key in the Chord ring. Thus, as long as one copy of a key-value pair is alive, the data object is available.

    7. **Finger Table Consistency:** By ensuring each node ``n`` maintains information about the nodes at ``n+2^i mod 2^m`` for ``i = 0,...,m-1``, the algorithm guarantees rapid convergence towards the target of a query even under concurrent joins and node failures.


Complexity 
~~~~~~~~~~

    The significantly noteworthy aspect of the Chord algorithm is its simplicity and scalability. As the network expands, the algorithm scales logarithmically in terms of the number of nodes, rendering it suitable for large-scale distributed systems.

    1. **Time Complexity:** The Chord Lookup :ref:`Algorithm <ChordLookupAlgorithm>` takes O(log N) lookup time in an N-node network (in expectation and with high probability). The time complexity increases logarithmically as the size of the network increases, enabling efficiency and scalability even in large-scale networks.

    2. **Message Complexity:** The Chord :ref:`Algorithm <ChordLookupAlgorithm>` employs a stabilization protocol that runs periodically in the background which exchanges O(log N) control messages per stabilization step, leading to a situation where the algorithm can keep up with continuous node joins and failures.


.. [Chord] Stoica, Ion, Robert Morris, David Karger, M. Frans Kaashoek, and Hari Balakrishnan. "Chord: A scalable peer-to-peer lookup service for internet applications." ACM SIGCOMM computer communication review 31, no. 4 (2001): 149-160.
.. [Clarke1999] CLARKE, I. A distributed decentralised information storage and retrieval system. Master’s thesis, University of Edinburgh, 1999
.. [Clarke2000] CLARKE, I., SANDBERG, O., WILEY, B., AND HONG, T. W. Freenet: A distributed anonymous information storage and retrieval system. In Proceedings of the ICSI Workshop on Design Issues in Anonymity and Unobservability (Berkeley, California, June 2000)
.. [Mockapetris1988] P. Mockapetris, K. J. Dunlap, Development of the Domain Name System, Proc. ACM SIGCOMM, Stanford, CA, 1988, pp. 123–133
.. [Ohaha] Ohaha, Smart decentralized peer-to-peer sharing, http://www.ohaha.com/design.html
.. [Globe2000] BAKKER, A., AMADE, E., BALLINTIJN, G., KUZ, I., VERKAIK, P., VAN DER WIJK, I., VAN STEEN, M., TANENBAUM, A., The Globe distribution network, Proc. 2000 USENIX Annual Conf. (FREENIX Track), San Diego, CA, June 2000, pp. 141–152