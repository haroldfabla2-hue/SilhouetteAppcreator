# Ejemplos de Implementación: Mejoras de Arquitectura Silhouette

## Ejemplo 1: McpMessage Mejorado

### Implementación Extendida de McpMessage

```csharp
// McpMessage.cs - Versión Mejorada
public class McpMessageV2
{
    // Identificación y Context
    public string TraceId { get; set; } = Guid.NewGuid().ToString();
    public string? ParentId { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime ExpiresAt { get; set; } = DateTime.UtcNow.AddMinutes(30);
    public string CorrelationStrategy { get; set; } = "hashed";
    
    // Comunicación y Identity
    public string SenderId { get; set; } = string.Empty;
    public string SenderType { get; set; } = "agent"; // agent, system, human
    public string ReceiverId { get; set; } = string.Empty;
    public string ReceiverType { get; set; } = "agent";
    public string SessionId { get; set; } = string.Empty;
    
    // Execution Context
    public string Intent { get; set; } = string.Empty;
    public string IntentVersion { get; set; } = "1.0";
    public string Capability { get; set; } = string.Empty;
    public string CapabilityVersion { get; set; } = string.Empty;
    
    // Execution Parameters
    public int Priority { get; set; } = 5; // 1-10 scale
    public Dictionary<string, object> Context { get; set; } = new();
    public object Payload { get; set; } = new();
    public object? Result { get; set; }
    public Dictionary<string, object> Attachments { get; set; } = new();
    
    // Error Handling
    public McpError? Error { get; set; }
    public bool IsError { get; set; }
    public string? RecoveryId { get; set; }
    
    // Performance and Monitoring
    public Dictionary<string, string> PerformanceHints { get; set; } = new();
    public Dictionary<string, string> ObservabilityLabels { get; set; } = new();
    public object? CachedResult { get; set; }
    public string CacheKey { get; set; } = string.Empty;
    public int RetryCount { get; set; } = 0;
    public int MaxRetries { get; set; } = 3;
    public TimeSpan ExpectedDuration { get; set; } = TimeSpan.FromSeconds(30);
    
    // Security
    public string SecurityLevel { get; set; } = "standard"; // standard, elevated, confidential
    public List<string> DataClassifications { get; set; } = new();
    public bool RequiresHumanApproval { get; set; }
    public string? ApprovalToken { get; set; }
    
    public bool IsExpired => DateTime.UtcNow > ExpiresAt;
    public bool ShouldRetry => RetryCount < MaxRetries && !IsExpired;
}

// McpError mejorada
public class McpErrorV2
{
    public string Code { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
    public string? Details { get; set; }
    public string? StackTrace { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    public string? CorrelationId { get; set; }
    public string? RecoverySuggestion { get; set; }
    public string? RequestId { get; set; }
    
    public bool IsRetryable 
    { 
        get 
        { 
            var retryableCodes = new[] { "TIMEOUT", "RATE_LIMITED", "TEMPORARY_UNAVAILABLE" };
            return retryableCodes.Contains(Code);
        } 
    }
}

// Factory Pattern para crear mensajes consistentes
public class McpMessageFactory
{
    private readonly ICapabilityRegistry _registry;
    private readonly ISecurityService _security;
    
    public McpMessageFactory(ICapabilityRegistry registry, ISecurityService security)
    {
        _registry = registry;
        _security = security;
    }
    
    public async Task<McpMessageV2> CreateMessageAsync(
        string senderId,
        string receiverId, 
        string intent,
        object payload,
        string? sessionId = null,
        string? parentId = null)
    {
        var capability = await _registry.FindCapabilityForIntentAsync(intent);
        
        var message = new McpMessageV2
        {
            SenderId = senderId,
            ReceiverId = receiverId,
            SessionId = sessionId ?? GenerateSessionId(),
            Intent = intent,
            Capability = capability?.Name ?? string.Empty,
            CapabilityVersion = capability?.Version ?? string.Empty,
            Payload = payload,
            ParentId = parentId,
            SecurityLevel = capability?.SecurityLevel ?? "standard",
            RequiresHumanApproval = capability?.RequiresApproval ?? false
        };
        
        message.Context = await _security.EnrichContextWithSecurityInfoAsync(message);
        
        return message;
    }
    
    private string GenerateSessionId()
    {
        return $"session_{Guid.NewGuid():N}";
    }
}
```

## Ejemplo 2: McpRouter Inteligente

### Router Avanzado con Inteligencia Adaptativa

```csharp
// McpRouterV2.cs - Versión Inteligente
public class McpRouterV2 : IMcpRouter
{
    private readonly ILogger<McpRouterV2> _logger;
    private readonly ICapabilityRegistry _registry;
    private readonly IPolicyEngine _policyEngine;
    private readonly ILoadBalancer _loadBalancer;
    private readonly ICacheManager _cache;
    private readonly IPerformanceMonitor _monitor;
    private readonly ISecurityService _security;
    
    // Inteligencia adaptativa
    private readonly AdaptiveLearningEngine _learningEngine;
    private readonly PerformancePredictor _performancePredictor;
    
    public async Task<McpResponse> RouteMessageAsync(McpMessageV2 message)
    {
        var correlationId = $"route_{message.TraceId}";
        using var activity = Activity.StartActivity($"Route Message: {message.Intent}");
        
        try
        {
            // 1. Preprocessing Inteligente
            message = await PreprocessMessageAsync(message, correlationId);
            
            // 2. Validación de Seguridad
            var securityResult = await _security.ValidateMessageAsync(message);
            if (!securityResult.IsValid)
            {
                return CreateSecurityError(securityResult);
            }
            
            // 3. Validación de Políticas
            var policyResult = await _policyEngine.ValidateAsync(message);
            if (!policyResult.IsCompliant)
            {
                return CreatePolicyError(policyResult);
            }
            
            // 4. Predicción de Performance
            var performancePrediction = await _performancePredictor.PredictAsync(message);
            message.ExpectedDuration = performancePrediction.ExpectedDuration;
            message.PerformanceHints = performancePrediction.Hints;
            
            // 5. Búsqueda de Capacidad
            var capability = await FindOptimalCapabilityAsync(message);
            if (capability == null)
            {
                return CreateCapabilityNotFoundError(message);
            }
            
            // 6. Selección de Receptor
            var receiver = await _loadBalancer.SelectOptimalReceiverAsync(capability, message);
            if (receiver == null)
            {
                return CreateReceiverUnavailableError(message);
            }
            
            message.ReceiverId = receiver.Id;
            
            // 7. Ejecución con Circuit Breaker
            return await ExecuteWithCircuitBreakerAsync(message, receiver);
            
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error routing message {CorrelationId}", correlationId);
            return CreateInternalError(ex, correlationId);
        }
    }
    
    private async Task<McpMessageV2> PreprocessMessageAsync(McpMessageV2 message, string correlationId)
    {
        // Aplicar normalización
        message.Payload = await NormalizePayloadAsync(message.Payload);
        
        // Actualizar contexto con información de correlacción
        message.Context["correlation_id"] = correlationId;
        message.Context["routing_timestamp"] = DateTime.UtcNow;
        
        // Aplicar reglas de optimización basadas en aprendizaje
        var optimizationRules = await _learningEngine.GetOptimizationRulesAsync(message.Intent);
        await ApplyOptimizationRulesAsync(message, optimizationRules);
        
        return message;
    }
    
    private async Task<McpResponse> ExecuteWithCircuitBreakerAsync(McpMessageV2 message, AgentInfo receiver)
    {
        var circuitBreaker = await _loadBalancer.GetCircuitBreakerAsync(receiver.Id);
        
        try
        {
            circuitBreaker.Execute(() => { });
            
            // Ejecutar con timeout adaptativo
            var timeout = CalculateAdaptiveTimeout(message, receiver);
            return await ExecuteWithTimeoutAsync(message, receiver, timeout);
        }
        catch (CircuitBreakerOpenException)
        {
            _logger.LogWarning("Circuit breaker open for receiver {ReceiverId}", receiver.Id);
            
            // Fallback a capacidad alternativa
            return await ExecuteFallbackAsync(message);
        }
        catch (CircuitBreakerHalfOpenException)
        {
            _logger.LogInformation("Circuit breaker half-open for receiver {ReceiverId}", receiver.Id);
            
            // Probe request para determinar si podemos continuar
            return await ProbeWithReducedTimeoutAsync(message, receiver);
        }
    }
    
    private async Task<McpResponse> ExecuteFallbackAsync(McpMessageV2 message)
    {
        // Buscar capacidad alternativa
        var fallbackCapability = await FindFallbackCapabilityAsync(message);
        if (fallbackCapability != null)
        {
            var fallbackReceiver = await _loadBalancer.SelectOptimalReceiverAsync(fallbackCapability, message);
            if (fallbackReceiver != null)
            {
                return await ExecuteMessageAsync(message, fallbackReceiver);
            }
        }
        
        // Usar caché si está disponible
        var cachedResult = await _cache.GetAsync(message.CacheKey);
        if (cachedResult != null)
        {
            return new McpResponse
            {
                Success = true,
                Result = cachedResult,
                IsFromCache = true
            };
        }
        
        // Retornar error específico de fallback
        return new McpResponse
        {
            Success = false,
            Error = new McpErrorV2
            {
                Code = "FALLBACK_UNAVAILABLE",
                Message = "No fallback options available for this request",
                RecoverySuggestion = "Please try again later or contact support"
            }
        };
    }
}

// Engine de Aprendizaje Adaptativo
public class AdaptiveLearningEngine
{
    private readonly IMetricsCollector _metrics;
    private readonly ICacheManager _cache;
    
    public async Task<List<OptimizationRule>> GetOptimizationRulesAsync(string intent)
    {
        // Analizar métricas históricas
        var recentMetrics = await _metrics.GetRecentMetricsAsync(intent, TimeSpan.FromMinutes(10));
        
        var rules = new List<OptimizationRule>();
        
        // Regla de optimización de timeout basada en performance histórica
        var avgResponseTime = recentMetrics.Average(m => m.ResponseTime);
        if (avgResponseTime > TimeSpan.FromSeconds(5))
        {
            rules.Add(new OptimizationRule
            {
                Type = "timeout_increase",
                Parameter = "1.5", // 50% aumento
                Confidence = 0.8
            });
        }
        
        // Regla de optimización de prioridad
        var errorRate = recentMetrics.Count(m => m.IsError) / (double)recentMetrics.Count;
        if (errorRate > 0.1)
        {
            rules.Add(new OptimizationRule
            {
                Type = "priority_adjustment",
                Parameter = "increase_priority",
                Confidence = 0.7
            });
        }
        
        return rules;
    }
}

// Predictor de Performance
public class PerformancePredictor
{
    public async Task<PerformancePrediction> PredictAsync(McpMessageV2 message)
    {
        // Análisis basado en patrones históricos
        var historicalPattern = await AnalyzeHistoricalPattern(message.Intent);
        
        return new PerformancePrediction
        {
            ExpectedDuration = historicalPattern.AverageResponseTime,
            Confidence = historicalPattern.Confidence,
            Hints = new Dictionary<string, string>
            {
                { "optimal_timeout", $"{historicalPattern.AverageResponseTime.TotalSeconds * 2:F1}s" },
                { "retry_strategy", historicalPattern.ErrorRate > 0.05 ? "exponential" : "linear" },
                { "load_balancing_strategy", historicalPattern.LoadDistribution.ToString() }
            }
        };
    }
}
```

## Ejemplo 3: Capability Registry Mejorado

### Sistema de Registry Dinámico

```csharp
// CapabilityRegistryV2.cs - Registro Dinámico
public class CapabilityRegistryV2 : ICapabilityRegistry
{
    private readonly ISqliteDatabase _database;
    private readonly ICacheManager _cache;
    private readonly IEventBus _eventBus;
    private readonly ILogger<CapabilityRegistryV2> _logger;
    
    public async Task<CapabilityRegistration?> RegisterAsync(CapabilityDefinition capability)
    {
        using var transaction = await _database.BeginTransactionAsync();
        
        try
        {
            // Validar esquema
            await ValidateCapabilitySchemaAsync(capability);
            
            // Registrar o actualizar
            var registration = new CapabilityRegistration
            {
                Id = GenerateCapabilityId(capability),
                Name = capability.Name,
                Version = capability.Version,
                Type = capability.Type,
                InputSchema = capability.InputSchema,
                OutputSchema = capability.OutputSchema,
                Policies = capability.Policies,
                Performance = capability.Performance,
                Status = "active",
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            };
            
            await InsertCapabilityAsync(registration);
            await transaction.CommitAsync();
            
            // Limpiar caché y notificar
            await _cache.ClearAsync($"capabilities:{capability.Name}");
            await _eventBus.PublishAsync(new CapabilityRegisteredEvent(registration));
            
            return registration;
        }
        catch (Exception ex)
        {
            await transaction.RollbackAsync();
            _logger.LogError(ex, "Error registering capability {CapabilityName}", capability.Name);
            throw;
        }
    }
    
    public async Task<CapabilityRegistration?> FindBestMatchAsync(string intent, MessageContext context)
    {
        // Cache lookup
        var cacheKey = $"capability_match:{intent}:{context.SecurityLevel}:{context.DataClassification}";
        var cached = await _cache.GetAsync<CapabilityRegistration>(cacheKey);
        if (cached != null) return cached;
        
        var capabilities = await FindCapabilitiesByIntentAsync(intent);
        
        // Algoritmo de selección inteligente
        var bestMatch = await SelectBestMatchAsync(capabilities, context);
        
        if (bestMatch != null)
        {
            await _cache.SetAsync(cacheKey, bestMatch, TimeSpan.FromMinutes(5));
        }
        
        return bestMatch;
    }
    
    private async Task<CapabilityRegistration?> SelectBestMatchAsync(
        List<CapabilityRegistration> capabilities, 
        MessageContext context)
    {
        var scoredCapabilities = new List<(CapabilityRegistration Capability, double Score)>();
        
        foreach (var capability in capabilities)
        {
            var score = await CalculateMatchScoreAsync(capability, context);
            scoredCapabilities.Add((capability, score));
        }
        
        var bestMatch = scoredCapabilities.OrderByDescending(x => x.Score).FirstOrDefault();
        return bestMatch.Score > 0.7 ? bestMatch.Capability : null;
    }
    
    private async Task<double> CalculateMatchScoreAsync(CapabilityRegistration capability, MessageContext context)
    {
        double score = 0;
        
        // Factor de compatibilidad de versión (30%)
        var versionScore = CalculateVersionCompatibility(capability.Version, context.VersionRequirement);
        score += versionScore * 0.3;
        
        // Factor de políticas (25%)
        var policyScore = CalculatePolicyCompatibility(capability.Policies, context);
        score += policyScore * 0.25;
        
        // Factor de performance (20%)
        var perfScore = await CalculatePerformanceScoreAsync(capability.Performance, context);
        score += perfScore * 0.2;
        
        // Factor de disponibilidad (15%)
        var availabilityScore = await CalculateAvailabilityScoreAsync(capability);
        score += availabilityScore * 0.15;
        
        // Factor de confiabilidad (10%)
        var reliabilityScore = await CalculateReliabilityScoreAsync(capability);
        score += reliabilityScore * 0.1;
        
        return score;
    }
}

// Capability Versioning System
public class CapabilityVersioningSystem
{
    public class VersionCompatibility
    {
        public string FromVersion { get; set; } = string.Empty;
        public string ToVersion { get; set; } = string.Empty;
        public CompatibilityLevel Level { get; set; }
        public string? BreakingChanges { get; set; }
        public MigrationPath? Migration { get; set; }
    }
    
    public enum CompatibilityLevel
    {
        Full,      // 100% compatible
        Minor,     // Backward compatible
        Major,     // Breaking changes
        None       // Incompatible
    }
    
    public bool IsCompatible(string fromVersion, string toVersion)
    {
        var from = Version.Parse(fromVersion);
        var to = Version.Parse(toVersion);
        
        if (from.Major == to.Major)
        {
            return from.Minor <= to.Minor;
        }
        
        return false;
    }
}
```

## Ejemplo 4: Sistema de Observabilidad Avanzado

### Instrumentación OpenTelemetry Mejorada

```csharp
// OpenTelemetryInstrumentation.cs - Sistema Avanzado
public class OpenTelemetryInstrumentation : IDisposable
{
    private readonly ActivitySource _activitySource;
    private readonly Meter _meter;
    private readonly ILogger<OpenTelemetryInstrumentation> _logger;
    
    // Métricas personalizadas
    private readonly Counter<long> _messageCounter;
    private readonly Histogram<double> _responseTimeHistogram;
    private readonly Counter<long> _errorCounter;
    private readonly Gauge<double> _activeMessageGauge;
    
    public OpenTelemetryInstrumentation(IConfiguration configuration)
    {
        var serviceName = configuration["ServiceName"] ?? "Silhouette MCP Router";
        
        _activitySource = new ActivitySource(serviceName, "1.0.0");
        _meter = new Meter(serviceName);
        
        // Definir métricas
        _messageCounter = _meter.CreateCounter<long>("mcp.messages.total", "Total MCP messages processed");
        _responseTimeHistogram = _meter.CreateHistogram<double>("mcp.response.time", "Response time in milliseconds");
        _errorCounter = _meter.CreateCounter<long>("mcp.errors.total", "Total MCP errors");
        _activeMessageGauge = _meter.CreateGauge<double>("mcp.active.messages", "Currently active MCP messages");
    }
    
    public Activity? StartMessageProcessingActivity(McpMessageV2 message)
    {
        var activity = _activitySource.StartActivity("MCP Message Processing", ActivityKind.Internal);
        
        if (activity != null)
        {
            // Tags estándar
            activity.SetTag("mcp.message.intent", message.Intent);
            activity.SetTag("mcp.message.sender", message.SenderId);
            activity.SetTag("mcp.message.receiver", message.ReceiverId);
            activity.SetTag("mcp.message.capability", message.Capability);
            activity.SetTag("mcp.message.priority", message.Priority);
            activity.SetTag("mcp.message.security_level", message.SecurityLevel);
            
            // Tags contextuales
            activity.SetTag("mcp.message.correlation_id", message.Context.GetValueOrDefault("correlation_id"));
            activity.SetTag("mcp.message.session_id", message.SessionId);
            activity.SetTag("mcp.message.parent_id", message.ParentId);
            
            // Baggage para información adicional
            if (!string.IsNullOrEmpty(message.SessionId))
            {
                activity.AddBaggage("session.id", message.SessionId);
            }
            
            activity.AddBaggage("user.id", message.Context.GetValueOrDefault("user_id", "anonymous"));
            activity.AddBaggage("execution.start", DateTime.UtcNow.ToString("O"));
        }
        
        return activity;
    }
    
    public async Task<T> InstrumentAsync<T>(Func<Task<T>> operation, string operationName, McpMessageV2? message = null)
    {
        using var activity = _activitySource.StartActivity(operationName);
        
        try
        {
            var startTime = DateTime.UtcNow;
            
            if (message != null && activity != null)
            {
                activity.SetTag("mcp.message.intent", message.Intent);
                activity.SetTag("mcp.message.capability", message.Capability);
            }
            
            var result = await operation();
            
            // Registro de métricas de éxito
            var duration = DateTime.UtcNow - startTime;
            _responseTimeHistogram.Record(duration.TotalMilliseconds);
            _messageCounter.Add(1);
            
            if (activity != null)
            {
                activity.SetStatus(ActivityStatusCode.Ok);
                activity.SetTag("mcp.response.duration_ms", duration.TotalMilliseconds);
                activity.SetTag("mcp.response.success", true);
            }
            
            return result;
        }
        catch (Exception ex)
        {
            _errorCounter.Add(1);
            
            if (activity != null)
            {
                activity.SetStatus(ActivityStatusCode.Error, ex.Message);
                activity.SetTag("mcp.response.success", false);
                activity.SetTag("mcp.error.type", ex.GetType().Name);
                activity.SetTag("mcp.error.message", ex.Message);
            }
            
            _logger.LogError(ex, "Operation {OperationName} failed", operationName);
            throw;
        }
    }
    
    // Instrumentación de circuit breaker
    public void RecordCircuitBreakerEvent(string receiverId, CircuitBreakerEventType eventType)
    {
        using var activity = _activitySource.StartActivity("Circuit Breaker Event");
        
        if (activity != null)
        {
            activity.SetTag("circuit_breaker.receiver_id", receiverId);
            activity.SetTag("circuit_breaker.event_type", eventType.ToString());
            activity.SetTag("circuit_breaker.timestamp", DateTime.UtcNow.ToString("O"));
        }
    }
    
    // Instrumentación de capacidades
    public void RecordCapabilityUsage(string capabilityName, string version, bool success, TimeSpan duration)
    {
        using var activity = _activitySource.StartActivity("Capability Execution");
        
        if (activity != null)
        {
            activity.SetTag("capability.name", capabilityName);
            activity.SetTag("capability.version", version);
            activity.SetTag("capability.success", success);
            activity.SetTag("capability.duration_ms", duration.TotalMilliseconds);
        }
    }
    
    public void Dispose()
    {
        _activitySource?.Dispose();
        _meter?.Dispose();
    }
}

// Custom Activity Source para aspectos específicos
public static class CustomActivityNames
{
    public const string MessageRouting = "MCP.Message.Routing";
    public const string CapabilityExecution = "MCP.Capability.Execution";
    public const string SecurityValidation = "MCP.Security.Validation";
    public const string PolicyEvaluation = "MCP.Policy.Evaluation";
    public const string CacheOperation = "MCP.Cache.Operation";
    public const string CircuitBreaker = "MCP.Circuit.Breaker";
}

// Dashboard de Observabilidad
public class ObservabilityDashboard
{
    public class DashboardMetrics
    {
        public long TotalMessages { get; set; }
        public long TotalErrors { get; set; }
        public double AverageResponseTime { get; set; }
        public double SuccessRate { get; set; }
        public int ActiveConnections { get; set; }
        public Dictionary<string, int> CapabilityUsage { get; set; } = new();
        public Dictionary<string, int> ErrorTypes { get; set; } = new();
        public PerformanceMetrics Performance { get; set; } = new();
    }
    
    public class PerformanceMetrics
    {
        public double CpuUsage { get; set; }
        public double MemoryUsage { get; set; }
        public int QueueDepth { get; set; }
        public double CacheHitRate { get; set; }
        public int CircuitBreakersOpen { get; set; }
    }
}
```

## Ejemplo 5: Seguridad Enterprise

### Sistema de Redacción Avanzado

```csharp
// AdvancedRedactionService.cs - Redacción Empresarial
public class AdvancedRedactionService : IRedactionService
{
    private readonly ILogger<AdvancedRedactionService> _logger;
    private readonly IEncryptionService _encryption;
    private readonly IPolicyEngine _policyEngine;
    private readonly IAuditLogger _auditLogger;
    
    // Compilador de reglas de redacción
    private readonly IRedactionRuleCompiler _ruleCompiler;
    private readonly Dictionary<string, ICompiledRedactionRule> _compiledRules;
    
    public AdvancedRedactionService(
        ILogger<AdvancedRedactionService> logger,
        IEncryptionService encryption,
        IPolicyEngine policyEngine,
        IAuditLogger auditLogger)
    {
        _logger = logger;
        _encryption = encryption;
        _policyEngine = policyEngine;
        _auditLogger = auditLogger;
        _ruleCompiler = new RedactionRuleCompiler();
        _compiledRules = new Dictionary<string, ICompiledRedactionRule>();
    }
    
    public async Task<RedactionResult> ApplyRedactionAsync(
        object data, 
        RedactionContext context,
        RedactionMode mode = RedactionMode.Standard)
    {
        var correlationId = Guid.NewGuid().ToString();
        
        try
        {
            // 1. Análizar sensibilidad del dato
            var sensitivityAnalysis = await AnalyzeDataSensitivityAsync(data, context);
            
            // 2. Compilar reglas dinámicas
            var applicableRules = await CompileApplicableRulesAsync(sensitivityAnalysis, context);
            
            // 3. Aplicar redacción contextual
            var redactedData = await ApplyContextualRedactionAsync(data, applicableRules, context);
            
            // 4. Validar que se mantiene la utilidad
            var utilityValidation = await ValidateDataUtilityAsync(redactedData, context);
            
            // 5. Registrar auditoría
            await _auditLogger.LogRedactionAsync(new RedactionAuditEntry
            {
                CorrelationId = correlationId,
                DataType = data.GetType().Name,
                RedactionMode = mode,
                RulesApplied = applicableRules.Select(r => r.Id).ToList(),
                SensitivityLevel = sensitivityAnalysis.Level,
                UtilityPreserved = utilityValidation.IsValid
            });
            
            return new RedactionResult
            {
                RedactedData = redactedData,
                CorrelationId = correlationId,
                RulesApplied = applicableRules.Select(r => r.Id).ToList(),
                SensitivityLevel = sensitivityAnalysis.Level
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Redaction failed for correlation {CorrelationId}", correlationId);
            
            // En caso de falla, aplicar redacción mínima
            return await ApplyMinimalRedactionAsync(data, correlationId);
        }
    }
    
    private async Task<List<ICompiledRedactionRule>> CompileApplicableRulesAsync(
        DataSensitivityAnalysis sensitivity,
        RedactionContext context)
    {
        var applicableRules = new List<ICompiledRedactionRule>();
        
        foreach (var ruleId in sensitivity.MatchedRules)
        {
            if (_compiledRules.TryGetValue(ruleId, out var compiledRule))
            {
                // Validar que la regla es aplicable al contexto actual
                if (await compiledRule.IsApplicableToContextAsync(context))
                {
                    applicableRules.Add(compiledRule);
                }
            }
            else
            {
                // Compilar regla dinámicamente
                var rule = await _ruleCompiler.CompileAsync(ruleId, context);
                _compiledRules[ruleId] = rule;
                applicableRules.Add(rule);
            }
        }
        
        // Ordenar por prioridad
        return applicableRules.OrderByDescending(r => r.Priority).ToList();
    }
    
    private async Task<object> ApplyContextualRedactionAsync(
        object data,
        List<ICompiledRedactionRule> rules,
        RedactionContext context)
    {
        var currentData = data;
        
        foreach (var rule in rules)
        {
            try
            {
                currentData = await rule.ApplyAsync(currentData, context);
                
                // Verificar utilidad después de cada regla
                var utilityCheck = await ValidateDataUtilityAsync(currentData, context);
                if (!utilityCheck.IsValid && rule.IsCriticalForUtility)
                {
                    _logger.LogWarning("Rule {RuleId} would compromise data utility, skipping", rule.Id);
                    continue;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error applying redaction rule {RuleId}", rule.Id);
            }
        }
        
        return currentData;
    }
}

// Policy Engine para Seguridad
public class PolicyEngine : IPolicyEngine
{
    private readonly ISqliteDatabase _database;
    private readonly ILogger<PolicyEngine> _logger;
    
    public async Task<PolicyValidationResult> ValidateAsync(McpMessageV2 message)
    {
        // Obtener políticas aplicables
        var policies = await GetApplicablePoliciesAsync(message);
        
        var validation = new PolicyValidationResult();
        var violations = new List<PolicyViolation>();
        
        foreach (var policy in policies)
        {
            var policyValidation = await ValidatePolicyAsync(message, policy);
            if (!policyValidation.IsValid)
            {
                violations.AddRange(policyValidation.Violations);
            }
        }
        
        validation.IsValid = violations.Count == 0;
        validation.Violations = violations;
        
        return validation;
    }
    
    private async Task<PolicyValidationResult> ValidatePolicyAsync(McpMessageV2 message, PolicyDefinition policy)
    {
        var result = new PolicyValidationResult();
        
        // Validar límites de tasa
        var rateLimitValidation = await ValidateRateLimitAsync(message, policy.RateLimit);
        if (!rateLimitValidation.IsValid)
        {
            result.Violations.Add(new PolicyViolation
            {
                PolicyId = policy.Id,
                ViolationType = "RateLimitExceeded",
                Message = rateLimitValidation.Message
            });
        }
        
        // Validar permisos de acceso
        var accessValidation = await ValidateAccessPermissionsAsync(message, policy.AccessControl);
        if (!accessValidation.IsValid)
        {
            result.Violations.Add(new PolicyViolation
            {
                PolicyId = policy.Id,
                ViolationType = "AccessDenied",
                Message = accessValidation.Message
            });
        }
        
        // Validar TTL
        if (message.IsExpired)
        {
            result.Violations.Add(new PolicyViolation
            {
                PolicyId = policy.Id,
                ViolationType = "TimeToLiveExceeded",
                Message = "Message has expired"
            });
        }
        
        result.IsValid = result.Violations.Count == 0;
        return result;
    }
}
```

## Conclusión

Estas implementaciones demuestran cómo las mejoras propuestas pueden materializarse en código concreto. Los ejemplos muestran:

1. **Estructuras de datos más robustas** con capacidades de versionado, performance hints y observabilidad integrada
2. **Sistemas de routing inteligentes** con aprendizaje adaptativo, predicción de performance y manejo resiliente de errores
3. **Registries dinámicos** con algoritmos de selección inteligentes y versionado semántico
4. **Instrumentación avanzada** con métricas personalizadas y correlación completa
5. **Seguridad enterprise** con redacción contextual, validación de políticas y auditoría completa

Estas mejoras transformarán Silhouette en un sistema multi-agente más robusto, observable y seguro, preparado para operaciones enterprise complejas.