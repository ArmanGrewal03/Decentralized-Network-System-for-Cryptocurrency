import grpc
import warnings

from proto import blockchain_pb2 as proto_dot_blockchain__pb2

GRPC_GENERATED_VERSION = '1.78.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + ' but the generated code in proto/blockchain_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class BlockchainNodeStub(object):
    """Node-to-node sync: get chain, submit new block (distributed systems).
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetChain = channel.unary_unary(
                '/coe892.blockchain.BlockchainNode/GetChain',
                request_serializer=proto_dot_blockchain__pb2.GetChainRequest.SerializeToString,
                response_deserializer=proto_dot_blockchain__pb2.ChainResponse.FromString,
                _registered_method=True)
        self.SubmitBlock = channel.unary_unary(
                '/coe892.blockchain.BlockchainNode/SubmitBlock',
                request_serializer=proto_dot_blockchain__pb2.BlockMessage.SerializeToString,
                response_deserializer=proto_dot_blockchain__pb2.Ack.FromString,
                _registered_method=True)
        self.StreamBlocks = channel.unary_stream(
                '/coe892.blockchain.BlockchainNode/StreamBlocks',
                request_serializer=proto_dot_blockchain__pb2.StreamBlocksRequest.SerializeToString,
                response_deserializer=proto_dot_blockchain__pb2.BlockMessage.FromString,
                _registered_method=True)


class BlockchainNodeServicer(object):
    """Node-to-node sync: get chain, submit new block (distributed systems).
    """

    def GetChain(self, request, context):
        """Get full chain for sync.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SubmitBlock(self, request, context):
        """Submit a newly mined block to the network.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StreamBlocks(self, request, context):
        """Stream chain updates (optional).
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_BlockchainNodeServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetChain': grpc.unary_unary_rpc_method_handler(
                    servicer.GetChain,
                    request_deserializer=proto_dot_blockchain__pb2.GetChainRequest.FromString,
                    response_serializer=proto_dot_blockchain__pb2.ChainResponse.SerializeToString,
            ),
            'SubmitBlock': grpc.unary_unary_rpc_method_handler(
                    servicer.SubmitBlock,
                    request_deserializer=proto_dot_blockchain__pb2.BlockMessage.FromString,
                    response_serializer=proto_dot_blockchain__pb2.Ack.SerializeToString,
            ),
            'StreamBlocks': grpc.unary_stream_rpc_method_handler(
                    servicer.StreamBlocks,
                    request_deserializer=proto_dot_blockchain__pb2.StreamBlocksRequest.FromString,
                    response_serializer=proto_dot_blockchain__pb2.BlockMessage.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'coe892.blockchain.BlockchainNode', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('coe892.blockchain.BlockchainNode', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class BlockchainNode(object):
    """Node-to-node sync: get chain, submit new block (distributed systems).
    """

    @staticmethod
    def GetChain(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/coe892.blockchain.BlockchainNode/GetChain',
            proto_dot_blockchain__pb2.GetChainRequest.SerializeToString,
            proto_dot_blockchain__pb2.ChainResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def SubmitBlock(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/coe892.blockchain.BlockchainNode/SubmitBlock',
            proto_dot_blockchain__pb2.BlockMessage.SerializeToString,
            proto_dot_blockchain__pb2.Ack.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def StreamBlocks(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/coe892.blockchain.BlockchainNode/StreamBlocks',
            proto_dot_blockchain__pb2.StreamBlocksRequest.SerializeToString,
            proto_dot_blockchain__pb2.BlockMessage.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
