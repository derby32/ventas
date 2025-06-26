# Sistema de Ventas para Boliche

Este proyecto contiene un script en Python que implementa una base de datos local usando SQLite para gestionar las ventas de un boliche. Permite crear usuarios, roles, manejar stock general y de barras, registrar recetas y realizar ventas.

## Requisitos

- Python 3.12 (o compatible)
- No necesita dependencias externas.

## Uso rápido

1. Inicializar la base de datos:
   ```bash
   python3 app.py setup
   ```
2. Crear roles, usuarios, barras, ingredientes y productos:
   ```bash
   python3 app.py add-role cajero
   python3 app.py add-user juan secret cajero
   python3 app.py add-bar barra1
   python3 app.py add-ingredient vodka litros
   python3 app.py add-product "Trago de vodka" 5.0
   ```
3. Definir receta del producto (por ejemplo, 50 ml de vodka):
   ```bash
   python3 app.py add-recipe "Trago de vodka" vodka 0.05
   ```
4. Ingresar stock al almacén general y transferir a la barra:
   ```bash
   python3 app.py stock-in vodka 10.0
   python3 app.py transfer-stock barra1 vodka 1.0
   ```
5. Registrar una venta:
   ```bash
   python3 app.py sale "Trago de vodka" barra1 juan
   ```
   El comando mostrará un JSON con el identificador y el código hexadecimal de la venta.
6. Cuando la barra entregue el producto puede marcar la venta como entregada usando el código hexadecimal:
   ```bash
   python3 app.py scan <codigo> barra1
   ```

Consulte `python3 app.py --help` para ver todas las opciones disponibles.
