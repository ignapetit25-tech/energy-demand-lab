# Publicar Energy Demand Lab en GitHub Pages

La web está preparada para funcionar tanto en `https://USUARIO.github.io/REPOSITORIO/` como en un dominio propio. No necesita servidor de aplicaciones, claves de API ni servicios pagos de IA. Tablero e informe funcionan en el navegador con una instantánea de los archivos del proyecto.

## Primera publicación

1. Crear o elegir un repositorio de GitHub y subir **el proyecto completo** a su rama `main`, incluyendo `.github/workflows`. Conservar los archivos de datos y resultados necesarios para reproducirlo. No subir `.browser-temp` ni `_site`; están excluidos de Git.
2. En el repositorio, abrir **Settings → Pages → Build and deployment → Source → GitHub Actions**.
3. En **Actions**, abrir **Publish website** y pulsar **Run workflow**. También se ejecuta con cada nuevo cambio enviado a `main`.
4. El proceso verifica los resultados, construye `_site` y publica ese directorio. La dirección definitiva aparece en el despliegue `github-pages`.

GitHub Pages admite repositorios públicos con GitHub Free; la disponibilidad para repositorios privados depende del plan. Referencia oficial: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages

## Construcción y vista previa

Desde la raíz del proyecto:

```sh
python3 scripts/build_site.py
python3 -m http.server 8766 --bind 127.0.0.1 --directory _site
```

Abrir `http://127.0.0.1:8766/`. El generador comprueba enlaces internos y utiliza una lista explícita de archivos públicos. Las capturas de pruebas, los scripts, el historial Git y los archivos temporales no se incluyen en el artefacto web. Si el repositorio es público, su contenido versionado sí será visible por separado.

## Actualización

Editar y verificar el proyecto, luego enviar los cambios a `main`. La web se vuelve a construir. Esto **no descarga datos nuevos**: el corte sigue siendo agosto de 2026 hasta que se incorporen y validen nuevas fuentes. Los pronósticos congelados conservan su registro original.

Los botones de descarga e impresión funcionan en el sitio público. Los enlaces metodológicos apuntan a documentos Markdown incluidos en la publicación. No hay formularios, cuentas de usuario ni seguimiento de visitantes en esta versión.

## Estado de entrega

Configuración preparada y construcción local verificable. Un repositorio remoto, acceso de GitHub válido y Pages habilitado son necesarios para obtener la dirección pública. La preparación local por sí sola no publica la página.
