import pydoc
import os

os.makedirs('docs', exist_ok=True)

# Generar documentación de código a texto plano
modulos = ['app.apps.clientes', 'app.apps.users', 'app.apps.dashboard']
with open('docs/documentacion_codigo.txt', 'w', encoding='utf-8') as f:
    f.write("DOCUMENTACION AUTOMATICA DEL CODIGO FUENTE\n\n")
    for mod in modulos:
        try:
            f.write(pydoc.plain(pydoc.render_doc(mod)))
            f.write("\n" + "="*50 + "\n")
        except Exception as e:
            f.write(f"Modulo {mod}: {e}\n")

print("Archivo docs/documentacion_codigo.txt generado con éxito.")