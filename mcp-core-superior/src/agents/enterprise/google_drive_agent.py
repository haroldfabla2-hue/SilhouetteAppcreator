"""
Google Drive Agent - Agente Especializado para Google Drive
Proporciona capacidades avanzadas de gestión de archivos, carpetas y sincronización
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import mimetypes
from pathlib import Path

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaInMemoryUpload
import httpx

from .base_google_workspace_agent import (
    BaseGoogleWorkspaceAgent, 
    GoogleWorkspaceService, 
    GoogleWorkspaceConfig,
    ApiResponse
)
from ...core.exceptions import AgentException, handle_exceptions
from ...core.config import settings


class FileType(Enum):
    """Tipos de archivo"""
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    FOLDER = "folder"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    PDF = "pdf"
    TEXT = "text"
    ARCHIVE = "archive"
    CODE = "code"
    OTHER = "other"


class PermissionRole(Enum):
    """Roles de permisos"""
    READER = "reader"
    COMMENTER = "commenter"
    WRITER = "writer"
    OWNER = "owner"
    ORGANIZER = "organizer"
    FILE_ORGANIZER = "fileOrganizer"


class FileStatus(Enum):
    """Estados de archivo"""
    ACTIVE = "active"
    TRASHED = "trashed"
    STARRED = "starred"
    SHARED = "shared"
    CORRUPTED = "corrupted"


@dataclass
class FileMetadata:
    """Metadatos de archivo"""
    id: str
    name: str
    mime_type: str
    size: Optional[int] = None
    created_time: Optional[datetime] = None
    modified_time: Optional[datetime] = None
    owner: Optional[str] = None
    parents: List[str] = field(default_factory=list)
    description: Optional[str] = None
    web_view_link: Optional[str] = None
    file_type: Optional[FileType] = None


@dataclass
class FolderStructure:
    """Estructura de carpeta"""
    id: str
    name: str
    path: str
    children: List[Union['FileMetadata', 'FolderStructure']] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)


@dataclass
class SyncOperation:
    """Operación de sincronización"""
    operation_type: str  # upload, download, update, delete
    file_id: str
    local_path: Optional[str] = None
    drive_path: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


@dataclass
class BatchOperation:
    """Operación en lote"""
    operation_type: str
    files: List[str]
    parameters: Dict[str, Any]
    status: str = "pending"
    results: List[Dict[str, Any]] = field(default_factory=list)


class GoogleDriveAgent(BaseGoogleWorkspaceAgent):
    """
    Agente Especializado para Google Drive
    
    Funcionalidades:
    - Subir y descargar archivos
    - Gestión de carpetas y estructura
    - Búsqueda avanzada de archivos
    - Gestión de permisos y compartir
    - Sincronización bidireccional
    - Versionado de archivos
    - Operaciones en lote
    - Backup y restauración
    """
    
    def __init__(self, config: GoogleWorkspaceConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.drive_service = None
        self.sync_operations: List[SyncOperation] = []
        self.local_cache: Dict[str, FileMetadata] = {}
        
        # Configurar capacidades específicas
        self.add_capability(AgentCapability.FILE_PROCESSING)
        self.add_capability(AgentCapability.AUTOMATION)
    
    async def initialize(self):
        """Inicializar servicio de Drive"""
        await super().authenticate()
        self.drive_service = await self.get_service(GoogleWorkspaceService.DRIVE)
    
    @handle_exceptions
    async def upload_file(
        self,
        file_path: str,
        parent_folder_id: Optional[str] = None,
        file_name: Optional[str] = None
    ) -> ApiResponse:
        """
        Subir archivo a Google Drive
        
        Args:
            file_path: Ruta del archivo local
            parent_folder_id: ID de carpeta destino
            file_name: Nombre del archivo (opcional)
            
        Returns:
            ApiResponse: Resultado de la subida
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return ApiResponse(success=False, error="Archivo no encontrado")
            
            # Metadatos del archivo
            metadata = {
                'name': file_name or file_path.name
            }
            
            if parent_folder_id:
                metadata['parents'] = [parent_folder_id]
            
            # Detectar MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Subir archivo
            media = MediaFileUpload(
                str(file_path),
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=metadata,
                media_body=media,
                fields='id,name,webViewLink,size,createdTime,modifiedTime'
            ).execute()
            
            # Crear metadatos
            file_metadata = FileMetadata(
                id=file['id'],
                name=file['name'],
                mime_type=mime_type,
                size=int(file.get('size', 0)),
                created_time=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')),
                modified_time=datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00')),
                web_view_link=file.get('webViewLink', ''),
                file_type=self._detect_file_type(mime_type)
            )
            
            # Cachear archivo
            self.local_cache[file['id']] = file_metadata
            
            self.logger.info(f"Archivo subido: {file_metadata.name} ({file_metadata.id})")
            
            return ApiResponse(
                success=True,
                data={
                    'file_metadata': file_metadata.__dict__,
                    'file_id': file['id'],
                    'web_link': file.get('webViewLink', '')
                }
            )
            
        except Exception as e:
            error_msg = f"Error subiendo archivo: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def download_file(
        self,
        file_id: str,
        destination_path: str
    ) -> ApiResponse:
        """
        Descargar archivo de Google Drive
        
        Args:
            file_id: ID del archivo
            destination_path: Ruta destino local
            
        Returns:
            ApiResponse: Resultado de la descarga
        """
        try:
            # Obtener metadatos del archivo
            file_metadata = await self.get_file_metadata(file_id)
            if not file_metadata.success:
                return file_metadata
            
            file_info = FileMetadata(**file_metadata.data)
            
            # Descargar contenido
            request = self.drive_service.files().get_media(fileId=file_id)
            
            destination_path = Path(destination_path)
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(destination_path, 'wb') as fh:
                downloader = MediaDownloader(fh)
                status, done = downloader.download(request)
            
            self.logger.info(f"Archivo descargado: {file_info.name} a {destination_path}")
            
            return ApiResponse(
                success=True,
                data={
                    'file_id': file_id,
                    'local_path': str(destination_path),
                    'file_name': file_info.name,
                    'size': file_info.size
                }
            )
            
        except Exception as e:
            error_msg = f"Error descargando archivo: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def get_file_metadata(self, file_id: str) -> ApiResponse:
        """
        Obtener metadatos de un archivo
        
        Args:
            file_id: ID del archivo
            
        Returns:
            ApiResponse: Metadatos del archivo
        """
        try:
            file = self.drive_service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,size,createdTime,modifiedTime,parents,description,webViewLink,owners'
            ).execute()
            
            metadata = FileMetadata(
                id=file['id'],
                name=file['name'],
                mime_type=file['mimeType'],
                size=int(file.get('size', 0)),
                created_time=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')),
                modified_time=datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00')),
                owners=[owner.get('emailAddress', '') for owner in file.get('owners', [])],
                parents=file.get('parents', []),
                description=file.get('description', ''),
                web_view_link=file.get('webViewLink', ''),
                file_type=self._detect_file_type(file['mimeType'])
            )
            
            return ApiResponse(success=True, data=metadata.__dict__)
            
        except Exception as e:
            error_msg = f"Error obteniendo metadatos: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def create_folder(
        self,
        name: str,
        parent_folder_id: Optional[str] = None
    ) -> ApiResponse:
        """
        Crear carpeta
        
        Args:
            name: Nombre de la carpeta
            parent_folder_id: ID de carpeta padre (opcional)
            
        Returns:
            ApiResponse: Resultado de la creación
        """
        try:
            metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                metadata['parents'] = [parent_folder_id]
            
            folder = self.drive_service.files().create(
                body=metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            self.logger.info(f"Carpeta creada: {name} ({folder['id']})")
            
            return ApiResponse(
                success=True,
                data={
                    'folder_id': folder['id'],
                    'name': folder['name'],
                    'web_link': folder.get('webViewLink', '')
                }
            )
            
        except Exception as e:
            error_msg = f"Error creando carpeta: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def list_files(
        self,
        folder_id: Optional[str] = None,
        file_type: Optional[FileType] = None,
        limit: int = 100
    ) -> ApiResponse:
        """
        Listar archivos en carpeta
        
        Args:
            folder_id: ID de carpeta (opcional)
            file_type: Filtrar por tipo de archivo
            limit: Límite de resultados
            
        Returns:
            ApiResponse: Lista de archivos
        """
        try:
            # Construir query
            query_parts = ["trashed=false"]
            
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            
            if file_type:
                mime_type = self._get_mime_type_for_file_type(file_type)
                query_parts.append(f"mimeType='{mime_type}'")
            
            query = ' and '.join(query_parts)
            
            # Ejecutar búsqueda
            results = self.drive_service.files().list(
                q=query,
                pageSize=limit,
                fields='files(id,name,mimeType,size,createdTime,modifiedTime,webViewLink,parents)'
            ).execute()
            
            files = results.get('files', [])
            
            # Convertir a metadatos
            file_metadata_list = []
            for file in files:
                metadata = FileMetadata(
                    id=file['id'],
                    name=file['name'],
                    mime_type=file['mimeType'],
                    size=int(file.get('size', 0)),
                    created_time=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')),
                    modified_time=datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00')),
                    parents=file.get('parents', []),
                    web_view_link=file.get('webViewLink', ''),
                    file_type=self._detect_file_type(file['mimeType'])
                )
                file_metadata_list.append(metadata.__dict__)
            
            return ApiResponse(
                success=True,
                data={
                    'files': file_metadata_list,
                    'total_count': len(file_metadata_list)
                }
            )
            
        except Exception as e:
            error_msg = f"Error listando archivos: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def search_files(
        self,
        query: str,
        file_type: Optional[FileType] = None,
        owner: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 50
    ) -> ApiResponse:
        """
        Búsqueda avanzada de archivos
        
        Args:
            query: Consulta de búsqueda
            file_type: Filtrar por tipo
            owner: Filtrar por propietario
            date_range: Rango de fechas (created, modified)
            limit: Límite de resultados
            
        Returns:
            ApiResponse: Resultados de búsqueda
        """
        try:
            # Construir query de búsqueda
            query_parts = ["trashed=false"]
            
            # Texto de búsqueda
            if query:
                query_parts.append(f"fullText contains '{query}'")
            
            # Filtro por tipo
            if file_type:
                mime_type = self._get_mime_type_for_file_type(file_type)
                query_parts.append(f"mimeType='{mime_type}'")
            
            # Filtro por propietario
            if owner:
                query_parts.append(f"'{owner}' in owners")
            
            # Filtro por fecha
            if date_range:
                start_date, end_date = date_range
                query_parts.append(f"modifiedTime >= '{start_date.isoformat()}'")
                query_parts.append(f"modifiedTime <= '{end_date.isoformat()}'")
            
            search_query = ' and '.join(query_parts)
            
            # Ejecutar búsqueda
            results = self.drive_service.files().list(
                q=search_query,
                pageSize=limit,
                fields='files(id,name,mimeType,size,createdTime,modifiedTime,webViewLink,owners)',
                orderBy='modifiedTime desc'
            ).execute()
            
            files = results.get('files', [])
            
            # Procesar resultados
            search_results = []
            for file in files:
                metadata = FileMetadata(
                    id=file['id'],
                    name=file['name'],
                    mime_type=file['mimeType'],
                    size=int(file.get('size', 0)),
                    created_time=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')),
                    modified_time=datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00')),
                    web_view_link=file.get('webViewLink', ''),
                    file_type=self._detect_file_type(file['mimeType'])
                )
                search_results.append(metadata.__dict__)
            
            return ApiResponse(
                success=True,
                data={
                    'search_results': search_results,
                    'query': query,
                    'total_results': len(search_results)
                }
            )
            
        except Exception as e:
            error_msg = f"Error en búsqueda: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def share_file(
        self,
        file_id: str,
        email: str,
        role: PermissionRole = PermissionRole.READER
    ) -> ApiResponse:
        """
        Compartir archivo con usuario
        
        Args:
            file_id: ID del archivo
            email: Email del usuario
            role: Rol a asignar
            
        Returns:
            ApiResponse: Resultado del compartir
        """
        try:
            permission = {
                'type': 'user',
                'role': role.value,
                'emailAddress': email
            }
            
            result = self.drive_service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=False
            ).execute()
            
            self.logger.info(f"Archivo {file_id} compartido con {email} como {role.value}")
            
            return ApiResponse(
                success=True,
                data={
                    'file_id': file_id,
                    'shared_with': email,
                    'role': role.value,
                    'permission_id': result.get('id', '')
                }
            )
            
        except Exception as e:
            error_msg = f"Error compartiendo archivo: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def get_folder_structure(
        self,
        folder_id: Optional[str] = None,
        max_depth: int = 3
    ) -> ApiResponse:
        """
        Obtener estructura completa de carpeta
        
        Args:
            folder_id: ID de carpeta (raíz si no se especifica)
            max_depth: Profundidad máxima
            
        Returns:
            ApiResponse: Estructura de carpetas
        """
        try:
            async def build_structure(folder_id: Optional[str], current_depth: int) -> FolderStructure:
                if current_depth > max_depth:
                    return None
                
                if folder_id is None:
                    # Es la raíz
                    folder_name = "Mi Unidad"
                    folder_path = "/"
                else:
                    # Obtener info de la carpeta
                    folder_info = await self.get_file_metadata(folder_id)
                    if not folder_info.success:
                        return None
                    
                    folder_name = folder_info.data['name']
                    folder_path = folder_info.data.get('web_view_link', '')
                
                # Listar contenido
                list_result = await self.list_files(folder_id=folder_id)
                if not list_result.success:
                    return None
                
                children = []
                for file_data in list_result.data['files']:
                    file_id = file_data['id']
                    file_name = file_data['name']
                    file_type = file_data.get('file_type')
                    
                    if file_type == FileType.FOLDER:
                        # Recursión para carpetas
                        child_structure = await build_structure(file_id, current_depth + 1)
                        if child_structure:
                            children.append(child_structure)
                    else:
                        # Archivo normal
                        file_metadata = FileMetadata(**file_data)
                        children.append(file_metadata)
                
                return FolderStructure(
                    id=folder_id or "root",
                    name=folder_name,
                    path=folder_path,
                    children=children
                )
            
            structure = await build_structure(folder_id, 0)
            
            return ApiResponse(success=True, data=structure.__dict__)
            
        except Exception as e:
            error_msg = f"Error obteniendo estructura: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def batch_operation(
        self,
        operation: BatchOperation
    ) -> ApiResponse:
        """
        Ejecutar operación en lote
        
        Args:
            operation: Configuración de operación
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            results = []
            
            if operation.operation_type == "delete":
                # Eliminar archivos en lote
                for file_id in operation.files:
                    try:
                        self.drive_service.files().delete(fileId=file_id).execute()
                        results.append({"file_id": file_id, "status": "success"})
                    except Exception as e:
                        results.append({"file_id": file_id, "status": "error", "error": str(e)})
            
            elif operation.operation_type == "move":
                # Mover archivos
                target_folder = operation.parameters.get('target_folder_id')
                for file_id in operation.files:
                    try:
                        file = self.drive_service.files().get(fileId=file_id, fields='parents').execute()
                        
                        # Remover de carpeta actual
                        previous_parents = ','.join(file.get('parents', []))
                        
                        # Mover a nueva carpeta
                        self.drive_service.files().update(
                            fileId=file_id,
                            addParents=target_folder,
                            removeParents=previous_parents,
                            fields='id,parents'
                        ).execute()
                        
                        results.append({"file_id": file_id, "status": "success"})
                    except Exception as e:
                        results.append({"file_id": file_id, "status": "error", "error": str(e)})
            
            else:
                return ApiResponse(
                    success=False,
                    error=f"Operación en lote no soportada: {operation.operation_type}"
                )
            
            operation.status = "completed"
            operation.results = results
            
            return ApiResponse(
                success=True,
                data={
                    'operation_type': operation.operation_type,
                    'total_files': len(operation.files),
                    'successful': len([r for r in results if r['status'] == 'success']),
                    'failed': len([r for r in results if r['status'] == 'error']),
                    'results': results
                }
            )
            
        except Exception as e:
            error_msg = f"Error en operación en lote: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    def _detect_file_type(self, mime_type: str) -> FileType:
        """Detectar tipo de archivo por MIME type"""
        if 'google-apps' in mime_type:
            if 'document' in mime_type:
                return FileType.DOCUMENT
            elif 'spreadsheet' in mime_type:
                return FileType.SPREADSHEET
            elif 'presentation' in mime_type:
                return FileType.PRESENTATION
            elif 'folder' in mime_type:
                return FileType.FOLDER
        
        elif mime_type.startswith('image/'):
            return FileType.IMAGE
        elif mime_type.startswith('video/'):
            return FileType.VIDEO
        elif mime_type.startswith('audio/'):
            return FileType.AUDIO
        elif mime_type == 'application/pdf':
            return FileType.PDF
        elif mime_type.startswith('text/') or 'application/json' in mime_type:
            return FileType.TEXT
        elif mime_type in ['application/zip', 'application/x-zip-compressed', 'application/x-tar']:
            return FileType.ARCHIVE
        elif any(ext in mime_type for ext in ['python', 'javascript', 'java', 'cpp']):
            return FileType.CODE
        else:
            return FileType.OTHER
    
    def _get_mime_type_for_file_type(self, file_type: FileType) -> str:
        """Obtener MIME type para tipo de archivo"""
        mapping = {
            FileType.DOCUMENT: "application/vnd.google-apps.document",
            FileType.SPREADSHEET: "application/vnd.google-apps.spreadsheet",
            FileType.PRESENTATION: "application/vnd.google-apps.presentation",
            FileType.FOLDER: "application/vnd.google-apps.folder",
            FileType.IMAGE: "image/",
            FileType.VIDEO: "video/",
            FileType.AUDIO: "audio/",
            FileType.PDF: "application/pdf",
            FileType.TEXT: "text/",
            FileType.CODE: "text/",
            FileType.ARCHIVE: "application/zip",
            FileType.OTHER: "application/octet-stream"
        }
        
        return mapping.get(file_type, "application/octet-stream")
    
    @handle_exceptions
    async def delete_file(self, file_id: str) -> ApiResponse:
        """Eliminar archivo"""
        try:
            self.drive_service.files().delete(fileId=file_id).execute()
            
            # Remover del cache
            if file_id in self.local_cache:
                del self.local_cache[file_id]
            
            return ApiResponse(
                success=True,
                data={'file_id': file_id, 'deleted': True}
            )
            
        except Exception as e:
            error_msg = f"Error eliminando archivo: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del agente Google Drive"""
        try:
            # Verificar servicio base
            base_health = await super().health_check()
            
            if not base_health["healthy"]:
                return base_health
            
            # Test específico de Drive API
            test_folder = await self.create_folder("Health Check Test")
            
            if test_folder.success:
                folder_id = test_folder.data['folder_id']
                
                # Test de listado
                list_result = await self.list_files(folder_id=folder_id, limit=10)
                
                # Limpiar prueba
                await self.delete_file(folder_id)
                
                if list_result.success:
                    return {
                        "healthy": True,
                        "service": "Google Drive Agent",
                        "test_folder_creation": "passed",
                        "test_listing": "passed",
                        "details": base_health
                    }
            
            return {
                "healthy": False,
                "error": "Error en tests de Drive API",
                "details": base_health
            }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": f"Error en health check: {str(e)}",
                "service": "Google Drive Agent"
            }


# Helper class para descarga de archivos
class MediaDownloader:
    """Helper para descarga de archivos de Google Drive"""
    
    def __init__(self, file_handle):
        self.file_handle = file_handle
    
    def download(self, request):
        """Descargar archivo"""
        response = request.execute()
        self.file_handle.write(response)
        return 1, True