# Troubleshooting Guide

## Overview

Esta guía proporciona soluciones para problemas comunes, técnicas de debugging y respuesta a incidentes en el MCP Core Superior. Incluye diagnóstico de problemas en agentes, rendimiento, conectividad y configuración.

## 🔍 Common Issues

### Performance Issues

#### High Response Times

**Symptoms**
- P95 response time > 2 seconds
- User complaints about slow responses
- Timeout errors in logs

**Diagnosis Steps**

1. **Check System Resources**
   ```bash
   # CPU usage
   top -p $(pgrep -f "mcp-core")
   
   # Memory usage
   free -h
   ps aux | grep "mcp-core" | awk '{print $4, $11}'
   
   # Database connections
   SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
   
   # Redis memory
   redis-cli INFO memory
   ```

2. **Analyze Slow Queries**
   ```sql
   -- Find slow database queries
   SELECT query, calls, total_time, mean_time, stddev_time
   FROM pg_stat_statements 
   ORDER BY total_time DESC 
   LIMIT 10;
   
   -- Check for blocking queries
   SELECT blocked_locks.pid AS blocked_pid,
          blocked_activity.usename AS blocked_user,
          blocking_locks.pid AS blocking_pid,
          blocking_activity.usename AS blocking_user,
          blocked_activity.query AS blocked_statement,
          blocking_activity.query AS blocking_statement
   FROM pg_catalog.pg_locks blocked_locks
   JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
   JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
   JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
   WHERE NOT blocked_locks.granted;
   ```

3. **Check Agent Performance**
   ```python
   # Use built-in performance metrics
   from src.observability.metrics_service import metrics
   
   # Check agent execution times
   agent_metrics = metrics.get_agent_performance_metrics()
   for agent, perf_data in agent_metrics.items():
       if perf_data['avg_duration'] > 5.0:  # > 5 seconds average
           print(f"Agent {agent} is slow: {perf_data}")
   ```

**Solutions**

1. **Database Optimization**
   ```sql
   -- Add missing indexes
   CREATE INDEX CONCURRENTLY idx_conversation_contexts_id 
   ON conversation_contexts(conversation_id);
   
   -- Update table statistics
   ANALYZE conversation_contexts;
   
   -- Check query plans
   EXPLAIN ANALYZE SELECT * FROM conversation_contexts 
   WHERE conversation_id = 'conv_123';
   ```

2. **Agent Optimization**
   ```python
   # Increase agent concurrency
   config = {
       'agent_concurrent_limit': 5,  # Increase from default 3
       'agent_timeout_seconds': 300,  # Increase timeout
       'cache_results': True,  # Enable result caching
   }
   
   # Optimize memory usage
   config = {
       'max_memory_mb': 2048,
       'gc_threshold': 700,  # Force garbage collection
       'memory_pool_size': 100,
   }
   ```

3. **Caching Strategy**
   ```python
   # Enable aggressive caching for frequently accessed data
   cache_config = {
       'context_cache_ttl': 300,  # 5 minutes
       'embedding_cache_ttl': 3600,  # 1 hour
       'result_cache_ttl': 1800,  # 30 minutes
       'max_cache_size': 1000,
   }
   ```

#### High Memory Usage

**Symptoms**
- Memory usage > 80%
- OutOfMemory errors
- Application restart due to memory limits

**Diagnosis**

1. **Memory Analysis**
   ```python
   import tracemalloc
   import psutil
   
   # Start memory tracing
   tracemalloc.start()
   
   # Check current memory usage
   process = psutil.Process()
   memory_info = process.memory_info()
   print(f"RSS Memory: {memory_info.rss / 1024 / 1024:.2f} MB")
   print(f"VMS Memory: {memory_info.vms / 1024 / 1024:.2f} MB")
   
   # Get top memory-consuming objects
   snapshot = tracemalloc.take_snapshot()
   top_stats = snapshot.statistics('lineno')
   
   print("Top 10 memory-consuming lines:")
   for stat in top_stats[:10]:
       print(stat)
   ```

2. **Memory Leak Detection**
   ```python
   import gc
   import sys
   
   # Enable garbage collection debugging
   gc.set_debug(gc.DEBUG_SAVEALL)
   
   def check_memory_leaks():
       # Get all objects
       objects = gc.get_objects()
       
       # Group by type
       type_counts = {}
       for obj in objects:
           obj_type = type(obj).__name__
           type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
       
       # Show types with high counts
       sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
       print("Top 10 object types:")
       for obj_type, count in sorted_types[:10]:
           print(f"{obj_type}: {count}")
   
   # Run periodically to detect leaks
   ```

**Solutions**

1. **Memory Optimization**
   ```python
   # Implement memory limits for agents
   class AgentMemoryManager:
       def __init__(self, max_memory_mb=500):
           self.max_memory_mb = max_memory_mb
           self.current_memory = 0
       
       async def check_memory_limit(self):
           process = psutil.Process()
           memory_mb = process.memory_info().rss / 1024 / 1024
           
           if memory_mb > self.max_memory_mb:
               # Force garbage collection
               gc.collect()
               
               # Log memory usage
               logger.warning(f"Memory limit exceeded: {memory_mb:.2f}MB")
               
               # Optionally restart heavy operations
               if memory_mb > self.max_memory_mb * 1.5:
                   await self.restart_heavy_operations()
   ```

2. **Database Connection Pool Tuning**
   ```python
   # Optimize database connection pool
   database_config = {
       'pool_size': 10,          # Increase from default 5
       'max_overflow': 20,       # Allow more connections
       'pool_timeout': 30,       # Timeout for connection
       'pool_recycle': 3600,     # Recycle connections after 1 hour
       'pool_pre_ping': True,    # Validate connections before use
   }
   ```

### Agent-Related Issues

#### Agent Not Responding

**Symptoms**
- Agent shows as offline in status
- Requests to agent timeout
- Agent health check fails

**Diagnosis**

1. **Agent Status Check**
   ```bash
   # Check if agent process is running
   ps aux | grep "reasoner_agent\|planner_agent\|executor_agent\|verifier_agent"
   
   # Check agent logs
   tail -f /var/log/mcp-core-superior/agents.log
   
   # Check agent health endpoint
   curl -X GET http://localhost:8080/agents/status
   ```

2. **Database Connection Issues**
   ```python
   # Test database connectivity
   from src.database import get_db_session
   
   async def test_agent_database_connection():
       try:
           async with get_db_session() as session:
               result = await session.execute("SELECT 1")
               print("Database connection: OK")
               return True
       except Exception as e:
           print(f"Database connection failed: {e}")
           return False
   ```

**Solutions**

1. **Restart Agent Process**
   ```bash
   # Graceful restart of specific agent
   sudo systemctl restart mcp-core-reasoner
   sudo systemctl restart mcp-core-planner
   sudo systemctl restart mcp-core-executor
   sudo systemctl restart mcp-core-verifier
   ```

2. **Agent Configuration Reset**
   ```python
   # Reset agent configuration
   async def reset_agent_config(agent_name: str):
       config_path = f"/etc/mcp-core/agents/{agent_name}.json"
       
       # Backup current config
       backup_config(config_path)
       
       # Reset to defaults
       default_config = get_default_agent_config(agent_name)
       save_config(config_path, default_config)
       
       # Restart agent
       await restart_agent(agent_name)
   ```

#### Incorrect Agent Routing

**Symptoms**
- Wrong agent handling specific request types
- Suboptimal routing decisions
- Performance degradation due to routing

**Diagnosis**

1. **Routing Logic Analysis**
   ```python
   from src.orchestrator.intelligent_router import IntelligentRouter
   
   async def analyze_routing_decisions():
       router = IntelligentRouter()
       
       # Get recent routing decisions
       decisions = await router.get_recent_decisions(hours=1)
       
       # Analyze routing accuracy
       for decision in decisions:
           actual_agent = decision['actual_agent_used']
           predicted_agent = decision['predicted_agent']
           if actual_agent != predicted_agent:
               print(f"Routing error: Predicted {predicted_agent}, used {actual_agent}")
               print(f"Request: {decision['request_summary']}")
   ```

2. **ML Model Performance**
   ```python
   # Check routing model accuracy
   async def check_routing_model_performance():
       model_stats = await router.get_model_statistics()
       
       print(f"Model accuracy: {model_stats['accuracy']:.2%}")
       print(f"Prediction confidence: {model_stats['avg_confidence']:.2f}")
       
       # Check feature importance
       feature_importance = model_stats['feature_importance']
       for feature, importance in sorted(feature_importance.items(), 
                                       key=lambda x: x[1], reverse=True):
           print(f"{feature}: {importance:.3f}")
   ```

**Solutions**

1. **Retrain Routing Model**
   ```python
   # Retrain with recent data
   await router.retrain_model(
       training_data_path="/var/data/routing_training_data.json",
       model_save_path="/var/models/routing_model.pkl"
   )
   ```

2. **Update Routing Rules**
   ```python
   # Add manual routing rules
   routing_rules = {
       "analysis.*": "reasoner_agent",
       "planning.*": "planner_agent", 
       "execution.*": "executor_agent",
       "validation.*": "verifier_agent"
   }
   
   await router.update_manual_rules(routing_rules)
   ```

### Database Issues

#### Connection Pool Exhausted

**Symptoms**
- "connection pool exhausted" errors
- Slow query responses
- Application timeouts

**Diagnosis**

1. **Check Connection Usage**
   ```sql
   -- Check active connections
   SELECT count(*) as active_connections,
          state,
          application_name
   FROM pg_stat_activity 
   WHERE state = 'active'
   GROUP BY state, application_name;
   
   -- Check connection limits
   SELECT name, setting, unit, context 
   FROM pg_settings 
   WHERE name IN ('max_connections', 'superuser_reserved_connections');
   
   -- Check for long-running queries
   SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
   FROM pg_stat_activity 
   WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
   ```

**Solutions**

1. **Increase Connection Pool**
   ```python
   # Adjust connection pool settings
   database_config = {
       'pool_size': 20,          # Increase from 10
       'max_overflow': 30,       # Increase from 20
       'pool_timeout': 60,       # Increase timeout
       'pool_recycle': 1800,     # Recycle every 30 minutes
   }
   ```

2. **Optimize Long-Running Queries**
   ```sql
   -- Kill long-running queries (use carefully)
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE (now() - query_start) > interval '10 minutes' 
   AND state = 'active';
   
   -- Analyze and vacuum tables
   ANALYZE;
   VACUUM ANALYZE;
   ```

#### Query Performance Issues

**Symptoms**
- Slow query execution
- High CPU usage on database
- Timeout errors

**Diagnosis**

1. **Query Analysis**
   ```sql
   -- Find most time-consuming queries
   SELECT query, calls, total_time, mean_time, rows, 100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
   FROM pg_stat_statements 
   ORDER BY total_time DESC 
   LIMIT 10;
   
   -- Check for missing indexes
   SELECT schemaname, tablename, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch,
          seq_tup_read / nullif(seq_scan, 0) AS seq_tup_per_scan,
          idx_tup_fetch / nullif(idx_scan, 0) AS idx_tup_per_index
   FROM pg_stat_user_tables 
   WHERE seq_scan > 1000 AND idx_scan = 0
   ORDER BY seq_scan DESC;
   
   -- Check table bloat
   SELECT tablename, 
          pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
          pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
          pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as bloat_size
   FROM pg_tables 
   WHERE schemaname = 'public'
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

**Solutions**

1. **Add Missing Indexes**
   ```sql
   -- Common indexes for MCP Core
   CREATE INDEX CONCURRENTLY idx_conversation_contexts_conversation_id 
   ON conversation_contexts(conversation_id);
   
   CREATE INDEX CONCURRENTLY idx_execution_results_task_id 
   ON execution_results(task_id);
   
   CREATE INDEX CONCURRENTLY idx_agent_executions_timestamp 
   ON agent_executions(executed_at DESC);
   
   -- Composite indexes for common queries
   CREATE INDEX CONCURRENTLY idx_conversation_contexts_user_time 
   ON conversation_contexts(user_id, created_at DESC);
   ```

2. **Update Table Statistics**
   ```sql
   -- Update statistics for better query planning
   ANALYZE conversation_contexts;
   ANALYZE execution_results;
   ANALYZE agent_executions;
   
   -- Vacuum to reclaim space and update visibility maps
   VACUUM ANALYZE conversation_contexts;
   ```

### Redis Issues

#### Connection Failures

**Symptoms**
- "Connection refused" errors
- Cache misses
- Session data loss

**Diagnosis**

1. **Redis Health Check**
   ```bash
   # Check Redis status
   redis-cli ping
   
   # Check Redis info
   redis-cli info memory
   redis-cli info clients
   redis-cli info stats
   
   # Check Redis logs
   tail -f /var/log/redis/redis-server.log
   ```

2. **Connection Testing**
   ```python
   import aioredis
   
   async def test_redis_connection():
       try:
           redis = await aioredis.from_url("redis://localhost:6379")
           await redis.ping()
           print("Redis connection: OK")
           
           # Test basic operations
           await redis.set("test_key", "test_value")
           value = await redis.get("test_key")
           print(f"Redis read/write: {value}")
           
       except Exception as e:
           print(f"Redis connection failed: {e}")
       finally:
           await redis.close()
   ```

**Solutions**

1. **Redis Configuration Update**
   ```bash
   # Update redis.conf
   maxmemory 512mb
   maxmemory-policy allkeys-lru
   save 900 1
   save 300 10
   save 60 10000
   ```

2. **Connection Pool Tuning**
   ```python
   # Optimize Redis connection pool
   redis_config = {
       'max_connections': 20,
       'retry_on_timeout': True,
       'socket_timeout': 5,
       'socket_connect_timeout': 5,
       'health_check_interval': 30,
   }
   ```

### Streaming Issues

#### SSE Connection Drops

**Symptoms**
- Clients disconnect unexpectedly
- Interrupted streaming updates
- Missing real-time notifications

**Diagnosis**

1. **SSE Connection Analysis**
   ```python
   # Check SSE connection stats
   from src.streaming.streaming_engine import StreamingEngine
   
   async def analyze_sse_connections():
       streaming_engine = StreamingEngine()
       stats = await streaming_engine.get_connection_statistics()
       
       print(f"Active connections: {stats['active_connections']}")
       print(f"Disconnected sessions: {stats['disconnections']}")
       print(f"Average session duration: {stats['avg_duration']:.2f}s")
       
       # Check for common disconnect reasons
       for reason, count in stats['disconnect_reasons'].items():
           if count > 0:
               print(f"Disconnects due to {reason}: {count}")
   ```

2. **Network Analysis**
   ```bash
   # Check for network issues
   netstat -an | grep :8080 | grep ESTABLISHED
   
   # Monitor connection timeouts
   tcpdump -i any -n 'port 8080' -w /tmp/traffic.pcap
   ```

**Solutions**

1. **SSE Configuration Optimization**
   ```python
   # Optimize SSE settings
   sse_config = {
       'heartbeat_interval': 30,      # Send heartbeat every 30s
       'connection_timeout': 300,     # 5 minute timeout
       'max_buffer_size': 1000,       # Buffer size for queued messages
       'retry_delay': 5,              # Delay before retry after disconnect
       'keep_alive_headers': True,    # Send keep-alive headers
   }
   ```

2. **Client-Side Retry Logic**
   ```javascript
   // Implement exponential backoff for SSE reconnects
   function connectWithRetry(url, maxRetries = 5) {
       let retries = 0;
       
       function connect() {
           const eventSource = new EventSource(url);
           
           eventSource.onerror = function(event) {
               console.log('SSE connection error:', event);
               
               if (retries < maxRetries) {
                   retries++;
                   const delay = Math.pow(2, retries) * 1000; // Exponential backoff
                   console.log(`Retrying in ${delay}ms...`);
                   
                   setTimeout(() => {
                       eventSource.close();
                       connect();
                   }, delay);
               } else {
                   console.log('Max retries reached, giving up');
               }
           };
           
           return eventSource;
       }
       
       return connect();
   }
   ```

## 🔧 Debugging Techniques

### Application Debugging

#### Python Debugging

1. **PDB Debugging**
   ```python
   import pdb; pdb.set_trace()  # Set breakpoint
   
   # Or use pdb++ for enhanced debugging
   import pdb; pdb.set_trace()  # Enhanced with pdb++
   
   # Conditional breakpoints
   if debug_mode:
       import pdb; pdb.set_trace()
   ```

2. **Logging Debugging**
   ```python
   import logging
   
   # Configure debug logging
   logging.basicConfig(
       level=logging.DEBUG,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   # Add debug logging to specific components
   logger = logging.getLogger('mcp_core.agents')
   logger.debug(f"Agent {agent_name} processing request: {request_data}")
   ```

3. **Memory Profiling**
   ```python
   from memory_profiler import profile
   import tracemalloc
   
   @profile
   async def memory_intensive_operation():
       # Your code here
       pass
   
   # Tracemalloc for memory analysis
   tracemalloc.start()
   
   # Your code here
   
   snapshot = tracemalloc.take_snapshot()
   top_stats = snapshot.statistics('lineno')
   
   print("Top 10 memory-consuming lines:")
   for stat in top_stats[:10]:
       print(stat)
   ```

#### Database Debugging

1. **Query Debugging**
   ```python
   from sqlalchemy import event
   from sqlalchemy.engine import Engine
   import logging
   
   # Log all SQL queries
   @event.listens_for(Engine, "before_cursor_execute")
   def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
       logging.debug(f"SQL: {statement}")
       logging.debug(f"PARAMS: {parameters}")
   
   # Debug ORM queries
   from sqlalchemy import event
   
   @event.listens_for(Engine, "after_cursor_execute")
   def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
       import time
       duration = time.time() - context._execution_options.get('start_time', time.time())
       if duration > 1.0:  # Log slow queries
           logging.warning(f"Slow query ({duration:.2f}s): {statement}")
   ```

2. **Connection Debugging**
   ```python
   # Debug connection pool
   from sqlalchemy.pool import QueuePool
   
   pool = engine.pool
   print(f"Pool size: {pool.size()}")
   print(f"Checked in: {pool.checkedin()}")
   print(f"Checked out: {pool.checkedout()}")
   print(f"Overflow: {pool.overflow()}")
   ```

#### Network Debugging

1. **HTTP Request Debugging**
   ```python
   import aiohttp
   import logging
   
   # Debug HTTP requests
   logging.basicConfig(level=logging.DEBUG)
   
   async def debug_http_request(url: str):
       async with aiohttp.ClientSession() as session:
           async with session.get(url) as response:
               print(f"Status: {response.status}")
               print(f"Headers: {dict(response.headers)}")
               content = await response.text()
               print(f"Content: {content[:500]}...")  # First 500 chars
   ```

2. **WebSocket Debugging**
   ```python
   import websockets
   import logging
   
   # Debug WebSocket connections
   logging.basicConfig(level=logging.DEBUG)
   
   async def debug_websocket(uri: str):
       async with websockets.connect(uri) as websocket:
           # Log connection
           logging.debug(f"Connected to {uri}")
           
           # Log messages
           async for message in websocket:
               logging.debug(f"Received: {message}")
               
               # Echo back for testing
               await websocket.send(f"Echo: {message}")
   ```

### Performance Debugging

#### CPU Profiling

```python
import cProfile
import pstats
from io import StringIO

def profile_function(func, *args, **kwargs):
    """Profile a function call"""
    pr = cProfile.Profile()
    pr.enable()
    
    result = func(*args, **kwargs)
    
    pr.disable()
    
    # Analyze results
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    print("=== PROFILING RESULTS ===")
    print(s.getvalue())
    
    return result

# Usage
result = profile_function(some_expensive_function, arg1, arg2)
```

#### Async Debugging

```python
import asyncio
import time

async def debug_async_operations():
    """Debug async operation performance"""
    start_time = time.time()
    
    # Create tasks
    tasks = [
        asyncio.create_task(some_async_operation(i))
        for i in range(10)
    ]
    
    # Wait for completion with timeout
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks),
            timeout=30.0
        )
        
        duration = time.time() - start_time
        print(f"All operations completed in {duration:.2f}s")
        print(f"Average time per operation: {duration/len(tasks):.2f}s")
        
    except asyncio.TimeoutError:
        print("Operations timed out!")
        
        # Check which tasks completed
        for i, task in enumerate(tasks):
            if task.done():
                print(f"Task {i}: completed")
            else:
                print(f"Task {i}: still running")
```

### Error Analysis

#### Exception Handling

```python
import traceback
import logging
from functools import wraps

def debug_exceptions(func):
    """Decorator to debug exceptions in functions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Log full traceback
            logging.error(f"Exception in {func.__name__}:")
            logging.error(traceback.format_exc())
            
            # Log function arguments
            logging.error(f"Args: {args}")
            logging.error(f"Kwargs: {kwargs}")
            
            # Re-raise the exception
            raise
    
    return wrapper

# Usage
@debug_exceptions
async def problematic_function():
    # Your code here
    pass
```

#### Error Tracking

```python
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

# Configure Sentry for error tracking
sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.ERROR,
)

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    integrations=[sentry_logging],
    traces_sample_rate=1.0,
)

def log_error_with_context(error: Exception, context: dict):
    """Log error with additional context"""
    with sentry_sdk.configure_scope() as scope:
        # Add context to scope
        for key, value in context.items():
            scope.set_extra(key, value)
        
        # Capture exception
        sentry_sdk.capture_exception(error)
        
        # Log locally as well
        logging.error(f"Error with context: {context}")
        logging.error(str(error), exc_info=True)

# Usage
try:
    result = await some_operation()
except Exception as e:
    log_error_with_context(e, {
        "user_id": user_id,
        "request_id": request_id,
        "operation": "some_operation"
    })
```

## 🚨 Incident Response

### Incident Classification

#### Severity Levels

1. **Critical (P0)**
   - Complete service outage
   - Data loss
   - Security breach
   - Payment processing affected

2. **High (P1)**
   - Major functionality impaired
   - Performance significantly degraded
   - Multiple users affected

3. **Medium (P2)**
   - Minor functionality issues
   - Single user affected
   - Workaround available

4. **Low (P3)**
   - Cosmetic issues
   - Enhancement requests
   - Documentation updates

#### Incident Response Workflow

```python
# incident_response.py
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class IncidentStatus(Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"

@dataclass
class Incident:
    id: str
    title: str
    description: str
    severity: str
    status: IncidentStatus
    created_at: datetime
    assigned_to: str = None
    affected_services: List[str] = None
    tags: List[str] = None

class IncidentResponse:
    """Incident response management system"""
    
    def __init__(self):
        self.incidents = {}
        self.notification_channels = {}
    
    def create_incident(self, 
                       title: str, 
                       description: str, 
                       severity: str,
                       affected_services: List[str] = None) -> str:
        """Create a new incident"""
        incident_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{len(self.incidents) + 1:03d}"
        
        incident = Incident(
            id=incident_id,
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.OPEN,
            created_at=datetime.utcnow(),
            affected_services=affected_services or [],
            tags=self._extract_tags(description)
        )
        
        self.incidents[incident_id] = incident
        
        # Send notifications
        self._notify_incident_creation(incident)
        
        return incident_id
    
    def acknowledge_incident(self, incident_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an incident"""
        if incident_id not in self.incidents:
            return False
        
        incident = self.incidents[incident_id]
        incident.status = IncidentStatus.ACKNOWLEDGED
        incident.assigned_to = acknowledged_by
        
        self._notify_incident_update(incident, f"Acknowledged by {acknowledged_by}")
        return True
    
    def update_incident_status(self, 
                              incident_id: str, 
                              status: IncidentStatus,
                              notes: str = None) -> bool:
        """Update incident status"""
        if incident_id not in self.incidents:
            return False
        
        incident = self.incidents[incident_id]
        old_status = incident.status
        incident.status = status
        
        # Log status change
        change_note = f"Status changed from {old_status.value} to {status.value}"
        if notes:
            change_note += f". Notes: {notes}"
        
        self._notify_incident_update(incident, change_note)
        return True
    
    def resolve_incident(self, incident_id: str, resolution_notes: str) -> bool:
        """Resolve an incident"""
        if incident_id not in self.incidents:
            return False
        
        incident = self.incidents[incident_id]
        incident.status = IncidentStatus.RESOLVED
        
        resolution_msg = f"Incident resolved. Resolution: {resolution_notes}"
        self._notify_incident_update(incident, resolution_msg)
        
        # Auto-close after monitoring period
        self._schedule_auto_close(incident_id)
        
        return True
    
    def _notify_incident_creation(self, incident: Incident):
        """Send notifications for new incident"""
        # PagerDuty integration
        if incident.severity in ['critical', 'high']:
            self._send_pagerduty_alert(incident)
        
        # Slack notification
        self._send_slack_notification(incident)
        
        # Email notification for non-critical
        if incident.severity in ['medium', 'low']:
            self._send_email_notification(incident)
    
    def _notify_incident_update(self, incident: Incident, message: str):
        """Send notifications for incident updates"""
        # Update all notification channels
        for channel_type, notifier in self.notification_channels.items():
            notifier.notify(incident, message)
    
    def _extract_tags(self, description: str) -> List[str]:
        """Extract tags from incident description"""
        # Simple keyword extraction
        keywords = ['database', 'agent', 'performance', 'security', 'network', 'cache']
        tags = []
        
        for keyword in keywords:
            if keyword.lower() in description.lower():
                tags.append(keyword)
        
        return tags
    
    def _send_pagerduty_alert(self, incident: Incident):
        """Send PagerDuty alert"""
        # Implementation depends on PagerDuty API
        pass
    
    def _send_slack_notification(self, incident: Incident):
        """Send Slack notification"""
        # Implementation depends on Slack API
        pass
    
    def _send_email_notification(self, incident: Incident):
        """Send email notification"""
        # Implementation depends on email service
        pass
    
    def _schedule_auto_close(self, incident_id: str):
        """Schedule auto-close after monitoring period"""
        # Close incident after 24 hours of being resolved
        # if no new issues are reported
        pass

# Usage example
incident_manager = IncidentResponse()

# Create incident
incident_id = incident_manager.create_incident(
    title="High CPU usage on mcp-core-server",
    description="Server CPU usage has been above 90% for the last 10 minutes",
    severity="high",
    affected_services=["mcp-core-superior", "reasoner_agent"]
)

# Acknowledge incident
incident_manager.acknowledge_incident(incident_id, "oncall-engineer")

# Update status as investigating
incident_manager.update_incident_status(
    incident_id, 
    IncidentStatus.INVESTIGATING,
    "Investigating high CPU usage - checking for memory leaks"
)

# Resolve incident
incident_manager.resolve_incident(
    incident_id,
    "Restarted service and cleared memory cache. CPU usage normalized."
)
```

### Runbook Templates

#### Database Connection Issues

```markdown
# Runbook: Database Connection Issues

## Symptoms
- "connection pool exhausted" errors
- Application timeouts
- Slow query responses

## Immediate Actions
1. Check database server status
   ```bash
   sudo systemctl status postgresql
   ps aux | grep postgres
   ```

2. Check connection usage
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   ```

3. Restart connection pool if needed
   ```bash
   sudo systemctl restart mcp-core-superior
   ```

## Investigation Steps
1. Identify connection source
2. Check for connection leaks
3. Review recent deployments
4. Analyze slow queries

## Resolution
1. Increase pool size temporarily
2. Fix underlying connection leak
3. Optimize slow queries
4. Update configuration

## Prevention
1. Regular connection pool monitoring
2. Query optimization
3. Connection timeout tuning
4. Regular database maintenance
```

#### Agent Performance Issues

```markdown
# Runbook: Agent Performance Issues

## Symptoms
- Slow agent response times
- Agent timeouts
- Queue backlog building up

## Immediate Actions
1. Check agent status
   ```bash
   curl -X GET http://localhost:8080/agents/status
   ```

2. Check system resources
   ```bash
   top -p $(pgrep -f "agent")
   free -h
   ```

3. Restart problematic agent
   ```bash
   sudo systemctl restart mcp-core-reasoner
   ```

## Investigation Steps
1. Check agent logs for errors
2. Analyze recent performance metrics
3. Review agent configuration changes
4. Check for resource contention

## Resolution
1. Adjust agent concurrency limits
2. Increase memory allocation
3. Update agent timeout settings
4. Scale agent instances if needed

## Prevention
1. Regular performance monitoring
2. Capacity planning
3. Load testing
4. Alert thresholds tuning
```

### Post-Incident Analysis

```python
# post_incident_analysis.py
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

class PostIncidentAnalysis:
    """Post-incident analysis and learning"""
    
    def __init__(self):
        self.incident_db = {}  # Store incident history
    
    def analyze_incident(self, incident_id: str) -> Dict[str, Any]:
        """Perform comprehensive post-incident analysis"""
        incident = self.get_incident(incident_id)
        if not incident:
            return {}
        
        # Collect data from various sources
        metrics_data = self._collect_metrics_data(incident)
        logs_data = self._collect_logs_data(incident)
        user_feedback = self._collect_user_feedback(incident)
        
        # Analyze root cause
        root_cause = self._analyze_root_cause(incident, logs_data, metrics_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(incident, root_cause)
        
        # Calculate impact
        impact_assessment = self._assess_impact(incident, user_feedback)
        
        return {
            'incident_summary': {
                'id': incident['id'],
                'title': incident['title'],
                'duration_minutes': self._calculate_duration(incident),
                'severity': incident['severity'],
                'affected_users': impact_assessment['affected_users'],
                'affected_services': incident['affected_services']
            },
            'root_cause_analysis': root_cause,
            'impact_assessment': impact_assessment,
            'response_effectiveness': self._analyze_response(incident),
            'recommendations': recommendations,
            'lessons_learned': self._extract_lessons_learned(incident),
            'preventive_measures': self._suggest_preventive_measures(root_cause)
        }
    
    def _collect_metrics_data(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics data during incident period"""
        start_time = incident['created_at']
        end_time = incident.get('resolved_at', datetime.utcnow())
        
        # Query Prometheus for relevant metrics
        metrics_queries = {
            'response_time': 'histogram_quantile(0.95, sum(rate(mcp_core_request_duration_seconds_bucket[5m])) by (le))',
            'error_rate': 'sum(rate(mcp_core_requests_total{status_code=~"5.."}[5m])) / sum(rate(mcp_core_requests_total[5m]))',
            'throughput': 'sum(rate(mcp_core_requests_total[5m]))',
            'active_connections': 'mcp_core_database_connections{state="active"}',
        }
        
        collected_data = {}
        for metric_name, query in metrics_queries.items():
            # Execute query against Prometheus
            # data = query_prometheus(query, start_time, end_time)
            # collected_data[metric_name] = data
            pass  # Simplified for example
        
        return collected_data
    
    def _collect_logs_data(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Collect logs data during incident period"""
        # Query Elasticsearch or log aggregation system
        log_filters = {
            'timestamp_range': (incident['created_at'], incident.get('resolved_at')),
            'services': incident['affected_services'],
            'log_levels': ['ERROR', 'WARN', 'CRITICAL']
        }
        
        # Search logs for error patterns
        # log_data = search_logs(log_filters)
        return {}  # Simplified for example
    
    def _collect_user_feedback(self, incident: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect user feedback during incident"""
        # Query user feedback system
        # feedback_data = get_user_feedback(incident['created_at'], incident.get('resolved_at'))
        return []  # Simplified for example
    
    def _analyze_root_cause(self, incident: Dict[str, Any], logs_data: Dict, metrics_data: Dict) -> Dict[str, Any]:
        """Analyze root cause of the incident"""
        
        # Pattern analysis
        patterns = {
            'database_connection_issues': self._check_database_patterns(metrics_data),
            'memory_issues': self._check_memory_patterns(metrics_data),
            'network_issues': self._check_network_patterns(logs_data),
            'code_deployment': self._check_deployment_correlation(incident),
        }
        
        # Identify most likely root cause
        root_cause = {
            'primary_cause': self._identify_primary_cause(patterns),
            'contributing_factors': self._identify_contributing_factors(patterns),
            'confidence_level': self._calculate_confidence(patterns),
            'evidence': self._compile_evidence(patterns, incident)
        }
        
        return root_cause
    
    def _assess_impact(self, incident: Dict[str, Any], user_feedback: List[Dict]) -> Dict[str, Any]:
        """Assess the impact of the incident"""
        
        # Calculate affected users
        affected_users = len(set([fb.get('user_id') for fb in user_feedback if fb.get('user_id')]))
        
        # Estimate service disruption
        duration_minutes = self._calculate_duration(incident)
        
        impact_assessment = {
            'affected_users': affected_users,
            'duration_minutes': duration_minutes,
            'affected_services': incident.get('affected_services', []),
            'business_impact': self._assess_business_impact(incident, affected_users, duration_minutes),
            'customer_satisfaction_impact': self._analyze_customer_satisfaction(user_feedback)
        }
        
        return impact_assessment
    
    def _generate_recommendations(self, incident: Dict[str, Any], root_cause: Dict) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Immediate actions
        if root_cause.get('primary_cause') == 'database_connection_issues':
            recommendations.append({
                'priority': 'high',
                'category': 'configuration',
                'title': 'Optimize database connection pooling',
                'description': 'Increase connection pool size and implement connection recycling',
                'estimated_effort': '2-4 hours',
                'owner': 'database_team'
            })
        
        # Long-term improvements
        recommendations.append({
            'priority': 'medium',
            'category': 'monitoring',
            'title': 'Enhance connection monitoring',
            'description': 'Implement proactive alerts for connection pool usage',
            'estimated_effort': '1-2 days',
            'owner': 'platform_team'
        })
        
        return recommendations
    
    def _analyze_response_effectiveness(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze effectiveness of incident response"""
        
        duration_minutes = self._calculate_duration(incident)
        severity = incident['severity']
        
        # Expected response times by severity
        expected_response = {
            'critical': 15,  # 15 minutes
            'high': 30,      # 30 minutes
            'medium': 120,   # 2 hours
            'low': 480       # 8 hours
        }
        
        expected_resolution = {
            'critical': 60,  # 1 hour
            'high': 240,     # 4 hours
            'medium': 1440,  # 24 hours
            'low': 10080     # 7 days
        }
        
        response_time = self._get_response_time(incident)
        resolution_time = duration_minutes
        
        effectiveness = {
            'response_time': {
                'actual_minutes': response_time,
                'expected_minutes': expected_response.get(severity, 999999),
                'meets_expectation': response_time <= expected_response.get(severity, 999999)
            },
            'resolution_time': {
                'actual_minutes': resolution_time,
                'expected_minutes': expected_resolution.get(severity, 999999),
                'meets_expectation': resolution_time <= expected_resolution.get(severity, 999999)
            },
            'communication_quality': self._assess_communication_quality(incident),
            'customer_impact_minimization': self._assess_impact_minimization(incident)
        }
        
        return effectiveness
    
    def generate_incident_report(self, incident_id: str) -> str:
        """Generate comprehensive incident report"""
        analysis = self.analyze_incident(incident_id)
        
        report = f"""
# Incident Report: {analysis['incident_summary']['id']}

## Summary
- **Title**: {analysis['incident_summary']['title']}
- **Severity**: {analysis['incident_summary']['severity']}
- **Duration**: {analysis['incident_summary']['duration_minutes']} minutes
- **Affected Users**: {analysis['incident_summary']['affected_users']}

## Root Cause Analysis
- **Primary Cause**: {analysis['root_cause_analysis']['primary_cause']}
- **Confidence Level**: {analysis['root_cause_analysis']['confidence_level']}
- **Contributing Factors**: {', '.join(analysis['root_cause_analysis']['contributing_factors'])}

## Impact Assessment
- **Services Affected**: {', '.join(analysis['incident_summary']['affected_services'])}
- **Business Impact**: {analysis['impact_assessment']['business_impact']}

## Response Effectiveness
- **Response Time**: {analysis['response_effectiveness']['response_time']['actual_minutes']} minutes
- **Resolution Time**: {analysis['response_effectiveness']['resolution_time']['actual_minutes']} minutes

## Recommendations
"""
        
        for rec in analysis['recommendations']:
            report += f"- **{rec['title']}** ({rec['priority']} priority)\n"
            report += f"  - {rec['description']}\n"
            report += f"  - Owner: {rec['owner']}, Effort: {rec['estimated_effort']}\n\n"
        
        report += """
## Lessons Learned
"""
        for lesson in analysis['lessons_learned']:
            report += f"- {lesson}\n"
        
        return report
```

---

## 🏥 Health Checks & Diagnostics

### Application Health Monitoring

```python
# health_check_service.py
from typing import Dict, Any, List
import asyncio
import aiohttp
from datetime import datetime

class HealthCheckService:
    """Comprehensive health checking service"""
    
    def __init__(self):
        self.checks = {
            'database': self._check_database,
            'redis': self._check_redis,
            'agents': self._check_agents,
            'external_services': self._check_external_services,
            'system_resources': self._check_system_resources
        }
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        results = {}
        overall_status = "healthy"
        
        for check_name, check_function in self.checks.items():
            try:
                result = await check_function()
                results[check_name] = result
                
                if result['status'] != 'healthy':
                    overall_status = 'degraded'
                    
            except Exception as e:
                results[check_name] = {
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
                overall_status = 'critical'
        
        return {
            'overall_status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': results,
            'version': '2.0.0'
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            # Test basic connectivity
            async with self.get_db_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                
                if result != 1:
                    raise Exception("Database connectivity test failed")
            
            # Check connection pool
            pool_status = await self.get_db_pool_status()
            
            # Check for blocking queries
            blocking_queries = await self.check_blocking_queries()
            
            return {
                'status': 'healthy',
                'message': 'Database is operational',
                'connection_pool': pool_status,
                'blocking_queries': len(blocking_queries),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Database check failed: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            redis_client = await self.get_redis_client()
            
            # Test ping
            pong = await redis_client.ping()
            if not pong:
                raise Exception("Redis ping failed")
            
            # Test basic operations
            await redis_client.set("health_check", "ok", ex=10)
            value = await redis_client.get("health_check")
            
            if value != "ok":
                raise Exception("Redis read/write test failed")
            
            # Get Redis info
            info = await redis_client.info()
            
            return {
                'status': 'healthy',
                'message': 'Redis is operational',
                'memory_usage': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Redis check failed: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _check_agents(self) -> Dict[str, Any]:
        """Check agent health"""
        agents_status = {}
        all_healthy = True
        
        agent_names = ['reasoner_agent', 'planner_agent', 'executor_agent', 'verifier_agent']
        
        for agent_name in agent_names:
            try:
                # Check agent via API
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://localhost:8080/agents/{agent_name}/health") as resp:
                        if resp.status == 200:
                            agent_data = await resp.json()
                            agents_status[agent_name] = {
                                'status': 'healthy',
                                'response_time': agent_data.get('response_time'),
                                'last_activity': agent_data.get('last_activity')
                            }
                        else:
                            agents_status[agent_name] = {
                                'status': 'unhealthy',
                                'error': f"HTTP {resp.status}"
                            }
                            all_healthy = False
                            
            except Exception as e:
                agents_status[agent_name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                all_healthy = False
        
        return {
            'status': 'healthy' if all_healthy else 'degraded',
            'message': 'All agents operational' if all_healthy else 'Some agents unhealthy',
            'agents': agents_status,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _check_external_services(self) -> Dict[str, Any]:
        """Check external service dependencies"""
        services = {
            'contextforge_gateway': 'http://contextforge:8001/health',
            'jaeger_collector': 'http://jaeger-collector:14268/',
            'prometheus': 'http://prometheus:9090/api/v1/query?query=up'
        }
        
        services_status = {}
        all_healthy = True
        
        async with aiohttp.ClientSession() as session:
            for service_name, health_url in services.items():
                try:
                    async with session.get(health_url, timeout=5) as resp:
                        if resp.status == 200:
                            services_status[service_name] = {
                                'status': 'healthy',
                                'response_time': resp.headers.get('X-Response-Time', 'N/A')
                            }
                        else:
                            services_status[service_name] = {
                                'status': 'unhealthy',
                                'error': f"HTTP {resp.status}"
                            }
                            all_healthy = False
                            
                except asyncio.TimeoutError:
                    services_status[service_name] = {
                        'status': 'unhealthy',
                        'error': 'Timeout'
                    }
                    all_healthy = False
                    
                except Exception as e:
                    services_status[service_name] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
                    all_healthy = False
        
        return {
            'status': 'healthy' if all_healthy else 'degraded',
            'message': 'All external services operational' if all_healthy else 'Some external services unhealthy',
            'services': services_status,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        import psutil
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Load average
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            
            # Check thresholds
            issues = []
            if cpu_percent > 90:
                issues.append('High CPU usage')
            if memory_percent > 90:
                issues.append('High memory usage')
            if disk_percent > 90:
                issues.append('High disk usage')
            
            status = 'healthy' if len(issues) == 0 else 'degraded' if len(issues) < 2 else 'unhealthy'
            
            return {
                'status': status,
                'message': 'System resources OK' if status == 'healthy' else '; '.join(issues),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'load_average': load_avg,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'System resource check failed: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_detailed_diagnostics(self) -> Dict[str, Any]:
        """Get detailed diagnostic information"""
        
        # Collect various diagnostic data
        diagnostics = {
            'timestamp': datetime.utcnow().isoformat(),
            'health_check': await self.perform_health_check(),
            'performance_metrics': await self._collect_performance_metrics(),
            'recent_errors': await self._collect_recent_errors(),
            'active_connections': await self._get_active_connections(),
            'resource_usage_trends': await self._get_resource_trends(),
        }
        
        return diagnostics
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics"""
        # Query Prometheus for current metrics
        metrics_queries = {
            'requests_per_second': 'sum(rate(mcp_core_requests_total[1m]))',
            'average_response_time': 'avg(mcp_core_request_duration_seconds)',
            'error_rate': 'sum(rate(mcp_core_requests_total{status_code=~"5.."}[1m])) / sum(rate(mcp_core_requests_total[1m]))',
            'active_sessions': 'mcp_core_active_sessions',
        }
        
        # Execute queries and collect results
        # metrics_data = await query_prometheus(metrics_queries)
        
        return {}  # Simplified for example
    
    async def _collect_recent_errors(self) -> List[Dict[str, Any]]:
        """Collect recent errors from logs"""
        # Query log aggregation system for recent errors
        # error_logs = await search_logs({
        #     'timestamp_range': (datetime.utcnow() - timedelta(hours=1), datetime.utcnow()),
        #     'levels': ['ERROR', 'CRITICAL'],
        #     'limit': 100
        # })
        
        return []  # Simplified for example

# Health check endpoint
health_service = HealthCheckService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_data = await health_service.perform_health_check()
    status_code = 200 if health_data['overall_status'] == 'healthy' else 503
    return Response(health_data, status_code=status_code)

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with diagnostics"""
    diagnostics = await health_service.get_detailed_diagnostics()
    return diagnostics
```

---

## 📋 Quick Reference

### Common Commands

```bash
# Service management
sudo systemctl status mcp-core-superior
sudo systemctl restart mcp-core-superior
sudo journalctl -u mcp-core-superior -f

# Database operations
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction';"

# Redis operations
redis-cli ping
redis-cli info memory
redis-cli monitor

# Log analysis
tail -f /var/log/mcp-core-superior/application.log
grep ERROR /var/log/mcp-core-superior/application.log | tail -20

# Performance monitoring
top -p $(pgrep -f "mcp-core")
curl -s http://localhost:9090/api/v1/query?query=up
```

### Debug URLs

```bash
# Health checks
curl http://localhost:8080/health
curl http://localhost:8080/health/detailed

# Metrics
curl http://localhost:8080/metrics

# Agent status
curl http://localhost:8080/agents/status

# Database connection status
curl http://localhost:8080/admin/database/status

# Redis status
curl http://localhost:8080/admin/redis/status
```

### Emergency Procedures

1. **Service Outage**
   ```bash
   # Quick restart
   sudo systemctl restart mcp-core-superior
   
   # Check logs immediately
   sudo journalctl -u mcp-core-superior --since "5 minutes ago"
   ```

2. **Database Connection Issues**
   ```bash
   # Restart database connections
   sudo systemctl restart postgresql
   
   # Clear connection pool
   curl -X POST http://localhost:8080/admin/database/reset-pool
   ```

3. **High Memory Usage**
   ```bash
   # Restart specific agent
   sudo systemctl restart mcp-core-executor
   
   # Trigger garbage collection
   curl -X POST http://localhost:8080/admin/system/garbage-collect
   ```

---

## 🎯 Best Practices

### Prevention Strategies

1. **Proactive Monitoring**
   - Set up comprehensive alerting before issues occur
   - Monitor trend data, not just current values
   - Use predictive analytics for capacity planning

2. **Regular Maintenance**
   - Schedule regular database maintenance windows
   - Update dependencies and security patches
   - Review and optimize slow queries monthly

3. **Testing and Validation**
   - Run load tests before major deployments
   - Test disaster recovery procedures
   - Validate backup and restore processes

4. **Documentation and Training**
   - Keep runbooks updated
   - Train team members on troubleshooting procedures
   - Maintain incident response playbooks

---

**Próximos pasos**: Después de dominar el troubleshooting, revisar [Performance Tuning Guide](../performance/tuning.md) para optimización avanzada.