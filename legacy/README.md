# Archivo histórico

Este directorio conserva **íntegro** el código de iteraciones anteriores del
proyecto. No se ha borrado nada: los archivos están completos, con su historial
de Git intacto (se movieron con `git mv`, no se recrearon).

Lo que **no** es: código en ejecución. Nada de aquí se importa, se sirve ni se
arranca. Está fuera de la superficie activa a propósito.

## Por qué se apartó

Estos directorios estaban en la raíz del repositorio, indistinguibles del código
vivo. Dos problemas concretos:

1. **39 archivos de producción fabricaban datos.** No eran mocks de test —era
   código que se presentaba como funcional y devolvía resultados inventados. El
   ejemplo más claro es `code/silhouettemcp_expanded_research.py`, un «Research
   Intelligence Agent» que genera números de patente, fechas y nombres de
   inventores con `random.choice()`:

   ```python
   patent_number = f"{random.choice(['US','EP','WO'])}{random.randint(1000000, 9999999)}..."
   "inventors": [{"name": f"Dr. {random.choice(['John','Mary','Carlos','Ana'])} ..."}]
   ```

   Quien ejecutara ese archivo obtenía patentes con aspecto plausible que no
   existen.

2. **Estaban huérfanos.** Ni `backend/`, ni `silhouettemcp_server.py`, ni
   `docker-compose.yml` importaban una sola línea de aquí. Eran 194 scripts
   sueltos con su propio `__main__`, restos de iteraciones previas.

Mantenerlos en la raíz significaba que cualquiera —persona o agente— podía
ejecutar uno y creerse el resultado.

## Qué hay

| Directorio | Archivos .py | de ellos tests | Líneas | Con datos fabricados | Otros archivos |
|---|---:|---:|---:|---:|---:|
| `code/` | 55 | 8 | 47,234 | 9 | 27 |
| `enterprise_testing_suite/` | 13 | 10 | 5,743 | 0 | 2 |
| `iris-agent/` | 0 | 0 | 0 | 0 | 34 |
| `iris-mcp-integration/` | 13 | 2 | 8,519 | 4 | 16 |
| `mcp-core-superior/` | 238 | 59 | 141,465 | 23 | 104 |
| `microsoft365-integration/` | 33 | 11 | 18,017 | 3 | 2 |
| `package/` | 1 | 0 | 1,079 | 0 | 6 |
| `silhouettemcp-dashboard/` | 0 | 0 | 0 | 0 | 4 |
| `src/` | 1 | 0 | 841 | 0 | 0 |
| **Total** | **354** | **90** | **222,898** | **39** | **195** |

Los 90 archivos de test usan `unittest.mock` de forma legítima: simular una
dependencia dentro de un test es ingeniería correcta, no una fabricación. El
problema eran los 39 de producción.

## Si necesita algo de aquí

No lo importe desde el código activo — hay una barrera en CI que lo impide, y
existe por una razón: reintroducir estos módulos reintroduce sus datos
inventados.

El camino correcto es **portarlo**: leer la idea, implementarla de verdad en
`backend/app/`, y cubrirla con un test que pueda fallar. Es lo que se hizo con
la memoria cognitiva (`silhouette-brain`), la matriz de debate y la jerarquía de
equipos, que vivían aquí como fachadas y ahora funcionan.

Al portar, aplique las tres reglas de `AGENTS.md`:

1. Un fallo debe parecer un fallo.
2. «Sin datos» es una respuesta válida.
3. Lo que no está en un test, no está hecho.

## Recuperar un archivo

Todo sigue en el historial de Git:

```bash
git log --follow -- legacy/code/nombre_del_archivo.py
git show <commit>:code/nombre_del_archivo.py
```
