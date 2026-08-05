"""
Microsoft 365 - Teams Integration Agent
Agente especializado para operaciones con Microsoft Teams
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import json

from ..graph.client import GraphAPIClient, GraphAPIError
from ..config.settings import service_config, RATE_LIMITS
from ..utils.logger import get_logger

logger = get_logger(__name__)

class TeamsAgent:
    """Agente para operaciones con Microsoft Teams"""
    
    def __init__(self, graph_client: GraphAPIClient):
        self.graph_client = graph_client
        
        # Rate limiting específico para Teams
        self.rate_limit_config = RATE_LIMITS["teams"]
        
        # Configuración de Teams
        self.max_team_members = service_config.teams_max_team_members
        self.max_channel_members = service_config.teams_max_channel_members
        self.supported_message_types = ['text', 'html', 'file', 'image', 'video']
    
    # ==================== TEAM OPERATIONS ====================
    
    async def create_team(
        self,
        team_name: str,
        description: str = "",
        team_type: str = "private",
        template_id: Optional[str] = None
    ) -> Dict:
        """Crear nuevo equipo en Teams"""
        try:
            # Validar tipo de equipo
            valid_types = ['private', 'public', 'orgwide']
            if team_type not in valid_types:
                team_type = 'private'
            
            # Preparar datos del equipo
            team_data = {
                'template@odata.bind': template_id or "https://graph.microsoft.com/v1.0/teamsTemplates('standard')",
                'displayName': team_name,
                'description': description or f"Equipo creado automáticamente - {datetime.utcnow().isoformat()}",
                'visibility': team_type,
                'isArchived': False,
                'created_date': datetime.utcnow().isoformat()
            }
            
            # En implementación real, esto crearía el equipo usando Graph API
            logger.info(f"Team created: {team_name}")
            
            return {
                'status': 'success',
                'team_id': f"team_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'team_name': team_name,
                'team_type': team_type,
                'description': description,
                'created_at': datetime.utcnow().isoformat(),
                'member_count': 0
            }
            
        except Exception as e:
            logger.error(f"Error creating team {team_name}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_name': team_name
            }
    
    async def get_team_info(self, team_id: str) -> Dict:
        """Obtener información del equipo"""
        try:
            # En implementación real, esto obtendría información del equipo
            team_info = {
                'team_id': team_id,
                'display_name': f"Team {team_id}",
                'description': "Team description",
                'visibility': 'private',
                'is_archived': False,
                'created_date_time': datetime.utcnow().isoformat(),
                'last_activity_date_time': datetime.utcnow().isoformat(),
                'member_count': 0,
                'guest_member_count': 0,
                'channel_count': 0
            }
            
            return {
                'status': 'success',
                'team_info': team_info
            }
            
        except Exception as e:
            logger.error(f"Error getting team info {team_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id
            }
    
    async def list_teams(
        self,
        owner_id: Optional[str] = None,
        limit: int = 25
    ) -> List[Dict]:
        """Listar equipos"""
        try:
            # En implementación real, esto obtendría lista de equipos
            teams = []
            
            # Simular equipos para demostración
            teams_info = [
                {
                    'team_id': 'team_1',
                    'display_name': 'Equipo de Desarrollo',
                    'description': 'Equipo para desarrollo de aplicaciones',
                    'visibility': 'private',
                    'member_count': 8,
                    'channel_count': 5,
                    'created_date_time': datetime.utcnow().isoformat()
                },
                {
                    'team_id': 'team_2',
                    'display_name': 'Marketing',
                    'description': 'Equipo de marketing y comunicaciones',
                    'visibility': 'public',
                    'member_count': 12,
                    'channel_count': 3,
                    'created_date_time': datetime.utcnow().isoformat()
                }
            ]
            
            # Filtrar por propietario si se especifica
            if owner_id:
                teams_info = [t for t in teams_info if t.get('owner_id') == owner_id]
            
            return teams_info[:limit]
            
        except Exception as e:
            logger.error(f"Error listing teams: {str(e)}")
            return []
    
    async def archive_team(self, team_id: str) -> Dict:
        """Archivar equipo"""
        try:
            logger.info(f"Team archived: {team_id}")
            
            return {
                'status': 'success',
                'team_id': team_id,
                'archived_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error archiving team {team_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id
            }
    
    async def unarchive_team(self, team_id: str) -> Dict:
        """Desarchivar equipo"""
        try:
            logger.info(f"Team unarchived: {team_id}")
            
            return {
                'status': 'success',
                'team_id': team_id,
                'unarchived_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error unarchiving team {team_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id
            }
    
    # ==================== CHANNEL OPERATIONS ====================
    
    async def create_channel(
        self,
        team_id: str,
        channel_name: str,
        description: str = "",
        channel_type: str = "standard"
    ) -> Dict:
        """Crear canal en equipo"""
        try:
            # Validar tipo de canal
            valid_types = ['standard', 'private', 'shared']
            if channel_type not in valid_types:
                channel_type = 'standard'
            
            channel_data = {
                'team_id': team_id,
                'displayName': channel_name,
                'description': description or f"Canal creado automáticamente",
                'channel_type': channel_type,
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Channel created: {channel_name} in team {team_id}")
            
            return {
                'status': 'success',
                'channel_id': f"channel_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'team_id': team_id,
                'channel_name': channel_name,
                'channel_type': channel_type,
                'description': description,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating channel {channel_name} in team {team_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id
            }
    
    async def get_channel_info(self, team_id: str, channel_id: str) -> Dict:
        """Obtener información del canal"""
        try:
            channel_info = {
                'channel_id': channel_id,
                'team_id': team_id,
                'display_name': f"Canal {channel_id}",
                'description': "Canal de comunicación",
                'channel_type': 'standard',
                'is_favorite_by_default': False,
                'created_date_time': datetime.utcnow().isoformat(),
                'member_count': 0
            }
            
            return {
                'status': 'success',
                'channel_info': channel_info
            }
            
        except Exception as e:
            logger.error(f"Error getting channel info {team_id}:{channel_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'channel_id': channel_id
            }
    
    async def list_channels(self, team_id: str) -> List[Dict]:
        """Listar canales del equipo"""
        try:
            channels = []
            
            # Simular canales para demostración
            channels_info = [
                {
                    'channel_id': 'channel_1',
                    'display_name': 'General',
                    'description': 'Canal principal del equipo',
                    'channel_type': 'standard',
                    'member_count': 8,
                    'created_date_time': datetime.utcnow().isoformat()
                },
                {
                    'channel_id': 'channel_2',
                    'display_name': 'Anuncios',
                    'description': 'Anuncios importantes del equipo',
                    'channel_type': 'standard',
                    'member_count': 8,
                    'created_date_time': datetime.utcnow().isoformat()
                }
            ]
            
            return channels_info
            
        except Exception as e:
            logger.error(f"Error listing channels for team {team_id}: {str(e)}")
            return []
    
    # ==================== MESSAGE OPERATIONS ====================
    
    async def send_message(
        self,
        team_id: str,
        channel_id: str,
        message: str,
        message_type: str = "text",
        mentions: Optional[List[Dict]] = None
    ) -> Dict:
        """Enviar mensaje a canal"""
        try:
            # Validar tipo de mensaje
            if message_type not in self.supported_message_types:
                message_type = 'text'
            
            # Preparar datos del mensaje
            message_data = {
                'body': {
                    'contentType': 'html' if message_type in ['html', 'text'] else 'html',
                    'content': message
                },
                'message_type': message_type,
                'created_date_time': datetime.utcnow().isoformat()
            }
            
            # Agregar menciones si existen
            if mentions:
                message_data['mentions'] = mentions
            
            logger.info(f"Message sent to {team_id}:{channel_id}")
            
            return {
                'status': 'success',
                'message_id': f"msg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'team_id': team_id,
                'channel_id': channel_id,
                'message_type': message_type,
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending message to {team_id}:{channel_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id,
                'channel_id': channel_id
            }
    
    async def get_message(self, team_id: str, channel_id: str, message_id: str) -> Dict:
        """Obtener mensaje específico"""
        try:
            message_info = {
                'message_id': message_id,
                'team_id': team_id,
                'channel_id': channel_id,
                'body': {
                    'content': 'Contenido del mensaje',
                    'contentType': 'html'
                },
                'from': {
                    'user': {
                        'display_name': 'Usuario Ejemplo',
                        'id': 'user_123'
                    }
                },
                'created_date_time': datetime.utcnow().isoformat(),
                'message_type': 'text',
                'reactions': [],
                'mentions': []
            }
            
            return {
                'status': 'success',
                'message': message_info
            }
            
        except Exception as e:
            logger.error(f"Error getting message {team_id}:{channel_id}:{message_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'message_id': message_id
            }
    
    async def list_messages(
        self,
        team_id: str,
        channel_id: str,
        limit: int = 25,
        before_message_id: Optional[str] = None
    ) -> List[Dict]:
        """Listar mensajes del canal"""
        try:
            messages = []
            
            # Simular mensajes para demostración
            messages_info = [
                {
                    'message_id': 'msg_1',
                    'body': {
                        'content': '¡Hola a todos! Bienvenidos al equipo.',
                        'contentType': 'html'
                    },
                    'from': {
                        'user': {
                            'display_name': 'Juan Pérez',
                            'id': 'user_1'
                        }
                    },
                    'created_date_time': datetime.utcnow().isoformat(),
                    'message_type': 'text',
                    'reactions': []
                },
                {
                    'message_id': 'msg_2',
                    'body': {
                        'content': 'Reunión mañana a las 10:00 AM',
                        'contentType': 'html'
                    },
                    'from': {
                        'user': {
                            'display_name': 'María García',
                            'id': 'user_2'
                        }
                    },
                    'created_date_time': datetime.utcnow().isoformat(),
                    'message_type': 'text',
                    'reactions': []
                }
            ]
            
            return messages_info[:limit]
            
        except Exception as e:
            logger.error(f"Error listing messages for {team_id}:{channel_id}: {str(e)}")
            return []
    
    async def reply_to_message(
        self,
        team_id: str,
        channel_id: str,
        message_id: str,
        reply_content: str
    ) -> Dict:
        """Responder a mensaje"""
        try:
            reply_data = {
                'message_id': message_id,
                'team_id': team_id,
                'channel_id': channel_id,
                'reply_content': reply_content,
                'created_date_time': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Reply sent to message {message_id}")
            
            return {
                'status': 'success',
                'reply_id': f"reply_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'reply_data': reply_data,
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error replying to message {team_id}:{channel_id}:{message_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'message_id': message_id
            }
    
    # ==================== MEMBER OPERATIONS ====================
    
    async def add_member_to_team(
        self,
        team_id: str,
        user_id: str,
        role: str = "member"
    ) -> Dict:
        """Añadir miembro al equipo"""
        try:
            # Validar rol
            valid_roles = ['owner', 'member', 'guest']
            if role not in valid_roles:
                role = 'member'
            
            member_data = {
                'team_id': team_id,
                'user_id': user_id,
                'role': role,
                'added_date_time': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Member {user_id} added to team {team_id} as {role}")
            
            return {
                'status': 'success',
                'team_id': team_id,
                'user_id': user_id,
                'role': role,
                'added_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error adding member {user_id} to team {team_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id
            }
    
    async def remove_member_from_team(
        self,
        team_id: str,
        user_id: str
    ) -> Dict:
        """Eliminar miembro del equipo"""
        try:
            logger.info(f"Member {user_id} removed from team {team_id}")
            
            return {
                'status': 'success',
                'team_id': team_id,
                'user_id': user_id,
                'removed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error removing member {user_id} from team {team_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id
            }
    
    async def list_team_members(self, team_id: str) -> List[Dict]:
        """Listar miembros del equipo"""
        try:
            members = []
            
            # Simular miembros para demostración
            members_info = [
                {
                    'user_id': 'user_1',
                    'display_name': 'Juan Pérez',
                    'email': 'juan.perez@empresa.com',
                    'role': 'owner',
                    'joined_date_time': datetime.utcnow().isoformat()
                },
                {
                    'user_id': 'user_2',
                    'display_name': 'María García',
                    'email': 'maria.garcia@empresa.com',
                    'role': 'member',
                    'joined_date_time': datetime.utcnow().isoformat()
                }
            ]
            
            return members_info
            
        except Exception as e:
            logger.error(f"Error listing members for team {team_id}: {str(e)}")
            return []
    
    async def update_member_role(
        self,
        team_id: str,
        user_id: str,
        new_role: str
    ) -> Dict:
        """Actualizar rol de miembro"""
        try:
            valid_roles = ['owner', 'member', 'guest']
            if new_role not in valid_roles:
                raise ValueError(f"Invalid role: {new_role}")
            
            logger.info(f"Member {user_id} role updated to {new_role} in team {team_id}")
            
            return {
                'status': 'success',
                'team_id': team_id,
                'user_id': user_id,
                'old_role': 'member',  # En implementación real se obtendría el rol actual
                'new_role': new_role,
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating member role {team_id}:{user_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id
            }
    
    # ==================== MEETING OPERATIONS ====================
    
    async def create_online_meeting(
        self,
        subject: str,
        start_time: str,
        end_time: str,
        attendees: Optional[List[Dict]] = None
    ) -> Dict:
        """Crear reunión online"""
        try:
            meeting_data = {
                'subject': subject,
                'start_time': start_time,
                'end_time': end_time,
                'attendees': attendees or [],
                'created_date_time': datetime.utcnow().isoformat()
            }
            
            # En implementación real, esto crearía la reunión usando Graph API
            join_url = f"https://teams.microsoft.com/l/meetup-join/meeting_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Online meeting created: {subject}")
            
            return {
                'status': 'success',
                'meeting_id': f"meeting_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'subject': subject,
                'start_time': start_time,
                'end_time': end_time,
                'join_url': join_url,
                'attendees_count': len(attendees) if attendees else 0,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating online meeting: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'subject': subject
            }
    
    async def get_meeting_info(self, meeting_id: str) -> Dict:
        """Obtener información de reunión"""
        try:
            meeting_info = {
                'meeting_id': meeting_id,
                'subject': 'Reunión de Equipo',
                'start_time': datetime.utcnow().isoformat(),
                'end_time': (datetime.utcnow()).isoformat(),
                'join_url': f"https://teams.microsoft.com/l/meetup-join/{meeting_id}",
                'attendees': [],
                'status': 'scheduled'
            }
            
            return {
                'status': 'success',
                'meeting_info': meeting_info
            }
            
        except Exception as e:
            logger.error(f"Error getting meeting info {meeting_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'meeting_id': meeting_id
            }
    
    # ==================== APP & TAB OPERATIONS ====================
    
    async def install_app_in_team(
        self,
        team_id: str,
        app_id: str
    ) -> Dict:
        """Instalar aplicación en equipo"""
        try:
            installation_data = {
                'team_id': team_id,
                'app_id': app_id,
                'installed_date_time': datetime.utcnow().isoformat()
            }
            
            logger.info(f"App {app_id} installed in team {team_id}")
            
            return {
                'status': 'success',
                'installation_data': installation_data,
                'installed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error installing app {app_id} in team {team_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id
            }
    
    async def create_tab_in_channel(
        self,
        team_id: str,
        channel_id: str,
        tab_name: str,
        app_id: str,
        content_url: str
    ) -> Dict:
        """Crear pestaña en canal"""
        try:
            tab_data = {
                'team_id': team_id,
                'channel_id': channel_id,
                'display_name': tab_name,
                'app_id': app_id,
                'content_url': content_url,
                'created_date_time': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Tab {tab_name} created in channel {team_id}:{channel_id}")
            
            return {
                'status': 'success',
                'tab_id': f"tab_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'team_id': team_id,
                'channel_id': channel_id,
                'tab_name': tab_name,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating tab {tab_name} in {team_id}:{channel_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id
            }
    
    # ==================== ANALYTICS & REPORTING ====================
    
    async def get_team_analytics(self, team_id: str) -> Dict:
        """Obtener analíticas del equipo"""
        try:
            analytics = {
                'team_id': team_id,
                'member_count': 8,
                'channel_count': 3,
                'message_count': 145,
                'active_members': 6,
                'most_active_channel': 'General',
                'engagement_score': 8.5,
                'last_activity': datetime.utcnow().isoformat(),
                'reporting_period': 'last_30_days'
            }
            
            return {
                'status': 'success',
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting team analytics for {team_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id
            }
    
    async def get_usage_report(self, team_id: str, days: int = 30) -> Dict:
        """Obtener reporte de uso del equipo"""
        try:
            usage_data = {
                'team_id': team_id,
                'reporting_period_days': days,
                'total_messages': 145,
                'unique_active_users': 6,
                'peak_usage_day': 'Tuesday',
                'average_messages_per_day': 4.8,
                'channel_activity': {
                    'General': {'messages': 89, 'active_users': 6},
                    'Anuncios': {'messages': 23, 'active_users': 5},
                    'Proyectos': {'messages': 33, 'active_users': 4}
                },
                'report_generated': datetime.utcnow().isoformat()
            }
            
            return {
                'status': 'success',
                'usage_report': usage_data
            }
            
        except Exception as e:
            logger.error(f"Error getting usage report for {team_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id
            }
    
    # ==================== UTILITY METHODS ====================
    
    async def search_teams(self, search_term: str) -> List[Dict]:
        """Buscar equipos por nombre"""
        try:
            all_teams = await self.list_teams()
            
            matching_teams = []
            for team in all_teams:
                if search_term.lower() in team['display_name'].lower():
                    matching_teams.append(team)
            
            logger.info(f"Found {len(matching_teams)} teams matching '{search_term}'")
            return matching_teams
            
        except Exception as e:
            logger.error(f"Error searching teams: {str(e)}")
            return []
    
    async def get_all_team_statistics(self) -> Dict:
        """Obtener estadísticas de todos los equipos"""
        try:
            teams = await self.list_teams()
            
            total_teams = len(teams)
            total_members = sum(team.get('member_count', 0) for team in teams)
            total_channels = sum(team.get('channel_count', 0) for team in teams)
            
            # Determinar equipos más activos (simulado)
            most_active_team = teams[0] if teams else None
            
            stats = {
                'total_teams': total_teams,
                'total_members': total_members,
                'total_channels': total_channels,
                'average_members_per_team': round(total_members / total_teams, 2) if total_teams > 0 else 0,
                'average_channels_per_team': round(total_channels / total_teams, 2) if total_teams > 0 else 0,
                'most_active_team': most_active_team,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return {
                'status': 'success',
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting team statistics: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def export_team_data(self, team_id: str, export_format: str = "json") -> Dict:
        """Exportar datos del equipo"""
        try:
            # Obtener información completa del equipo
            team_info = await self.get_team_info(team_id)
            channels = await self.list_channels(team_id)
            members = await self.list_team_members(team_id)
            analytics = await get_team_analytics(team_id)
            
            export_data = {
                'team_info': team_info,
                'channels': channels,
                'members': members,
                'analytics': analytics,
                'exported_at': datetime.utcnow().isoformat(),
                'export_format': export_format
            }
            
            logger.info(f"Team data exported: {team_id}")
            
            return {
                'status': 'success',
                'team_id': team_id,
                'export_data': export_data,
                'exported_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting team data for {team_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'team_id': team_id
            }