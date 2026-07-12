# 🐍 Python Executor Agent - Guía Completa

## Descripción General

El **Python Executor Agent** es un agente especializado que proporciona capacidades avanzadas de **ejecución segura de código Python**, gestión de paquetes, análisis de datos, y desarrollo de aplicaciones usando **entornos Python reales**. Es una herramienta **operacional real** que ejecuta código Python en sandbox aislado con limitaciones de recursos y gestión automática de dependencias.

**Estado**: ✅ **PRODUCCIÓN ACTIVA**  
**Tecnologías**: Python 3.9+, pip, virtualenv, pytest, jupyter  
**Capacidades**: Code execution, package management, data analysis, ML workflows  
**Seguridad**: Sandbox aislado, resource limits, network isolation  
**Ambiente**: Virtual environments automáticos, dependency management

## 🎯 Capacidades Principales

### Ejecución Segura de Código
- **Sandbox Isolation**: Ejecución en entorno aislado con límites de recursos
- **Resource Management**: CPU, memoria, disco y tiempo limitado
- **Network Security**: Aislamiento de red configurable
- **Package Security**: Instalación segura solo de packages verificados
- **Execution Monitoring**: Monitoreo en tiempo real de la ejecución

### Gestión de Paquetes y Dependencias
- **Virtual Environment**: Creación automática de entornos virtuales
- **Package Installation**: Instalación segura de paquetes desde PyPI
- **Dependency Resolution**: Resolución automática de dependencias
- **Version Management**: Gestión de versiones específicas
- **Requirements Tracking**: Generación y seguimiento de requirements.txt

### Análisis de Datos y ML
- **Data Processing**: pandas, numpy para análisis de datos
- **Visualization**: matplotlib, seaborn, plotly para gráficos
- **Machine Learning**: scikit-learn, tensorflow, pytorch
- **Jupyter Integration**: Ejecución de notebooks Jupyter
- **Statistical Analysis**: scipy, statsmodels para análisis estadístico

### Testing y Quality Assurance
- **Unit Testing**: pytest, unittest para testing automatizado
- **Code Coverage**: Medición de cobertura de código
- **Linting**: flake8, black, mypy para calidad de código
- **Performance Testing**: timeit, cProfile para profiling
- **Security Scanning**: bandit para análisis de seguridad

## 🛠️ Instalación y Configuración

### Prerrequisitos del Sistema

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3.9 \
    python3.9-venv \
    python3.9-dev \
    python3-pip \
    build-essential \
    libssl-dev \
    libffi-dev

# Verificar instalación
python3.9 --version
pip3.9 --version
```

### Configuración de Seguridad

```bash
# Configurar límites del sistema
echo "python_executor soft nofile 1024" | sudo tee -a /etc/security/limits.conf
echo "python_executor hard nofile 4096" | sudo tee -a /etc/security/limits.conf

# Crear usuario sandbox
sudo useradd -r -s /bin/false python_executor
sudo mkdir -p /opt/python_executor
sudo chown python_executor:python_executor /opt/python_executor
```

### Variables de Entorno

```bash
# Configuración de ejecución
export PYTHON_SANDBOX_DIR=/opt/python_executor
export MAX_EXECUTION_TIME=300
export MAX_MEMORY_MB=1024
export MAX_DISK_MB=512
export MAX_OUTPUT_SIZE=10MB

# Configuración de seguridad
export NETWORK_ISOLATION=true
export DISALLOW_MODULES="os,subprocess,importlib,__import__"
export ALLOW_NETWORK_MODULES="urllib,requests,json"

# Configuración de paquetes
export PYPI_TRUSTED_HOST="pypi.org,pypi.python.org,files.pythonhosted.org"
export PIP_TIMEOUT=120
export PIP_RETRIES=3
```

### Configuración de Entornos Virtuales

```bash
# Crear estructura de directorios
sudo mkdir -p /opt/python_executor/environments
sudo mkdir -p /opt/python_executor/executions
sudo mkdir -p /opt/python_executor/temp
sudo mkdir -p /opt/python_executor/logs

# Configurar permisos
sudo chown -R python_executor:python_executor /opt/python_executor
sudo chmod -R 755 /opt/python_executor
```

## 📚 API Reference

### Ejecución Básica de Código

#### 1. Ejecutar Código Python

```http
POST /api/v1/tools/python_executor
Content-Type: application/json

{
    "agent": "python_executor",
    "action": "execute_code",
    "code": "import pandas as pd\nimport numpy as np\n\n# Análisis de datos de ejemplo\ndata = pd.DataFrame({\n    'ventas': np.random.normal(1000, 200, 100),\n    'meses': pd.date_range('2024-01-01', periods=100, freq='D')\n})\n\nresultado = data.describe()\nprint(resultado.to_json())",
    "packages": ["pandas", "numpy", "matplotlib"],
    "timeout": 60,
    "memory_limit": "512MB",
    "save_output": true,
    "environment_name": "data_analysis_env"
}
```

**Respuesta:**
```json
{
    "status": "success",
    "data": {
        "output": "{\n    \"ventas\":{\n        \"count\":100.0,\n        \"mean\":998.73,\n        \"std\":201.45,\n        \"min\":412.11,\n        \"25%\":860.12,\n        \"50%\":1001.89,\n        \"75%\":1139.21,\n        \"max\":1487.33\n    }\n}",
        "execution_time": 1.25,
        "packages_installed": ["pandas==2.1.0", "numpy==1.24.3", "matplotlib==3.7.2"],
        "memory_used": "45MB",
        "environment_path": "/opt/python_executor/environments/data_analysis_env"
    },
    "metrics": {
        "cpu_time": 1.23,
        "wall_time": 1.25,
        "peak_memory": "45MB",
        "lines_executed": 15,
        "functions_called": 8
    }
}
```

#### 2. Instalación de Paquetes

```http
POST /api/v1/tools/python_executor
Content-Type: application/json

{
    "agent": "python_executor",
    "action": "install_packages",
    "packages": [
        {
            "name": "requests",
            "version": "2.31.0",
            "trusted": true
        },
        {
            "name": "beautifulsoup4",
            "version": "4.12.0",
            "trusted": true
        }
    ],
    "environment_name": "web_scraping_env",
    "requirements_file": "/path/to/requirements.txt",
    "upgrade_existing": false,
    "verify_checksums": true
}
```

#### 3. Análisis de Datos con Pandas

```http
POST /api/v1/tools/python_executor
Content-Type: application/json

{
    "agent": "python_executor",
    "action": "data_analysis",
    "code": "import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\n\n# Cargar datos de ejemplo\ndf = pd.read_csv('sales_data.csv')\n\n# Análisis exploratorio\nprint(\"Estadísticas generales:\")\nprint(df.describe())\n\nprint(\"\\nValores nulos:\")\nprint(df.isnull().sum())\n\n# Visualizaciones\nfig, axes = plt.subplots(2, 2, figsize=(12, 8))\n\n# Histograma de ventas\naxes[0,0].hist(df['sales'], bins=30, alpha=0.7)\naxes[0,0].set_title('Distribución de Ventas')\n\n# Scatter plot ventas vs mes\naxes[0,1].scatter(df['month'], df['sales'])\naxes[0,1].set_title('Ventas por Mes')\n\n# Box plot por región\ndf.boxplot(column='sales', by='region', ax=axes[1,0])\naxes[1,0].set_title('Ventas por Región')\n\n# Correlación\ncorr_matrix = df.corr()\naxes[1,1].imshow(corr_matrix, cmap='coolwarm')\naxes[1,1].set_title('Matriz de Correlación')\n\nplt.tight_layout()\nplt.savefig('analysis_plots.png')\n\n# Insights\ninsights = {\n    'total_sales': df['sales'].sum(),\n    'average_sales': df['sales'].mean(),\n    'best_month': df.loc[df['sales'].idxmax(), 'month'],\n    'best_region': df.groupby('region')['sales'].mean().idxmax()\n}\n\nprint(\"\\nInsights generados:\")\nfor key, value in insights.items():\n    print(f\"{key}: {value}\")\n\n# Guardar resultados\ndf.to_csv('processed_data.csv', index=False)",
    "data_files": [
        {
            "path": "sales_data.csv",
            "content": "sales,month,region\\n1200,1,North\\n800,2,South\\n1500,3,North\\n950,4,East"
        }
    ],
    "packages": ["pandas", "numpy", "matplotlib", "seaborn"],
    "output_files": ["analysis_plots.png", "processed_data.csv"],
    "timeout": 120
}
```

### Machine Learning

#### 4. Entrenamiento de Modelos ML

```http
POST /api/v1/tools/python_executor
Content-Type: application/json

{
    "agent": "python_executor",
    "action": "ml_training",
    "code": "import pandas as pd\nimport numpy as np\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.ensemble import RandomForestRegressor\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error\nfrom sklearn.preprocessing import StandardScaler, LabelEncoder\nimport joblib\n\n# Generar datos de ejemplo\nnp.random.seed(42)\nn_samples = 1000\n\ndata = pd.DataFrame({\n    'feature_1': np.random.normal(0, 1, n_samples),\n    'feature_2': np.random.normal(5, 2, n_samples),\n    'feature_3': np.random.exponential(2, n_samples),\n    'category': np.random.choice(['A', 'B', 'C'], n_samples),\n    'target': np.random.normal(10, 3, n_samples)\n})\n\n# Crear variable target con relación a features\ndata['target'] = (\n    2 * data['feature_1'] + \n    1.5 * data['feature_2'] + \n    0.5 * data['feature_3'] + \n    np.random.normal(0, 1, n_samples) +\n    data['category'].map({'A': 2, 'B': -1, 'C': 1})\n)\n\n# Preprocesamiento\nle = LabelEncoder()\ndata['category_encoded'] = le.fit_transform(data['category'])\n\n# Features y target\nX = data[['feature_1', 'feature_2', 'feature_3', 'category_encoded']]\ny = data['target']\n\n# División train/test\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n\n# Scaling\nscaler = StandardScaler()\nX_train_scaled = scaler.fit_transform(X_train)\nX_test_scaled = scaler.transform(X_test)\n\n# Modelos\nmodels = {\n    'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42),\n    'LinearRegression': LinearRegression()\n}\n\nresults = {}\n\nfor name, model in models.items():\n    print(f\"\\nEntrenando {name}...\")\n    \n    # Entrenar\n    if name == 'LinearRegression':\n        model.fit(X_train_scaled, y_train)\n        y_pred = model.predict(X_test_scaled)\n    else:\n        model.fit(X_train, y_train)\n        y_pred = model.predict(X_test)\n    \n    # Métricas\n    mse = mean_squared_error(y_test, y_pred)\n    rmse = np.sqrt(mse)\n    mae = mean_absolute_error(y_test, y_pred)\n    r2 = r2_score(y_test, y_pred)\n    \n    results[name] = {\n        'MSE': mse,\n        'RMSE': rmse,\n        'MAE': mae,\n        'R2': r2\n    }\n    \n    print(f\"MSE: {mse:.4f}\")\n    print(f\"RMSE: {rmse:.4f}\")\n    print(f\"MAE: {mae:.4f}\")\n    print(f\"R²: {r2:.4f}\")\n    \n    # Guardar modelo\n    model_filename = f'{name.lower()}_model.pkl'\n    if name == 'LinearRegression':\n        joblib.dump({'model': model, 'scaler': scaler}, model_filename)\n    else:\n        joblib.dump(model, model_filename)\n\n# Feature importance (Random Forest)\nrf_model = models['RandomForest']\nfeature_importance = pd.DataFrame({\n    'feature': X.columns,\n    'importance': rf_model.feature_importances_\n}).sort_values('importance', ascending=False)\n\nprint(\"\\nFeature Importance (Random Forest):\")\nprint(feature_importance)\n\n# Comparación de modelos\ncomparison_df = pd.DataFrame(results).T\nprint(\"\\nComparación de Modelos:\")\nprint(comparison_df)\n\n# Mejor modelo\nbest_model = min(results.keys(), key=lambda x: results[x]['RMSE'])\nprint(f\"\\nMejor modelo: {best_model}\")\n\nprint(\"\\nModelos entrenados exitosamente!\")",
    "packages": ["scikit-learn", "pandas", "numpy", "joblib", "matplotlib"],
    "output_files": ["randomforest_model.pkl", "linearregression_model.pkl", "training_report.csv"],
    "timeout": 180
}
```

#### 5. Ejecución de Tests

```http
POST /api/v1/tools/python_executor
Content-Type: application/json

{
    "agent": "python_executor",
    "action": "run_tests",
    "test_files": [
        {
            "path": "test_calculator.py",
            "content": "import unittest\nfrom calculator import Calculator\n\nclass TestCalculator(unittest.TestCase):\n    \n    def setUp(self):\n        self.calc = Calculator()\n    \n    def test_add(self):\n        self.assertEqual(self.calc.add(2, 3), 5)\n        self.assertEqual(self.calc.add(-1, 1), 0)\n        self.assertEqual(self.calc.add(0, 0), 0)\n    \n    def test_subtract(self):\n        self.assertEqual(self.calc.subtract(5, 3), 2)\n        self.assertEqual(self.calc.subtract(0, 5), -5)\n    \n    def test_multiply(self):\n        self.assertEqual(self.calc.multiply(3, 4), 12)\n        self.assertEqual(self.calc.multiply(0, 5), 0)\n    \n    def test_divide(self):\n        self.assertEqual(self.calc.divide(10, 2), 5)\n        with self.assertRaises(ValueError):\n            self.calc.divide(10, 0)\n\nif __name__ == '__main__':\n    unittest.main()"
        },
        {
            "path": "calculator.py",
            "content": "class Calculator:\n    def add(self, a, b):\n        return a + b\n    \n    def subtract(self, a, b):\n        return a - b\n    \n    def multiply(self, a, b):\n        return a * b\n    \n    def divide(self, a, b):\n        if b == 0:\n            raise ValueError(\"Cannot divide by zero\")\n        return a / b"
        }
    ],
    "test_config": {
        "coverage": True,
        "coverage_threshold": 80,
        "verbose": True,
        "parallel": False
    },
    "packages": ["pytest", "coverage"],
    "output_format": "detailed"
}
```

### Análisis de Código y Linting

#### 6. Code Quality Analysis

```http
POST /api/v1/tools/python_executor
Content-Type: application/json

{
    "agent": "python_executor",
    "action": "code_quality_analysis",
    "code_files": [
        {
            "path": "data_processor.py",
            "content": "import pandas as pd\nimport numpy as np\nimport os\n\nclass DataProcessor:\n    def __init__(self, file_path):\n        self.file_path = file_path\n        self.data = None\n    \n    def load_data(self):\n        if not os.path.exists(self.file_path):\n            raise FileNotFoundError(f\"File {self.file_path} not found\")\n        \n        self.data = pd.read_csv(self.file_path)\n        return self.data\n    \n    def clean_data(self):\n        if self.data is None:\n            raise ValueError(\"Data not loaded. Call load_data() first.\")\n        \n        # Remove duplicates\n        self.data = self.data.drop_duplicates()\n        \n        # Handle missing values\n        self.data = self.data.fillna(self.data.mean())\n        \n        return self.data\n    \n    def get_statistics(self):\n        if self.data is None:\n            raise ValueError(\"Data not loaded. Call load_data() first.\")\n        \n        return self.data.describe()\n    \n    def process_data(self):\n        self.load_data()\n        self.clean_data()\n        return self.get_statistics()\n\n# Usage\nprocessor = DataProcessor('data.csv')\ntry:\n    stats = processor.process_data()\n    print(stats)\nexcept Exception as e:\n    print(f\"Error: {e}\")"
        }
    ],
    "analysis_tools": ["flake8", "black", "mypy", "bandit"],
    "config": {
        "flake8": {"max_line_length": 88, "ignore": ["E203", "W503"]},
        "black": {"line_length": 88, "target_version": ["py39"]},
        "mypy": {"strict": True, "ignore_missing_imports": True},
        "bandit": {"exclude_dirs": ["tests"]}
    },
    "output_format": "detailed"
}
```

## 💻 Ejemplos de Uso

### Ejemplo 1: Pipeline de Análisis de Datos Completo

```python
import requests
import json

# Configuración
base_url = "http://localhost:8000/api/v1/tools/python_executor"
headers = {"Content-Type": "application/json"}

# Pipeline completo de análisis de datos
data_pipeline = requests.post(base_url, headers=headers, json={
    "agent": "python_executor",
    "action": "complete_data_analysis",
    "code": """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# 1. GENERACIÓN DE DATOS DE EJEMPLO
print("=== Generando datos de ejemplo ===")
np.random.seed(42)
n_samples = 1000

# Generar dataset empresarial simulado
data = pd.DataFrame({
    'department': np.random.choice(['Sales', 'Marketing', 'IT', 'HR'], n_samples),
    'experience_years': np.random.normal(5, 2, n_samples),
    'education_level': np.random.choice(['Bachelor', 'Master', 'PhD'], n_samples),
    'performance_score': np.random.normal(75, 15, n_samples),
    'salary_bonus': np.random.normal(10000, 5000, n_samples)
})

# Crear relaciones realistas
data['salary'] = (
    30000 + 
    data['experience_years'] * 5000 +
    data['performance_score'] * 1000 +
    data['salary_bonus']
)
# Ajustar por educación
education_bonus = {'Bachelor': 0, 'Master': 15000, 'PhD': 25000}
data['salary'] += data['education_level'].map(education_bonus)
# Ajuste por departamento
dept_bonus = {'Sales': 10000, 'Marketing': 8000, 'IT': 12000, 'HR': 6000}
data['salary'] += data['department'].map(dept_bonus)

print(f"Dataset generado: {data.shape[0]} filas, {data.shape[1]} columnas")
print("\\nPrimeras 5 filas:")
print(data.head())

# 2. ANÁLISIS EXPLORATORIO
print("\\n=== Análisis Exploratorio ===")
print("\\nEstadísticas descriptivas:")
print(data.describe())

print("\\nValores nulos:")
print(data.isnull().sum())

print("\\nDistribución por categorías:")
for col in ['department', 'education_level']:
    print(f"\\n{col}:")
    print(data[col].value_counts())

# 3. VISUALIZACIONES
print("\\n=== Generando Visualizaciones ===")

# Configurar estilo
plt.style.use('seaborn-v0_8')
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Histograma de salarios
axes[0,0].hist(data['salary'], bins=30, alpha=0.7, color='skyblue')
axes[0,0].set_title('Distribución de Salarios')
axes[0,0].set_xlabel('Salario')
axes[0,0].set_ylabel('Frecuencia')

# Salario por departamento
dept_salary = data.groupby('department')['salary'].mean()
axes[0,1].bar(dept_salary.index, dept_salary.values, color=['coral', 'lightgreen', 'lightblue', 'gold'])
axes[0,1].set_title('Salario Promedio por Departamento')
axes[0,1].set_ylabel('Salario Promedio')
axes[0,1].tick_params(axis='x', rotation=45)

# Scatter plot experiencia vs salario
axes[0,2].scatter(data['experience_years'], data['salary'], alpha=0.6, color='purple')
axes[0,2].set_title('Experiencia vs Salario')
axes[0,2].set_xlabel('Años de Experiencia')
axes[0,2].set_ylabel('Salario')

# Box plot educación
data.boxplot(column='salary', by='education_level', ax=axes[1,0])
axes[1,0].set_title('Salario por Nivel de Educación')
axes[1,0].set_xlabel('Nivel de Educación')
axes[1,0].set_ylabel('Salario')

# Correlación
numeric_cols = ['experience_years', 'performance_score', 'salary_bonus', 'salary']
corr_matrix = data[numeric_cols].corr()
im = axes[1,1].imshow(corr_matrix, cmap='coolwarm', aspect='auto')
axes[1,1].set_title('Matriz de Correlación')
axes[1,1].set_xticks(range(len(numeric_cols)))
axes[1,1].set_yticks(range(len(numeric_cols)))
axes[1,1].set_xticklabels(numeric_cols, rotation=45)
axes[1,1].set_yticklabels(numeric_cols)

# Heatmap por departamento
dept_performance = data.groupby('department')['performance_score'].mean()
axes[1,2].barh(dept_performance.index, dept_performance.values, color='lightcoral')
axes[1,2].set_title('Puntuación de Rendimiento Promedio')
axes[1,2].set_xlabel('Puntuación Promedio')

plt.tight_layout()
plt.savefig('data_analysis_report.png', dpi=300, bbox_inches='tight')
print("Visualizaciones guardadas en 'data_analysis_report.png'")

# 4. MODELO PREDICTIVO
print("\\n=== Modelo Predictivo ===")

# Preparar datos para ML
data_encoded = pd.get_dummies(data, columns=['department', 'education_level'], drop_first=True)

X = data_encoded.drop('salary', axis=1)
y = data_encoded['salary']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entrenar Random Forest
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# Predicciones
y_pred_train = rf_model.predict(X_train)
y_pred_test = rf_model.predict(X_test)

# Métricas
train_r2 = r2_score(y_train, y_pred_train)
test_r2 = r2_score(y_test, y_pred_test)
train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

print(f"R² Train: {train_r2:.4f}")
print(f"R² Test: {test_r2:.4f}")
print(f"RMSE Train: {train_rmse:.2f}")
print(f"RMSE Test: {test_rmse:.2f}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\\nTop 5 Features Más Importantes:")
print(feature_importance.head())

# 5. GENERACIÓN DE INSIGHTS
print("\\n=== Insights Empresariales ===")

insights = {
    'total_employees': len(data),
    'average_salary': data['salary'].mean(),
    'highest_paid_department': dept_salary.idxmax(),
    'salary_gap_by_department': dept_salary.max() - dept_salary.min(),
    'most_important_factor': feature_importance.iloc[0]['feature'],
    'model_performance': test_r2
}

for key, value in insights.items():
    if isinstance(value, float):
        print(f"{key}: {value:.2f}")
    else:
        print(f"{key}: {value}")

# 6. GENERAR RESUMEN EJECUTIVO
print("\\n=== Resumen Ejecutivo ===")
print(f"""
RESUMEN EJECUTIVO - ANÁLISIS DE DATOS DE EMPLEADOS
=================================================

• Total de empleados analizados: {len(data):,}
• Salario promedio: €{data['salary'].mean():,.0f}
• Departamento mejor pagado: {dept_salary.idxmax()} (€{dept_salary.max():,.0f})
• Brecha salarial entre departamentos: €{dept_salary.max() - dept_salary.min():,.0f}
• Factor más predictivo del salario: {feature_importance.iloc[0]['feature']}
• Precisión del modelo predictivo: {test_r2:.1%}

RECOMENDACIONES:
1. Enfocar la formación en: {feature_importance.iloc[0]['feature']}
2. Revisar estructura salarial del departamento de {dept_salary.idxmin()}
3. Considerar planes de desarrollo de carrera basados en años de experiencia
""")

print("\\n=== Pipeline completado exitosamente ===")
""",
    "packages": ["pandas", "numpy", "matplotlib", "seaborn", "scikit-learn"],
    "output_files": ["data_analysis_report.png", "analysis_summary.txt"],
    "timeout": 300,
    "memory_limit": "1GB"
})

result = data_pipeline.json()
print("Pipeline completado:", result["status"])
print(f"Tiempo de ejecución: {result['metrics']['execution_time']}s")
print(f"Archivos generados: {result['output_files']}")
```

### Ejemplo 2: Web Scraping con Python

```python
# Scraping web usando requests y BeautifulSoup
web_scraping_code = requests.post(base_url, headers=headers, json={
    "agent": "python_executor",
    "action": "web_scraping_task",
    "code": """
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from urllib.parse import urljoin

# Lista de sitios web para scrapear (ejemplo)
target_sites = [
    {"name": "GitHub Trending", "url": "https://github.com/trending", "selector": ".Box-row"},
    {"name": "Hacker News", "url": "https://news.ycombinator.com/", "selector": ".athing"}
]

scraped_data = []

for site in target_sites:
    print(f"Scraping {site['name']}...")
    
    try:
        # Headers para simular un navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Hacer request
        response = requests.get(site['url'], headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parsear HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraer datos según el selector
        elements = soup.select(site['selector'])
        
        site_data = {
            'site_name': site['name'],
            'url': site['url'],
            'items_found': len(elements),
            'data': []
        }
        
        for i, element in enumerate(elements[:10]):  # Limitar a 10 items
            item_data = {
                'position': i + 1,
                'title': '',
                'url': '',
                'description': ''
            }
            
            # Extraer título y enlace
            title_elem = element.find('h2') or element.find('h3') or element.find('a')
            if title_elem:
                item_data['title'] = title_elem.get_text().strip()
                if title_elem.name == 'a':
                    item_data['url'] = urljoin(site['url'], title_elem.get('href', ''))
            
            # Extraer descripción
            desc_elem = element.find('p') or element.find('span')
            if desc_elem:
                item_data['description'] = desc_elem.get_text().strip()
            
            site_data['data'].append(item_data)
        
        scraped_data.append(site_data)
        print(f"  ✓ Extraídos {len(site_data['data'])} elementos")
        
        # Delay para evitar sobrecargar el servidor
        time.sleep(2)
        
    except Exception as e:
        print(f"  ✗ Error al scrapear {site['name']}: {e}")
        scraped_data.append({
            'site_name': site['name'],
            'url': site['url'],
            'error': str(e),
            'items_found': 0,
            'data': []
        })

# Guardar datos en JSON
with open('scraped_data.json', 'w', encoding='utf-8') as f:
    json.dump(scraped_data, f, indent=2, ensure_ascii=False)

# Crear DataFrame y guardar en CSV
all_items = []
for site_data in scraped_data:
    if 'error' not in site_data:
        for item in site_data['data']:
            item['source_site'] = site_data['site_name']
            all_items.append(item)

if all_items:
    df = pd.DataFrame(all_items)
    df.to_csv('scraped_items.csv', index=False, encoding='utf-8')
    
    print(f"\\nDatos guardados:")
    print(f"- JSON: scraped_data.json")
    print(f"- CSV: scraped_items.csv")
    print(f"- Total de items: {len(all_items)}")
    
    # Mostrar resumen
    print(f"\\nResumen por sitio:")
    site_summary = df.groupby('source_site').size()
    for site, count in site_summary.items():
        print(f"- {site}: {count} items")
else:
    print("No se pudieron extraer datos.")

print("\\nScraping completado!")
""",
    "packages": ["requests", "beautifulsoup4", "pandas"],
    "timeout": 180
})
```

### Ejemplo 3: API Integration y Data Pipeline

```python
# Pipeline completo de integración con APIs
api_pipeline = requests.post(base_url, headers=headers, json={
    "agent": "python_executor",
    "action": "api_data_pipeline",
    "code": """
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time

# Configuración de APIs (ejemplo)
api_config = {
    "weather": {
        "url": "https://api.openweathermap.org/data/2.5/weather",
        "params": {"q": "Madrid", "appid": "demo_key", "units": "metric"}
    },
    "crypto": {
        "url": "https://api.coingecko.com/api/v3/simple/price",
        "params": {"ids": "bitcoin,ethereum,cardano", "vs_currencies": "usd"}
    }
}

# 1. SIMULACIÓN DE LLAMADAS A APIs (datos de ejemplo)
print("=== Simulando llamadas a APIs ===")

# Datos simulados del clima (Madrid)
weather_data = {
    "coord": {"lon": -3.7, "lat": 40.42},
    "weather": [{"main": "Clear", "description": "clear sky"}],
    "main": {"temp": 22.5, "humidity": 65},
    "name": "Madrid",
    "dt": 1635789600
}

# Datos simulados de criptomonedas
crypto_data = {
    "bitcoin": {"usd": 67500},
    "ethereum": {"usd": 3800},
    "cardano": {"usd": 1.45}
}

print("Datos del clima obtenidos:")
print(f"Temperatura: {weather_data['main']['temp']}°C")
print(f"Humedad: {weather_data['main']['humidity']}%")
print(f"Descripción: {weather_data['weather'][0]['description']}")

print("\\nPrecios de criptomonedas:")
for coin, price in crypto_data.items():
    print(f"{coin.capitalize()}: ${price['usd']:,.2f}")

# 2. PROCESAMIENTO Y ANÁLISIS
print("\\n=== Procesando datos ===")

# Combinar datos
combined_data = {
    "timestamp": datetime.now().isoformat(),
    "weather": {
        "city": weather_data['name'],
        "temperature": weather_data['main']['temp'],
        "humidity": weather_data['main']['humidity'],
        "condition": weather_data['weather'][0]['description']
    },
    "crypto_prices": crypto_data
}

# Calcular métricas
temp = weather_data['main']['temp']
humidity = weather_data['main']['humidity']
bitcoin_price = crypto_data['bitcoin']['usd']
ethereum_price = crypto_data['ethereum']['usd']

# Simular score de "sentiment" basado en datos
weather_score = (temp / 30) * 50  # Temp ideal ~30°C
crypto_score = (bitcoin_price / 70000) * 50  # Bitcoin ideal ~70k

overall_sentiment = (weather_score + crypto_score) / 2

metrics = {
    "weather_score": round(weather_score, 2),
    "crypto_score": round(crypto_score, 2),
    "overall_sentiment": round(overall_sentiment, 2),
    "market_cad_ratio": round(bitcoin_price / ethereum_price, 2)
}

print("Métricas calculadas:")
for key, value in metrics.items():
    print(f"- {key}: {value}")

# 3. GENERAR DATASET HISTÓRICO SIMULADO
print("\\n=== Generando dataset histórico ===")

# Generar 30 días de datos simulados
dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
historical_data = []

for i, date in enumerate(dates):
    # Simular variaciones
    temp_var = temp + (i % 7 - 3) * 2  # Variación semanal
    btc_var = bitcoin_price * (1 + (i % 14 - 7) * 0.02)  # Variación quincenal
    
    historical_data.append({
        "date": date.strftime("%Y-%m-%d"),
        "temperature": round(temp_var + (i % 5 - 2), 1),
        "humidity": humidity + (i % 3 - 1),
        "bitcoin_price": round(btc_var, 2),
        "day_of_week": date.strftime("%A"),
        "week_number": date.isocalendar()[1]
    })

df = pd.DataFrame(historical_data)

# 4. ANÁLISIS Y VISUALIZACIÓN
print("\\n=== Análisis de tendencias ===")

# Calcular tendencias
df['temp_trend'] = df['temperature'].rolling(window=7).mean()
df['btc_trend'] = df['bitcoin_price'].rolling(window=7).mean()

# Correlaciones
temp_btc_corr = df['temperature'].corr(df['bitcoin_price'])
print(f"Correlación temperatura-Bitcoin: {temp_btc_corr:.3f}")

# Estadísticas por día de la semana
weekly_stats = df.groupby('day_of_week').agg({
    'temperature': 'mean',
    'bitcoin_price': 'mean'
}).round(2)

print("\\nEstadísticas por día de la semana:")
print(weekly_stats)

# 5. GENERAR INSIGHTS
print("\\n=== Generando insights ===")

insights = []

if temp_btc_corr > 0.3:
    insights.append("Fuerte correlación positiva entre temperatura y precio de Bitcoin")
elif temp_btc_corr < -0.3:
    insights.append("Fuerte correlación negativa entre temperatura y precio de Bitcoin")
else:
    insights.append("No hay correlación significativa entre temperatura y Bitcoin")

# Mejores/peores días para Bitcoin
best_day = weekly_stats['bitcoin_price'].idxmax()
worst_day = weekly_stats['bitcoin_price'].idxmin()

insights.append(f"Mejor día para Bitcoin: {best_day} (${weekly_stats.loc[best_day, 'bitcoin_price']:,.2f})")
insights.append(f"Peor día para Bitcoin: {worst_day} (${weekly_stats.loc[worst_day, 'bitcoin_price']:,.2f})")

# 6. EXPORTAR RESULTADOS
print("\\n=== Exportando resultados ===")

# Guardar datos procesados
df.to_csv('market_weather_data.csv', index=False)

# Guardar insights
insights_report = {
    "generated_at": datetime.now().isoformat(),
    "current_data": combined_data,
    "metrics": metrics,
    "insights": insights,
    "data_summary": {
        "total_records": len(df),
        "date_range": f"{df['date'].min()} to {df['date'].max()}",
        "avg_temperature": round(df['temperature'].mean(), 1),
        "avg_bitcoin_price": round(df['bitcoin_price'].mean(), 2)
    }
}

with open('market_weather_analysis.json', 'w') as f:
    json.dump(insights_report, f, indent=2)

print(f"Datos exportados:")
print(f"- CSV: market_weather_data.csv")
print(f"- JSON: market_weather_analysis.json")
print(f"- Registros procesados: {len(df)}")

print("\\n=== Pipeline completado ===")
""",
    "packages": ["requests", "pandas", "matplotlib"],
    "output_files": ["market_weather_data.csv", "market_weather_analysis.json"],
    "timeout": 180
})
```

## 🔧 Configuración Avanzada

### Configuración de Seguridad

```yaml
# security_config.yaml
security:
  sandbox:
    enabled: true
    user: python_executor
    home_dir: /opt/python_executor
    temp_dir: /opt/python_executor/temp
    
  resource_limits:
    max_execution_time: 300  # 5 minutos
    max_memory_mb: 1024      # 1GB
    max_disk_mb: 512         # 512MB
    max_output_size: 10MB    # 10MB
    
  network:
    isolation: true
    allowed_domains:
      - "pypi.org"
      - "files.pythonhosted.org"
      - "github.com"
      - "api.github.com"
    blocked_ports:
      - 22     # SSH
      - 23     # Telnet
      - 25     # SMTP
      
  python_restrictions:
    blocked_modules:
      - "os.system"
      - "subprocess.call"
      - "importlib"
    allowed_exceptions:
      - "ValueError"
      - "TypeError"
      - "KeyError"
```

### Configuración de Performance

```yaml
# performance_config.yaml
performance:
  execution:
    parallel_processing: true
    max_workers: 4
    batch_size: 10
    
  caching:
    package_cache: true
    package_cache_size: "2GB"
    result_cache: true
    result_cache_ttl: 3600
    
  optimization:
    enable_jit: false
    optimize_memory: true
    garbage_collection: "aggressive"
    cache_dependencies: true
    
  monitoring:
    memory_tracking: true
    cpu_monitoring: true
    execution_tracing: false
    performance_metrics: true
```

## 📊 Monitoreo y Métricas

### Métricas de Performance

```python
# Métricas disponibles
metrics = {
    "execution_performance": {
        "execution_time": "time per code execution",
        "success_rate": "percentage of successful runs",
        "memory_usage": "peak memory consumption",
        "cpu_utilization": "CPU usage during execution"
    },
    "package_management": {
        "install_time": "time to install packages",
        "cache_hit_rate": "percentage of cached installations",
        "dependency_resolution_time": "time to resolve dependencies",
        "package_size": "size of installed packages"
    },
    "resource_usage": {
        "temp_storage": "temporary file usage",
        "network_bandwidth": "bandwidth consumption",
        "disk_io": "read/write operations",
        "file_count": "number of files created"
    },
    "code_quality": {
        "lint_errors": "number of linting errors",
        "test_coverage": "percentage of test coverage",
        "complexity_score": "cyclomatic complexity",
        "security_issues": "security vulnerabilities found"
    }
}
```

### Dashboard de Monitoreo

Las métricas están disponibles en:
- **Execution Dashboard**: Tiempo de ejecución, éxito, memoria
- **Package Management**: Instalaciones, cache, dependencias
- **Resource Usage**: Almacenamiento, red, archivos
- **Code Quality**: Linting, tests, seguridad

## 🚨 Troubleshooting

### Problemas Comunes

#### Error: Package installation failed

```python
# Verificar instalación de paquetes
package_check = requests.post(base_url, headers=headers, json={
    "agent": "python_executor",
    "action": "install_packages_debug",
    "packages": ["problematic-package"],
    "debug": True,
    "force_reinstall": True
})

print("Debug de instalación:", package_check.json())
```

#### Error: Memory limit exceeded

```python
# Configurar para optimización de memoria
memory_optimized_execution = {
    "agent": "python_executor",
    "action": "execute_with_optimization",
    "code": "import gc; gc.collect()",
    "memory_optimization": {
        "chunk_processing": True,
        "streaming_mode": True,
        "garbage_collection": True
    },
    "memory_limit": "512MB"
}
```

#### Error: Timeout during execution

```python
# Aumentar timeout para operaciones largas
long_operation_config = {
    "agent": "python_executor",
    "action": "execute_long_operation",
    "code": "# Operación que toma tiempo",
    "timeout": 600,  # 10 minutos
    "progress_monitoring": True,
    "checkpoint_frequency": 100
}
```

### Debugging Avanzado

```bash
# Ver logs del agente
docker-compose logs python-executor-agent

# Habilitar debug detallado
export PYTHON_EXECUTOR_DEBUG=true
export PYTHON_EXECUTOR_LOG_LEVEL=DEBUG

# Verificar entorno
python -c "import sys; print(sys.path)"
pip list
```

## 🔒 Seguridad

### Medidas de Seguridad

1. **Sandbox Isolation**: Ejecución en usuario limitado
2. **Resource Limits**: CPU, memoria, disco, tiempo
3. **Network Isolation**: Solo dominios autorizados
4. **Module Restrictions**: Bloqueo de módulos peligrosos
5. **Output Sanitization**: Sanitización de salida

### Configuración de Seguridad

```python
# security_restrictions.py
SECURITY_RULES = {
    "blocked_operations": [
        "os.system",
        "subprocess.call",
        "eval",
        "exec",
        "__import__"
    ],
    "safe_modules": [
        "math",
        "random",
        "datetime",
        "json",
        "csv",
        "pandas",
        "numpy"
    ],
    "network_restrictions": {
        "allowed_protocols": ["https"],
        "blocked_ports": [22, 23, 25, 135, 139, 445],
        "allowed_domains": ["*.python.org", "*.github.com"]
    }
}
```

## 📈 Optimización

### Performance Tips

1. **Virtual Environments**: Reutilizar entornos cuando sea posible
2. **Package Caching**: Cache de paquetes frecuentes
3. **Memory Management**: Garbage collection agresivo
4. **Chunk Processing**: Procesamiento en chunks para datos grandes
5. **Parallel Execution**: Paralelización cuando sea seguro

### Configuración de Optimización

```yaml
# optimization.yaml
optimization:
  environment_reuse: true
  package_pre_caching: true
  memory_efficient_processing: true
  parallel_safe_operations: true
  result_caching: true
  gc_frequency: "aggressive"
```

## 🎯 Casos de Uso Empresariales

### 1. Data Science Pipeline

```python
# Pipeline de ciencia de datos empresarial
ds_pipeline = {
    "data_sources": ["databases", "apis", "files"],
    "processing_steps": [
        "data_extraction",
        "cleaning_validation",
        "feature_engineering",
        "model_training",
        "evaluation_validation"
    ],
    "ml_models": ["classification", "regression", "clustering"],
    "outputs": ["predictions", "reports", "dashboards"],
    "quality": {
        "validation_rules": True,
        "data_lineage": True,
        "model_monitoring": True
    }
}
```

### 2. Financial Analysis

```python
# Sistema de análisis financiero
financial_analysis = {
    "data_sources": ["market_data", "company_reports", "news"],
    "analysis_types": [
        "portfolio_optimization",
        "risk_assessment",
        "sentiment_analysis"
    ],
    "outputs": [
        "investment_recommendations",
        "risk_reports",
        "market_insights"
    ],
    "compliance": {
        "audit_trail": True,
        "data_validation": True,
        "regulatory_reporting": True
    }
}
```

### 3. Automated Testing

```python
# Sistema de testing automatizado
automated_testing = {
    "test_types": ["unit", "integration", "performance"],
    "frameworks": ["pytest", "unittest", "selenium"],
    "coverage": {"target": "90%", "tracking": True},
    "reporting": {
        "detailed_reports": True,
        "trend_analysis": True,
        "quality_metrics": True
    },
    "integration": {
        "ci_cd": True,
        "slack_notifications": True,
        "jira_integration": True
    }
}
```

---

## 📞 Soporte

**Documentación API**: http://localhost:8000/docs#/Python%20Executor  
**Issues**: GitHub Issues en el repositorio del proyecto  
**Logs**: http://localhost:8000/logs/python-executor  
**Métricas**: http://localhost:3001 (Grafana dashboard)

---

**🚀 Estado**: **HERRAMIENTA REAL OPERATIVA**  
**📅 Última Actualización**: 2025-11-04  
**✅ Producción**: **READY FOR ENTERPRISE PYTHON EXECUTION**
