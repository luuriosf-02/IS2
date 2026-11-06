# Facturación electrónica

La app `apps.facturacion` emite una factura SIFEN cuando Stripe confirma el
pago de una operación de compra o venta de divisas. La factura se expresa en
PYG; la cantidad, moneda, tasa aplicada y referencia de la operación quedan en
la descripción del servicio facturado. Primero se llama a `calcular_de` y el DE
calculado se envía a `generar_de`.

El token se envía en el encabezado `Authentication-Token`, como prescribe la
API de Factura Segura. Configurar `FS_TOKEN`, `FS_API_URL` y, opcionalmente,
`FS_TIMEOUT_SECONDS` en el entorno de Django.

## Variables de emisor

Los nombres solicitados se leen literalmente desde el entorno:

```dotenv
dRucEm=
dVEmi=
iTipCont=
dNumTim=
dFeIniT=
dTelEmi=
cActEco1=
cActEco2=
dDesActEco1=
dDesActEco2=
```

El contrato SIFEN también exige datos que no estaban en la lista anterior. Se
leen con estos nombres adicionales; sus valores y códigos deben ser los
registrados para el emisor en Factura Segura/DNIT:

```dotenv
FS_D_NOM_EMI=
FS_D_DIR_EMI=
FS_D_NUM_CAS=
FS_C_DEP_EMI=
FS_D_DES_DEP_EMI=
FS_C_CIU_EMI=
FS_D_DES_CIU_EMI=
FS_D_EMAIL_E=
FS_D_EST=
FS_D_PUN_EXP=
FS_I_T_IMP=
FS_I_IND_PRES=
FS_I_AFEC_IVA=
FS_D_PROP_IVA=
FS_D_TASA_IVA=
FS_I_FOR_PRO_PA=
FS_I_TI_CONT_REC_FISICA=
FS_I_TI_CONT_REC_JURIDICA=
FS_I_DEN_TARJ_VISA=
FS_I_DEN_TARJ_MASTERCARD=
FS_I_DEN_TARJ_AMEX=
FS_I_DEN_TARJ_OTRA=
FS_I_TIP_TRA_COMPRA=
FS_I_TIP_TRA_VENTA=
FS_I_TI_OPE_B2B=
FS_I_TI_OPE_B2C=
DS_I_TI_DE_FACTURA=
DS_I_TI_DE_NOTA=
FS_I_NAT_REC_CONTRIBUYENTE=
FS_I_NAT_REC_NO_CONTRIBUYENTE=
FS_I_MOT_EMI_NOTA=
```

En particular, `FS_I_FOR_PRO_PA`, `FS_I_DEN_TARJ_VISA` (o la marca usada) y
las dos variables de actividad económica deben tener valores oficiales; sin
ellas el constructor detiene la emisión con el nombre de la variable faltante.

Al solicitar una vinculación se declara por cliente si es contribuyente. Esa
condición queda bloqueada después del primer envío. `iTipTra` usa la opción de
compra o venta de la operación; `iTiOpe` usa B2B para personas jurídicas y B2C
para personas físicas. Las facturas son el documento habitual; una nota de
crédito requiere el CDC de la factura original y `FS_I_MOT_EMI_NOTA`.

El cliente debe tener correo de facturación y documento válido. Se usa el campo
`email` del cliente, luego el correo de su creador o el de una vinculación
aprobada. La condición tributaria determina `iNatRec`: contribuyentes se envían
con RUC y dígito verificador; no contribuyentes se envían con `iTipIDRec=1` y
el número de cédula en `dNumIDRec`. El campo `tipo_persona` determina el código
`iTiContRec` configurado para persona física o jurídica.

## Emisión y reintentos

La numeración está separada por tipo de documento: facturas `0000285` a
`0000296`, y notas de crédito `0000097` a `0000108`. Cada serie se reserva con
bloqueo transaccional; si se agota, se detiene la emisión en vez de asignar un
número fuera del rango. Los números ya utilizados se saltan, no se reutilizan.

Desde el historial, un pago con factura aprobada puede reembolsarse totalmente
durante las 72 horas posteriores a `fecha_finalizacion`. La solicitud requiere
un motivo de 5 a 500 caracteres. Se reembolsa primero en Stripe y, si Stripe
confirma el reembolso, se emite la nota de crédito asociada al CDC de la factura
original. El `PaymentIntent`, el refund y su motivo se guardan para reintentar
consultas pendientes sin crear un segundo reembolso. Si falla la emisión fiscal
después de que Stripe confirme, contactar soporte antes de volver a solicitar;
el reembolso no se revierte automáticamente.

Cada transacción tiene como máximo un registro local de factura y un número de
documento de cada tipo, ambos con siete dígitos. Si Factura Segura devuelve CDC,
se conserva junto con el DE y la respuesta. Si una llamada falla, el pago permanece
confirmado y la factura queda marcada como error para revisión; no se reenvía
automáticamente porque un timeout puede ocurrir después de que Factura Segura
haya procesado la emisión. Consultar el estado con `get_estado_sifen` antes de
reintentar una emisión ambigua.