class Seq:
    """8-bit Wrap-around sequence number"""
    MOD = 1 << 8  # 8 bit sequence number
    HALF = MOD >> 1

    def __init__(self, number):
        if not isinstance(number, int):
            raise TypeError('not int type')
        self.seq = number % Seq.MOD

    def __repr__(self):
        return 'Seq({})'.format(self.seq)

    def __int__(self):
        return self.seq  # int conversion

    def distance(self, other):
        """distance from self to other Seq

        :return: int  (-Seq.HALF <= distance < Seq.HALF)
            positive: forward distance
            negative: backward distance
        """
        if not isinstance(other, Seq):
            raise TypeError('not Seq type')
        signed_self = self.seq if self.seq < Seq.HALF else self.seq - Seq.MOD
        signed_other = other.seq if other.seq < Seq.HALF else other.seq - Seq.MOD
        return signed_self - signed_other

    def __add__(self, n):
        """Forward n steps"""
        if isinstance(n, int):
            return Seq(self.seq + n)
        else:
            raise TypeError('not int type')

    def __sub__(self, n):
        """Backward n steps"""
        if isinstance(n, int):
            return Seq(self.distance(Seq(n)))
        else:
            raise TypeError('not int type')

    # Comparison on Seq types
    def __eq__(self, other):
        if isinstance(other, Seq):
            return self.seq == other.seq
        else:
            raise TypeError('not Seq type')

    def __lt__(self, other):
        return self.distance(other) < 0

    def __ne__(self, other):
        return not self.__eq__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        return not self.__le__(other)

def srange(start, end):
    if not (isinstance(start, Seq) and isinstance(end, Seq)):
        raise TypeError('not Seq type')
    seq = Seq(start.seq)
    while seq != end:
        yield seq
        seq += 1

def ichecksum(packet, sum=0):
    """ Compute the Internet Checksum of the supplied data.  The checksum is
    initialized to zero.  Place the return value in the checksum field of a
    packet.  When the packet is received, check the checksum, by passing
    in the checksum field of the packet and the data.  If the result is zero,
    then the checksum has not detected an error.
    """
    if not isinstance(packet, (bytes, bytearray)):
        raise TypeError('Packet type should be bytes or bytearray')

    for i in range(0, len(packet), 2):
        if i + 1 >= len(packet):
            sum += packet[i]
        else:
            sum += (packet[i] << 8) + packet[i+1]
    # take only 16 bits out of the 32 bit sum and add up the carries
    while (sum >> 16) > 0:
        sum = (sum & 0xFFFF) + (sum >> 16)
    # one's complement the result
    sum = ~sum
    return sum & 0xFFFF
    
def make_pkt(seq, packet_type, data=b''):
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError('data is not bytes or bytearray type')
    packet = bytearray([packet_type, int(seq), 0, 0])  # header with zero checksum field
    packet.extend(data)
    checksum = ichecksum(packet)
    packet[2:4] = bytearray([checksum >> 8, checksum & 0xFF])  # overwrite checksum
    return packet

def get_seqnum(packet): return Seq(packet[1])

def get_type(packet): return packet[0]

def extract(packet): return packet[4:]

def corrupt(packet): return True if ichecksum(packet) != 0 else False

class PacketBuffer:
    """Packet buffers indexed by Seq bumber for GBNsend's send buffer or GBNrecv's receive buffer
    Note: for indexing, gbn.base attribute is used.
        popfron method updates gbn.base variable
    """
    def __init__(self, gbn, bufsize):
        """Packet buffer for GBNsend's send buffer or GBNrecv's receive buffer
        :param gbn: GBNsend or GBNrecv object
        :param bufsize: number of pacekt cells in the buffer
        """
        self.buf = dict([(i, None) for i in range(Seq.MOD)])  # None mean empty packet
        self.gbn = gbn
        self.bufsize = bufsize

    def __str__(self):
        s =  []
        for seq in srange(self.gbn.base, self.gbn.base + self.bufsize):
            packet = self.buf[int(seq)]
            if packet is None:
                s.append(packet)
            else:
                s.append(get_seqnum(packet))
        return str(s)

    # support indexing. e.g) sndpkt[Seq(5)]
    def __getitem__(self, seq):
        self._check_key(seq)
        return self.buf[int(seq)]

    def __setitem__(self, seq, item):
        self._check_key(seq)
        self.buf[int(seq)] = item

    def _check_key(self, seq):
        if not isinstance(seq, Seq):
            raise KeyError('not Seq type')
        if seq not in srange(self.gbn.base, self.gbn.base + self.bufsize):
            raise KeyError(seq)

    def popfront(self):     # shift right
        """pop from front. Note: gbn.base will be modified"""
        packet =  self.buf[int(self.gbn.base)]
        self.buf[int(self.gbn.base)] = None
        self.gbn.base += 1
        return packet

    def find_hole(self):
        """Find the seq. of first hole in the buffer

        :return: seq if hole found
                 next seq of the last packet, if no hole
        """
        for seq in srange(self.gbn.base, self.gbn.base + self.bufsize):
            if self.__getitem__(seq) is None:
                return seq
        return self.gbn.base + self.bufsize + 1  # All the packets occupied contiguously. Return next seq.

if __name__ == '__main__':
    # testing ichecksum
    data = b'abcd123'
    DATA = 1
    packet = make_pkt(seq=Seq(1), packet_type=DATA, data=data)
    print('Packet:', packet)
    if ichecksum(packet) == 0:
        print('No checksum error detected')
    else:
        print('Checksum error found')

    # testing Seq
    N = 16     # Window size
    base = Seq(253)
    nextseqnum = Seq(2)
    print('N:', N)
    print('base:', base)
    print('nextseqnum:', nextseqnum)
    nextseqnum += 1
    print('nextseqnum:', nextseqnum)
    print('base + N:', base + N)
    print('base <= nextseqnum < base + N:', base <= nextseqnum < base + N)
    print('srange(base, nextseqnum):')
    for s in srange(base, nextseqnum):
        print(s)

    # testing action cause by event rdt_send(data)
    nextseqnum = base    # empty buffer
    sndpkt = []
    print('6 rdt_send(date) events:')
    data = bytearray(b'abcd000')
    for s in srange(base, base + 6):
        if nextseqnum < base + N:
            packet = make_pkt(s, DATA, data)
            # udt_send(sock, packet)
            sndpkt.append(packet)
            if base == nextseqnum:
                print('start timer')
            nextseqnum += 1
        data[-1] += 1   # just for changing data
    print('sndpkt:', sndpkt)

    # ACK reveived
    ack = 255
    print('After ACK {} received:', ack)
    acknum = Seq(ack)
    for s in srange(base, acknum):
        del sndpkt[0]
    base = acknum
    print('base:', base, 'nextseqnum:', nextseqnum)
    print('sndpkt:', sndpkt)

    # testing retransmission taken by timeout event
    print('ReTx after timeout:')
    for i, s in enumerate(srange(base, nextseqnum)):
        print('ReTx:', sndpkt[i])

