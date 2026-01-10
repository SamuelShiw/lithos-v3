# Lithos V3 — Sistema de gestión de costos mineros 💎

## Descripción

**Lithos V3** es una plataforma enfocada en la optimización y control de costos operativos en minería subterránea. Digitaliza la captura diaria de datos de campo y automatiza el cálculo de indicadores clave de desempeño (KPIs), reduciendo la dependencia de hojas de cálculo y acortando el tiempo entre la recolección de datos y la toma de decisiones.

## Características principales

- Captura y validación de reportes operativos diarios.
- Cálculo automático de KPIs financieros y operativos.
- Interfaz de usuario interactiva y accesible.
- Persistencia segura y escalable con Supabase (PostgreSQL).
- Arquitectura modular que facilita el mantenimiento y la extensibilidad.

## Arquitectura

- **Frontend**: Implementado en Streamlit para una experiencia web rápida y sencilla.
- **Backend / Lógica de negocio**: Módulos en Python que procesan datos y aplican reglas de negocio.
- **Persistencia**: Supabase (PostgreSQL) para almacenamiento relacional y control de permisos.

## Requisitos

- Python 3.9 o superior
- Cuenta activa en Supabase (para credenciales)
- Git

## Instalación y ejecución (local)

1. Clonar el repositorio:

```bash
git clone https://github.com/tu-usuario/lithos-v3.git
cd lithos-v3
```

2. Crear y activar un entorno virtual (recomendado):

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Configurar credenciales de Supabase:

Cree el archivo `.streamlit/secrets.toml` con las siguientes entradas:

```toml
[supabase]
url = "TU_SUPABASE_URL"
key = "TU_SUPABASE_KEY"
```

5. Iniciar la aplicación:

```bash
streamlit run app.py
```

## Estructura del proyecto

- `app.py` — Punto de entrada de la aplicación
- `pages/` — Vistas y pantallas de Streamlit
- `services/` — Lógica de servicios y orquestación
- `db/` — Cliente y repositorios para la base de datos
- `domain/` — Modelos y reglas de negocio
- `analytics/` — Módulos de generación de indicadores
- `ui/`, `views/` — Componentes de interfaz y vistas
- `requirements.txt` — Dependencias del proyecto

> Nota: Esta estructura es orientativa; consulte el código para detalles específicos.

## Seguridad

- No incluya credenciales en el código fuente. Use `.streamlit/secrets.toml` o variables de entorno para gestionar claves.
- Asegúrese de configurar reglas de acceso en Supabase para proteger los datos sensibles.

## Roadmap (prioridades)

- Integración de métricas en tiempo real.
- Dashboards personalizados por rol.
- Optimización de consultas y rendimiento en Supabase.
- Despliegue en la nube con pipelines CI/CD.

## Contribuciones

Las contribuciones son bienvenidas. Para colaborar por favor:

1. Haga fork del repositorio.
2. Cree una rama con la convención `feature/descripcion` o `fix/descripcion`.
3. Envíe un pull request describiendo los cambios y el motivo.

## Licencia

Este proyecto está bajo la licencia MIT. Consulte el archivo `LICENSE` para más información.

## Autor

**Jose Samuel Quispe Mamani** — Estudiante de Ingeniería de Software con especialización en Inteligencia Artificial

---
