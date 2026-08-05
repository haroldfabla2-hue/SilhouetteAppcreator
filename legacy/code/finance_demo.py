#!/usr/bin/env python3
"""
Ejemplo de uso del SilhouetteMCP Finance Server
Demostración de las 9 herramientas financieras integradas
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8001"
ADMIN_EMAIL = "alberto.farahb@hotmail.com"
ADMIN_PASSWORD = "Fbalberto1910"

class FinanceClient:
    """Cliente para el Financial Intelligence Agent"""
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.admin_token = None
        self.session = requests.Session()
        
    def admin_login(self):
        """Login como administrador"""
        print("🔐 Realizando login de administrador...")
        
        response = self.session.post(
            f"{self.base_url}/admin/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data["token"]
            print(f"✅ Login exitoso para {data['user']['email']}")
            return True
        else:
            print(f"❌ Error de login: {response.text}")
            return False
    
    def test_health(self):
        """Probar health check"""
        print("\n🏥 Probando health check...")
        
        response = self.session.get(f"{self.base_url}/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Estado: {data['status']}")
            print(f"⏱️ Uptime: {data['uptime']:.1f}s")
            print(f"💰 Financial Agent: {data['financial_agent']['status']}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    
    def test_stocks_price(self):
        """Probar obtención de precios de acciones"""
        print("\n📈 Probando stocks_price...")
        
        data = {
            "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
            "period": "1mo",
            "interval": "1d"
        }
        
        response = self.session.post(
            f"{self.base_url}/mcp/finance/stocks/price",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Herramienta: {result['tool']}")
            print(f"⏱️ Tiempo de ejecución: {result['execution_time']}s")
            print(f"📊 Símbolos procesados: {result['total_symbols']}")
            
            # Mostrar primer resultado
            first_stock = result['data'][0]
            stock_data = first_stock['data']
            print(f"💡 Ejemplo - {first_stock['symbol']}:")
            print(f"   Precio actual: ${stock_data['current_price']}")
            print(f"   Cambio: ${stock_data['change']} ({stock_data['change_percent']}%)")
            print(f"   Volumen: {stock_data['volume']:,}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    
    def test_stocks_news(self):
        """Probar noticias de acciones"""
        print("\n📰 Probando stocks_news...")
        
        data = {
            "symbols": ["TSLA", "AMZN"],
            "count": 5
        }
        
        response = self.session.post(
            f"{self.base_url}/mcp/finance/stocks/news",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Herramienta: {result['tool']}")
            print(f"📊 Símbolos: {result['total_symbols']}")
            print(f"📰 Noticias encontradas: {result['total_news']}")
            
            # Mostrar noticias del primer símbolo
            first_news = result['data'][0]
            print(f"💡 Ejemplo - {first_news['symbol']}:")
            for i, headline in enumerate(first_news['data']['headlines'][:3], 1):
                print(f"   {i}. {headline}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    
    def test_stocks_info(self):
        """Probar información de acciones"""
        print("\nℹ️ Probando stocks_info...")
        
        data = {
            "symbols": ["AAPL", "MSFT"],
            "include_metadata": True
        }
        
        response = self.session.post(
            f"{self.base_url}/mcp/finance/stocks/info",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Herramienta: {result['tool']}")
            print(f"📊 Símbolos: {result['total_symbols']}")
            
            # Mostrar información del primer símbolo
            first_info = result['data'][0]
            info_data = first_info['data']
            print(f"💡 Ejemplo - {first_info['symbol']}:")
            print(f"   Empresa: {info_data['company_name']}")
            print(f"   Sector: {info_data['sector']}")
            print(f"   Industria: {info_data['industry']}")
            print(f"   Market Cap: ${info_data['market_cap']:,}")
            print(f"   Empleados: {info_data['employees']:,}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    
    def test_commodities_supported(self):
        """Probar lista de commodities soportados"""
        print("\n🌾 Probando commodities_supported...")
        
        response = self.session.get(f"{self.base_url}/mcp/finance/commodities/supported")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Herramienta: {result['tool']}")
            print(f"📊 Total commodities: {result['data']['total_commodities']}")
            print(f"📂 Categorías: {', '.join(result['data']['categories'])}")
            
            # Mostrar algunos commodities
            print("💡 Commodities disponibles:")
            for commodity in result['data']['commodities'][:3]:
                print(f"   • {commodity['name']} ({commodity['symbol']}) - {commodity['unit']}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    
    def test_commodities_price(self):
        """Probar precios de commodities"""
        print("\n💰 Probando commodities_price...")
        
        data = {
            "commodities": ["oil", "gold", "corn"],
            "currency": "USD"
        }
        
        response = self.session.post(
            f"{self.base_url}/mcp/finance/commodities/price",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Herramienta: {result['tool']}")
            print(f"💱 Moneda: {result['currency']}")
            print(f"📊 Commodities: {result['total_commodities']}")
            
            # Mostrar precios
            print("💡 Precios actuales:")
            for commodity in result['data']:
                c_data = commodity['data']
                print(f"   • {commodity['commodity'].title()}: ${c_data['current_price']} {commodity['unit'].replace('USD per ', '')}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    
    def test_metal_price(self):
        """Probar precios de metales"""
        print("\n🥇 Probando metal_price...")
        
        data = {
            "metals": ["gold", "silver", "platinum"],
            "currency": "USD"
        }
        
        response = self.session.post(
            f"{self.base_url}/mcp/finance/metal/price",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Herramienta: {result['tool']}")
            print(f"💱 Moneda: {result['currency']}")
            print(f"📊 Metales: {result['total_metals']}")
            
            # Mostrar precios
            print("💡 Precios de metales:")
            for metal in result['data']:
                m_data = metal['data']
                print(f"   • {metal['metal'].title()}: ${m_data['current_price']} {m_data['unit']}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    
    def test_finance_metrics(self):
        """Probar métricas financieras"""
        print("\n📊 Probando métricas financieras...")
        
        if not self.admin_token:
            print("❌ Necesita autenticación de admin")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.get(
            f"{self.base_url}/admin/finance/metrics",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Estado del agente: {result['agent_status']}")
            print(f"🛠️ Total herramientas: {result['total_tools']}")
            print(f"📈 Requests totales: {result['performance']['total_requests']}")
            print(f"⚡ Tiempo respuesta promedio: {result['performance']['avg_response_time']}")
            print(f"✅ Tasa de éxito: {result['performance']['success_rate']}")
            
            print("📂 Por categorías:")
            for category, data in result['categories'].items():
                print(f"   • {category.title()}: {data['total_requests']} requests")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    
    def run_demo(self):
        """Ejecutar demo completa"""
        print("🚀 DEMO SilhouetteMCP Finance Server v3.0.0")
        print("=" * 50)
        
        # Login de admin
        if not self.admin_login():
            return False
        
        # Pruebas básicas
        self.test_health()
        
        # Pruebas de herramientas financieras
        print("\n" + "=" * 50)
        print("🧪 PRUEBAS DE HERRAMIENTAS FINANCIERAS")
        print("=" * 50)
        
        self.test_stocks_price()
        self.test_stocks_news()
        self.test_stocks_info()
        self.test_commodities_supported()
        self.test_commodities_price()
        self.test_metal_price()
        
        # Métricas
        print("\n" + "=" * 50)
        print("📊 MÉTRICAS Y MONITOREO")
        print("=" * 50)
        
        self.test_finance_metrics()
        
        print("\n🎉 ¡Demo completada exitosamente!")
        print(f"⏰ Finalizada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True

def main():
    """Función principal"""
    client = FinanceClient()
    client.run_demo()

if __name__ == "__main__":
    main()