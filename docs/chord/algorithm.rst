.. include:: substitutions.rst

|chord|
=========================================



Background and Related Work
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Present any background information survey the related work. Provide citations.

Distributed Algorithm: |chord|
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An example distributed algorithm for broadcasting on an undirected graph is presented in  :ref:`Algorithm <BlindFloodingAlgorithmLabel>`.

.. _BlindFloodingAlgorithmLabel:

.. code-block:: RST
    :linenos:
    :caption: Blind flooding algorithm.
    

    Implements: BlindFlooding Instance: cf
    Uses: LinkLayerBroadcast Instance: lbc
    Events: Init, MessageFromTop, MessageFromBottom
    Needs:

    OnInit: () do
    
    OnMessageFromBottom: ( m ) do
        Trigger lbc.Broadcast ( m )
    
    OnMessageFromTop: ( m ) do
        Trigger lbc.Broadcast ( m )


Do not forget to explain the algorithm line by line in the text.

Example
~~~~~~~~

Provide an example for the distributed algorithm.

Correctness
~~~~~~~~~~~

Present Correctness, safety, liveness and fairness proofs.


Complexity 
~~~~~~~~~~

Present theoretic complexity results in terms of number of messages and computational complexity.




.. admonition:: EXAMPLE 

    Snapshot algorithms are fundamental tools in distributed systems, enabling the capture of consistent global states during system execution. These snapshots provide insights into the system's behavior, facilitating various tasks such as debugging, recovery from failures, and monitoring for properties like deadlock or termination. In this section, we delve into snapshot algorithms, focusing on two prominent ones: the Chandy-Lamport algorithm and the Lai-Yang algorithm. We will present the principles behind these algorithms, their implementation details, and compare their strengths and weaknesses.

    **Chandy-Lamport Snapshot Algorithm:**

    The Chandy-Lamport :ref:`Algorithm <ChandyLamportSnapshotAlgorithm>` [Lamport1985]_ , proposed by Leslie Lamport and K. Mani Chandy, aims to capture a consistent global state of a distributed system without halting its execution. It operates by injecting markers into the communication channels between processes, which propagate throughout the system, collecting local states as they traverse. Upon reaching all processes, these markers signify the completion of a global snapshot. This algorithm requires FIFO channels. There are no failures and all messages arrive intact and only once. Any process may initiate the snapshot algorithm. The snapshot algorithm does not interfere with the normal execution of the processes. Each process in the system records its local state and the state of its incoming channels.

    1. **Marker Propagation:** When a process initiates a snapshot, it sends markers along its outgoing communication channels.
    2. **Recording Local States:** Each process records its local state upon receiving a marker and continues forwarding it.
    3. **Snapshot Construction:** When a process receives markers from all incoming channels, it captures its local state along with the incoming messages as a part of the global snapshot.
    4. **Termination Detection:** The algorithm ensures that all markers have traversed the system, indicating the completion of the snapshot.


    .. _ChandyLamportSnapshotAlgorithm:

    .. code-block:: RST
        :linenos:
        :caption: Chandy-Lamport Snapshot Algorithm [Fokking2013]_.
                
        bool recordedp, markerp[c] for all incoming channels c of p; 
        mess-queue statep[c] for all incoming channels c of p;

        If p wants to initiate a snapshot 
            perform procedure TakeSnapshotp;

        If p receives a basic message m through an incoming channel c0
        if recordedp = true and markerp[c0] = false then 
            statep[c0] ← append(statep[c0],m);
        end if

        If p receives ⟨marker⟩ through an incoming channel c0
            perform procedure TakeSnapshotp;
            markerp[c0] ← true;
            if markerp[c] = true for all incoming channels c of p then
                terminate; 
            end if

        Procedure TakeSnapshotp
        if recordedp = false then
            recordedp ← true;
            send ⟨marker⟩ into each outgoing channel of p; 
            take a local snapshot of the state of p;
        end if


    **Example**

    DRAW FIGURES REPRESENTING THE EXAMPLE AND EXPLAIN USING THE FIGURE. Imagine a distributed system with three processes, labeled Process A, Process B, and Process C, connected by communication channels. When Process A initiates a snapshot, it sends a marker along its outgoing channel. Upon receiving the marker, Process B marks its local state and forwards the marker to Process C. Similarly, Process C marks its state upon receiving the marker. As the marker propagates back through the channels, each process records the messages it sends or receives after marking its state. Finally, once the marker returns to Process A, it collects the markers and recorded states from all processes to construct a consistent global snapshot of the distributed system. This example demonstrates how the Chandy-Lamport algorithm captures a snapshot without halting the system's execution, facilitating analysis and debugging in distributed environments.


    **Correctness:**
    
    *Termination (liveness)*: As each process initiates a snapshot and sends at most one marker message, the snapshot algorithm activity terminates within a finite timeframe. If process p has taken a snapshot by this point, and q is a neighbor of p, then q has also taken a snapshot. This is because the marker message sent by p has been received by q, prompting q to take a snapshot if it hadn't already done so. Since at least one process initiated the algorithm, at least one process has taken a snapshot; moreover, the network's connectivity ensures that all processes have taken a snapshot [Tel2001]_.

    *Correctness*: We need to demonstrate that the resulting snapshot is feasible, meaning that each post-shot (basic) message is received during a post-shot event. Consider a post-shot message, denoted as m, sent from process p to process q. Before transmitting m, process p captured a local snapshot and dispatched a marker message to all its neighbors, including q. As the channels are FIFO (first-in-first-out), q received this marker message before receiving m. As per the algorithm's protocol, q took its snapshot upon receiving this marker message or earlier. Consequently, the receipt of m by q constitutes a post-shot event [Tel2001]_.

    **Complexity:**

    1. **Time Complexity**  The Chandy-Lamport :ref:`Algorithm <ChandyLamportSnapshotAlgorithm>` takes at most O(D) time units to complete where D is ...
    2. **Message Complexity:** The Chandy-Lamport :ref:`Algorithm <ChandyLamportSnapshotAlgorithm>` requires 2|E| control messages.


    **Lai-Yang Snapshot Algorithm:**

    The Lai-Yang algorithm also captures a consistent global snapshot of a distributed system. Lai and Yang proposed a modification of Chandy-Lamport's algorithm for distributed snapshot on a network of processes where the channels need not be FIFO. ALGORTHM, FURTHER DETAILS

.. [Fokking2013] Wan Fokkink, Distributed Algorithms An Intuitive Approach, The MIT Press Cambridge, Massachusetts London, England, 2013
.. [Tel2001] Gerard Tel, Introduction to Distributed Algorithms, CAMBRIDGE UNIVERSITY PRESS, 2001
.. [Lamport1985] Leslie Lamport, K. Mani Chandy: Distributed Snapshots: Determining Global States of a Distributed System. In: ACM Transactions on Computer Systems 3. Nr. 1, Februar 1985.