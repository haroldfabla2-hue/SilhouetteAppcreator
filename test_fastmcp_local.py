#!/usr/bin/env python3
"""
Script de Prueba para FastMCP Local
Verifica que todas las funcionalidades del módulo local funcionan correctamente
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
workspace_root = Path(__file__).parent
sys.path.insert(0, str(workspace_root))

# Importar el módulo local
try:
    from src.core.fastmcp_local import (
        FastMCP, Context, InitializeRequest, InitializeResult, 
        CallToolRequest, CallToolResult, Tool, ToolInputSchema, Content,
        MCPCapabilities, ClientInfo, ServerInfo, ToolArguments,
        create_fastmcp_server
    )
    print("✅ Importación exitosa del módulo FastMCP Local")
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    sys.exit(1)


async def test_fastmcp_basic():
    """Test básico de FastMCP"""
    print("\n🧪 Test: Funcionalidad Básica de FastMCP")
    
    # Crear servidor
    server = FastMCP("Test Server")
    
    # Registrar herramientas de prueba
    @server.tool(description="Suma dos números")
    def sumar(a: int, b: int) -> int:
        return a + b
    
    @server.tool(description="Obtener información del servidor")
    def obtener_info() -> dict:
        return {
            "servidor": server.name,
            "herramientas": len(server._tools),
            "estado": server.status.value
        }
    
    @server.tool(description="Saludo personalizado")
    def saludar(nombre: str = "Mundo") -> str:
        return f"¡Hola, {nombre}!"
    
    print(f"   ✅ Registradas {len(server._tools)} herramientas")
    
    # Iniciar servidor
    await server.start()
    print(f"   ✅ Servidor iniciado en estado: {server.status.value}")
    
    # Listar herramientas
    tools = await server.list_tools()
    print(f"   ✅ Listadas {len(tools)} herramientas:")
    for tool in tools:
        print(f"      - {tool.name}: {tool.description}")
    
    # Ejecutar herramientas
    result1 = await server.call_tool("sumar", {"a": 5, "b": 3})
    print(f"   ✅ Test sumar(5, 3): {result1.content[0].text}")
    assert not result1.isError
    
    result2 = await server.call_tool("obtener_info", {})
    print(f"   ✅ Test obtener_info(): {result2.content[0].text}")
    assert not result2.isError
    
    result3 = await server.call_tool("saludar", {"nombre": "FastMCP"})
    print(f"   ✅ Test saludar('FastMCP'): {result3.content[0].text}")
    assert not result3.isError
    
    # Test de herramienta inexistente
    result_error = await server.call_tool("herramienta_inexistente", {})
    print(f"   ✅ Test herramienta inexistente: {result_error.isError}")
    assert result_error.isError
    
    # Estado del servidor
    status = server.get_server_status()
    print(f"   ✅ Estado del servidor: {status['tools_count']} herramientas, {status['request_count']} requests")
    
    # Health check
    health = await server.health_check()
    print(f"   ✅ Health check: {health['status']}")
    
    # Detener servidor
    await server.stop()
    print(f"   ✅ Servidor detenido")
    
    return True


async def test_models():
    """Test de modelos MCP"""
    print("\n🧪 Test: Modelos MCP")
    
    # Test ToolInputSchema
    schema = ToolInputSchema(
        type="object",
        properties={
            "nombre": {"type": "string", "description": "Nombre del usuario"},
            "edad": {"type": "integer", "description": "Edad del usuario"}
        },
        required=["nombre"]
    )
    print(f"   ✅ ToolInputSchema creado: {schema.type}")
    
    # Test Tool
    tool = Tool(
        name="test_tool",
        description="Herramienta de prueba",
        inputSchema=schema
    )
    print(f"   ✅ Tool creado: {tool.name}")
    
    # Test InitializeRequest
    init_request = InitializeRequest(
        protocolVersion="2024-11-05",
        capabilities=MCPCapabilities(),
        clientInfo=ClientInfo(name="TestClient", version="1.0.0")
    )
    print(f"   ✅ InitializeRequest creado: {init_request.protocolVersion}")
    
    # Test InitializeResult
    init_result = InitializeResult(
        protocolVersion="2024-11-05",
        serverInfo=ServerInfo(name="TestServer", version="1.0.0"),
        capabilities=MCPCapabilities()
    )
    print(f"   ✅ InitializeResult creado: {init_result.serverInfo.name}")
    
    # Test CallToolRequest
    call_request = CallToolRequest(
        params=ToolArguments(name="test_tool", arguments={"param1": "value1"})
    )
    print(f"   ✅ CallToolRequest creado: {call_request.params.name}")
    
    # Test CallToolResult
    success_result = CallToolResult.success([
        Content(type="text", text="Operación exitosa")
    ])
    print(f"   ✅ CallToolResult.success creado: {not success_result.isError}")
    
    error_result = CallToolResult.error("Error de prueba")
    print(f"   ✅ CallToolResult.error creado: {error_result.isError}")
    
    return True


async def test_context():
    """Test de Context"""
    print("\n🧪 Test: Context MCP")
    
    # Crear contexto con InitializeRequest
    init_request = InitializeRequest(
        protocolVersion="2024-11-05",
        capabilities=MCPCapabilities(),
        clientInfo=ClientInfo(name="TestClient")
    )
    
    context = Context(init_request, ClientInfo(name="TestClient"))
    print(f"   ✅ Context creado con request_id: {context.request_id}")
    
    # Test metadata
    context.add_metadata("user_id", "12345")
    context.add_metadata("session", "test_session")
    
    user_id = context.get_metadata("user_id")
    session = context.get_metadata("session")
    not_exist = context.get_metadata("not_exist", "default")
    
    print(f"   ✅ Metadata user_id: {user_id}")
    print(f"   ✅ Metadata session: {session}")
    print(f"   ✅ Metadata default: {not_exist}")
    
    # Test capabilities
    capabilities = context.get_client_capabilities()
    print(f"   ✅ Client capabilities: {type(capabilities).__name__}")
    
    return True


async def test_error_handling():
    """Test de manejo de errores"""
    print("\n🧪 Test: Manejo de Errores")
    
    server = FastMCP("Error Test Server")
    
    # Herramienta que lanza error
    @server.tool(description="Herramienta con error")
    def tool_with_error():
        raise ValueError("Error de prueba")
    
    @server.tool(description="Herramienta lenta")
    async def slow_tool():
        await asyncio.sleep(0.1)
        return "Completado después de delay"
    
    await server.start()
    
    # Test error en herramienta
    result = await server.call_tool("tool_with_error", {})
    print(f"   ✅ Error manejado correctamente: {result.isError}")
    assert result.isError
    
    # Test herramienta lenta
    result = await server.call_tool("slow_tool", {})
    print(f"   ✅ Herramienta asíncrona funciona: {not result.isError}")
    assert not result.isError
    
    await server.stop()
    
    return True


async def main():
    """Función principal de tests"""
    print("🚀 Iniciando Tests del Módulo FastMCP Local")
    print("=" * 60)
    
    tests = [
        ("Modelos MCP", test_models),
        ("Context MCP", test_context), 
        ("Funcionalidad Básica", test_fastmcp_basic),
        ("Manejo de Errores", test_error_handling)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n📋 Ejecutando: {test_name}")
            result = await test_func()
            if result:
                print(f"✅ {test_name}: PASÓ")
                passed += 1
            else:
                print(f"❌ {test_name}: FALLÓ")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print(f"✅ Pasados: {passed}")
    print(f"❌ Fallidos: {failed}")
    print(f"📈 Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 ¡Todos los tests pasaron! El módulo FastMCP Local funciona correctamente.")
    else:
        print("⚠️  Algunos tests fallaron. Revisar implementación.")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)