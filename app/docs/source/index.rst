Documentación de Global Exchange
================================

Global Exchange es una plataforma para la gestión de clientes,
usuarios, vinculaciones, medios de pago, cajas, transacciones y facturación
electrónica.

La documentación siguiente fue generada a partir de los docstrings
del código fuente.

Aplicación de medios de pago
----------------------------

Modelos
~~~~~~~

.. automodule:: apps.payments.models
   :members:
   :undoc-members:
   :show-inheritance:

Formularios
~~~~~~~~~~~

.. automodule:: apps.payments.forms
   :members:
   :undoc-members:
   :show-inheritance:

Vistas
~~~~~~

.. automodule:: apps.payments.views
   :members:
   :undoc-members:
   :show-inheritance:

Administración
~~~~~~~~~~~~~~

.. automodule:: apps.payments.admin
   :members:
   :undoc-members:
   :show-inheritance:

Aplicación de clientes
----------------------

Modelos
~~~~~~~

.. automodule:: apps.clientes.models
   :members:
   :undoc-members:
   :show-inheritance:

Formularios
~~~~~~~~~~~

.. automodule:: apps.clientes.forms
   :members:
   :undoc-members:
   :show-inheritance:

Vistas
~~~~~~

.. automodule:: apps.clientes.views
   :members:
   :undoc-members:
   :show-inheritance:

Aplicación de usuarios
----------------------

Modelos
~~~~~~~

.. automodule:: apps.users.models
   :members:
   :undoc-members:
   :show-inheritance:

Formularios
~~~~~~~~~~~

.. automodule:: apps.users.forms
   :members:
   :undoc-members:
   :show-inheritance:

Vistas
~~~~~~

.. automodule:: apps.users.views
   :members:
   :undoc-members:
   :show-inheritance:

Aplicación de cajas
-------------------

Permite abrir y aceptar cajas, registrar movimientos y operaciones de cambio,
anular operaciones y realizar el cierre con el conteo de los importes por moneda.

.. automodule:: apps.cajas.models
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: apps.cajas.forms
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: apps.cajas.services
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: apps.cajas.views
   :members:
   :undoc-members:
   :show-inheritance:

Facturación electrónica
-----------------------

Integra Factura Segura para solicitar la emisión de facturas electrónicas de
las transacciones pagadas y registrar su CDC y estado. Desde el historial de
transacciones se pueden consultar los documentos asociados y descargar el
KuDE en PDF o el XML, una vez aprobados por SIFEN. Los documentos cancelados
o inutilizados no están disponibles para descarga.

Modelos
~~~~~~~

.. automodule:: apps.facturacion.models
   :members:
   :undoc-members:
   :show-inheritance:

Servicios de integración
~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: apps.facturacion.services
   :members:
   :undoc-members:
   :show-inheritance:

Vistas y descarga de documentos
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: apps.facturacion.views
   :members:
   :undoc-members:
   :show-inheritance:

Simulación y gestión de transacciones
-------------------------------------

El conversor permite simular la compra o venta de divisas y calcular el importe
según la cotización vigente. Con un cliente activo, la operación puede guardarse
como pendiente o confirmarse con un medio de pago activo. Al confirmar, se
verifica la cotización, se procesa el pago mediante Stripe y se solicita la
factura electrónica. El historial permite consultar las operaciones y sus
documentos asociados, retomar pagos pendientes y cancelar operaciones pendientes.

Conversor y cálculo de cotizaciones
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: apps.dashboard.views
   :members:
   :undoc-members:
   :show-inheritance:

Modelos de transacciones
~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: apps.transacciones.models
   :members:
   :undoc-members:
   :show-inheritance:

Vistas e historial de transacciones
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: apps.transacciones.views
   :members:
   :undoc-members:
   :show-inheritance:

Índices
-------

* :ref:`genindex`
* :ref:`modindex`
