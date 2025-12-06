from fastapi import APIRouter, HTTPException
import grpc
import logging
import os

from api_gateway.app.models.sync import SyncRequest, SyncResponse
from api_gateway.app.models.document import DeleteVectorResponse

from shared.protos import service_pb2, service_pb2_grpc
from shared.config import config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sync", response_model=SyncResponse, tags=["Upload"])
async def trigger_sync(request: SyncRequest):
    """
    Tells RAG Service to start processing the file we just uploaded.
    """
    logger.info(f"Received sync request: {request}")
    try:
        # Open gRPC connection to RAG Service
        async with grpc.aio.insecure_channel(config.RAG_SERVICE_HOST) as channel:
            stub = service_pb2_grpc.RAGServiceStub(channel)

            # Construct gRPC message
            grpc_req = service_pb2.SyncRequest(  # type: ignore
                doc_id=request.doc_id,
                file_path=os.path.join(config.UPLOAD_DIR, request.filename),
            )

            # Call remote method
            response = await stub.TriggerSync(grpc_req)
            return {"job_id": response.job_id, "status": response.status}

    except grpc.RpcError as e:
        logger.error(f"gRPC RAG Service error: {e.details()}")
        raise HTTPException(status_code=500, detail=f"RAG Service Error: {e.details()}")


@router.delete("/{doc_id}", response_model=DeleteVectorResponse, tags=["Vectors"])
async def delete_vectors(doc_id: str):
    try:
        async with grpc.aio.insecure_channel(config.RAG_SERVICE_HOST) as channel:
            stub = service_pb2_grpc.RAGServiceStub(channel)
            response = await stub.DeleteVectors(service_pb2.DeleteVectorRequest(doc_id=doc_id))  # type: ignore
            return DeleteVectorResponse(success=response.success)
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"RAG Service Error: {e.details()}")
