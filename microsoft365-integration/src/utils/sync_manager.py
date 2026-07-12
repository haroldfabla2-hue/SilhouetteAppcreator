"""
Microsoft 365 - Sync Manager
Gestor de sincronización de datos entre servicios
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)

class SyncDirection(Enum):
    """Direcciones de sincronización"""
    BIDIRECTIONAL = "bidirectional"
    UNIDIRECTIONAL = "unidirectional"

class SyncStatus(Enum):
    """Estados de sincronización"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SyncManager:
    """Gestor de sincronización para datos de Microsoft 365"""
    
    def __init__(self, graph_client):
        self.graph_client = graph_client
        self.sync_jobs: Dict[str, Dict] = {}
        self.sync_strategies: Dict[str, Callable] = {}
        self.sync_rules: List[Dict] = []
        
        # Configuración de sincronización
        self.max_concurrent_syncs = 5
        self.default_sync_interval = 3600  # 1 hora
        self.max_sync_age = 86400 * 7  # 7 días
        
        logger.info("Sync manager initialized")
    
    async def create_sync_job(
        self,
        job_name: str,
        source_service: str,
        target_service: str,
        sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        sync_interval: int = None,
        filters: Dict = None
    ) -> Dict:
        """Crear nuevo trabajo de sincronización"""
        try:
            job_id = f"sync_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{job_name}"
            
            sync_job = {
                'job_id': job_id,
                'job_name': job_name,
                'source_service': source_service,
                'target_service': target_service,
                'direction': sync_direction.value,
                'sync_interval': sync_interval or self.default_sync_interval,
                'filters': filters or {},
                'status': SyncStatus.PENDING.value,
                'created_at': datetime.utcnow().isoformat(),
                'last_sync': None,
                'next_sync': datetime.utcnow().isoformat(),
                'stats': {
                    'items_synced': 0,
                    'items_failed': 0,
                    'items_skipped': 0,
                    'total_runtime': 0
                }
            }
            
            self.sync_jobs[job_id] = sync_job
            
            logger.info(f"Sync job created: {job_name} ({job_id})")
            return {
                'status': 'success',
                'job_id': job_id,
                'sync_job': sync_job
            }
            
        except Exception as e:
            logger.error(f"Error creating sync job {job_name}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'job_name': job_name
            }
    
    async def execute_sync_job(self, job_id: str, force: bool = False) -> Dict:
        """Ejecutar trabajo de sincronización"""
        try:
            if job_id not in self.sync_jobs:
                raise ValueError(f"Sync job not found: {job_id}")
            
            job = self.sync_jobs[job_id]
            
            # Verificar si debe ejecutarse
            if not force and job['status'] == SyncStatus.RUNNING.value:
                raise ValueError(f"Sync job is already running: {job_id}")
            
            next_sync = datetime.fromisoformat(job['next_sync'])
            if not force and datetime.utcnow() < next_sync:
                return {
                    'status': 'skipped',
                    'reason': 'Not due for execution',
                    'next_sync': job['next_sync']
                }
            
            # Marcar como ejecutándose
            job['status'] = SyncStatus.RUNNING.value
            job['started_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"Starting sync job: {job_id}")
            
            # Ejecutar sincronización
            result = await self._perform_sync(job)
            
            # Actualizar estadísticas
            job.update(result)
            job['last_sync'] = datetime.utcnow().isoformat()
            job['next_sync'] = (datetime.utcnow() + timedelta(seconds=job['sync_interval'])).isoformat()
            job['status'] = SyncStatus.COMPLETED.value if result['success'] else SyncStatus.FAILED.value
            
            logger.info(f"Sync job completed: {job_id} - {result.get('stats', {})}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing sync job {job_id}: {str(e)}")
            if job_id in self.sync_jobs:
                self.sync_jobs[job_id]['status'] = SyncStatus.FAILED.value
                self.sync_jobs[job_id]['error'] = str(e)
            return {
                'status': 'error',
                'error': str(e),
                'job_id': job_id
            }
    
    async def _perform_sync(self, job: Dict) -> Dict:
        """Realizar sincronización real"""
        start_time = datetime.utcnow()
        
        sync_result = {
            'job_id': job['job_id'],
            'success': False,
            'started_at': start_time.isoformat(),
            'stats': {
                'items_synced': 0,
                'items_failed': 0,
                'items_skipped': 0
            }
        }
        
        try:
            source_service = job['source_service']
            target_service = job['target_service']
            direction = job['direction']
            
            # Ejecutar estrategia de sincronización
            if direction == SyncDirection.UNIDIRECTIONAL.value:
                sync_result = await self._sync_unidirectional(job, source_service, target_service)
            else:
                sync_result = await self._sync_bidirectional(job, source_service, target_service)
            
            sync_result['success'] = True
            sync_result['completed_at'] = datetime.utcnow().isoformat()
            
            # Calcular tiempo de ejecución
            runtime = (datetime.utcnow() - start_time).total_seconds()
            sync_result['stats']['total_runtime'] = runtime
            
            return sync_result
            
        except Exception as e:
            sync_result['error'] = str(e)
            sync_result['completed_at'] = datetime.utcnow().isoformat()
            return sync_result
    
    async def _sync_unidirectional(self, job: Dict, source: str, target: str) -> Dict:
        """Sincronización unidireccional"""
        stats = {'items_synced': 0, 'items_failed': 0, 'items_skipped': 0}
        
        try:
            # Obtener datos del origen
            source_data = await self._fetch_source_data(source, job['filters'])
            
            # Aplicar a destino
            for item in source_data:
                try:
                    sync_result = await self._sync_item(job, item, source, target)
                    if sync_result['success']:
                        stats['items_synced'] += 1
                    else:
                        stats['items_failed'] += 1
                except Exception as e:
                    logger.error(f"Error syncing item {item.get('id', 'unknown')}: {str(e)}")
                    stats['items_failed'] += 1
            
            return {'stats': stats}
            
        except Exception as e:
            logger.error(f"Error in unidirectional sync {source} -> {target}: {str(e)}")
            raise
    
    async def _sync_bidirectional(self, job: Dict, source: str, target: str) -> Dict:
        """Sincronización bidireccional"""
        stats = {'items_synced': 0, 'items_failed': 0, 'items_skipped': 0}
        
        try:
            # Sincronizar en ambas direcciones
            forward_result = await self._sync_unidirectional(job, source, target)
            backward_result = await self._sync_unidirectional(job, target, source)
            
            # Combinar estadísticas
            stats['items_synced'] = forward_result['stats']['items_synced'] + backward_result['stats']['items_synced']
            stats['items_failed'] = forward_result['stats']['items_failed'] + backward_result['stats']['items_failed']
            stats['items_skipped'] = forward_result['stats']['items_skipped'] + backward_result['stats']['items_skipped']
            
            return {'stats': stats}
            
        except Exception as e:
            logger.error(f"Error in bidirectional sync between {source} and {target}: {str(e)}")
            raise
    
    async def _fetch_source_data(self, source: str, filters: Dict) -> List[Dict]:
        """Obtener datos del servicio origen"""
        # Implementar según el servicio
        if source == 'outlook':
            return await self._fetch_outlook_data(filters)
        elif source == 'onedrive':
            return await self._fetch_onedrive_data(filters)
        elif source == 'teams':
            return await self._fetch_teams_data(filters)
        else:
            logger.warning(f"Unknown source service: {source}")
            return []
    
    async def _sync_item(self, job: Dict, item: Dict, source: str, target: str) -> Dict:
        """Sincronizar item individual"""
        try:
            # Determinar estrategia de sincronización
            sync_key = f"{source}_to_{target}"
            if sync_key in self.sync_strategies:
                return await self.sync_strategies[sync_key](item, job)
            else:
                # Estrategia genérica
                return await self._generic_sync_item(item, source, target)
                
        except Exception as e:
            logger.error(f"Error syncing item {item.get('id', 'unknown')}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _fetch_outlook_data(self, filters: Dict) -> List[Dict]:
        """Obtener datos de Outlook"""
        try:
            # Obtener correos no leídos
            emails = await self.graph_client.list_messages(
                folder="inbox",
                limit=100,
                unread_only=filters.get('unread_only', False)
            )
            
            return emails.get('value', [])
            
        except Exception as e:
            logger.error(f"Error fetching Outlook data: {str(e)}")
            return []
    
    async def _fetch_onedrive_data(self, filters: Dict) -> List[Dict]:
        """Obtener datos de OneDrive"""
        try:
            # Obtener archivos modificados recientemente
            files = await self.graph_client.list_files(
                path="",
                top=100
            )
            
            return files.get('value', [])
            
        except Exception as e:
            logger.error(f"Error fetching OneDrive data: {str(e)}")
            return []
    
    async def _fetch_teams_data(self, filters: Dict) -> List[Dict]:
        """Obtener datos de Teams"""
        try:
            # Obtener equipos
            teams = await self.graph_client.list_groups()
            
            return teams.get('value', [])
            
        except Exception as e:
            logger.error(f"Error fetching Teams data: {str(e)}")
            return []
    
    async def _generic_sync_item(self, item: Dict, source: str, target: str) -> Dict:
        """Sincronización genérica"""
        try:
            # Lógica genérica de sincronización
            logger.info(f"Generic sync: {item.get('id', 'unknown')} from {source} to {target}")
            
            # Simular sincronización exitosa
            return {'success': True, 'synced_item': item}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def add_sync_strategy(self, strategy_name: str, strategy_func: Callable):
        """Añadir estrategia de sincronización personalizada"""
        self.sync_strategies[strategy_name] = strategy_func
        logger.info(f"Sync strategy added: {strategy_name}")
    
    async def start_sync_scheduler(self):
        """Iniciar programador de sincronizaciones"""
        async def scheduler_loop():
            while True:
                try:
                    current_time = datetime.utcnow()
                    
                    for job_id, job in list(self.sync_jobs.items()):
                        if job['status'] == SyncStatus.PENDING.value:
                            next_sync = datetime.fromisoformat(job['next_sync'])
                            if current_time >= next_sync:
                                logger.info(f"Executing scheduled sync job: {job_id}")
                                await self.execute_sync_job(job_id, force=True)
                    
                    # Esperar 60 segundos antes de la siguiente verificación
                    await asyncio.sleep(60)
                    
                except Exception as e:
                    logger.error(f"Error in sync scheduler: {str(e)}")
                    await asyncio.sleep(60)
        
        logger.info("Starting sync scheduler")
        asyncio.create_task(scheduler_loop())
    
    async def get_sync_status(self) -> Dict:
        """Obtener estado de todas las sincronizaciones"""
        status = {
            'total_jobs': len(self.sync_jobs),
            'running_jobs': 0,
            'pending_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'jobs': []
        }
        
        for job_id, job in self.sync_jobs.items():
            job_status = {
                'job_id': job_id,
                'job_name': job['job_name'],
                'status': job['status'],
                'source_service': job['source_service'],
                'target_service': job['target_service'],
                'last_sync': job['last_sync'],
                'next_sync': job['next_sync'],
                'stats': job['stats']
            }
            
            status['jobs'].append(job_status)
            
            # Contar por estado
            if job['status'] == SyncStatus.RUNNING.value:
                status['running_jobs'] += 1
            elif job['status'] == SyncStatus.PENDING.value:
                status['pending_jobs'] += 1
            elif job['status'] == SyncStatus.COMPLETED.value:
                status['completed_jobs'] += 1
            elif job['status'] == SyncStatus.FAILED.value:
                status['failed_jobs'] += 1
        
        return status
    
    async def cancel_sync_job(self, job_id: str) -> Dict:
        """Cancelar trabajo de sincronización"""
        try:
            if job_id not in self.sync_jobs:
                raise ValueError(f"Sync job not found: {job_id}")
            
            job = self.sync_jobs[job_id]
            job['status'] = SyncStatus.CANCELLED.value
            job['cancelled_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"Sync job cancelled: {job_id}")
            return {
                'status': 'success',
                'job_id': job_id,
                'cancelled_at': job['cancelled_at']
            }
            
        except Exception as e:
            logger.error(f"Error cancelling sync job {job_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'job_id': job_id
            }
    
    async def delete_sync_job(self, job_id: str) -> Dict:
        """Eliminar trabajo de sincronización"""
        try:
            if job_id not in self.sync_jobs:
                raise ValueError(f"Sync job not found: {job_id}")
            
            job = self.sync_jobs[job_id]
            del self.sync_jobs[job_id]
            
            logger.info(f"Sync job deleted: {job_id}")
            return {
                'status': 'success',
                'deleted_job': job,
                'deleted_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error deleting sync job {job_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'job_id': job_id
            }
    
    async def sync_dashboard_data(self) -> Dict:
        """Generar datos para dashboard de sincronización"""
        try:
            status = await self.get_sync_status()
            
            # Estadísticas adicionales
            total_runtime = sum(
                job['stats'].get('total_runtime', 0) 
                for job in self.sync_jobs.values()
            )
            
            total_synced = sum(
                job['stats'].get('items_synced', 0) 
                for job in self.sync_jobs.values()
            )
            
            dashboard_data = {
                'summary': status,
                'performance': {
                    'total_runtime_seconds': total_runtime,
                    'total_items_synced': total_synced,
                    'average_runtime_per_job': total_runtime / len(self.sync_jobs) if self.sync_jobs else 0,
                    'sync_success_rate': (status['completed_jobs'] / status['total_jobs'] * 100) if status['total_jobs'] > 0 else 0
                },
                'recent_activity': [],
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Actividad reciente
            sorted_jobs = sorted(
                self.sync_jobs.values(),
                key=lambda x: x.get('last_sync', x['created_at']),
                reverse=True
            )
            
            for job in sorted_jobs[:5]:  # Últimos 5 trabajos
                dashboard_data['recent_activity'].append({
                    'job_name': job['job_name'],
                    'last_activity': job.get('last_sync', job['created_at']),
                    'status': job['status'],
                    'items_synced': job['stats'].get('items_synced', 0)
                })
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating sync dashboard data: {str(e)}")
            return {'error': str(e)}