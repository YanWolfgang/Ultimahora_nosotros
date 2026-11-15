# nosotros-fotos

Repo para que Claude baje fotos libres de Wikimedia Commons
para los carruseles ÚLTIMA NOTICIA de NOSOTROS.

1. Claude hace push de `pedidos/<id>.txt` con una foto por renglón.
2. La Action `nosotros-fotos` las baja y deja `fotos/<id>/01.jpg…` y `fotos/<id>/meta.json`
   (autor, licencia, página) y mueve el pedido a `pedidos/hecho/`.
3. Claude hace pull y arma las láminas.
