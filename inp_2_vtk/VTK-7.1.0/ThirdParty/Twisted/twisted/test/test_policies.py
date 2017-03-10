# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test code for policies.
"""

from __future__ import division, absolute_import

from zope.interface import Interface, implementer, implementedBy

from twisted.python.compat import NativeStringIO, _PY3
from twisted.trial import unittest
from twisted.test.proto_helpers import StringTransport
from twisted.test.proto_helpers import StringTransportWithDisconnection

from twisted.internet import protocol, reactor, address, defer, task
from twisted.protocols import policies



class SimpleProtocol(protocol.Protocol):

    connected = disconnected = 0
    buffer = b""

    def __init__(self):
        self.dConnected = defer.Deferred()
        self.dDisconnected = defer.Deferred()

    def connectionMade(self):
        self.connected = 1
        self.dConnected.callback('')

    def connectionLost(self, reason):
        self.disconnected = 1
        self.dDisconnected.callback('')

    def dataReceived(self, data):
        self.buffer += data



class SillyFactory(protocol.ClientFactory):

    def __init__(self, p):
        self.p = p

    def buildProtocol(self, addr):
        return self.p


class EchoProtocol(protocol.Protocol):
    paused = False

    def pauseProducing(self):
        self.paused = True

    def resumeProducing(self):
        self.paused = False

    def stopProducing(self):
        pass

    def dataReceived(self, data):
        self.transport.write(data)



class Server(protocol.ServerFactory):
    """
    A simple server factory using L{EchoProtocol}.
    """
    protocol = EchoProtocol



class TestableThrottlingFactory(policies.ThrottlingFactory):
    """
    L{policies.ThrottlingFactory} using a L{task.Clock} for tests.
    """

    def __init__(self, clock, *args, **kwargs):
        """
        @param clock: object providing a callLater method that can be used
            for tests.
        @type clock: C{task.Clock} or alike.
        """
        policies.ThrottlingFactory.__init__(self, *args, **kwargs)
        self.clock = clock


    def callLater(self, period, func):
        """
        Forward to the testable clock.
        """
        return self.clock.callLater(period, func)



class TestableTimeoutFactory(policies.TimeoutFactory):
    """
    L{policies.TimeoutFactory} using a L{task.Clock} for tests.
    """

    def __init__(self, clock, *args, **kwargs):
        """
        @param clock: object providing a callLater method that can be used
            for tests.
        @type clock: C{task.Clock} or alike.
        """
        policies.TimeoutFactory.__init__(self, *args, **kwargs)
        self.clock = clock


    def callLater(self, period, func):
        """
        Forward to the testable clock.
        """
        return self.clock.callLater(period, func)



class WrapperTestCase(unittest.TestCase):
    """
    Tests for L{WrappingFactory} and L{ProtocolWrapper}.
    """
    def test_protocolFactoryAttribute(self):
        """
        Make sure protocol.factory is the wrapped factory, not the wrapping
        factory.
        """
        f = Server()
        wf = policies.WrappingFactory(f)
        p = wf.buildProtocol(address.IPv4Address('TCP', '127.0.0.1', 35))
        self.assertIdentical(p.wrappedProtocol.factory, f)


    def test_transportInterfaces(self):
        """
        The transport wrapper passed to the wrapped protocol's
        C{makeConnection} provides the same interfaces as are provided by the
        original transport.
        """
        class IStubTransport(Interface):
            pass

        @implementer(IStubTransport)
        class StubTransport:
            pass

        # Looking up what ProtocolWrapper implements also mutates the class.
        # It adds __implemented__ and __providedBy__ attributes to it.  These
        # prevent __getattr__ from causing the IStubTransport.providedBy call
        # below from returning True.  If, by accident, nothing else causes
        # these attributes to be added to ProtocolWrapper, the test will pass,
        # but the interface will only be provided until something does trigger
        # their addition.  So we just trigger it right now to be sure.
        implementedBy(policies.ProtocolWrapper)

        proto = protocol.Protocol()
        wrapper = policies.ProtocolWrapper(policies.WrappingFactory(None), proto)

        wrapper.makeConnection(StubTransport())
        self.assertTrue(IStubTransport.providedBy(proto.transport))


    def test_factoryLogPrefix(self):
        """
        L{WrappingFactory.logPrefix} is customized to mention both the original
        factory and the wrapping factory.
        """
        server = Server()
        factory = policies.WrappingFactory(server)
        self.assertEqual("Server (WrappingFactory)", factory.logPrefix())


    def test_factoryLogPrefixFallback(self):
        """
        If the wrapped factory doesn't have a L{logPrefix} method,
        L{WrappingFactory.logPrefix} falls back to the factory class name.
        """
        class NoFactory(object):
            pass

        server = NoFactory()
        factory = policies.WrappingFactory(server)
        self.assertEqual("NoFactory (WrappingFactory)", factory.logPrefix())


    def test_protocolLogPrefix(self):
        """
        L{ProtocolWrapper.logPrefix} is customized to mention both the original
        protocol and the wrapper.
        """
        server = Server()
        factory = policies.WrappingFactory(server)
        protocol = factory.buildProtocol(
            address.IPv4Address('TCP', '127.0.0.1', 35))
        self.assertEqual("EchoProtocol (ProtocolWrapper)",
                         protocol.logPrefix())


    def test_protocolLogPrefixFallback(self):
        """
        If the wrapped protocol doesn't have a L{logPrefix} method,
        L{ProtocolWrapper.logPrefix} falls back to the protocol class name.
        """
        class NoProtocol(object):
            pass

        server = Server()
        server.protocol = NoProtocol
        factory = policies.WrappingFactory(server)
        protocol = factory.buildProtocol(
            address.IPv4Address('TCP', '127.0.0.1', 35))
        self.assertEqual("NoProtocol (ProtocolWrapper)",
                         protocol.logPrefix())


    def _getWrapper(self):
        """
        Return L{policies.ProtocolWrapper} that has been connected to a
        L{StringTransport}.
        """
        wrapper = policies.ProtocolWrapper(policies.WrappingFactory(Server()),
                                           protocol.Protocol())
        transport = StringTransport()
        wrapper.makeConnection(transport)
        return wrapper


    def test_getHost(self):
        """
        L{policies.ProtocolWrapper.getHost} calls C{getHost} on the underlying
        transport.
        """
        wrapper = self._getWrapper()
        self.assertEqual(wrapper.getHost(), wrapper.transport.getHost())


    def test_getPeer(self):
        """
        L{policies.ProtocolWrapper.getPeer} calls C{getPeer} on the underlying
        transport.
        """
        wrapper = self._getWrapper()
        self.assertEqual(wrapper.getPeer(), wrapper.transport.getPeer())


    def test_registerProducer(self):
        """
        L{policies.ProtocolWrapper.registerProducer} calls C{registerProducer}
        on the underlying transport.
        """
        wrapper = self._getWrapper()
        producer = object()
        wrapper.registerProducer(producer, True)
        self.assertIdentical(wrapper.transport.producer, producer)
        self.assertTrue(wrapper.transport.streaming)


    def test_unregisterProducer(self):
        """
        L{policies.ProtocolWrapper.unregisterProducer} calls
        C{unregisterProducer} on the underlying transport.
        """
        wrapper = self._getWrapper()
        producer = object()
        wrapper.registerProducer(producer, True)
        wrapper.unregisterProducer()
        self.assertIdentical(wrapper.transport.producer, None)
        self.assertIdentical(wrapper.transport.streaming, None)


    def test_stopConsuming(self):
        """
        L{policies.ProtocolWrapper.stopConsuming} calls C{stopConsuming} on
        the underlying transport.
        """
        wrapper = self._getWrapper()
        result = []
        wrapper.transport.stopConsuming = lambda: result.append(True)
        wrapper.stopConsuming()
        self.assertEqual(result, [True])


    def test_startedConnecting(self):
        """
        L{policies.WrappingFactory.startedConnecting} calls
        C{startedConnecting} on the underlying factory.
        """
        result = []
        class Factory(object):
            def startedConnecting(self, connector):
                result.append(connector)

        wrapper = policies.WrappingFactory(Factory())
        connector = object()
        wrapper.startedConnecting(connector)
        self.assertEqual(result, [connector])


    def test_clientConnectionLost(self):
        """
        L{policies.WrappingFactory.clientConnectionLost} calls
        C{clientConnectionLost} on the underlying factory.
        """
        result = []
        class Factory(object):
            def clientConnectionLost(self, connector, reason):
                result.append((connector, reason))

        wrapper = policies.WrappingFactory(Factory())
        connector = object()
        reason = object()
        wrapper.clientConnectionLost(connector, reason)
        self.assertEqual(result, [(connector, reason)])


    def test_clientConnectionFailed(self):
        """
        L{policies.WrappingFactory.clientConnectionFailed} calls
        C{clientConnectionFailed} on the underlying factory.
        """
        result = []
        class Factory(object):
            def clientConnectionFailed(self, connector, reason):
                result.append((connector, reason))

        wrapper = policies.WrappingFactory(Factory())
        connector = object()
        reason = object()
        wrapper.clientConnectionFailed(connector, reason)
        self.assertEqual(result, [(connector, reason)])



class WrappingFactory(policies.WrappingFactory):
    protocol = lambda s, f, p: p

    def startFactory(self):
        policies.WrappingFactory.startFactory(self)
        self.deferred.callback(None)



class ThrottlingTestCase(unittest.TestCase):
    """
    Tests for L{policies.ThrottlingFactory}.
    """

    def test_limit(self):
        """
        Full test using a custom server limiting number of connections.
        """
        server = Server()
        c1, c2, c3, c4 = [SimpleProtocol() for i in range(4)]
        tServer = policies.ThrottlingFactory(server, 2)
        wrapTServer = WrappingFactory(tServer)
        wrapTServer.deferred = defer.Deferred()

        # Start listening
        p = reactor.listenTCP(0, wrapTServer, interface="127.0.0.1")
        n = p.getHost().port

        def _connect123(results):
            reactor.connectTCP("127.0.0.1", n, SillyFactory(c1))
            c1.dConnected.addCallback(
                lambda r: reactor.connectTCP("127.0.0.1", n, SillyFactory(c2)))
            c2.dConnected.addCallback(
                lambda r: reactor.connectTCP("127.0.0.1", n, SillyFactory(c3)))
            return c3.dDisconnected

        def _check123(results):
            self.assertEqual([c.connected for c in (c1, c2, c3)], [1, 1, 1])
            self.assertEqual([c.disconnected for c in (c1, c2, c3)], [0, 0, 1])
            self.assertEqual(len(tServer.protocols.keys()), 2)
            return results

        def _lose1(results):
            # disconnect one protocol and now another should be able to connect
            c1.transport.loseConnection()
            return c1.dDisconnected

        def _connect4(results):
            reactor.connectTCP("127.0.0.1", n, SillyFactory(c4))
            return c4.dConnected

        def _check4(results):
            self.assertEqual(c4.connected, 1)
            self.assertEqual(c4.disconnected, 0)
            return results

        def _cleanup(results):
            for c in c2, c4:
                c.transport.loseConnection()
            return defer.DeferredList([
                defer.maybeDeferred(p.stopListening),
                c2.dDisconnected,
                c4.dDisconnected])

        wrapTServer.deferred.addCallback(_connect123)
        wrapTServer.deferred.addCallback(_check123)
        wrapTServer.deferred.addCallback(_lose1)
        wrapTServer.deferred.addCallback(_connect4)
        wrapTServer.deferred.addCallback(_check4)
        wrapTServer.deferred.addCallback(_cleanup)
        return wrapTServer.deferred


    def test_writeSequence(self):
        """
        L{ThrottlingProtocol.writeSequence} is called on the underlying factory.
        """
        server = Server()
        tServer = TestableThrottlingFactory(task.Clock(), server)
        protocol = tServer.buildProtocol(
            address.IPv4Address('TCP', '127.0.0.1', 0))
        transport = StringTransportWithDisconnection()
        transport.protocol = protocol
        protocol.makeConnection(transport)

        protocol.writeSequence([b'bytes'] * 4)
        self.assertEqual(transport.value(), b"bytesbytesbytesbytes")
        self.assertEqual(tServer.writtenThisSecond, 20)


    def test_writeLimit(self):
        """
        Check the writeLimit parameter: write data, and check for the pause
        status.
        """
        server = Server()
        tServer = TestableThrottlingFactory(task.Clock(), server, writeLimit=10)
        port = tServer.buildProtocol(address.IPv4Address('TCP', '127.0.0.1', 0))
        tr = StringTransportWithDisconnection()
        tr.protocol = port
        port.makeConnection(tr)
        port.producer = port.wrappedProtocol

        port.dataReceived(b"0123456789")
        port.dataReceived(b"abcdefghij")
        self.assertEqual(tr.value(), b"0123456789abcdefghij")
        self.assertEqual(tServer.writtenThisSecond, 20)
        self.assertFalse(port.wrappedProtocol.paused)

        # at this point server should've written 20 bytes, 10 bytes
        # above the limit so writing should be paused around 1 second
        # from 'now', and resumed a second after that
        tServer.clock.advance(1.05)
        self.assertEqual(tServer.writtenThisSecond, 0)
        self.assertTrue(port.wrappedProtocol.paused)

        tServer.clock.advance(1.05)
        self.assertEqual(tServer.writtenThisSecond, 0)
        self.assertFalse(port.wrappedProtocol.paused)


    def test_readLimit(self):
        """
        Check the readLimit parameter: read data and check for the pause
        status.
        """
        server = Server()
        tServer = TestableThrottlingFactory(task.Clock(), server, readLimit=10)
        port = tServer.buildProtocol(address.IPv4Address('TCP', '127.0.0.1', 0))
        tr = StringTransportWithDisconnection()
        tr.protocol = port
        port.makeConnection(tr)

        port.dataReceived(b"0123456789")
        port.dataReceived(b"abcdefghij")
        self.assertEqual(tr.value(), b"0123456789abcdefghij")
        self.assertEqual(tServer.readThisSecond, 20)

        tServer.clock.advance(1.05)
        self.assertEqual(tServer.readThisSecond, 0)
        self.assertEqual(tr.producerState, 'paused')

        tServer.clock.advance(1.05)
        self.assertEqual(tServer.readThisSecond, 0)
        self.assertEqual(tr.producerState, 'producing')

        tr.clear()
        port.dataReceived(b"0123456789")
        port.dataReceived(b"abcdefghij")
        self.assertEqual(tr.value(), b"0123456789abcdefghij")
        self.assertEqual(tServer.readThisSecond, 20)

        tServer.clock.advance(1.05)
        self.assertEqual(tServer.readThisSecond, 0)
        self.assertEqual(tr.producerState, 'paused')

        tServer.clock.advance(1.05)
        self.assertEqual(tServer.readThisSecond, 0)
        self.assertEqual(tr.producerState, 'producing')



class TimeoutTestCase(unittest.TestCase):
    """
    Tests for L{policies.TimeoutFactory}.
    """

    def setUp(self):
        """
        Create a testable, deterministic clock, and a set of
        server factory/protocol/transport.
        """
        self.clock = task.Clock()
        wrappedFactory = protocol.ServerFactory()
        wrappedFactory.protocol = SimpleProtocol
        self.factory = TestableTimeoutFactory(self.clock, wrappedFactory, 3)
        self.proto = self.factory.buildProtocol(
            address.IPv4Address('TCP', '127.0.0.1', 12345))
        self.transport = StringTransportWithDisconnection()
        self.transport.protocol = self.proto
        self.proto.makeConnection(self.transport)


    def test_timeout(self):
        """
        Make sure that when a TimeoutFactory accepts a connection, it will
        time out that connection if no data is read or written within the
        timeout period.
        """
        # Let almost 3 time units pass
        self.clock.pump([0.0, 0.5, 1.0, 1.0, 0.4])
        self.failIf(self.proto.wrappedProtocol.disconnected)

        # Now let the timer elapse
        self.clock.pump([0.0, 0.2])
        self.failUnless(self.proto.wrappedProtocol.disconnected)


    def test_sendAvoidsTimeout(self):
        """
        Make sure that writing data to a transport from a protocol
        constructed by a TimeoutFactory resets the timeout countdown.
        """
        # Let half the countdown period elapse
        self.clock.pump([0.0, 0.5, 1.0])
        self.failIf(self.proto.wrappedProtocol.disconnected)

        # Send some data (self.proto is the /real/ proto's transport, so this
        # is the write that gets called)
        self.proto.write(b'bytes bytes bytes')

        # More time passes, putting us past the original timeout
        self.clock.pump([0.0, 1.0, 1.0])
        self.failIf(self.proto.wrappedProtocol.disconnected)

        # Make sure writeSequence delays timeout as well
        self.proto.writeSequence([b'bytes'] * 3)

        # Tick tock
        self.clock.pump([0.0, 1.0, 1.0])
        self.failIf(self.proto.wrappedProtocol.disconnected)

        # Don't write anything more, just let the timeout expire
        self.clock.pump([0.0, 2.0])
        self.failUnless(self.proto.wrappedProtocol.disconnected)


    def test_receiveAvoidsTimeout(self):
        """
        Make sure that receiving data also resets the timeout countdown.
        """
        # Let half the countdown period elapse
        self.clock.pump([0.0, 1.0, 0.5])
        self.failIf(self.proto.wrappedProtocol.disconnected)

        # Some bytes arrive, they should reset the counter
        self.proto.dataReceived(b'bytes bytes bytes')

        # We pass the original timeout
        self.clock.pump([0.0, 1.0, 1.0])
        self.failIf(self.proto.wrappedProtocol.disconnected)

        # Nothing more arrives though, the new timeout deadline is passed,
        # the connection should be dropped.
        self.clock.pump([0.0, 1.0, 1.0])
        self.failUnless(self.proto.wrappedProtocol.disconnected)



class TimeoutTester(protocol.Protocol, policies.TimeoutMixin):
    """
    A testable protocol with timeout facility.

    @ivar timedOut: set to C{True} if a timeout has been detected.
    @type timedOut: C{bool}
    """
    timeOut  = 3
    timedOut = False

    def __init__(self, clock):
        """
        Initialize the protocol with a C{task.Clock} object.
        """
        self.clock = clock


    def connectionMade(self):
        """
        Upon connection, set the timeout.
        """
        self.setTimeout(self.timeOut)


    def dataReceived(self, data):
        """
        Reset the timeout on data.
        """
        self.resetTimeout()
        protocol.Protocol.dataReceived(self, data)


    def connectionLost(self, reason=None):
        """
        On connection lost, cancel all timeout operations.
        """
        self.setTimeout(None)


    def timeoutConnection(self):
        """
        Flags the timedOut variable to indicate the timeout of the connection.
        """
        self.timedOut = True


    def callLater(self, timeout, func, *args, **kwargs):
        """
        Override callLater to use the deterministic clock.
        """
        return self.clock.callLater(timeout, func, *args, **kwargs)



class TestTimeout(unittest.TestCase):
    """
    Tests for L{policies.TimeoutMixin}.
    """

    def setUp(self):
        """
        Create a testable, deterministic clock and a C{TimeoutTester} instance.
        """
        self.clock = task.Clock()
        self.proto = TimeoutTester(self.clock)


    def test_overriddenCallLater(self):
        """
        Test that the callLater of the clock is used instead of
        C{reactor.callLater}.
        """
        self.proto.setTimeout(10)
        self.assertEqual(len(self.clock.calls), 1)


    def test_timeout(self):
        """
        Check that the protocol does timeout at the time specified by its
        C{timeOut} attribute.
        """
        self.proto.makeConnection(StringTransport())

        # timeOut value is 3
        self.clock.pump([0, 0.5, 1.0, 1.0])
        self.failIf(self.proto.timedOut)
        self.clock.pump([0, 1.0])
        self.failUnless(self.proto.timedOut)


    def test_noTimeout(self):
        """
        Check that receiving data is delaying the timeout of the connection.
        """
        self.proto.makeConnection(StringTransport())

        self.clock.pump([0, 0.5, 1.0, 1.0])
        self.failIf(self.proto.timedOut)
        self.proto.dataReceived(b'hello there')
        self.clock.pump([0, 1.0, 1.0, 0.5])
        self.failIf(self.proto.timedOut)
        self.clock.pump([0, 1.0])
        self.failUnless(self.proto.timedOut)


    def test_resetTimeout(self):
        """
        Check that setting a new value for timeout cancel the previous value
        and install a new timeout.
        """
        self.proto.timeOut = None
        self.proto.makeConnection(StringTransport())

        self.proto.setTimeout(1)
        self.assertEqual(self.proto.timeOut, 1)

        self.clock.pump([0, 0.9])
        self.failIf(self.proto.timedOut)
        self.clock.pump([0, 0.2])
        self.failUnless(self.proto.timedOut)


    def test_cancelTimeout(self):
        """
        Setting the timeout to C{None} cancel any timeout operations.
        """
        self.proto.timeOut = 5
        self.proto.makeConnection(StringTransport())

        self.proto.setTimeout(None)
        self.assertEqual(self.proto.timeOut, None)

        self.clock.pump([0, 5, 5, 5])
        self.failIf(self.proto.timedOut)


    def test_return(self):
        """
        setTimeout should return the value of the previous timeout.
        """
        self.proto.timeOut = 5

        self.assertEqual(self.proto.setTimeout(10), 5)
        self.assertEqual(self.proto.setTimeout(None), 10)
        self.assertEqual(self.proto.setTimeout(1), None)
        self.assertEqual(self.proto.timeOut, 1)

        # Clean up the DelayedCall
        self.proto.setTimeout(None)



class LimitTotalConnectionsFactoryTestCase(unittest.TestCase):
    """Tests for policies.LimitTotalConnectionsFactory"""
    def testConnectionCounting(self):
        # Make a basic factory
        factory = policies.LimitTotalConnectionsFactory()
        factory.protocol = protocol.Protocol

        # connectionCount starts at zero
        self.assertEqual(0, factory.connectionCount)

        # connectionCount increments as connections are made
        p1 = factory.buildProtocol(None)
        self.assertEqual(1, factory.connectionCount)
        p2 = factory.buildProtocol(None)
        self.assertEqual(2, factory.connectionCount)

        # and decrements as they are lost
        p1.connectionLost(None)
        self.assertEqual(1, factory.connectionCount)
        p2.connectionLost(None)
        self.assertEqual(0, factory.connectionCount)

    def testConnectionLimiting(self):
        # Make a basic factory with a connection limit of 1
        factory = policies.LimitTotalConnectionsFactory()
        factory.protocol = protocol.Protocol
        factory.connectionLimit = 1

        # Make a connection
        p = factory.buildProtocol(None)
        self.assertNotEqual(None, p)
        self.assertEqual(1, factory.connectionCount)

        # Try to make a second connection, which will exceed the connection
        # limit.  This should return None, because overflowProtocol is None.
        self.assertEqual(None, factory.buildProtocol(None))
        self.assertEqual(1, factory.connectionCount)

        # Define an overflow protocol
        class OverflowProtocol(protocol.Protocol):
            def connectionMade(self):
                factory.overflowed = True
        factory.overflowProtocol = OverflowProtocol
        factory.overflowed = False

        # Try to make a second connection again, now that we have an overflow
        # protocol.  Note that overflow connections count towards the connection
        # count.
        op = factory.buildProtocol(None)
        op.makeConnection(None) # to trigger connectionMade
        self.assertEqual(True, factory.overflowed)
        self.assertEqual(2, factory.connectionCount)

        # Close the connections.
        p.connectionLost(None)
        self.assertEqual(1, factory.connectionCount)
        op.connectionLost(None)
        self.assertEqual(0, factory.connectionCount)


class WriteSequenceEchoProtocol(EchoProtocol):
    def dataReceived(self, bytes):
        if bytes.find(b'vector!') != -1:
            self.transport.writeSequence([bytes])
        else:
            EchoProtocol.dataReceived(self, bytes)

class TestLoggingFactory(policies.TrafficLoggingFactory):
    openFile = None
    def open(self, name):
        assert self.openFile is None, "open() called too many times"
        self.openFile = NativeStringIO()
        return self.openFile



class LoggingFactoryTestCase(unittest.TestCase):
    """
    Tests for L{policies.TrafficLoggingFactory}.
    """

    def test_thingsGetLogged(self):
        """
        Check the output produced by L{policies.TrafficLoggingFactory}.
        """
        wrappedFactory = Server()
        wrappedFactory.protocol = WriteSequenceEchoProtocol
        t = StringTransportWithDisconnection()
        f = TestLoggingFactory(wrappedFactory, 'test')
        p = f.buildProtocol(('1.2.3.4', 5678))
        t.protocol = p
        p.makeConnection(t)

        v = f.openFile.getvalue()
        self.assertIn('*', v)
        self.failIf(t.value())

        p.dataReceived(b'here are some bytes')

        v = f.openFile.getvalue()
        self.assertIn("C 1: %r" % (b'here are some bytes',), v)
        self.assertIn("S 1: %r" % (b'here are some bytes',), v)
        self.assertEqual(t.value(), b'here are some bytes')

        t.clear()
        p.dataReceived(b'prepare for vector! to the extreme')
        v = f.openFile.getvalue()
        self.assertIn("SV 1: %r" % ([b'prepare for vector! to the extreme'],), v)
        self.assertEqual(t.value(), b'prepare for vector! to the extreme')

        p.loseConnection()

        v = f.openFile.getvalue()
        self.assertIn('ConnectionDone', v)


    def test_counter(self):
        """
        Test counter management with the resetCounter method.
        """
        wrappedFactory = Server()
        f = TestLoggingFactory(wrappedFactory, 'test')
        self.assertEqual(f._counter, 0)
        f.buildProtocol(('1.2.3.4', 5678))
        self.assertEqual(f._counter, 1)
        # Reset log file
        f.openFile = None
        f.buildProtocol(('1.2.3.4', 5679))
        self.assertEqual(f._counter, 2)

        f.resetCounter()
        self.assertEqual(f._counter, 0)

