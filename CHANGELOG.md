# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.1] - 2026-11-19

### Changed

- La importación de facturas se conecta directamente con la API de tu proveedor de IA, sin módulos adicionales
- El proveedor de IA viene creado al instalar: solo falta cargar la URL de la API y la clave

### Fixed

- Los asistentes del chat que usan herramientas ya no fallan con un error de mensajes de sistema

## [1.0.0] - 2026-11-12

### Added

- Importación de facturas de proveedor con IA desde un PDF o una imagen, que deja un borrador listo para revisar
- Lectura de facturas argentinas: CUIT del proveedor, letra del comprobante, punto de venta y número, alícuotas de IVA y percepciones
- Procesamiento con IA de una factura ya creada que tiene el PDF o la imagen adjunto
- Chat con IA dentro de Odoo, disponible solo para los usuarios habilitados
- Presentación e íconos de los módulos para la tienda de aplicaciones de Odoo
