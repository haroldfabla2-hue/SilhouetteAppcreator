"""
Agente de Análisis Financiero - Integración con Plaid y Análisis Avanzado
Procesa datos bancarios, análisis de patrones y insights financieros
"""

import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import plaid
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest

@dataclass
class AccountInfo:
    """Información de cuenta bancaria"""
    account_id: str
    institution_name: str
    account_type: str
    account_subtype: str
    balance: float
    currency: str
    last_updated: datetime
    
@dataclass
class Transaction:
    """Transacción bancaria"""
    transaction_id: str
    account_id: str
    amount: float
    currency: str
    date: datetime
    description: str
    category: List[str]
    merchant_name: Optional[str] = None
    pending: bool = False
    
@dataclass
class FinancialInsight:
    """Insight financiero generado"""
    type: str  # spending_pattern, cash_flow, savings_opportunity, etc.
    title: str
    description: str
    impact_score: float  # 0-1
    actionable: bool
    recommendations: List[str]
    data_points: Dict[str, Any]

class AnalysisPeriod(Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class FinancialAnalysisAgent:
    """
    Agente especializado en análisis financiero con integración Plaid
    Procesa datos bancarios, identifica patrones y genera insights accionables
    """
    
    def __init__(self,
                 plaid_client_id: str,
                 plaid_secret: str,
                 plaid_env: str = "sandbox"):
        
        # Configurar cliente Plaid
        self.client = plaid.PlaidApi(
            plaid.Configuration(
                host=plaid_env,
                api_key={
                    'clientId': plaid_client_id,
                    'secret': plaid_secret,
                },
                options={
                    'version': '2020-09-14'
                }
            )
        )
        
        self.session = aiohttp.ClientSession()
        self.access_tokens = {}  # Almacenar tokens de acceso por usuario
        
    async def connect_bank_account(self,
                                 user_id: str,
                                 public_token: str) -> Dict[str, Any]:
        """
        Conecta cuenta bancaria usando token público de Plaid
        """
        try:
            # Intercambiar token público por token de acceso
            exchange_response = self.client.item_public_token_exchange(
                public_token=public_token
            )
            
            access_token = exchange_response['access_token']
            item_id = exchange_response['item_id']
            
            # Almacenar token de acceso
            self.access_tokens[user_id] = {
                'access_token': access_token,
                'item_id': item_id,
                'connected_at': datetime.now()
            }
            
            # Obtener información de la institución
            item_info = await self.client.item_get(access_token=access_token)
            institution_id = item_info['item']['institution_id']
            
            institution_info = await self.client.institutions_get_by_id(
                institutions_get_by_id_request=InstitutionsGetByIdRequest(
                    institution_id=institution_id,
                    country_codes=['US', 'MX']  # Configurable
                )
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "item_id": item_id,
                "institution_name": institution_info['institution']['name'],
                "accounts_count": len(exchange_response['accounts'])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    async def get_account_balances(self, user_id: str) -> List[AccountInfo]:
        """
        Obtiene saldos actuales de todas las cuentas conectadas
        """
        if user_id not in self.access_tokens:
            raise ValueError(f"Usuario {user_id} no tiene cuentas conectadas")
        
        access_token = self.access_tokens[user_id]['access_token']
        
        try:
            accounts_response = await self.client.accounts_get(
                accounts_get_request=AccountsGetRequest(access_token=access_token)
            )
            
            accounts = []
            for account in accounts_response['accounts']:
                # Obtener balance más reciente
                balances = account['balances']
                current_balance = balances.get('current', balances.get('available', 0))
                
                account_info = AccountInfo(
                    account_id=account['account_id'],
                    institution_name=self.access_tokens[user_id].get('institution_name', 'Unknown'),
                    account_type=account['type'],
                    account_subtype=account.get('subtype', ''),
                    balance=current_balance,
                    currency=account.get('iso_currency_code', 'USD'),
                    last_updated=datetime.now()
                )
                accounts.append(account_info)
            
            return accounts
            
        except Exception as e:
            raise Exception(f"Error obteniendo saldos: {str(e)}")
    
    async def get_transactions(self,
                             user_id: str,
                             start_date: datetime,
                             end_date: datetime,
                             account_ids: Optional[List[str]] = None,
                             count: int = 500) -> List[Transaction]:
        """
        Obtiene transacciones dentro de un período específico
        """
        if user_id not in self.access_tokens:
            raise ValueError(f"Usuario {user_id} no tiene cuentas conectadas")
        
        access_token = self.access_tokens[user_id]['access_token']
        
        try:
            transactions_response = await self.client.transactions_get(
                transactions_get_request=TransactionsGetRequest(
                    access_token=access_token,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    count=count,
                    account_ids=account_ids
                )
            )
            
            transactions = []
            for transaction in transactions_response['transactions']:
                transaction_obj = Transaction(
                    transaction_id=transaction['transaction_id'],
                    account_id=transaction['account_id'],
                    amount=abs(transaction['amount']),  # Valor absoluto para análisis
                    currency=transaction.get('iso_currency_code', 'USD'),
                    date=datetime.strptime(transaction['date'], '%Y-%m-%d'),
                    description=transaction['name'],
                    category=transaction.get('category', []),
                    merchant_name=transaction.get('merchant_name'),
                    pending=transaction.get('pending', False)
                )
                transactions.append(transaction_obj)
            
            return transactions
            
        except Exception as e:
            raise Exception(f"Error obteniendo transacciones: {str(e)}")
    
    async def analyze_spending_patterns(self,
                                      user_id: str,
                                      period_days: int = 30) -> Dict[str, Any]:
        """
        Analiza patrones de gasto del usuario
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        transactions = await self.get_transactions(user_id, start_date, end_date)
        
        # Convertir a DataFrame para análisis
        df = pd.DataFrame([asdict(t) for t in transactions])
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.day_name()
        df['month'] = df['date'].dt.month
        
        analysis = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_analyzed": period_days
            },
            "summary": {
                "total_transactions": len(df),
                "total_spending": float(df['amount'].sum()),
                "average_transaction": float(df['amount'].mean()),
                "median_transaction": float(df['amount'].median()),
                "unique_merchants": int(df['merchant_name'].nunique())
            },
            "patterns": {
                "spending_by_day": self._analyze_spending_by_day(df),
                "spending_by_category": self._analyze_spending_by_category(df),
                "spending_by_merchant": self._analyze_spending_by_merchant(df),
                "monthly_trend": self._analyze_monthly_trend(df)
            },
            "insights": self._generate_spending_insights(df)
        }
        
        return analysis
    
    async def analyze_cash_flow(self, user_id: str, months: int = 6) -> Dict[str, Any]:
        """
        Analiza flujo de caja y patrones de ingresos/gastos
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        transactions = await self.get_transactions(user_id, start_date, end_date)
        
        # Separar ingresos y gastos
        df = pd.DataFrame([asdict(t) for t in transactions])
        df['date'] = pd.to_datetime(df['date'])
        
        # Categorizar transacciones (esto requiere lógica adicional)
        # Por ahora, asumimos gastos positivos e ingresos negativos
        df['is_income'] = df['amount'] < 0  # Ajustar según lógica real
        df['amount_signed'] = np.where(df['is_income'], -df['amount'], df['amount'])
        
        cash_flow_analysis = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "months_analyzed": months
            },
            "summary": {
                "total_income": float(df[df['is_income']]['amount'].sum() * -1),
                "total_expenses": float(df[~df['is_income']]['amount'].sum()),
                "net_flow": float(df['amount'].sum()),
                "average_monthly_income": float(df[df['is_income']]['amount'].sum() / months * -1),
                "average_monthly_expenses": float(df[~df['is_income']]['amount'].sum() / months)
            },
            "monthly_breakdown": self._analyze_monthly_cash_flow(df),
            "trends": self._analyze_cash_flow_trends(df),
            "insights": self._generate_cash_flow_insights(df)
        }
        
        return cash_flow_analysis
    
    async def detect_anomalies(self,
                             user_id: str,
                             anomaly_threshold: float = 2.0) -> Dict[str, Any]:
        """
        Detecta transacciones anómalas usando análisis estadístico
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # Últimos 90 días
        
        transactions = await self.get_transactions(user_id, start_date, end_date)
        
        if not transactions:
            return {"anomalies": [], "message": "No hay transacciones para analizar"}
        
        df = pd.DataFrame([asdict(t) for t in transactions])
        df['date'] = pd.to_datetime(df['date'])
        
        # Calcular estadísticas
        mean_amount = df['amount'].mean()
        std_amount = df['amount'].std()
        
        # Detectar outliers
        df['z_score'] = (df['amount'] - mean_amount) / std_amount
        anomalies = df[abs(df['z_score']) > anomaly_threshold].copy()
        
        anomaly_list = []
        for _, row in anomalies.iterrows():
            anomaly = {
                "transaction_id": row['transaction_id'],
                "amount": float(row['amount']),
                "description": row['description'],
                "date": row['date'].isoformat(),
                "merchant_name": row.get('merchant_name'),
                "anomaly_score": float(abs(row['z_score'])),
                "anomaly_type": "high_amount" if row['z_score'] > 0 else "unusual_low"
            }
            anomaly_list.append(anomaly)
        
        return {
            "analysis_period": f"{start_date.date()} to {end_date.date()}",
            "total_transactions": len(df),
            "anomalies_detected": len(anomaly_list),
            "threshold_used": anomaly_threshold,
            "anomalies": anomaly_list,
            "statistics": {
                "mean_amount": float(mean_amount),
                "std_amount": float(std_amount),
                "median_amount": float(df['amount'].median())
            }
        }
    
    async def generate_financial_report(self,
                                      user_id: str,
                                      report_type: str = "monthly",
                                      period_months: int = 1) -> Dict[str, Any]:
        """
        Genera reporte financiero completo
        """
        try:
            # Ejecutar diferentes tipos de análisis
            spending_analysis = await self.analyze_spending_patterns(
                user_id, period_months * 30
            )
            
            cash_flow_analysis = await self.analyze_cash_flow(
                user_id, period_months
            )
            
            anomalies = await self.detect_anomalies(user_id)
            
            # Obtener saldos actuales
            accounts = await self.get_account_balances(user_id)
            
            # Combinar análisis
            report = {
                "report_metadata": {
                    "user_id": user_id,
                    "report_type": report_type,
                    "period_months": period_months,
                    "generated_at": datetime.now().isoformat(),
                    "accounts_analyzed": len(accounts)
                },
                "executive_summary": self._generate_executive_summary(
                    spending_analysis, cash_flow_analysis, anomalies
                ),
                "account_balances": [asdict(acc) for acc in accounts],
                "spending_analysis": spending_analysis,
                "cash_flow_analysis": cash_flow_analysis,
                "anomaly_detection": anomalies,
                "recommendations": self._generate_recommendations(
                    spending_analysis, cash_flow_analysis, anomalies
                )
            }
            
            return report
            
        except Exception as e:
            return {
                "error": str(e),
                "report_type": report_type,
                "user_id": user_id
            }
    
    def _analyze_spending_by_day(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analiza gasto promedio por día de la semana"""
        day_spending = df.groupby('day_of_week')['amount'].mean().to_dict()
        return {k: float(v) for k, v in day_spending.items()}
    
    def _analyze_spending_by_category(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analiza gasto por categoría"""
        category_spending = {}
        for _, row in df.iterrows():
            categories = row.get('category', [])
            if categories:
                primary_category = categories[0] if categories else 'Other'
                category_spending[primary_category] = category_spending.get(primary_category, 0) + row['amount']
        return {k: float(v) for k, v in category_spending.items()}
    
    def _analyze_spending_by_merchant(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analiza gasto por merchant"""
        merchant_spending = df.groupby('merchant_name')['amount'].agg(['sum', 'count']).reset_index()
        merchant_list = []
        for _, row in merchant_spending.iterrows():
            merchant_list.append({
                "merchant_name": row['merchant_name'],
                "total_spent": float(row['sum']),
                "transaction_count": int(row['count']),
                "average_transaction": float(row['sum'] / row['count'])
            })
        return sorted(merchant_list, key=lambda x: x['total_spent'], reverse=True)
    
    def _analyze_monthly_trend(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analiza tendencia mensual de gastos"""
        df['year_month'] = df['date'].dt.to_period('M')
        monthly_spending = df.groupby('year_month')['amount'].sum().reset_index()
        
        trend = []
        for _, row in monthly_spending.iterrows():
            trend.append({
                "month": str(row['year_month']),
                "total_spending": float(row['amount'])
            })
        
        return trend
    
    def _analyze_monthly_cash_flow(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analiza flujo de caja mensual"""
        df['year_month'] = df['date'].dt.to_period('M')
        monthly_flow = df.groupby('year_month').agg({
            'amount': ['sum', 'count'],
            'is_income': 'sum'
        }).reset_index()
        
        flow_breakdown = []
        for _, row in monthly_flow.iterrows():
            income_amount = df[(df['year_month'] == row['year_month']) & df['is_income']]['amount'].sum() * -1
            expense_amount = df[(df['year_month'] == row['year_month']) & ~df['is_income']]['amount'].sum()
            
            flow_breakdown.append({
                "month": str(row['year_month']),
                "income": float(income_amount),
                "expenses": float(expense_amount),
                "net_flow": float(income_amount - expense_amount),
                "transaction_count": int(row[('amount', 'count')])
            })
        
        return flow_breakdown
    
    def _analyze_cash_flow_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza tendencias de flujo de caja"""
        df['year_month'] = df['date'].dt.to_period('M')
        monthly_summary = df.groupby('year_month')['amount'].sum().reset_index()
        
        if len(monthly_summary) < 2:
            return {"trend": "insufficient_data"}
        
        # Calcular tendencia
        recent_months = monthly_summary.tail(3)
        previous_months = monthly_summary.head(3)
        
        recent_avg = recent_months['amount'].mean()
        previous_avg = previous_months['amount'].mean()
        
        trend_direction = "improving" if recent_avg < previous_avg else "declining"
        change_percentage = abs((recent_avg - previous_avg) / previous_avg * 100)
        
        return {
            "trend_direction": trend_direction,
            "change_percentage": float(change_percentage),
            "recent_months_avg": float(recent_avg),
            "previous_months_avg": float(previous_avg)
        }
    
    def _generate_spending_insights(self, df: pd.DataFrame) -> List[FinancialInsight]:
        """Genera insights sobre patrones de gasto"""
        insights = []
        
        # Insight: Día de la semana con más gastos
        day_spending = df.groupby('day_of_week')['amount'].sum()
        highest_spending_day = day_spending.idxmax()
        
        insights.append(FinancialInsight(
            type="spending_pattern",
            title=f"Gasto más alto en {highest_spending_day}",
            description=f"El {highest_spending_day} tienes el mayor gasto promedio",
            impact_score=0.6,
            actionable=True,
            recommendations=[
                f"Considera revisar gastos los {highest_spending_day}",
                "Establece límites de gasto para ese día"
            ],
            data_points={"day": highest_spending_day, "amount": float(day_spending.max())}
        ))
        
        # Insight: Categoría principal de gasto
        category_spending = {}
        for _, row in df.iterrows():
            categories = row.get('category', [])
            if categories:
                primary_category = categories[0] if categories else 'Other'
                category_spending[primary_category] = category_spending.get(primary_category, 0) + row['amount']
        
        if category_spending:
            top_category = max(category_spending, key=category_spending.get)
            top_amount = category_spending[top_category]
            
            insights.append(FinancialInsight(
                type="category_analysis",
                title=f"Gasto principal: {top_category}",
                description=f"La categoría {top_category} representa tu mayor gasto",
                impact_score=0.8,
                actionable=True,
                recommendations=[
                    f"Analiza gastos en {top_category}",
                    "Busca alternativas para optimizar en esta categoría"
                ],
                data_points={"category": top_category, "amount": float(top_amount)}
            ))
        
        return insights
    
    def _generate_cash_flow_insights(self, df: pd.DataFrame) -> List[FinancialInsight]:
        """Genera insights sobre flujo de caja"""
        insights = []
        
        total_income = df[df['is_income']]['amount'].sum() * -1
        total_expenses = df[~df['is_income']]['amount'].sum()
        net_flow = total_income - total_expenses
        
        if net_flow < 0:
            insights.append(FinancialInsight(
                type="cash_flow",
                title="Flujo de caja negativo",
                description=f"Tus gastos superan tus ingresos por ${abs(net_flow):.2f}",
                impact_score=0.9,
                actionable=True,
                recommendations=[
                    "Reduce gastos no esenciales",
                    "Considera aumentar ingresos",
                    "Revisa suscripción y servicios"
                ],
                data_points={"net_flow": float(net_flow), "income": float(total_income), "expenses": float(total_expenses)}
            ))
        else:
            savings_rate = (net_flow / total_income) * 100 if total_income > 0 else 0
            
            insights.append(FinancialInsight(
                type="savings_opportunity",
                title="Oportunidad de ahorro identificada",
                description=f"Tasa de ahorro actual: {savings_rate:.1f}%",
                impact_score=0.7,
                actionable=True,
                recommendations=[
                    "Considera incrementar ahorros automáticos",
                    "Explora inversiones de bajo riesgo",
                    "Revisa metas de ahorro a largo plazo"
                ],
                data_points={"savings_rate": float(savings_rate), "net_flow": float(net_flow)}
            ))
        
        return insights
    
    def _generate_executive_summary(self, spending: Dict, cash_flow: Dict, anomalies: Dict) -> str:
        """Genera resumen ejecutivo del reporte"""
        summary_parts = []
        
        # Resumen de gastos
        total_spending = spending['summary']['total_spending']
        summary_parts.append(f"Gastos totales: ${total_spending:.2f}")
        
        # Resumen de flujo de caja
        net_flow = cash_flow['summary']['net_flow']
        flow_status = "positivo" if net_flow >= 0 else "negativo"
        summary_parts.append(f"Flujo de caja {flow_status}: ${abs(net_flow):.2f}")
        
        # Resumen de anomalías
        anomalies_count = len(anomalies.get('anomalies', []))
        if anomalies_count > 0:
            summary_parts.append(f"Anomalías detectadas: {anomalies_count}")
        
        return ". ".join(summary_parts) + "."
    
    def _generate_recommendations(self, spending: Dict, cash_flow: Dict, anomalies: Dict) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []
        
        # Recomendaciones basadas en flujo de caja
        net_flow = cash_flow['summary']['net_flow']
        if net_flow < 0:
            recommendations.append("Considera crear un presupuesto para controlar gastos")
            recommendations.append("Revisa suscripciones y servicios no utilizados")
        
        # Recomendaciones basadas en patrones de gasto
        avg_transaction = spending['summary']['average_transaction']
        if avg_transaction > 100:
            recommendations.append("Los gastos promedio son altos, considera limits de transacción")
        
        # Recomendaciones basadas en anomalías
        anomalies_count = len(anomalies.get('anomalies', []))
        if anomalies_count > 0:
            recommendations.append("Revisa las transacciones anómalas detectadas")
        
        return recommendations
    
    async def close(self):
        """Cierra recursos"""
        await self.session.close()