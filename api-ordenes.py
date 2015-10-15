from suds.client import Client

import config
import urlparse
import urllib
import os
import json
import urllib2

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine(config.db_url)
# create a configured "Session" class
Session = sessionmaker(bind=engine)
# create a Session
session = Session()
Base = declarative_base()


class Orden(Base):
    __tablename__ = 'ordenes'
    orden_id = Column(Integer, primary_key=True, autoincrement='ignore_fk')
    nro_orden = Column(String(50))
    clase_orden = Column(String(100))
    descripcion = Column(String(100))
    ubic_tecnica = Column(String(100))
    ubic_tecnica_desc = Column(String(100))
    geo_x = Column(String(20))
    geo_y = Column(String(20))
    tipo_resultado = Column(String(100))
    fecha_creacion = Column(Date)
    fecha_ini_extremo = Column(Date)
    fecha_fin_extremo = Column(Date)
    calle = Column(String(100))
    altura = Column(String(10))
    clave_modelo = Column(String(50))
    clave_modelo_txt = Column(String(100))
    area_empresa = Column(String(10))
    status_usuario = Column(String(50))
    fecha_ult_modif = Column(Date)
    comuna = Column(String(2))

    def __repr__(self):
        return "<Orden(nro_orden='%s', clase_orden='%s', descripcion='%s', ubic_tecnica='%s', ubic_tecnica_desc='%s', geo_x='%s', geo_y='%s', fecha_creacion='%s', fecha_ini_extremo='%s', fecha_fin_extremo='%s', calle='%s', altura='%s', clave_modelo_txt='%s', status_operacion='%s', comuna='%s')>" % (self.nro_orden, self.clase_orden, self.descripcion, self.ubic_tecnica, self.ubic_tecnica_desc, self.geo_x, self.geo_y, self.fecha_creacion,
                                                                                                                                                                                                                                                                                                            self.fecha_ini_extremo, self.fecha_fin_extremo, self.calle, self.altura, self.clave_modelo_txt, self.status_operacion, self.comuna)

Base.metadata.create_all(engine, checkfirst=True)

url = urlparse.urljoin(
    'file:', urllib.pathname2url(config.wsdl_path))
client = Client(
    url, username=config.wsdl_username, password=config.wsdl_password)

desde = "20150823"
hasta = "20150831"
tipos_ordenes = ["ACRE", "ACME", "CARE", "CAME"]
modo = "CREACION"
columnas = ["NRO_ORDEN", "CLASE_ORDEN", "DESCRIPCION", "UBIC_TECNICA", "UBIC_TECNICA_DESC", "FECHA_CREACION", "FECHA_INI_EXTREMO",
            "FECHA_FIN_EXTREMO",  "CALLE", "ALTURA", "CLAVE_MODELO", "CLAVE_MODELO_TXT", "AREA_EMPRESA", "STATUS_USUARIO", "FECHA_ULT_MODIF"]


for tipo_orden in tipos_ordenes:
    result = client.service.si_gobabierto(tipo_orden, desde, hasta, modo)
    print result
    for record in result:
        new_orden = {}
        for columna in columnas:
            if record[columna] is not None:
                new_orden[columna.lower()] = record[columna].encode(
                    'utf8', 'ignore')
            else:
                new_orden[columna.lower()] = None
        direccion_list = new_orden[
            "ubic_tecnica_desc"].split("-")[0].split(" ")
        altura = direccion_list[-1]
        calle = " ".join(
            direccion_list[:-1]).replace(",", "").replace(" ", "%20")

        geocod = json.load(urllib2.urlopen(
            'http://ws.usig.buenosaires.gob.ar/rest/normalizar_y_geocodificar_direcciones?calle=' + calle + '&altura=' + altura + '&desambiguar=1'))
        if "Normalizacion" in geocod.keys():
            new_orden["geo_x"] = ""
            new_orden["geo_y"] = ""
            new_orden["tipo_resultado"] = geocod[
                "Normalizacion"]["TipoResultado"]
        if "GeoCodificacion" in geocod.keys():
            new_orden["geo_x"] = geocod["GeoCodificacion"]["x"]
            new_orden["geo_y"] = geocod["GeoCodificacion"]["y"]

        # comuna = "na"
        # try:
        #     res_comuna = json.load(urllib2.urlopen(
        #         'http://ws.usig.buenosaires.gob.ar/datos_utiles?calle=' + calle + '&altura=' + altura))
        # except ValueError:
        #     print "Calle y altura inexistentes"
        # else:
        #     print "Otro tipo de error ocurrio en la request"
        # print comuna

        ev = session.query(Orden).filter(Orden.nro_orden == new_orden[
            'nro_orden'], Orden.clave_modelo == new_orden['clave_modelo']).count()
        if not ev:
            # Add record to DB
            session.add(Orden(**new_orden))
            session.commit()
