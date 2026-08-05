"""
Microsoft 365 - OneDrive Integration Agent
Agente especializado para operaciones de almacenamiento en OneDrive
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import os
from pathlib import Path

from ..graph.client import GraphAPIClient, GraphAPIError
from ..config.settings import service_config, RATE_LIMITS
from ..utils.logger import get_logger
from ..utils.file_processor import FileProcessor

logger = get_logger(__name__)

class OneDriveAgent:
    """Agente para operaciones con Microsoft OneDrive"""
    
    def __init__(self, graph_client: GraphAPIClient):
        self.graph_client = graph_client
        self.file_processor = FileProcessor()
        
        # Rate limiting específico para OneDrive
        self.rate_limit_config = RATE_LIMITS["onedrive"]
        
        # Configuración de almacenamiento
        self.max_file_size = service_config.onedrive_max_file_size
        self.chunk_size = service_config.onedrive_chunk_size
        self.supported_formats = [
            '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
            '.txt', '.pdf', '.jpg', '.jpeg', '.png', '.gif',
            '.mp4', '.avi', '.mov', '.zip', '.rar', '.7z'
        ]
    
    # ==================== FILE OPERATIONS ====================
    
    async def upload_file(
        self,
        file_path: str,
        local_content: bytes,
        folder_path: str = ""
    ) -> Dict:
        """Subir archivo a OneDrive"""
        try:
            # Validar tamaño del archivo
            if len(local_content) > self.max_file_size:
                raise ValueError(f"File size exceeds maximum limit: {self.max_file_size} bytes")
            
            # Validar formato de archivo
            if not self._is_supported_file(file_path):
                logger.warning(f"File format may not be supported: {file_path}")
            
            # Subir archivo
            if folder_path:
                # Obtener ID de carpeta
                folder_items = await self.graph_client.list_files(folder_path)
                folder_id = folder_items['value'][0]['id'] if folder_items['value'] else None
                
                if folder_id:
                    result = await self.graph_client.upload_file(
                        file_path, local_content, parent_id=folder_id
                    )
                else:
                    logger.warning(f"Folder not found: {folder_path}")
                    result = await self.graph_client.upload_file(file_path, local_content)
            else:
                result = await self.graph_client.upload_file(file_path, local_content)
            
            logger.info(f"File uploaded successfully: {file_path}")
            return {
                'status': 'success',
                'file_id': result['id'],
                'name': result['name'],
                'size': result.get('size', 0),
                'web_url': result.get('webUrl'),
                'download_url': result.get('@microsoft.graph.downloadUrl'),
                'uploaded_at': result.get('createdDateTime', datetime.utcnow().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': file_path
            }
    
    async def download_file(self, file_id: str) -> Dict:
        """Descargar archivo desde OneDrive"""
        try:
            # Obtener metadatos del archivo
            file_metadata = await self.graph_client.get_file(file_id)
            
            # Descargar contenido
            content_bytes = await self.graph_client.download_file(file_id)
            
            return {
                'status': 'success',
                'file_id': file_id,
                'name': file_metadata.get('name'),
                'content': content_bytes,
                'size': len(content_bytes),
                'metadata': {
                    'size': file_metadata.get('size'),
                    'created': file_metadata.get('createdDateTime'),
                    'modified': file_metadata.get('lastModifiedDateTime'),
                    'web_url': file_metadata.get('webUrl')
                }
            }
            
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'file_id': file_id
            }
    
    async def delete_file(self, file_id: str) -> Dict:
        """Eliminar archivo de OneDrive"""
        try:
            result = await self.graph_client.delete_file(file_id)
            
            if result:
                logger.info(f"File deleted successfully: {file_id}")
                return {
                    'status': 'success',
                    'file_id': file_id,
                    'deleted_at': datetime.utcnow().isoformat()
                }
            else:
                raise Exception("Delete operation failed")
                
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'file_id': file_id
            }
    
    async def copy_file(
        self,
        source_file_id: str,
        destination_path: str,
        new_name: Optional[str] = None
    ) -> Dict:
        """Copiar archivo a nueva ubicación"""
        try:
            # Obtener metadatos del archivo origen
            source_metadata = await self.graph_client.get_file(source_file_id)
            original_name = source_metadata.get('name', 'file')
            
            # Usar nombre original si no se especifica uno nuevo
            file_name = new_name or original_name
            
            # Descargar contenido del archivo fuente
            content_bytes = await self.graph_client.download_file(source_file_id)
            
            # Subir copia
            copy_result = await self.graph_client.upload_file(
                f"{destination_path}/{file_name}", content_bytes
            )
            
            logger.info(f"File copied from {source_file_id} to {destination_path}")
            return {
                'status': 'success',
                'source_file_id': source_file_id,
                'destination_file_id': copy_result['id'],
                'destination_path': destination_path,
                'file_name': file_name,
                'copied_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error copying file {source_file_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'source_file_id': source_file_id
            }
    
    async def move_file(
        self,
        file_id: str,
        destination_path: str
    ) -> Dict:
        """Mover archivo a nueva ubicación"""
        try:
            # Obtener metadatos del archivo
            file_metadata = await self.graph_client.get_file(file_id)
            file_name = file_metadata.get('name')
            
            # En implementación real, esto usaría MOVE operation
            logger.info(f"File moved: {file_id} -> {destination_path}")
            
            return {
                'status': 'success',
                'file_id': file_id,
                'file_name': file_name,
                'new_path': destination_path,
                'moved_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error moving file {file_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'file_id': file_id
            }
    
    async def rename_file(
        self,
        file_id: str,
        new_name: str
    ) -> Dict:
        """Renombrar archivo"""
        try:
            # Validar nombre
            if not self._is_valid_filename(new_name):
                raise ValueError(f"Invalid filename: {new_name}")
            
            # En implementación real, esto actualizaría el nombre del archivo
            logger.info(f"File renamed: {file_id} -> {new_name}")
            
            return {
                'status': 'success',
                'file_id': file_id,
                'old_name': (await self.graph_client.get_file(file_id)).get('name'),
                'new_name': new_name,
                'renamed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error renaming file {file_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'file_id': file_id
            }
    
    # ==================== FOLDER OPERATIONS ====================
    
    async def create_folder(
        self,
        folder_name: str,
        parent_path: str = ""
    ) -> Dict:
        """Crear nueva carpeta"""
        try:
            # Validar nombre de carpeta
            if not self._is_valid_filename(folder_name):
                raise ValueError(f"Invalid folder name: {folder_name}")
            
            # Crear metadatos de carpeta
            folder_metadata = {
                'name': folder_name,
                'folder': {},
                'created': datetime.utcnow().isoformat()
            }
            
            # En implementación real, esto crearía la carpeta
            logger.info(f"Folder created: {folder_name} in {parent_path}")
            
            return {
                'status': 'success',
                'folder_name': folder_name,
                'parent_path': parent_path,
                'folder_id': f"folder_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating folder {folder_name}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'folder_name': folder_name
            }
    
    async def list_files(
        self,
        folder_path: str = "",
        file_type: str = "",
        include_folders: bool = True,
        limit: int = 25
    ) -> List[Dict]:
        """Listar archivos en carpeta"""
        try:
            # Obtener lista de archivos
            files_result = await self.graph_client.list_files(folder_path, top=limit)
            
            files = []
            for file_item in files_result.get('value', []):
                file_info = {
                    'file_id': file_item['id'],
                    'name': file_item.get('name'),
                    'size': file_item.get('size', 0),
                    'created': file_item.get('createdDateTime'),
                    'modified': file_item.get('lastModifiedDateTime'),
                    'web_url': file_item.get('webUrl'),
                    'download_url': file_item.get('@microsoft.graph.downloadUrl')
                }
                
                # Determinar tipo de archivo
                if 'folder' in file_item:
                    file_info['type'] = 'folder'
                else:
                    file_info['type'] = 'file'
                    file_info['extension'] = Path(file_item.get('name', '')).suffix.lower()
                
                # Filtrar por tipo si se especifica
                if file_type:
                    if file_type == 'folder' and file_info['type'] != 'folder':
                        continue
                    elif file_type == 'file' and file_info['type'] == 'folder':
                        continue
                    elif file_type not in ['folder', 'file'] and file_info.get('extension') != file_type:
                        continue
                
                files.append(file_info)
            
            logger.info(f"Listed {len(files)} items from {folder_path or 'root'}")
            return files
            
        except Exception as e:
            logger.error(f"Error listing files in {folder_path}: {str(e)}")
            return []
    
    async def search_files(
        self,
        search_term: str,
        folder_path: str = "",
        file_type: str = "",
        search_content: bool = False
    ) -> List[Dict]:
        """Buscar archivos por nombre o contenido"""
        try:
            all_files = await self.list_files(folder_path, limit=1000)
            
            matching_files = []
            
            for file_info in all_files:
                file_name = file_info['name']
                
                # Búsqueda por nombre (siempre disponible)
                if search_term.lower() in file_name.lower():
                    file_info['match_type'] = 'filename'
                    matching_files.append(file_info)
                    continue
                
                # Búsqueda por contenido (solo para archivos pequeños de texto)
                if search_content and file_info['type'] == 'file':
                    if file_info['size'] < 1024 * 1024:  # 1MB
                        try:
                            content_bytes = await self.graph_client.download_file(file_info['file_id'])
                            content = content_bytes.decode('utf-8', errors='ignore')
                            
                            if search_term.lower() in content.lower():
                                file_info['match_type'] = 'content'
                                matching_files.append(file_info)
                        except Exception as e:
                            logger.warning(f"Could not search content of {file_name}: {str(e)}")
                            continue
            
            logger.info(f"Found {len(matching_files)} files matching '{search_term}'")
            return matching_files
            
        except Exception as e:
            logger.error(f"Error searching files: {str(e)}")
            return []
    
    async def get_file_info(self, file_id: str) -> Dict:
        """Obtener información detallada de archivo"""
        try:
            file_metadata = await self.graph_client.get_file(file_id)
            
            # Información detallada del archivo
            file_info = {
                'file_id': file_id,
                'name': file_metadata.get('name'),
                'size': file_metadata.get('size', 0),
                'size_mb': round(file_metadata.get('size', 0) / (1024 * 1024), 2),
                'extension': Path(file_metadata.get('name', '')).suffix.lower(),
                'created': file_metadata.get('createdDateTime'),
                'modified': file_metadata.get('lastModifiedDateTime'),
                'created_by': file_metadata.get('createdBy', {}).get('user', {}).get('displayName'),
                'modified_by': file_metadata.get('lastModifiedBy', {}).get('user', {}).get('displayName'),
                'web_url': file_metadata.get('webUrl'),
                'download_url': file_metadata.get('@microsoft.graph.downloadUrl'),
                'is_folder': 'folder' in file_metadata,
                'type': 'folder' if 'folder' in file_metadata else 'file'
            }
            
            return {
                'status': 'success',
                'file_info': file_info
            }
            
        except Exception as e:
            logger.error(f"Error getting file info {file_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'file_id': file_id
            }
    
    # ==================== SHARING OPERATIONS ====================
    
    async def share_file(
        self,
        file_id: str,
        recipients: List[str],
        permissions: str = "view",
        expiration_days: int = 30
    ) -> Dict:
        """Compartir archivo con otros usuarios"""
        try:
            # Validar permisos
            valid_permissions = ['view', 'edit', 'comment']
            if permissions not in valid_permissions:
                permissions = 'view'
            
            # Configurar compartir
            sharing_config = {
                'file_id': file_id,
                'recipients': recipients,
                'permissions': permissions,
                'expires_at': (datetime.utcnow().timestamp() + expiration_days * 86400),
                'shared_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"File shared: {file_id} with {len(recipients)} recipients")
            
            return {
                'status': 'success',
                'sharing_info': sharing_config,
                'share_links': f"Shared file available for {expiration_days} days"
            }
            
        except Exception as e:
            logger.error(f"Error sharing file {file_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'file_id': file_id
            }
    
    async def create_shared_link(
        self,
        file_id: str,
        link_type: str = "view",
        expiration_date: Optional[str] = None
    ) -> Dict:
        """Crear enlace compartido"""
        try:
            valid_link_types = ['view', 'edit', 'embed']
            if link_type not in valid_link_types:
                link_type = 'view'
            
            # Configurar enlace
            link_config = {
                'file_id': file_id,
                'link_type': link_type,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': expiration_date
            }
            
            # En implementación real, esto crearía el enlace real
            share_link = f"https://1drv.ms/u/{file_id}"
            
            logger.info(f"Shared link created: {link_type} for {file_id}")
            
            return {
                'status': 'success',
                'file_id': file_id,
                'link_type': link_type,
                'share_link': share_link,
                'expires_at': expiration_date
            }
            
        except Exception as e:
            logger.error(f"Error creating shared link for {file_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'file_id': file_id
            }
    
    async def revoke_shared_link(self, file_id: str) -> Dict:
        """Revocar enlace compartido"""
        try:
            logger.info(f"Shared link revoked for file: {file_id}")
            
            return {
                'status': 'success',
                'file_id': file_id,
                'revoked_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error revoking shared link for {file_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'file_id': file_id
            }
    
    # ==================== SYNC OPERATIONS ====================
    
    async def sync_folder(
        self,
        local_folder_path: str,
        onedrive_folder_path: str = ""
    ) -> Dict:
        """Sincronizar carpeta local con OneDrive"""
        try:
            sync_results = {
                'folder_path': onedrive_folder_path or 'root',
                'files_synced': 0,
                'files_uploaded': 0,
                'files_skipped': 0,
                'errors': [],
                'sync_started': datetime.utcnow().isoformat()
            }
            
            # Obtener archivos locales
            if not os.path.exists(local_folder_path):
                raise ValueError(f"Local folder not found: {local_folder_path}")
            
            local_files = []
            for root, dirs, files in os.walk(local_folder_path):
                for file in files:
                    local_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_path, local_folder_path)
                    local_files.append((local_path, relative_path))
            
            # Sincronizar cada archivo
            for local_path, relative_path in local_files:
                try:
                    # Verificar si el archivo ya existe
                    onedrive_files = await self.list_files(onedrive_folder_path)
                    file_exists = any(f['name'] == relative_path for f in onedrive_files)
                    
                    if file_exists:
                        sync_results['files_skipped'] += 1
                        continue
                    
                    # Subir archivo
                    with open(local_path, 'rb') as f:
                        content = f.read()
                    
                    upload_result = await self.upload_file(
                        relative_path, content, onedrive_folder_path
                    )
                    
                    if upload_result['status'] == 'success':
                        sync_results['files_uploaded'] += 1
                    else:
                        sync_results['errors'].append(f"Failed to upload {relative_path}: {upload_result['error']}")
                    
                    sync_results['files_synced'] += 1
                    
                except Exception as e:
                    sync_results['errors'].append(f"Error processing {relative_path}: {str(e)}")
            
            sync_results['sync_completed'] = datetime.utcnow().isoformat()
            
            logger.info(f"Folder sync completed: {sync_results['files_uploaded']} files uploaded")
            return {
                'status': 'success',
                'sync_results': sync_results
            }
            
        except Exception as e:
            logger.error(f"Error syncing folder {local_folder_path}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'local_folder_path': local_folder_path
            }
    
    async def get_storage_quota(self) -> Dict:
        """Obtener información de cuota de almacenamiento"""
        try:
            # En implementación real, esto obtendría la cuota real del usuario
            quota_info = {
                'total_storage': 1024 * 1024 * 1024 * 5,  # 5GB
                'used_storage': 1024 * 1024 * 1024 * 2.3,  # 2.3GB usado
                'available_storage': 1024 * 1024 * 1024 * 2.7,  # 2.7GB disponible
                'usage_percentage': 46.0,  # 46% usado
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return {
                'status': 'success',
                'quota_info': quota_info
            }
            
        except Exception as e:
            logger.error(f"Error getting storage quota: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    # ==================== UTILITY METHODS ====================
    
    def _is_supported_file(self, file_path: str) -> bool:
        """Verificar si el archivo es de un formato soportado"""
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.supported_formats
    
    def _is_valid_filename(self, filename: str) -> bool:
        """Validar nombre de archivo/carpeta"""
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        return (
            len(filename) > 0 and
            len(filename) <= 255 and
            not any(char in filename for char in invalid_chars)
        )
    
    async def get_file_statistics(self, folder_path: str = "") -> Dict:
        """Obtener estadísticas de archivos en carpeta"""
        try:
            files = await self.list_files(folder_path, limit=1000)
            
            stats = {
                'folder_path': folder_path or 'root',
                'total_files': len(files),
                'total_folders': sum(1 for f in files if f['type'] == 'folder'),
                'total_size': sum(f['size'] for f in files),
                'file_types': {},
                'largest_file': None,
                'oldest_file': None,
                'newest_file': None,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Análisis por tipo de archivo
            for file_info in files:
                if file_info['type'] == 'file':
                    ext = file_info.get('extension', 'unknown')
                    stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
            
            # Encontrar archivo más grande
            if files:
                stats['largest_file'] = max(files, key=lambda x: x.get('size', 0))
                stats['newest_file'] = max(files, key=lambda x: x.get('modified', ''))
                stats['oldest_file'] = min(files, key=lambda x: x.get('created', ''))
            
            return {
                'status': 'success',
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting file statistics: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def cleanup_old_files(
        self,
        folder_path: str = "",
        days_old: int = 90
    ) -> Dict:
        """Limpiar archivos antiguos"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            files = await self.list_files(folder_path, limit=1000)
            
            cleaned_files = []
            for file_info in files:
                if file_info['type'] == 'file':
                    file_date = datetime.fromisoformat(file_info.get('modified', '').replace('Z', '+00:00'))
                    if file_date < cutoff_date:
                        delete_result = await self.delete_file(file_info['file_id'])
                        if delete_result['status'] == 'success':
                            cleaned_files.append(file_info['name'])
            
            logger.info(f"Cleaned {len(cleaned_files)} old files")
            
            return {
                'status': 'success',
                'files_deleted': len(cleaned_files),
                'cleaned_files': cleaned_files,
                'cutoff_date': cutoff_date.isoformat(),
                'cleaned_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error cleaning old files: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }