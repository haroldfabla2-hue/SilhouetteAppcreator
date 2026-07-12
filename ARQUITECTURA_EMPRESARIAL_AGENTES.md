# Arquitectura Empresarial de Agentes (AEA)

## 1. Visión General

Esta propuesta documenta la evolución de la arquitectura del sistema hacia un modelo jerárquico y basado en dominios, denominado Arquitectura Empresarial de Agentes (AEA). La visión, inspirada por el usuario, es estructurar la colaboración de los agentes de una manera análoga a una organización empresarial, con equipos especializados, líderes de equipo y una dirección general.

Este enfoque reemplaza un modelo de orquestación plano por una jerarquía que mejora la escalabilidad, la modularidad y la claridad en la asignación de tareas.

## 2. Estructura Jerárquica

La AEA se compone de cuatro niveles principales:

1.  **Nivel 4: Orquestador General (CEO):**
    *   **Función:** Es el punto de entrada principal para las solicitudes del usuario. Su única responsabilidad es analizar el objetivo general y delegarlo al "Líder de Equipo" más apropiado. No se involucra en la planificación detallada.
    *   **Ejemplo:** Si el usuario pide "Desarrolla una nueva API para el login", el Orquestador General enruta esta tarea directamente al `Líder del Equipo de Desarrollo de Software`.

2.  **Nivel 3: Líderes de Equipo (Gerentes de Departamento):**
    *   **Función:** Son agentes especializados en un dominio de negocio (ej. Marketing, Desarrollo, Análisis de Datos). Encapsulan la lógica de **razonamiento y planificación** para su área.
    *   Reciben un objetivo del Orquestador General, lo descomponen en un plan detallado de subtareas y las asignan a los Agentes Ejecutores de su equipo.
    *   Supervisan la ejecución, gestionan la comunicación interna del equipo y reportan el resultado consolidado al Orquestador General.

3.  **Nivel 2: Agentes Ejecutores (Trabajadores Especializados):**
    *   **Función:** Son los agentes que realizan el trabajo práctico. Cada uno está especializado en el uso de una o varias herramientas específicas (Git, Playwright, SQL, etc.).
    *   Reciben órdenes claras de su Líder de Equipo y las ejecutan.
    *   **Ejemplo:** Dentro del Equipo de Desarrollo, habría agentes como `GitAgent`, `PythonExecutorAgent`, `DatabaseAgent`.

4.  **Nivel 1: Herramientas (Tools):**
    *   **Función:** Son las librerías, APIs y comandos subyacentes que los Agentes Ejecutores utilizan para interactuar con el mundo exterior (ej. la API de GitHub, la CLI de `psql`).

## 3. Flujo de Trabajo

Un ejemplo de flujo de trabajo para la tarea "Crear un reporte de ventas trimestral":

1.  **Usuario -> Orquestador General:** "Genera el reporte de ventas del último trimestre y envíalo por correo".
2.  **Orquestador General -> Líder de Equipo de Análisis de Datos:** El Orquestador identifica que esta es una tarea de análisis y la delega al líder correspondiente.
3.  **Líder de Equipo de Análisis de Datos (Planifica):**
    *   **Paso 1:** Obtener los datos de ventas de la base de datos.
    *   **Paso 2:** Analizar los datos y generar las visualizaciones.
    *   **Paso 3:** Redactar el resumen del reporte.
    *   **Paso 4:** Enviar el reporte por correo.
4.  **Líder de Equipo (Delega a Ejecutores):**
    *   Asigna el Paso 1 al `DatabaseAgent`.
    *   Asigna el Paso 2 al `DataAnalysisAgent` (que usa `pandas`, `matplotlib`).
    *   Asigna el Paso 3 al `ContentCreatorAgent`.
    *   Asigna el Paso 4 al `EmailAgent`.
5.  **Agentes Ejecutores -> Líder de Equipo:** Cada agente completa su tarea y devuelve el resultado a su líder.
6.  **Líder de Equipo -> Orquestador General:** El líder consolida los resultados, arma el reporte final y notifica al Orquestador que la tarea ha sido completada.
7.  **Orquestador General -> Usuario:** "El reporte de ventas ha sido generado y enviado."

## 4. Ventajas de este Modelo

*   **Escalabilidad:** Es mucho más fácil añadir nuevas capacidades. Para añadir un dominio nuevo (ej. "Recursos Humanos"), solo necesitamos crear un nuevo `Líder de Equipo de RRHH` y sus correspondientes agentes ejecutores, sin modificar el resto del sistema.
*   **Modularidad y Cohesión:** Cada equipo es un módulo autocontenido con una responsabilidad clara, lo que simplifica el desarrollo y el mantenimiento.
*   **Paralelismo Eficiente:** El Orquestador General puede delegar tareas a múltiples equipos para que trabajen en paralelo en objetivos complejos que abarcan varios dominios.
*   **Claridad y Organización:** La estructura es intuitiva y refleja un modelo mental probado para la división del trabajo.

## 5. Plan de Implementación

La transición a la AEA se realizará de forma iterativa:

1.  **Definir los Equipos:** Se crearán formalmente los equipos iniciales basados en los patrones de agentes existentes (Desarrollo, Marketing, Análisis, etc.).
2.  **Crear el primer Líder de Equipo:** Se desarrollará el primer agente `TeamLeader`, probablemente para el "Equipo de Desarrollo de Software", encapsulando la lógica de razonamiento y planificación.
3.  **Refactorizar el Orquestador General:** Se modificará el orquestador principal para que delegue las tareas de desarrollo a este nuevo líder.
4.  **Iterar:** Se replicará el patrón para los demás equipos, creando un `Líder de Equipo` para cada dominio de negocio.
