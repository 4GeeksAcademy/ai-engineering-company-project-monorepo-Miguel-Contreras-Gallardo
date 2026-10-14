# 🔧 System Patterns — Convenciones del Proyecto

> **Última actualización:** 2026-09-23
> Patrones, convenciones y guías de estilo. Para la estructura del monorepo, ver `project-brief.md`.

---

## 🧠 Patrón de Agente Orquestador

El patrón central del proyecto es un **agente orquestador** que actúa como "director de orquesta" de todos los departamentos:

```
Usuario → Agente Orquestador → Tools/Skills → Acciones/APIs → Resultado
```

1. Recibe una solicitud en lenguaje natural
2. Identifica el departamento/dominio involucrado
3. Invoca la herramienta o skill correspondiente
4. Recopila resultados y responde

Cada departamento tendrá:
- **System prompt** en `agents/rules/` con contexto y reglas de negocio
- **Tools** en `agents/tools/` para acciones concretas
- **Skills** en `skills/` para capacidades reutilizables

---

## 🐍 Convenciones de Código

### Python
- Type hints obligatorios en todas las funciones
- Docstrings en formato Google style
- Nombres de variables y funciones en `snake_case`
- Clases en `PascalCase`
- Constantes en `UPPER_SNAKE_CASE`

### TypeScript
- Interfaces sobre types cuando sea posible
- `PascalCase` para interfaces/types
- `camelCase` para variables y funciones
- `UPPER_SNAKE_CASE` para constantes

### General
- Código fuente en **inglés**
- Comentarios y documentación de trabajo en **español**
- READMEs bilingües (español + inglés)

---

## 📝 Convenciones de Documentación

### Memory Bank
Los archivos en `memory-bank/` deben:
- Tener una cabecera con fecha de última actualización
- Usar emojis para mejorar legibilidad
- Mantenerse actualizados al final de cada sesión

### Archivos nuevos
- Cada subcarpeta nueva debe incluir un `README.md`
- El README debe explicar propósito, contenido y cómo usarlo

---

## 🚀 Ciclo de Trabajo por Sesión

1. **Leer** `memory-bank/active-context.md` y `memory-bank/progress.md`
2. **Actualizar** `active-context.md` con el objetivo de la sesión
3. **Trabajar** en las tareas planificadas
4. **Actualizar** `progress.md` con los logros
5. **Registrar** decisiones en `decisions.md` si aplica
6. **Actualizar** `active-context.md` al cierre

---

## 🔗 Referencias

- [Project Brief](project-brief.md)
- [Active Context](active-context.md)
- [Progress Log](progress.md)
- [Architecture Decisions](decisions.md)