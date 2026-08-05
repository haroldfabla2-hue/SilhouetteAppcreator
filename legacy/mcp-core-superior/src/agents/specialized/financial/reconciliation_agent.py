"""
Agente de Reconciliación Automática - APIs Financieras y Bancarias
Automatiza reconciliación entre sistemas contables, bancos y procesadores de pago
Implementa validación, matching inteligente y reportes de discrepancias
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import json

@dataclass
class TransactionRecord:
    """Registro de transacción para reconciliación"""
    id: str
    date: datetime
    amount: float
    currency: str
    description: str
    source: str  # bank, stripe, paypal, quickbooks, xero
    reference: Optional[str] = None
    status: str = "unreconciled"
    matched_id: Optional[str] = None
    confidence_score: float = 0.0
    
@dataclass
class ReconciliationMatch:
    """Resultado de matching de transacciones"""
    match_id: str
    primary_record: TransactionRecord
    secondary_records: List[TransactionRecord]
    confidence_score: float
    match_type: str  # exact, fuzzy, probable
    total_amount_primary: float
    total_amount_secondary: float
    date_difference_days: int
    confidence_breakdown: Dict[str, float]

@dataclass
class ReconciliationResult:
    """Resultado completo de reconciliación"""
    reconciliation_id: str
    period_start: datetime
    period_end: datetime
    total_records: int
    matched_count: int
    unmatched_count: int
    discrepancy_amount: float
    matches: List[ReconciliationMatch]
    unmatched_records: List[TransactionRecord]
    report_generated_at: datetime
    confidence_threshold: float

class ReconciliationSource(Enum):
    BANK = "bank"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    QUICKBOOKS = "quickbooks"
    XERO = "xero"
    MANUAL = "manual"

class MatchStrategy(Enum):
    EXACT = "exact"
    AMOUNT_DATE = "amount_date"
    FUZZY = "fuzzy"
    INTELLIGENT = "intelligent"

class ReconciliationAgent:
    """
    Agente especializado en reconciliación automática de transacciones
    Integra múltiples fuentes de datos financieros y detecta discrepancias
    """
    
    def __init__(self, 
                 confidence_threshold: float = 0.85,
                 date_tolerance_days: int = 3,
                 amount_tolerance: float = 0.01):
        
        self.confidence_threshold = confidence_threshold
        self.date_tolerance_days = date_tolerance_days
        self.amount_tolerance = amount_tolerance
        
        # Almacenamiento temporal de datos de reconciliación
        self.reconciliation_cache = {}
        self.transaction_cache = {}
        
        # Configuración de matching
        self.match_rules = {
            "exact": self._match_exact,
            "amount_date": self._match_amount_date,
            "fuzzy": self._match_fuzzy,
            "intelligent": self._match_intelligent
        }
        
    async def reconcile_period(self,
                             start_date: datetime,
                             end_date: datetime,
                             source_1: ReconciliationSource,
                             source_2: ReconciliationSource,
                             account_mappings: Optional[Dict[str, str]] = None) -> ReconciliationResult:
        """
        Reconcilia un período específico entre dos fuentes de datos
        """
        reconciliation_id = self._generate_reconciliation_id(start_date, end_date, source_1, source_2)
        
        try:
            # Obtener transacciones de ambas fuentes
            transactions_1 = await self._get_transactions_from_source(source_1, start_date, end_date)
            transactions_2 = await self._get_transactions_from_source(source_2, start_date, end_date)
            
            print(f"Reconciliación {reconciliation_id}:")
            print(f"  Fuente 1 ({source_1}): {len(transactions_1)} transacciones")
            print(f"  Fuente 2 ({source_2}): {len(transactions_2)} transacciones")
            
            # Ejecutar matching inteligente
            matches = await self._perform_intelligent_matching(
                transactions_1, transactions_2, account_mappings
            )
            
            # Separar transacciones coincidentes y no coincidentes
            matched_ids = set()
            for match in matches:
                matched_ids.add(match.primary_record.id)
                for record in match.secondary_records:
                    matched_ids.add(record.id)
            
            unmatched_records = [
                t for t in transactions_1 + transactions_2 
                if t.id not in matched_ids
            ]
            
            # Calcular discrepancias
            discrepancy_amount = self._calculate_discrepancies(matches)
            
            # Crear resultado
            result = ReconciliationResult(
                reconciliation_id=reconciliation_id,
                period_start=start_date,
                period_end=end_date,
                total_records=len(transactions_1) + len(transactions_2),
                matched_count=sum(len(match.secondary_records) + 1 for match in matches),
                unmatched_count=len(unmatched_records),
                discrepancy_amount=discrepancy_amount,
                matches=matches,
                unmatched_records=unmatched_records,
                report_generated_at=datetime.now(),
                confidence_threshold=self.confidence_threshold
            )
            
            # Cache del resultado
            self.reconciliation_cache[reconciliation_id] = result
            
            return result
            
        except Exception as e:
            raise Exception(f"Error en reconciliación {reconciliation_id}: {str(e)}")
    
    async def auto_reconcile_multiple_sources(self,
                                            start_date: datetime,
                                            end_date: datetime,
                                            sources: List[ReconciliationSource],
                                            primary_source: ReconciliationSource = ReconciliationSource.QUICKBOOKS) -> Dict[str, ReconciliationResult]:
        """
        Reconcilia automáticamente múltiples fuentes de datos
        """
        results = {}
        
        # Reconciliar fuente primaria con cada fuente secundaria
        for secondary_source in sources:
            if secondary_source != primary_source:
                result = await self.reconcile_period(
                    start_date, end_date, primary_source, secondary_source
                )
                results[f"{primary_source.value}_vs_{secondary_source.value}"] = result
        
        # Generar reporte consolidado
        consolidated_report = await self._generate_consolidated_report(results)
        
        return {
            "individual_reconciliations": results,
            "consolidated_report": consolidated_report,
            "summary": self._generate_summary_statistics(results)
        }
    
    async def validate_reconciliation(self, 
                                    reconciliation_id: str,
                                    validation_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Valida la calidad de una reconciliación completada
        """
        if reconciliation_id not in self.reconciliation_cache:
            raise ValueError(f"Reconciliación {reconciliation_id} no encontrada")
        
        result = self.reconciliation_cache[reconciliation_id]
        
        # Criterios de validación por defecto
        default_criteria = {
            "min_confidence_score": 0.8,
            "max_unmatched_percentage": 0.1,  # 10%
            "max_amount_variance": 0.01,      # 1%
            "require_date_within_tolerance": True,
            "min_matched_percentage": 0.7     # 70%
        }
        
        criteria = {**default_criteria, **(validation_criteria or {})}
        
        # Ejecutar validaciones
        validation_results = {
            "validation_id": self._generate_validation_id(reconciliation_id),
            "reconciliation_id": reconciliation_id,
            "validated_at": datetime.now(),
            "criteria_applied": criteria,
            "validations": {}
        }
        
        # Validación 1: Puntaje de confianza mínimo
        high_confidence_matches = [m for m in result.matches if m.confidence_score >= criteria["min_confidence_score"]]
        validation_results["validations"]["confidence_score"] = {
            "passed": len(high_confidence_matches) / len(result.matches) >= 0.5,
            "high_confidence_count": len(high_confidence_matches),
            "total_matches": len(result.matches),
            "percentage": len(high_confidence_matches) / len(result.matches) * 100
        }
        
        # Validación 2: Porcentaje de transacciones no coincidentes
        unmatched_percentage = result.unmatched_count / result.total_records
        validation_results["validations"]["unmatched_percentage"] = {
            "passed": unmatched_percentage <= criteria["max_unmatched_percentage"],
            "unmatched_count": result.unmatched_count,
            "total_records": result.total_records,
            "percentage": unmatched_percentage * 100
        }
        
        # Validación 3: Variación de monto
        amount_variance = self._calculate_amount_variance(result.matches)
        validation_results["validations"]["amount_variance"] = {
            "passed": amount_variance <= criteria["max_amount_variance"],
            "variance": amount_variance * 100,
            "max_allowed": criteria["max_amount_variance"] * 100
        }
        
        # Validación 4: Porcentaje de matching
        matched_percentage = result.matched_count / result.total_records
        validation_results["validations"]["matched_percentage"] = {
            "passed": matched_percentage >= criteria["min_matched_percentage"],
            "matched_count": result.matched_count,
            "total_records": result.total_records,
            "percentage": matched_percentage * 100
        }
        
        # Calcular puntuación general
        passed_validations = sum(1 for v in validation_results["validations"].values() if v["passed"])
        overall_score = passed_validations / len(validation_results["validations"])
        
        validation_results["overall_validation"] = {
            "score": overall_score,
            "passed": overall_score >= 0.75,
            "passed_validations": passed_validations,
            "total_validations": len(validation_results["validations"])
        }
        
        return validation_results
    
    async def _get_transactions_from_source(self,
                                           source: ReconciliationSource,
                                           start_date: datetime,
                                           end_date: datetime) -> List[TransactionRecord]:
        """
        Obtiene transacciones de una fuente específica
        """
        if source == ReconciliationSource.STRIPE:
            return await self._get_stripe_transactions(start_date, end_date)
        elif source == ReconciliationSource.PAYPAL:
            return await self._get_paypal_transactions(start_date, end_date)
        elif source == ReconciliationSource.QUICKBOOKS:
            return await self._get_quickbooks_transactions(start_date, end_date)
        elif source == ReconciliationSource.XERO:
            return await self._get_xero_transactions(start_date, end_date)
        elif source == ReconciliationSource.BANK:
            return await self._get_bank_transactions(start_date, end_date)
        else:
            raise ValueError(f"Fuente no soportada: {source}")
    
    async def _get_stripe_transactions(self, start_date: datetime, end_date: datetime) -> List[TransactionRecord]:
        """Obtiene transacciones de Stripe"""
        # En implementación real, usar API de Stripe
        # Por ahora, generar datos de ejemplo
        transactions = []
        current_date = start_date
        
        while current_date <= end_date:
            # Simular transacciones de Stripe
            for i in range(np.random.randint(0, 3)):
                amount = round(np.random.uniform(10, 500), 2)
                transactions.append(TransactionRecord(
                    id=f"stripe_{current_date.strftime('%Y%m%d')}_{i}",
                    date=current_date,
                    amount=amount,
                    currency="USD",
                    description=f"Stripe Payment {i}",
                    source="stripe",
                    status="completed"
                ))
            current_date += timedelta(days=1)
        
        return transactions
    
    async def _get_paypal_transactions(self, start_date: datetime, end_date: datetime) -> List[TransactionRecord]:
        """Obtiene transacciones de PayPal"""
        # Simular transacciones de PayPal
        transactions = []
        current_date = start_date
        
        while current_date <= end_date:
            for i in range(np.random.randint(0, 2)):
                amount = round(np.random.uniform(5, 300), 2)
                transactions.append(TransactionRecord(
                    id=f"paypal_{current_date.strftime('%Y%m%d')}_{i}",
                    date=current_date,
                    amount=amount,
                    currency="USD",
                    description=f"PayPal Transfer {i}",
                    source="paypal",
                    status="completed"
                ))
            current_date += timedelta(days=1)
        
        return transactions
    
    async def _get_quickbooks_transactions(self, start_date: datetime, end_date: datetime) -> List[TransactionRecord]:
        """Obtiene transacciones de QuickBooks"""
        # Simular transacciones de QuickBooks
        transactions = []
        current_date = start_date
        
        while current_date <= end_date:
            for i in range(np.random.randint(1, 4)):
                amount = round(np.random.uniform(20, 800), 2)
                transactions.append(TransactionRecord(
                    id=f"qb_{current_date.strftime('%Y%m%d')}_{i}",
                    date=current_date,
                    amount=amount,
                    currency="USD",
                    description=f"QB Invoice {i}",
                    source="quickbooks",
                    status="posted",
                    reference=f"REF_{current_date.strftime('%Y%m%d')}_{i}"
                ))
            current_date += timedelta(days=1)
        
        return transactions
    
    async def _get_xero_transactions(self, start_date: datetime, end_date: datetime) -> List[TransactionRecord]:
        """Obtiene transacciones de Xero"""
        # Simular transacciones de Xero
        transactions = []
        current_date = start_date
        
        while current_date <= end_date:
            for i in range(np.random.randint(0, 2)):
                amount = round(np.random.uniform(15, 400), 2)
                transactions.append(TransactionRecord(
                    id=f"xero_{current_date.strftime('%Y%m%d')}_{i}",
                    date=current_date,
                    amount=amount,
                    currency="USD",
                    description=f"Xero Payment {i}",
                    source="xero",
                    status="authorised"
                ))
            current_date += timedelta(days=1)
        
        return transactions
    
    async def _get_bank_transactions(self, start_date: datetime, end_date: datetime) -> List[TransactionRecord]:
        """Obtiene transacciones bancarias"""
        # Simular transacciones bancarias
        transactions = []
        current_date = start_date
        
        while current_date <= end_date:
            for i in range(np.random.randint(1, 5)):
                amount = round(np.random.uniform(10, 1000), 2)
                transactions.append(TransactionRecord(
                    id=f"bank_{current_date.strftime('%Y%m%d')}_{i}",
                    date=current_date,
                    amount=amount,
                    currency="USD",
                    description=f"Bank Transaction {i}",
                    source="bank",
                    status="posted"
                ))
            current_date += timedelta(days=1)
        
        return transactions
    
    async def _perform_intelligent_matching(self,
                                          transactions_1: List[TransactionRecord],
                                          transactions_2: List[TransactionRecord],
                                          account_mappings: Optional[Dict[str, str]] = None) -> List[ReconciliationMatch]:
        """
        Realiza matching inteligente entre dos conjuntos de transacciones
        """
        matches = []
        used_transactions_2 = set()
        
        # Ordenar transacciones por fecha para optimizar matching
        sorted_transactions_1 = sorted(transactions_1, key=lambda t: t.date)
        sorted_transactions_2 = sorted(transactions_2, key=lambda t: t.date)
        
        for transaction_1 in sorted_transactions_1:
            best_match = None
            best_score = 0
            best_transaction_2 = None
            
            for transaction_2 in sorted_transactions_2:
                if transaction_2.id in used_transactions_2:
                    continue
                
                # Calcular score de matching
                score = self._calculate_match_score(transaction_1, transaction_2, account_mappings)
                
                if score > best_score and score >= self.confidence_threshold:
                    best_score = score
                    best_transaction_2 = transaction_2
                    best_match = transaction_1
            
            if best_match and best_transaction_2:
                # Crear match
                match = ReconciliationMatch(
                    match_id=self._generate_match_id(),
                    primary_record=transaction_1,
                    secondary_records=[best_transaction_2],
                    confidence_score=best_score,
                    match_type=self._determine_match_type(best_score),
                    total_amount_primary=transaction_1.amount,
                    total_amount_secondary=best_transaction_2.amount,
                    date_difference_days=abs((transaction_1.date - best_transaction_2.date).days),
                    confidence_breakdown=self._calculate_confidence_breakdown(transaction_1, best_transaction_2)
                )
                
                matches.append(match)
                used_transactions_2.add(best_transaction_2.id)
        
        return matches
    
    def _calculate_match_score(self, 
                             transaction_1: TransactionRecord, 
                             transaction_2: TransactionRecord,
                             account_mappings: Optional[Dict[str, str]] = None) -> float:
        """
        Calcula score de matching basado en múltiples criterios
        """
        score = 0.0
        max_score = 0.0
        
        # 1. Matching exacto de monto (peso: 40%)
        max_score += 0.4
        amount_diff = abs(transaction_1.amount - transaction_2.amount)
        if amount_diff <= self.amount_tolerance:
            score += 0.4
        else:
            # Matching parcial basado en proximidad
            relative_diff = amount_diff / max(transaction_1.amount, transaction_2.amount)
            if relative_diff <= 0.05:  # 5% de tolerancia
                score += 0.3
            elif relative_diff <= 0.1:  # 10% de tolerancia
                score += 0.2
        
        # 2. Matching de fecha (peso: 25%)
        max_score += 0.25
        date_diff = abs((transaction_1.date - transaction_2.date).days)
        if date_diff == 0:
            score += 0.25
        elif date_diff <= self.date_tolerance_days:
            score += 0.2 - (date_diff * 0.05)  # Penalizar por diferencia de días
        elif date_diff <= 7:  # 7 días de tolerancia para matching probable
            score += 0.1
        
        # 3. Matching de descripción (peso: 20%)
        max_score += 0.2
        desc_similarity = self._calculate_text_similarity(
            transaction_1.description, transaction_2.description
        )
        score += desc_similarity * 0.2
        
        # 4. Matching de referencia (peso: 15%)
        max_score += 0.15
        if transaction_1.reference and transaction_2.reference:
            if transaction_1.reference == transaction_2.reference:
                score += 0.15
            elif self._calculate_text_similarity(transaction_1.reference, transaction_2.reference) > 0.8:
                score += 0.1
        
        # Normalizar score
        final_score = score / max_score if max_score > 0 else 0
        return min(final_score, 1.0)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud entre dos textos usando algoritmo simple"""
        if not text1 or not text2:
            return 0.0
        
        # Normalizar textos
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()
        
        if t1 == t2:
            return 1.0
        
        # Similitud basada en palabras comunes
        words1 = set(t1.split())
        words2 = set(t2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _determine_match_type(self, confidence_score: float) -> str:
        """Determina tipo de matching basado en score"""
        if confidence_score >= 0.95:
            return "exact"
        elif confidence_score >= 0.85:
            return "high_confidence"
        elif confidence_score >= 0.75:
            return "probable"
        else:
            return "fuzzy"
    
    def _calculate_confidence_breakdown(self, 
                                      transaction_1: TransactionRecord, 
                                      transaction_2: TransactionRecord) -> Dict[str, float]:
        """Calcula desglose de confianza por criterio"""
        return {
            "amount_match": 1.0 if abs(transaction_1.amount - transaction_2.amount) <= self.amount_tolerance else 0.5,
            "date_match": 1.0 if (transaction_1.date - transaction_2.date).days == 0 else 0.7,
            "description_match": self._calculate_text_similarity(transaction_1.description, transaction_2.description),
            "reference_match": 1.0 if transaction_1.reference == transaction_2.reference else 0.0
        }
    
    def _calculate_discrepancies(self, matches: List[ReconciliationMatch]) -> float:
        """Calcula discrepancia total en montos"""
        total_discrepancy = 0.0
        for match in matches:
            amount_diff = abs(match.total_amount_primary - match.total_amount_secondary)
            total_discrepancy += amount_diff
        return total_discrepancy
    
    def _calculate_amount_variance(self, matches: List[ReconciliationMatch]) -> float:
        """Calcula varianza promedio en montos"""
        if not matches:
            return 0.0
        
        variances = []
        for match in matches:
            variance = abs(match.total_amount_primary - match.total_amount_secondary) / match.total_amount_primary
            variances.append(variance)
        
        return np.mean(variances)
    
    async def _generate_consolidated_report(self, results: Dict[str, ReconciliationResult]) -> Dict[str, Any]:
        """Genera reporte consolidado de múltiples reconciliaciones"""
        total_transactions = sum(r.total_records for r in results.values())
        total_matched = sum(r.matched_count for r in results.values())
        total_unmatched = sum(r.unmatched_count for r in results.values())
        total_discrepancy = sum(r.discrepancy_amount for r in results.values())
        
        return {
            "consolidated_summary": {
                "total_reconciliations": len(results),
                "total_transactions": total_transactions,
                "total_matched": total_matched,
                "total_unmatched": total_unmatched,
                "overall_match_rate": (total_matched / total_transactions * 100) if total_transactions > 0 else 0,
                "total_discrepancy_amount": total_discrepancy
            },
            "reconciliation_details": {
                name: {
                    "match_rate": (r.matched_count / r.total_records * 100) if r.total_records > 0 else 0,
                    "unmatched_count": r.unmatched_count,
                    "discrepancy_amount": r.discrepancy_amount
                }
                for name, r in results.items()
            }
        }
    
    def _generate_summary_statistics(self, results: Dict[str, ReconciliationResult]) -> Dict[str, Any]:
        """Genera estadísticas resumidas"""
        match_rates = []
        discrepancies = []
        
        for result in results.values():
            match_rate = (result.matched_count / result.total_records * 100) if result.total_records > 0 else 0
            match_rates.append(match_rate)
            discrepancies.append(result.discrepancy_amount)
        
        return {
            "average_match_rate": np.mean(match_rates) if match_rates else 0,
            "max_match_rate": max(match_rates) if match_rates else 0,
            "min_match_rate": min(match_rates) if match_rates else 0,
            "total_discrepancy": sum(discrepancies),
            "avg_discrepancy": np.mean(discrepancies) if discrepancies else 0
        }
    
    def _generate_reconciliation_id(self, start_date: datetime, end_date: datetime, 
                                  source_1: ReconciliationSource, source_2: ReconciliationSource) -> str:
        """Genera ID único de reconciliación"""
        timestamp = int(datetime.now().timestamp() * 1000000)
        hash_input = f"{start_date.isoformat()}_{end_date.isoformat()}_{source_1.value}_{source_2.value}_{timestamp}"
        hash_object = hashlib.md5(hash_input.encode())
        return f"recon_{hash_object.hexdigest()[:12]}"
    
    def _generate_validation_id(self, reconciliation_id: str) -> str:
        """Genera ID único de validación"""
        timestamp = int(datetime.now().timestamp() * 1000)
        hash_input = f"{reconciliation_id}_validation_{timestamp}"
        hash_object = hashlib.md5(hash_input.encode())
        return f"valid_{hash_object.hexdigest()[:10]}"
    
    def _generate_match_id(self) -> str:
        """Genera ID único de match"""
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"match_{timestamp}_{np.random.randint(1000, 9999)}"
    
    # Métodos de matching específicos
    def _match_exact(self, t1: TransactionRecord, t2: TransactionRecord) -> bool:
        """Matching exacto de monto y fecha"""
        return (abs(t1.amount - t2.amount) <= self.amount_tolerance and 
                t1.date.date() == t2.date.date())
    
    def _match_amount_date(self, t1: TransactionRecord, t2: TransactionRecord) -> bool:
        """Matching por monto y proximidad de fecha"""
        amount_ok = abs(t1.amount - t2.amount) <= (t1.amount * 0.05)  # 5% tolerancia
        date_ok = abs((t1.date - t2.date).days) <= self.date_tolerance_days
        return amount_ok and date_ok
    
    def _match_fuzzy(self, t1: TransactionRecord, t2: TransactionRecord) -> bool:
        """Matching fuzzy con múltiples criterios"""
        score = self._calculate_match_score(t1, t2)
        return score >= self.confidence_threshold
    
    def _match_intelligent(self, t1: TransactionRecord, t2: TransactionRecord, account_mappings: Dict[str, str] = None) -> bool:
        """Matching inteligente con lógica avanzada"""
        # Combinar múltiples estrategias de matching
        exact_match = self._match_exact(t1, t2)
        amount_date_match = self._match_amount_date(t1, t2)
        fuzzy_match = self._match_fuzzy(t1, t2)
        
        # Score ponderado
        final_score = (exact_match * 1.0 + amount_date_match * 0.8 + fuzzy_match * 0.6) / 3
        return final_score >= self.confidence_threshold
