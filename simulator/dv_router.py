"""
Your awesome Distance Vector router for CS 168
"""

import sim.api as api
import sim.basics as basics

from dv_utils import PeerTable, PeerTableEntry, ForwardingTable, \
    ForwardingTableEntry

# We define infinity as a distance of 16.
INFINITY = 16

# A route should time out after at least 15 seconds.
ROUTE_TTL = 15


class DVRouter(basics.DVRouterBase):
    # NO_LOG = True  # Set to True on an instance to disable its logging.
    # POISON_MODE = True  # Can override POISON_MODE here.
    # DEFAULT_TIMER_INTERVAL = 5  # Can override this yourself for testing.

    def __init__(self):
        """
        Called when the instance is initialized.

        DO NOT remove any existing code from this method.
        """
        self.start_timer()  # Starts calling handle_timer() at correct rate.

        # Maps a port to the latency of the link coming out of that port.
        self.link_latency = {}

        # Maps a port to the PeerTable for that port.
        # Contains an entry for each port whose link is up, and no entries
        # for any other ports.
        self.peer_tables = {}

        # Forwarding table for this router (constructed from peer tables).
        self.forwarding_table = ForwardingTable()

        # History data structure, dictionary within a dictionary. Maps ports to a dictionary, inner dictionary maps hosts/dst to advertisement packets
        self.history = {}

    def add_static_route(self, host, port):
        """
        Adds a static route to a host directly connected to this router.

        Called automatically by the framework whenever a host is connected
        to this router.

        :param host: the host.
        :param port: the port that the host is attached to.
        :returns: nothing.
        """
        # `port` should have been added to `peer_tables` by `handle_link_up`
        # when the link came up.
        assert port in self.peer_tables, "Link is not up?"

        table = self.peer_tables[port]

        table[host] = PeerTableEntry(dst = host, latency = 0, expire_time=PeerTableEntry.FOREVER)

        # TODO: fill this in!



        self.update_forwarding_table()
        self.send_routes(force=False)

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this router goes up.

        :param port: the port that the link is attached to.
        :param latency: the link latency.
        :returns: nothing.
        """
        self.link_latency[port] = latency
        self.peer_tables[port] = PeerTable()

        for host, entry in self.forwarding_table.items():

        	packet = basics.RoutePacket(destination=entry.dst, latency=entry.latency)
        	self.send(packet, port=port)


        # TODO: fill in the rest!

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this router does down.

        :param port: the port number used by the link.
        :returns: nothing.
        """

        self.peer_tables.pop(port)
        self.update_forwarding_table()
        self.send_routes(force=False)


        # TODO: fill this in!

    def handle_route_advertisement(self, dst, port, route_latency):
        """
        Called when the router receives a route advertisement from a neighbor.

        :param dst: the destination of the advertised route.
        :param port: the port that the advertisement came from.
        :param route_latency: latency from the neighbor to the destination.
        :return: nothing.
        """

        pTable = self.peer_tables[port]

        pTable[dst] = PeerTableEntry(dst=dst, latency=route_latency, expire_time=api.current_time()+15)

        self.update_forwarding_table()
        self.send_routes(force=False)

        # TODO: fill this in!

    def update_forwarding_table(self):
        """
        Computes and stores a new forwarding table merged from all peer tables.

        :returns: nothing.
        """
        self.forwarding_table.clear()  # First, clear the old forwarding table.
        
        newFT = self.forwarding_table
        for port, table in self.peer_tables.items():

        	for host, entry in table.items():
        		# print(host, entry)
        		currLatency = float(entry.latency) + float(self.link_latency[port])

        		# print(currLatency, int(entry.latency))

        		# Host exists, has a entry in it
        		if (host in newFT):
        			# Get old latency
        			oldLatency = newFT[host].latency

        			# Compare with newLatency, if less, replace object in forwarding table
        			if (currLatency < oldLatency):
        				newEntry = ForwardingTableEntry(dst=host, port=port, latency=currLatency)
        				newFT[host] = newEntry
        		else:
        			# forwarding entry doesn't exist for this host, add it
        			newEntry = ForwardingTableEntry(dst=host, port=port, latency=currLatency)
        			newFT[host] = newEntry

        self.forwarding_table = newFT


        # TODO: populate `self.forwarding_table` by combining peer tables.

    def handle_data_packet(self, packet, in_port):
        """
        Called when a data packet arrives at this router.

        You may want to forward the packet, drop the packet, etc. here.

        :param packet: the packet that arrived.
        :param in_port: the port from which the packet arrived.
        :return: nothing.
        """

        toDST = packet.dst

        # Check if destination is in the forwarding table, if not drop packet
        if (toDST in self.forwarding_table):
        	forwardingEntry = self.forwarding_table[toDST]

        	# Check if distance to destination is not long, if it is, drop packet (to prevent loops)
        	if (forwardingEntry.latency < INFINITY):

        		# Check if packet's in_port is different from out_port, if yes, send packet
        		if (forwardingEntry.port is not in_port):
        			self.send(packet, port=forwardingEntry.port)
        			
        # TODO: fill this in!

    def send_routes(self, force=False):
        """
        Send route advertisements for all routes in the forwarding table.

        :param force: if True, advertises ALL routes in the forwarding table;
                      otherwise, advertises only those routes that have
                      changed since the last advertisement.
        :return: nothing.
        """

        # print(self.history)
        # print(self.forwarding_table)


        if (self.POISON_MODE):
        	# print(self.history)
        	# print(self.forwarding_table)
        	for port in self.history:
		        pTable = self.history[port]

		        for host in pTable:

		            if ((host not in self.forwarding_table) and (port in self.peer_tables)):
		                packet = basics.RoutePacket(destination=host, latency=INFINITY)
		                # self.send(packet, port=port)

		                # pTable[host] = packet
		                # self.history[port] = pTable
		                temp = self.peer_tables[port]
		                temp[host] = PeerTableEntry(dst=host, latency=INFINITY, expire_time=api.current_time()+ROUTE_TTL)

			self.update_forwarding_table()


        for port, table in self.peer_tables.items():

        	for host, entry in self.forwarding_table.items():

        		tempLatency = None

        		if (self.POISON_MODE):

        			if (entry.port == port):
        				tempLatency = INFINITY
        			else:
        				if (entry.latency > INFINITY):
			        		tempLatency = INFINITY
			        	else:
	        				tempLatency = entry.latency

	        		# pTable = self.peer_tables[port]
	        		# pTable[host] = PeerTableEntry(dst=host, latency=INFINITY, expire_time=api.current_time()+ROUTE_TTL)
	        		# self.update_forwarding_table()

        		elif (entry.port != port):

		        	if (entry.latency > INFINITY):
		        		tempLatency = INFINITY
		        	else:
		        		tempLatency = entry.latency

		        if (tempLatency):
		        	packet = basics.RoutePacket(destination=entry.dst, latency=tempLatency)

		        	if (force):
		        		self.send(packet, port=port)

			        	pTable = {}

			        	# if port already in history, get the table
			        	if (port in self.history):
			        		pTable = self.history[port]

			        	# port not in history, create new dictionary entry
			        	else:
			        		self.history[port] = {}
			        		pTable = self.history[port]

			        	pTable[host] = packet
		        		self.history[port] = pTable



		        	# -------------------- Stage 8 --------------------
		        	else:
			        	send = False
			        	pTable = {}

			        	# if port already in history, get the table
			        	if (port in self.history):
			        		pTable = self.history[port]

			        	# port not in history, create new dictionary entry
			        	else:
			        		self.history[port] = {}
			        		pTable = self.history[port]

		        		# Host in history
		        		if (host in pTable):
		        			prevEntry = pTable[host]

		        			# Packet is not the same, update history and send
		        			if ((prevEntry.latency != tempLatency) or (host != entry.dst)):
		        				pTable[host] = packet
		        				send = True

		        		# Host not in history, add to history and send
		        		else:
		        			pTable[host] = packet
			        		send = True
			        		self.history[port] = pTable

	        			if (send):
			        		self.send(packet, port=port)

		# for host, entry in self.forwarding_table.items():

  #       	tempLatency = None
  #       	if (entry.latency > INFINITY):
  #       		tempLatency = INFINITY
  #       	else:
  #       		tempLatency = entry.latency

  #       	packet = basics.RoutePacket(destination=entry.dst, latency=tempLatency)
  #       	self.send(packet, port=entry.port, flood=force)

        # TODO: fill this in!

    def expire_routes(self):
        """
        Clears out expired routes from peer tables; updates forwarding table
        accordingly.
        """

        for port, table in self.peer_tables.items():

        	for host, entry in table.items():

        		if (entry.expire_time == PeerTableEntry.FOREVER):
        			continue

        		if (entry.expire_time < api.current_time()):
        			table.pop(host)

        self.update_forwarding_table()

        # TODO: fill this in!

    def handle_timer(self):
        """
        Called periodically.

        This function simply calls helpers to clear out expired routes and to
        send the forwarding table to neighbors.
        """
        self.expire_routes()
        self.send_routes(force=True)

    # Feel free to add any helper methods!
