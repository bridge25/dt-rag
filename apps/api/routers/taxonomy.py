"""
Taxonomy Router
택소노미 관리 API 엔드포인트
"""

import logging
import time
from typing import Dict, Any, List

from fastapi import APIRouter, Request, HTTPException, Depends, Path
from fastapi.responses import JSONResponse

from ..services.database_service import get_database_service, DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{version}/tree",
    summary="택소노미 트리 조회",
    description="특정 버전의 노드/엣지 구조 JSON 반환",
    responses={
        200: {"description": "트리 구조 반환"},
        404: {"description": "버전을 찾을 수 없음"},
        500: {"description": "서버 내부 오류"}
    }
)
async def get_taxonomy_tree(
    version: str = Path(..., description="Taxonomy version", example="1.8.1"),
    request: Request,
    db_service: DatabaseService = Depends(get_database_service)
) -> Dict[str, Any]:
    """택소노미 트리 구조 조회"""
    
    start_time = time.time()
    
    try:
        # Get taxonomy tree from database
        tree_data = await db_service.get_taxonomy_tree(version)
        
        if not tree_data["nodes"]:
            raise HTTPException(
                status_code=404,
                detail=f"Taxonomy version not found: {version}"
            )
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Taxonomy tree retrieved: version={version}, "
            f"nodes={len(tree_data['nodes'])}, "
            f"time={processing_time:.3f}s"
        )
        
        # Add metadata to response
        tree_data.update({
            "request_id": request.state.request_id,
            "processing_time": processing_time
        })
        
        return tree_data
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Failed to get taxonomy tree: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve taxonomy tree"
        )


@router.get(
    "/{version}/diff/{compare_version}",
    summary="택소노미 버전 간 차이점 조회",
    description="두 택소노미 버전 간의 차이점을 비교하여 반환"
)
async def get_taxonomy_diff(
    version: str = Path(..., description="Base version", example="1.8.1"),
    compare_version: str = Path(..., description="Compare version", example="1.8.0"),
    request: Request,
    db_service: DatabaseService = Depends(get_database_service)
) -> Dict[str, Any]:
    """택소노미 버전 간 차이점 조회"""
    
    start_time = time.time()
    
    try:
        async with db_service.get_connection() as conn:
            
            # Get base version nodes
            base_nodes = await conn.fetch("""
                SELECT node_id, canonical_path, node_name
                FROM taxonomy_nodes
                WHERE version = $1
            """, version)
            
            # Get compare version nodes
            compare_nodes = await conn.fetch("""
                SELECT node_id, canonical_path, node_name
                FROM taxonomy_nodes  
                WHERE version = $1
            """, compare_version)
            
            if not base_nodes:
                raise HTTPException(
                    status_code=404,
                    detail=f"Base version not found: {version}"
                )
            
            if not compare_nodes:
                raise HTTPException(
                    status_code=404,
                    detail=f"Compare version not found: {compare_version}"
                )
            
            # Convert to dictionaries for comparison
            base_dict = {row["node_id"]: dict(row) for row in base_nodes}
            compare_dict = {row["node_id"]: dict(row) for row in compare_nodes}
            
            # Find differences
            added_nodes = []
            removed_nodes = []
            modified_nodes = []
            
            # Find added nodes (in base, not in compare)
            for node_id, node_data in base_dict.items():
                if node_id not in compare_dict:
                    added_nodes.append(node_data)
            
            # Find removed nodes (in compare, not in base)
            for node_id, node_data in compare_dict.items():
                if node_id not in base_dict:
                    removed_nodes.append(node_data)
            
            # Find modified nodes
            for node_id in base_dict:
                if node_id in compare_dict:
                    base_node = base_dict[node_id]
                    compare_node = compare_dict[node_id]
                    
                    if (base_node["canonical_path"] != compare_node["canonical_path"] or
                        base_node["node_name"] != compare_node["node_name"]):
                        modified_nodes.append({
                            "node_id": node_id,
                            "base": base_node,
                            "compare": compare_node
                        })
            
            processing_time = time.time() - start_time
            
            return {
                "base_version": version,
                "compare_version": compare_version,
                "summary": {
                    "added": len(added_nodes),
                    "removed": len(removed_nodes),
                    "modified": len(modified_nodes)
                },
                "changes": {
                    "added_nodes": added_nodes,
                    "removed_nodes": removed_nodes,
                    "modified_nodes": modified_nodes
                },
                "processing_time": processing_time,
                "request_id": request.state.request_id
            }
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Failed to get taxonomy diff: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to compare taxonomy versions"
        )


@router.post(
    "/{version}/rollback",
    summary="택소노미 롤백 실행",
    description="특정 버전으로 택소노미 롤백 (Admin/Ops 권한 필요)",
    responses={
        200: {"description": "롤백 성공"},
        403: {"description": "권한 부족 - Admin/Ops 역할 필요"},
        404: {"description": "대상 버전을 찾을 수 없음"},
        409: {"description": "롤백 충돌 - 진행 중인 롤백 존재"},
        500: {"description": "롤백 실행 실패"}
    }
)
async def rollback_taxonomy(
    version: str = Path(..., description="Target rollback version", example="1.8.0"),
    request: Request,
    db_service: DatabaseService = Depends(get_database_service)
) -> Dict[str, Any]:
    """택소노미 롤백 실행 (Admin/Ops 전용)"""
    
    start_time = time.time()
    
    try:
        # Check user permissions (should have been validated by AuthMiddleware)
        user_permissions = getattr(request.state, "user_permissions", set())
        if "taxonomy:rollback" not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for taxonomy rollback operation"
            )
        
        user_id = getattr(request.state, "user_id", "unknown")
        
        logger.warning(
            f"Taxonomy rollback initiated: version={version}, "
            f"user={user_id}, request_id={request.state.request_id}"
        )
        
        async with db_service.get_connection() as conn:
            
            # Validate target version exists
            version_exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM taxonomy_nodes WHERE version = $1
                )
            """, version)
            
            if not version_exists:
                raise HTTPException(
                    status_code=404,
                    detail=f"Target rollback version not found: {version}"
                )
            
            # Check for ongoing rollback operations
            ongoing_rollback = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM audit_log 
                    WHERE action LIKE 'taxonomy_rollback_%' 
                    AND created_at > NOW() - INTERVAL '1 hour'
                    AND details->>'status' = 'in_progress'
                )
            """)
            
            if ongoing_rollback:
                raise HTTPException(
                    status_code=409,
                    detail="Rollback operation already in progress"
                )
            
            # Execute rollback procedure
            try:
                await conn.execute("CALL taxonomy_rollback($1)", version)
                
                # Record successful rollback in audit log
                await conn.execute("""
                    INSERT INTO audit_log (action, user_id, details, created_at)
                    VALUES ($1, $2, $3, NOW())
                """, 
                "taxonomy_rollback_success", 
                user_id,
                {
                    "target_version": version,
                    "status": "completed",
                    "request_id": request.state.request_id
                })
                
            except Exception as rollback_error:
                # Record failed rollback
                await conn.execute("""
                    INSERT INTO audit_log (action, user_id, details, created_at)
                    VALUES ($1, $2, $3, NOW())
                """,
                "taxonomy_rollback_failed",
                user_id, 
                {
                    "target_version": version,
                    "status": "failed",
                    "error": str(rollback_error),
                    "request_id": request.state.request_id
                })
                raise
            
            processing_time = time.time() - start_time
            
            logger.warning(
                f"Taxonomy rollback completed: version={version}, "
                f"time={processing_time:.3f}s, user={user_id}"
            )
            
            return {
                "status": "success",
                "message": f"Taxonomy successfully rolled back to version {version}",
                "target_version": version,
                "rollback_time": processing_time,
                "request_id": request.state.request_id,
                "operator": user_id
            }
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Taxonomy rollback failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Rollback operation failed"
        )


@router.get(
    "/versions",
    summary="사용 가능한 택소노미 버전 목록 조회",
    description="시스템에서 사용 가능한 모든 택소노미 버전 목록 반환"
)
async def get_available_versions(
    request: Request,
    db_service: DatabaseService = Depends(get_database_service)
) -> Dict[str, Any]:
    """사용 가능한 택소노미 버전 목록 조회"""
    
    try:
        async with db_service.get_connection() as conn:
            
            versions = await conn.fetch("""
                SELECT 
                    version,
                    COUNT(DISTINCT node_id) as node_count,
                    MIN(created_at) as created_at,
                    MAX(created_at) as last_updated
                FROM taxonomy_nodes
                GROUP BY version
                ORDER BY created_at DESC
            """)
            
            # Get current active version
            current_version = await conn.fetchval("""
                SELECT version 
                FROM taxonomy_nodes 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            return {
                "current_version": current_version,
                "available_versions": [
                    {
                        **dict(row),
                        "is_current": row["version"] == current_version
                    } 
                    for row in versions
                ],
                "total_versions": len(versions),
                "request_id": request.state.request_id
            }
            
    except Exception as e:
        logger.error(f"Failed to get taxonomy versions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve taxonomy versions"
        )


@router.get("/health")
async def taxonomy_health_check(
    db_service: DatabaseService = Depends(get_database_service)
):
    """택소노미 서비스 건강 상태 확인"""
    
    try:
        async with db_service.get_connection() as conn:
            
            # Check taxonomy tables
            tables_exist = await conn.fetch("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename IN ('taxonomy_nodes', 'taxonomy_edges')
            """)
            
            if len(tables_exist) < 2:
                return {
                    "status": "unhealthy",
                    "reason": "Taxonomy tables missing"
                }
            
            # Check if we have taxonomy data
            node_count = await conn.fetchval("""
                SELECT COUNT(*) FROM taxonomy_nodes
            """)
            
            if node_count == 0:
                return {
                    "status": "degraded",
                    "reason": "No taxonomy data found"
                }
            
            # Check rollback procedure exists
            rollback_proc = await conn.fetchval("""
                SELECT proname FROM pg_proc WHERE proname = 'taxonomy_rollback'
            """)
            
            if not rollback_proc:
                return {
                    "status": "degraded",
                    "reason": "Rollback procedure not found"
                }
            
            return {
                "status": "healthy",
                "taxonomy_nodes": node_count,
                "features": ["tree_structure", "version_diff", "rollback"]
            }
            
    except Exception as e:
        logger.error(f"Taxonomy health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}