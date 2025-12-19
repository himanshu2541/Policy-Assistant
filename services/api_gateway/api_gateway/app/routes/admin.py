import asyncio
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import grpc
import logging
import os

from api_gateway.app.models.sync import SyncRequest, SyncResponse
from api_gateway.app.models.document import DeleteVectorResponse

from api_gateway.core.dependencies import get_redis_pubsub
from shared.protos import service_pb2, service_pb2_grpc
from shared.config import config

logger = logging.getLogger("API-Gateway.Routes.Admin")

router = APIRouter()


@router.post("/sync", response_model=SyncResponse, tags=["Sync"])
async def trigger_sync(request: SyncRequest):
    """
    Tells RAG Service to start processing the file we just uploaded.
    """
    logger.info(f"Received sync request: {request}")
    target = f"{config.RAG_SERVICE_HOST}:{config.RAG_SERVICE_PORT}"
    logger.info(f"Connecting to RAG service at {target}")
    try:
        # Open gRPC connection to RAG Service
        async with grpc.aio.insecure_channel(target) as channel:
            stub = service_pb2_grpc.RAGServiceStub(channel)

            grpc_req = service_pb2.SyncRequest(  # type: ignore
                doc_id=request.doc_id,
                file_path=os.path.join(config.UPLOAD_DIR, request.filename),
            )
            logger.info(
                f"Sending sync request for doc_id: {request.doc_id}, file: {request.filename}"
            )

            response = await stub.TriggerSync(grpc_req)
            logger.info(
                f"Sync triggered successfully, job_id: {response.job_id}, status: {response.status}"
            )
            return {"job_id": response.job_id, "status": response.status}

    except grpc.RpcError as e:
        logger.error(f"gRPC RAG Service error: {e.details()}")
        raise HTTPException(status_code=500, detail=f"RAG Service Error: {e.details()}")


@router.websocket("/ws/notifications")
async def admin_notifications(websocket: WebSocket):
    """
    dedicated WebSocket endpoint for admin panel push notifications.
    """
    await websocket.accept()
    logger.info("Admin connected to notifications WebSocket.")

    redis = await get_redis_pubsub()
    try:
        async with redis.pubsub() as pubsub:
            await pubsub.subscribe("job_updates")
            
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

                if message:
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    await websocket.send_text(data)
                
                # Keep connection alive
                await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        logger.info("Client disconnected normally.")
    except Exception as e:
        logger.error(f"Socket Error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

@router.delete(
    "/vectors", response_model=DeleteVectorResponse, tags=["Vectors"]
)
async def delete_vectors(doc_id: str):
    logger.info(f"Received delete vectors request for doc_id: {doc_id}")
    try:
        target = f"{config.RAG_SERVICE_HOST}:{config.RAG_SERVICE_PORT}"
        logger.info(f"Connecting to RAG service at {target} for deletion")
        async with grpc.aio.insecure_channel(target) as channel:
            stub = service_pb2_grpc.RAGServiceStub(channel)
            logger.info(f"Sending delete request for doc_id: {doc_id}")
            response = await stub.DeleteVectors(service_pb2.DeleteVectorRequest(doc_id=doc_id))  # type: ignore
            logger.info(
                f"Vectors deleted successfully for doc_id: {doc_id}, success: {response.success}"
            )
            return DeleteVectorResponse(success=response.success)
    except grpc.RpcError as e:
        logger.error(f"gRPC RAG Service error during deletion: {e.details()}")
        raise HTTPException(status_code=500, detail=f"RAG Service Error: {e.details()}")


@router.get("/documents")
async def list_documents():
    """
    Fetch all ingested documents.
    """
    logger.info("Received request to list all documents")
    try:
        async with grpc.aio.insecure_channel(
            f"{config.RAG_SERVICE_HOST}:{config.RAG_SERVICE_PORT}"
        ) as channel:
            stub = service_pb2_grpc.RAGServiceStub(channel)
            # Empty request
            response = await stub.ListDocuments(service_pb2.Empty())  # type: ignore

            # Convert Proto list to JSON
            logger.info(f"Fetched {len(response.docs)} documents from RAG Service")
            return [
                {
                    "doc_id": doc.doc_id,
                    "filename": doc.filename,
                    "status": doc.status,
                    "timestamp": doc.timestamp,
                }
                for doc in response.docs
            ]
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
