from calculator_functions import *
from flask import Flask, jsonify, request, session, redirect, url_for
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import pandas as pd
from datetime import datetime
import psycopg2
import plotly.express as px
import json
import plotly.graph_objects as go
from key import usuario,contrasena
import os

app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = 's3cr3t0'
#------------------------------------------------------------Conectamos y sacamos los datos de la database---------------------------------------------------------

db_params = {
    'host': '34.78.249.103',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'cristian99'
}

"""db_params = {
    'host': 'localhost',
    'database': 'testeo',
    'user': 'postgres',
    'password': 'planta'
}"""

conn = psycopg2.connect(**db_params)
cursor = conn.cursor()

consulta_fixed = "SELECT * FROM fixed_price"
consulta_indexed = "SELECT * FROM indexed_price"
consulta_power = "SELECT * FROM indexed_price_power"

df_fixed = pd.read_sql_query(consulta_fixed, conn)
index_price = pd.read_sql_query(consulta_indexed, conn)
index_power = pd.read_sql_query(consulta_power, conn)
index_price_anual = index_price.copy()
index_price_power_anual = index_power.copy()

cursor.close()
conn.close()

"""df_fixed = pd.read_csv("../data/processed/fixed_price.csv")
index_price = pd.read_csv("../data/processed/indexed_price.csv")
index_power = pd.read_csv("../data/processed/indexed_price_power.csv")

df_fixed.columns = df_fixed.columns.str.lower()
index_price.columns = index_price.columns.str.lower()
index_power.columns = index_power.columns.str.lower()

index_price_anual = index_price.copy()
index_price_power_anual = index_power.copy()"""

#-------------------------------------------------------------CREAR GRAFICA-------------------------------------------------------

#-------------------------------------------------------------MENSUAL FIJO--------------------------------------------------------

#--------------------------------------------------------Mensual indexado------------------------------------------------------------------------

#------------------------------------------------------------ANUAL FIJO-----------------------------------------------------------------

#-------------------------------------------------------ANUAL INDEXADO----------------------------------------------------

#----------------------------------------------------FUNCIÓN WEBSCRAPING-------------------------------------------------------------------------------------------------------------------------------

#-------------------------------------------------------CREAMOS APP----------------------------------------------------


@app.route('/', methods=['GET'])
def home():
    return "<h1>Desafío de tripulaciones, grupo 2 (API Data homepage)</p>"


#---------------------------------------------------------PRIMER ENDPOINT------------------------------------------------


# 1./anualdata: recibe un CUPS, realiza el webscraping y devuelve los datos anuales
@app.route('/anualdata', methods=['GET'])
def anual_data():
    CUPS_input = request.args.get('CUPS_input', '')
    datos_anuales=webscraping(CUPS_input)
    session["datos"] = datos_anuales
    return datos_anuales
#----------------------------------------------------------SEGUNDO ENDPOINT----------------------------------------------------------

# 2./proposal: recibe los datos de factura, datos anuales, la compañía, modelo, etc, realiza los cálculos y devuelve todos los datos de la propuesta en concreto
@app.route('/proposal', methods=['GET'])
def proposal():
    
    Tipo_consumo_form = request.args.get('Tipo_consumo')
    Metodo_form = request.args.get('Metodo')
    cons_P1_form = float(request.args.get('cons_P1', 0))
    cons_P2_form = float(request.args.get('cons_P2', 0))
    cons_P3_form = float(request.args.get('cons_P3', 0))
    precio_P1_form = float(request.args.get('precio_P1', 0))
    precio_P2_form = float(request.args.get('precio_P2', 0))
    precio_P3_form = float(request.args.get('precio_P3', 0))
    descuento_form = float(request.args.get('descuento', 0))
    descuento_potencia_form = float(request.args.get('descuento_potencia', 0))
    potencia_contratada_P1_form = float(request.args.get('potencia_contratada_P1', 0))
    potencia_contratada_P2_form = float(request.args.get('potencia_contratada_P2', 0))
    dias_form = float(request.args.get('dias', 0))
    precio_potencia_dia_P1_form = float(request.args.get('precio_potencia_dia_P1', 0))
    precio_potencia_dia_P2_form = float(request.args.get('precio_potencia_dia_P2', 0))
    impuesto_electrico_form = float(request.args.get('impuesto_electrico', 0))
    alquiler_equipo_form = float(request.args.get('alquiler_equipo', 0))
    otros_form = float(request.args.get('otros', 0))
    CIA_form = request.args.get('CIA')
    producto_CIA_form = request.args.get('producto_CIA')
    mes_facturacion_form = request.args.get('mes_facturacion') #EJEMPLO FORMATO 2023-11-29, DEBE SER ASI, PORQUE SI NO NO SE CONVIERTE BIEN.
    FEE_form = request.args.get('FEE')
    IVA_form = float(request.args.get('IVA', 0))
    mes_facturacion_form = datetime.strptime(mes_facturacion_form, '%Y-%m-%d')

    datos_anuales = session["datos"]
    datos_anuales_objeto = json.loads(datos_anuales)
    df_anuales = pd.DataFrame(datos_anuales_objeto,index=[0])
    

    cons_anual_P1_scrap = df_anuales.at[0, "Consumo anual P1"]
    cons_anual_P2_scrap = df_anuales.at[0,"Consumo anual P2"]
    cons_anual_P3_scrap = df_anuales.at[0,"Consumo anual P3"]
    potencia_contratada_anual_P1_scrap = df_anuales.at[0,"P1"]
    potencia_contratada_anual_P2_scrap = df_anuales.at[0,"P2"]
    Distribuidora_scrap = df_anuales.at[0,"Distribuidora"] #PARA FULLSTACK

    #-----------------------------------------------Filtro mensual/anual fija------------------------------------------------------------------------
    #mensual utiliza la fixed price, la filtramos para peninsula y 2.0
    condiciones_sistema_tarifa = (df_fixed['sistema'] == 'PENINSULA') & (df_fixed['tarifa'] == '2.0TD')# & (df['PRODUCTO'] == 'FIJO')
    df_filtrado = df_fixed[condiciones_sistema_tarifa] # aplicar el filtro

    #----------------------------------------------Filtro mensual indexed energia--------------------------------------------------------------------
    #indexed price filtros
    fecha_actual = datetime.now()
    index_price2=index_price.copy()
    index_price2['diferencia'] = (fecha_actual - index_price2['mes']).abs() # diferencia entre cada fecha 'MES' y la fecha actual
    condicion = (index_price2['sistema'] == 'PENINSULA') & (index_price2['tarifa'] == '2.0TD') # filtrar para obtener las filas más cercanas por CIA y con SISTEMA y TARIFA específicos
    filas_mas_cercanas = index_price2[condicion].groupby(['sistema', 'tarifa', 'cia']).apply(lambda x: x[x['diferencia'] == x['diferencia'].min()])
    filas_mas_cercanas = filas_mas_cercanas.drop('diferencia', axis=1).reset_index(drop=True)
    filas_mas_cercanas.dropna(axis=0,inplace=True)

    #----------------------------------------------Filtro mensual indexed potencia--------------------------------------------------------------------
    #indexed price power filtros
    condiciones_sistema_tarifa = (index_power['sistema'] == 'PENINSULA') & (index_power['tarifa'] == '2.0TD') & (index_power['producto'] == 'INDEXADO')
    condiciones_cias = index_power['cia'].isin(['ACCIONA', 'AEQ', 'CANDELA', 'FACTOR', 'IGNIS', 'MAX'])
    index_power_filtrado = index_power[condiciones_sistema_tarifa & condiciones_cias]

    #----------------------------------------------Filtro anual indexed energia--------------------------------------------------------------------
    # Calcula la fecha máxima para cada combinación única de Sistema, Tarifa, Compañía y Fee
    fecha_max_por_grupo = index_price_anual.groupby(['sistema', 'tarifa', 'cia', 'fee'])['mes'].max()

    # Filtra los datos para los últimos 12 meses para cada grupo
    df_ult_12_meses = pd.DataFrame()
    for index, fecha_max in fecha_max_por_grupo.items():
        filtro_grupo = (
            (index_price_anual['sistema'] == index[0]) &
            (index_price_anual['tarifa'] == index[1]) &
            (index_price_anual['cia'] == index[2]) &
            (index_price_anual['fee'] == index[3]) &
            (index_price_anual['mes'] > fecha_max - pd.DateOffset(months=12))
        )
        df_ult_12_meses = pd.concat([df_ult_12_meses, index_price_anual[filtro_grupo]])

    # Calcula las medias para cada conjunto único de Sistema, Tarifa, Compañía y Fee
    df_medias_index_12 = df_ult_12_meses.groupby(['sistema', 'tarifa', 'cia', 'fee']).agg({
        'p1': 'mean',
        'p2': 'mean',
        'p3': 'mean',
        'p4': 'mean',
        'p5': 'mean',
        'p6': 'mean'
    }).reset_index()

    # Puedes renombrar las columnas si es necesario
    #df_medias_index_12.columns = ['SISTEMA', 'TARIFA', 'CIA', 'FEE', 'P1M_E', 'P2M_E', 'P3M_E', 'P4M_E', 'P5M_E', 'P6M_E']
    condicion = (df_medias_index_12['sistema'] == 'PENINSULA') & (df_medias_index_12['tarifa'] == '2.0TD') # filtrar para obtener las filas más cercanas por CIA y con SISTEMA y TARIFA específicos
    df_medindx12_penins_2 = df_medias_index_12[condicion]#.groupby(['SISTEMA', 'TARIFA', 'CIA'])#.apply(lambda x: x[x['diferencia'] == x['diferencia'].min()])
    df_medindx12_penins_2.dropna(axis=0,inplace=True)

    #----------------------------------------------Filtro anual indexed potencia--------------------------------------------------------------------
    #indexed price power filtros
    condiciones_sistema_tarifa_anual = (index_price_power_anual['sistema'] == 'PENINSULA') & (index_price_power_anual['tarifa'] == '2.0TD') & (index_price_power_anual['producto'] == 'INDEXADO')
    condiciones_cias_anual = index_price_power_anual['cia'].isin(['ACCIONA', 'AEQ', 'CANDELA', 'FACTOR', 'IGNIS', 'MAX'])
    index_power_filtrado_anual = index_price_power_anual[condiciones_sistema_tarifa_anual & condiciones_cias_anual]

    #----------------------------------------Calculadora de consumo mensual----------------------------------------------
    if Tipo_consumo_form=='Consumo_mensual':
        #------------------------------------------Mensual Fijo-------------------------------------------------------
        if Metodo_form=='Fijo':
            # funciones de cálculo importes
            opcion_barata_mens_fijo = encontrar_opcion_mas_barata_mens_fijo(2,df_filtrado,cons_P1_form,cons_P2_form,cons_P3_form,precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_P1_form, potencia_contratada_P2_form, dias_form, precio_potencia_dia_P1_form, precio_potencia_dia_P2_form, descuento_form, descuento_potencia_form,impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form)
            opcion_barata_anual_fijo = encontrar_opcion_mas_barata_anual_fijo(2,df_filtrado,cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap, precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_anual_P1_scrap,potencia_contratada_anual_P2_scrap,precio_potencia_dia_P1_form,precio_potencia_dia_P2_form,descuento_form, descuento_potencia_form, impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form)
            
            json1 = json.loads(opcion_barata_mens_fijo)
            json2 = json.loads(opcion_barata_anual_fijo)

            # Combina los dos conjuntos de datos
            data_combinado = json1 + json2

            # Convierte el resultado de vuelta a una cadena JSON
            opcion_barata = json.dumps(data_combinado, indent=2)
            
            
            return opcion_barata
        
        #------------------------------------------Mensual Indexado--------------------------------------------------
        elif Metodo_form=='Indexado':
            opcion_barata_mens_index = encontrar_opcion_mas_barata_mens_index(2,filas_mas_cercanas,index_power_filtrado,cons_P1_form,cons_P2_form,cons_P3_form,precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_P1_form, potencia_contratada_P2_form, dias_form, precio_potencia_dia_P1_form, precio_potencia_dia_P2_form, descuento_form,descuento_potencia_form, impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form)
            return opcion_barata_mens_index

#-------------------------------------------------Calculadora Consumo Anual--------------------------------------------------------------
    elif Tipo_consumo_form=='Consumo_anual':
        

        #---------------------------------------------------------Anual Fijo----------------------------------------------------------------
        if Metodo_form=='Fijo':
            opcion_barata_mens_fijo = encontrar_opcion_mas_barata_mens_fijo(2,df_filtrado,cons_P1_form,cons_P2_form,cons_P3_form,precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_P1_form, potencia_contratada_P2_form, dias_form, precio_potencia_dia_P1_form, precio_potencia_dia_P2_form, descuento_form, descuento_potencia_form,impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form)
            opcion_barata_anual_fijo = encontrar_opcion_mas_barata_anual_fijo(2,df_filtrado,cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap, precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_anual_P1_scrap,potencia_contratada_anual_P2_scrap,precio_potencia_dia_P1_form,precio_potencia_dia_P2_form,descuento_form, descuento_potencia_form, impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form)
            
            json1 = json.loads(opcion_barata_mens_fijo)
            json2 = json.loads(opcion_barata_anual_fijo)

            # Combina los dos conjuntos de datos
            data_combinado = json1 + json2

            # Convierte el resultado de vuelta a una cadena JSON
            opcion_barata = json.dumps(data_combinado, indent=2)

            return opcion_barata
        #--------------------------------------------------------Anual indexado-------------------------------------------------------------
        elif Metodo_form=='Indexado':
            opcion_barata_anual_index=encontrar_opcion_mas_barata_anual_index(2,df_medindx12_penins_2,index_power_filtrado_anual,cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap,precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_anual_P1_scrap,potencia_contratada_anual_P2_scrap,precio_potencia_dia_P1_form,precio_potencia_dia_P2_form,descuento_form, descuento_potencia_form, impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form)
            return opcion_barata_anual_index

# # 3./proposals/chart: recibe los datos de factura, datos anuales y calcula los 5 mejores resultados, devuelve la gráfica con los % de ahorro de cada compañía y el ahorro total (€)
#----------------------------------------------------------TERCER ENDPOINT----------------------------------------------------------
@app.route('/proposals/chart', methods=['GET'])
def proposalschart(): #tipo_consumo: mensual o anual; metodo: fijo o indexado
    
    Tipo_consumo_form = request.args.get('Tipo_consumo')
    Metodo_form = request.args.get('Metodo')
    cons_P1_form = float(request.args.get('cons_P1', 0))
    cons_P2_form = float(request.args.get('cons_P2', 0))
    cons_P3_form = float(request.args.get('cons_P3', 0))
    precio_P1_form = float(request.args.get('precio_P1', 0))
    precio_P2_form = float(request.args.get('precio_P2', 0))
    precio_P3_form = float(request.args.get('precio_P3', 0))
    descuento_form = float(request.args.get('descuento', 0))
    descuento_potencia_form = float(request.args.get('descuento_potencia', 0))
    potencia_contratada_P1_form = float(request.args.get('potencia_contratada_P1', 0))
    potencia_contratada_P2_form = float(request.args.get('potencia_contratada_P2', 0))
    dias_form = float(request.args.get('dias', 0))
    precio_potencia_dia_P1_form = float(request.args.get('precio_potencia_dia_P1', 0))
    precio_potencia_dia_P2_form = float(request.args.get('precio_potencia_dia_P2', 0))
    impuesto_electrico_form = float(request.args.get('impuesto_electrico', 0))
    alquiler_equipo_form = float(request.args.get('alquiler_equipo', 0))
    otros_form = float(request.args.get('otros', 0))
    CIA_form = request.args.get('CIA')
    producto_CIA_form = request.args.get('producto_CIA')
    mes_facturacion_form = request.args.get('mes_facturacion') #EJEMPLO FORMATO 2023-11-29, DEBE SER ASI, PORQUE SI NO NO SE CONVIERTE BIEN.
    FEE_form = request.args.get('FEE')
    IVA_form = float(request.args.get('IVA', 0))
    mes_facturacion_form = datetime.strptime(mes_facturacion_form, '%Y-%m-%d')

    datos_anuales = session["datos"]
    datos_anuales_objeto = json.loads(datos_anuales)
    df_anuales = pd.DataFrame(datos_anuales_objeto,index=[0])
    
    cons_anual_P1_scrap = df_anuales.at[0, "Consumo anual P1"]
    cons_anual_P2_scrap = df_anuales.at[0,"Consumo anual P2"]
    cons_anual_P3_scrap = df_anuales.at[0,"Consumo anual P3"]
    potencia_contratada_anual_P1_scrap = df_anuales.at[0,"P1"]
    potencia_contratada_anual_P2_scrap = df_anuales.at[0,"P2"]
    Distribuidora_scrap = df_anuales.at[0,"Distribuidora"] #PARA FULLSTACK

    #-----------------------------------------------Filtro mensual/anual fija------------------------------------------------------------------------
    #mensual utiliza la fixed price, la filtramos para peninsula y 2.0
    condiciones_sistema_tarifa = (df_fixed['sistema'] == 'PENINSULA') & (df_fixed['tarifa'] == '2.0TD')# & (df['PRODUCTO'] == 'FIJO')
    df_filtrado = df_fixed[condiciones_sistema_tarifa] # aplicar el filtro

    #----------------------------------------------Filtro mensual indexed energia--------------------------------------------------------------------
    #indexed price filtros
    fecha_actual = datetime.now()
    index_price2=index_price.copy()
    index_price2['diferencia'] = (fecha_actual - index_price2['mes']).abs() # diferencia entre cada fecha 'MES' y la fecha actual
    condicion = (index_price2['sistema'] == 'PENINSULA') & (index_price2['tarifa'] == '2.0TD') # filtrar para obtener las filas más cercanas por CIA y con SISTEMA y TARIFA específicos
    filas_mas_cercanas = index_price2[condicion].groupby(['sistema', 'tarifa', 'cia']).apply(lambda x: x[x['diferencia'] == x['diferencia'].min()])
    filas_mas_cercanas = filas_mas_cercanas.drop('diferencia', axis=1).reset_index(drop=True)
    filas_mas_cercanas.dropna(axis=0,inplace=True)

    #----------------------------------------------Filtro mensual indexed potencia--------------------------------------------------------------------
    #indexed price power filtros
    condiciones_sistema_tarifa = (index_power['sistema'] == 'PENINSULA') & (index_power['tarifa'] == '2.0TD') & (index_power['producto'] == 'INDEXADO')
    condiciones_cias = index_power['cia'].isin(['ACCIONA', 'AEQ', 'CANDELA', 'FACTOR', 'IGNIS', 'MAX'])
    index_power_filtrado = index_power[condiciones_sistema_tarifa & condiciones_cias]

    #----------------------------------------------Filtro anual indexed energia--------------------------------------------------------------------
    # Calcula la fecha máxima para cada combinación única de Sistema, Tarifa, Compañía y Fee
    fecha_max_por_grupo = index_price_anual.groupby(['sistema', 'tarifa', 'cia', 'fee'])['mes'].max()

    # Filtra los datos para los últimos 12 meses para cada grupo
    df_ult_12_meses = pd.DataFrame()
    for index, fecha_max in fecha_max_por_grupo.items():
        filtro_grupo = (
            (index_price_anual['sistema'] == index[0]) &
            (index_price_anual['tarifa'] == index[1]) &
            (index_price_anual['cia'] == index[2]) &
            (index_price_anual['fee'] == index[3]) &
            (index_price_anual['mes'] > fecha_max - pd.DateOffset(months=12))
        )
        df_ult_12_meses = pd.concat([df_ult_12_meses, index_price_anual[filtro_grupo]])

    # Calcula las medias para cada conjunto único de Sistema, Tarifa, Compañía y Fee
    df_medias_index_12 = df_ult_12_meses.groupby(['sistema', 'tarifa', 'cia', 'fee']).agg({
        'p1': 'mean',
        'p2': 'mean',
        'p3': 'mean',
        'p4': 'mean',
        'p5': 'mean',
        'p6': 'mean'
    }).reset_index()

    # Puedes renombrar las columnas si es necesario
    #df_medias_index_12.columns = ['SISTEMA', 'TARIFA', 'CIA', 'FEE', 'P1M_E', 'P2M_E', 'P3M_E', 'P4M_E', 'P5M_E', 'P6M_E']
    condicion = (df_medias_index_12['sistema'] == 'PENINSULA') & (df_medias_index_12['tarifa'] == '2.0TD') # filtrar para obtener las filas más cercanas por CIA y con SISTEMA y TARIFA específicos
    df_medindx12_penins_2 = df_medias_index_12[condicion]#.groupby(['SISTEMA', 'TARIFA', 'CIA'])#.apply(lambda x: x[x['diferencia'] == x['diferencia'].min()])
    df_medindx12_penins_2.dropna(axis=0,inplace=True)

    #----------------------------------------------Filtro anual indexed potencia--------------------------------------------------------------------
    #indexed price power filtros
    condiciones_sistema_tarifa_anual = (index_price_power_anual['sistema'] == 'PENINSULA') & (index_price_power_anual['tarifa'] == '2.0TD') & (index_price_power_anual['producto'] == 'INDEXADO')
    condiciones_cias_anual = index_price_power_anual['cia'].isin(['ACCIONA', 'AEQ', 'CANDELA', 'FACTOR', 'IGNIS', 'MAX'])
    index_power_filtrado_anual = index_price_power_anual[condiciones_sistema_tarifa_anual & condiciones_cias_anual]

    #----------------------------------------Calculadora de consumo mensual----------------------------------------------
    if Tipo_consumo_form=='Consumo_mensual':
        #------------------------------------------Mensual Fijo-------------------------------------------------------
        if Metodo_form=='Fijo':
            # funciones de cálculo importes

            opciones_baratas_mens_fijo, opciones_grafica_mens = encontrar_opcion_mas_barata_mens_fijo(3,df_filtrado,cons_P1_form,cons_P2_form,cons_P3_form,precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_P1_form, potencia_contratada_P2_form, dias_form, precio_potencia_dia_P1_form, precio_potencia_dia_P2_form, descuento_form, descuento_potencia_form,impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form)
            opciones_baratas_anual_fijo, opciones_grafica_anual = encontrar_opcion_mas_barata_anual_fijo(3,df_filtrado,cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap, precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_anual_P1_scrap,potencia_contratada_anual_P2_scrap,precio_potencia_dia_P1_form,precio_potencia_dia_P2_form,descuento_form, descuento_potencia_form, impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form)
            figura = grafica(opciones_grafica_mens,opciones_grafica_anual)
            return opciones_baratas_mens_fijo
            
         #------------------------------------------Mensual Indexado--------------------------------------------------
        elif Metodo_form=='Indexado':
            opciones_baratas_mens_index = encontrar_opcion_mas_barata_mens_index(3,filas_mas_cercanas,index_power_filtrado,cons_P1_form,cons_P2_form,cons_P3_form,precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_P1_form, potencia_contratada_P2_form, dias_form, precio_potencia_dia_P1_form, precio_potencia_dia_P2_form, descuento_form,descuento_potencia_form, impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form)

            return opciones_baratas_mens_index

#-------------------------------------------------Calculadora Consumo Anual--------------------------------------------------------------
    elif Tipo_consumo_form=='Consumo_anual':
        #---------------------------------------------------------Anual Fijo----------------------------------------------------------------
        if Metodo_form=='Fijo':

            opciones_baratas_mens_fijo, opciones_grafica_mens = encontrar_opcion_mas_barata_mens_fijo(3,df_filtrado,cons_P1_form,cons_P2_form,cons_P3_form,precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_P1_form, potencia_contratada_P2_form, dias_form, precio_potencia_dia_P1_form, precio_potencia_dia_P2_form, descuento_form, descuento_potencia_form,impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form)
            opciones_baratas_anual_fijo, opciones_grafica_anual = encontrar_opcion_mas_barata_anual_fijo(3,df_filtrado,cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap, precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_anual_P1_scrap,potencia_contratada_anual_P2_scrap,precio_potencia_dia_P1_form,precio_potencia_dia_P2_form,descuento_form, descuento_potencia_form, impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form)
            
            figura = grafica(opciones_grafica_mens,opciones_grafica_anual)
            return opciones_baratas_anual_fijo
        #--------------------------------------------------------Anual indexado-------------------------------------------------------------
        elif Metodo_form=='Indexado':
           
            opciones_baratas_anual_index = encontrar_opcion_mas_barata_anual_index(3,df_medindx12_penins_2,index_power_filtrado_anual,cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap,precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_anual_P1_scrap,potencia_contratada_anual_P2_scrap,precio_potencia_dia_P1_form,precio_potencia_dia_P2_form,descuento_form, descuento_potencia_form, impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form)
             
            return opciones_baratas_anual_index

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
