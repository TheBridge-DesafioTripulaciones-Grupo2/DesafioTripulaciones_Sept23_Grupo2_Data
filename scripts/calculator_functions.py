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
#-------------------------------------------------------------CREAR GRAFICA-------------------------------------------------------
def grafica(df_grafica_mens, df_grafica_anual):
    # Creamos un dataframe para cada barra a representar, en este caso mensual y anual
    customdata_mensual = df_grafica_mens[['FEE', 'PRODUCTO_CIA', 'PorcentajeAhorro', 'Ahorro']]
    customdata_anual = df_grafica_anual[['FEE', 'PRODUCTO_CIA', 'PorcentajeAhorro', 'Ahorro']]

    # Creación de barras por separado
    bar_mensual = px.bar(
        data_frame=df_grafica_mens,
        x='CIA', 
        y='Ahorro',
        title='Porcentajes de ahorro Mensual por Empresa',
        labels={'value': 'Porcentaje de Ahorro', 'CIA':'Compañía'},
        hover_data={
            'CIA': True, 
            'FEE': True,
            'PorcentajeAhorro': True,
            'PRODUCTO_CIA': True,
            'Ahorro': True},
        custom_data=customdata_mensual,)

    bar_anual = px.bar(
        data_frame=df_grafica_anual,
        x='CIA', 
        y='Ahorro',
        title='Porcentajes de ahorro Anual por Empresa',
        labels={'value': 'Porcentaje de Ahorro', 'CIA':'Compañía'},
        hover_data={
            'CIA': True, 
            'FEE': True,
            'PorcentajeAhorro': True,
            'PRODUCTO_CIA': True,
            'Ahorro': True},
        custom_data=customdata_anual)

    # Actualizar el color de las barras
    bar_mensual.update_traces(marker_color='#1F1D1C', name='Mensual')
    bar_anual.update_traces(marker_color='#701516', name='Anual')

    # Crear figura combinando las dos barras
    fig = go.Figure(data=bar_mensual.data + bar_anual.data)

    # Actualizar el diseño del gráfico
    fig.update_layout(
        barmode='group',
        width=800,
        legend=dict(title='', orientation='h', y=-0.12, x=0, traceorder='grouped'),
        hoverlabel=dict(bgcolor='#CCC8C8'))

    fig.update_traces(
        hovertemplate='<b style="color:#701516; font-size:16px">FEE: %{customdata[0]}</b><br>'
                  '<b style="color:#701516;">PRODUCTO_CIA:</b> %{customdata[1]}<br>'
                  '<b style="color:#701516;">Ahorro en euros:</b> %{customdata[2]:,.2f}<br>'
                  '<b style="color:#701516;">Porcentaje de ahorro:</b> %{customdata[3]}<br>', 
        hoverlabel=dict(bgcolor='#FFFFFF'),
)

    fig.update_layout(
        legend=dict(title='', orientation='h', y=-0.12, x=0, traceorder='grouped'),
        yaxis=dict(range=[0, 50], tickvals=[10, 20, 30, 40, 50], ticktext=['10%', '20%', '30%', '40%', '50%'],showgrid=True, gridcolor='#CCC8C8'),  # Ampliar el eje y al 50% y especificar los valores deseados
        margin=dict(l=50, r=150, b=50, t=50),  # Ajustar los márgenes
        xaxis=dict(showgrid=True, gridcolor='#CCC8C8'), 
        grid=dict(xside='top', yside='right'), 
        plot_bgcolor="#FFFFFF"  # Color de fondo del gráfico
)

    fig.update_xaxes(categoryorder='array', categoryarray=['Mensual', 'Anual'])  # Personalizar el orden de las barras
    fig.update_layout(bargap=0.45)  # Ajustar espacio entre las barras

    fig.show()

    return fig

#-------------------------------------------------------------MENSUAL FIJO--------------------------------------------------------

def calcular_energia_mens_fijo(cons_mens_P1,cons_mens_P2,cons_mens_P3, precio_mens_P1,precio_mens_P2,precio_mens_P3,descuento):
    # sumatorio_cons_mens=cons_mens_P1+cons_mens_P2+cons_mens_P3
    precio_P1_descuento= precio_mens_P1 * (1-descuento) #€
    precio_P2_descuento= precio_mens_P2 * (1-descuento)
    precio_P3_descuento= precio_mens_P3 * (1-descuento)

    total_pago_P1_energia= cons_mens_P1 * precio_P1_descuento #€
    total_pago_P2_energia= cons_mens_P2 * precio_P2_descuento
    total_pago_P3_energia= cons_mens_P3 * precio_P3_descuento

    sumatorio_total_pago_energia = total_pago_P1_energia + total_pago_P2_energia + total_pago_P3_energia
    return sumatorio_total_pago_energia

def calcular_potencia_mens_fijo(potencia_contratada_P1,potencia_contratada_P2,dias,precio_potencia_dia_P1,precio_potencia_dia_P2,dto_p):
    total_pago_P1_potencia= dias * precio_potencia_dia_P1 * potencia_contratada_P1 * (1-dto_p)
    total_pago_P2_potencia= dias * precio_potencia_dia_P2 * potencia_contratada_P2 * (1-dto_p)
    sumatorio_total_pago_potencia = total_pago_P1_potencia + total_pago_P2_potencia
    return sumatorio_total_pago_potencia

def calcular_total_factura_mens_fijo(sumatorio_total_pago_energia,sumatorio_total_pago_potencia,impuesto_electrico,otros,alquiler_equipo,IVA):
    bi_IVA= (sumatorio_total_pago_energia + sumatorio_total_pago_potencia
        +impuesto_electrico + alquiler_equipo + otros)
    importe_total_factura_mens= bi_IVA * (1+IVA)
    return importe_total_factura_mens

def encontrar_opcion_mas_barata_mens_fijo(endpoint:int,df,cons_mens_P1,cons_mens_P2,cons_mens_P3,precio_mens_P1,precio_mens_P2,precio_mens_P3,potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2, descuento, dto_p,impuesto_electrico, otros, alquiler_equipo, IVA): #df_filtrado
    opciones = []

    sumatorio_total_pago_energia = calcular_energia_mens_fijo(cons_mens_P1, cons_mens_P2, cons_mens_P3, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento)
    sumatorio_total_pago_potencia = calcular_potencia_mens_fijo(potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2, dto_p)
    importe_total_factura_mens_actual = round(calcular_total_factura_mens_fijo(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico, otros,alquiler_equipo, IVA),2)
    min_cost_dict = {}

    for index,row in df.iterrows():

        precio_mens_P1, precio_mens_P2, precio_mens_P3 = row['p1_e'], row['p2_e'], row['p3_e']
        precio_potencia_dia_P1, precio_potencia_dia_P2 = row['p1_p'], row['p2_p']

        sumatorio_total_pago_energia = calcular_energia_mens_fijo(cons_mens_P1, cons_mens_P2, cons_mens_P3, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento)
        sumatorio_total_pago_potencia = calcular_potencia_mens_fijo(potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2,dto_p)
        importe_total_factura_mens = round(calcular_total_factura_mens_fijo(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico, otros, alquiler_equipo,IVA),2)
        
        if row['cia'] not in min_cost_dict or importe_total_factura_mens < min_cost_dict[row['cia']]:
            min_cost_dict[row['cia']] = importe_total_factura_mens
            p1e_barata=precio_mens_P1
            p2e_barata=precio_mens_P2
            p3e_barata=precio_mens_P3
            p1p_barata=precio_potencia_dia_P1
            p2p_barata=precio_potencia_dia_P2


    opciones = [{
        'CIA': cia,
        'FEE': df.loc[df['cia'] == cia, 'fee'].values[0],
        'PRODUCTO_CIA': df.loc[df['cia'] == cia, 'producto_cia'].values[0],
        'CostoTotal': min_cost,
        'Ahorro': round(importe_total_factura_mens_actual - min_cost, 2),
        'PorcentajeAhorro': round(((importe_total_factura_mens_actual - min_cost) / importe_total_factura_mens_actual) * 100, 2)
        } for cia, min_cost in min_cost_dict.items()]

    # Opción más barata para cada compañía
    df_opciones = pd.DataFrame(opciones)
    idx_opcion_mas_barata = df_opciones['CostoTotal'].idxmin()
    
    opcion_barata=df_opciones.iloc[idx_opcion_mas_barata]

    opciones_mas_baratas = df_opciones.nsmallest(5, 'CostoTotal')
    ahorro_euros=round(importe_total_factura_mens_actual-opcion_barata['CostoTotal'],2)
    porcentaje_ahorro= round((ahorro_euros/importe_total_factura_mens_actual)*100,2)

    if endpoint == 2:

        dict1={
            'Precio actual': importe_total_factura_mens_actual,
            'Ahorro': ahorro_euros,
            'Porcentaje de ahorro': f"{porcentaje_ahorro:.1f}%",
        } 
        dict2=opcion_barata.to_dict()
        dict3={'p1e':p1e_barata,'p2e':p2e_barata,'p3e':p3e_barata,
            'p1p':p1p_barata, 'p2p':p2p_barata}
        dict1.update(dict2)
        dict1.update(dict3)
        return dict1
    
    elif endpoint==3:
        resultados_df = pd.DataFrame([{'Precio actual': importe_total_factura_mens_actual, 'Opciones más baratas': opciones_mas_baratas}])
        
        resultados = resultados_df.to_json(orient='records', force_ascii=False)
        
        
        return jsonify(resultados),opciones_mas_baratas
    
#--------------------------------------------------------Mensual indexado------------------------------------------------------------------------

# funciones de cálculo importes
def calcular_energia_mens_index(cons_mens_P1,cons_mens_P2,cons_mens_P3, precio_mens_P1,precio_mens_P2,precio_mens_P3,descuento):
    # sumatorio_cons_mens=cons_mens_P1+cons_mens_P2+cons_mens_P3
    precio_P1_descuento= precio_mens_P1 * (1-descuento) #€
    precio_P2_descuento= precio_mens_P2 * (1-descuento)
    precio_P3_descuento= precio_mens_P3 * (1-descuento)
    
    #añadir P4,P5,P6 como None/0/1

    total_pago_P1_energia= cons_mens_P1 * precio_P1_descuento #€
    total_pago_P2_energia= cons_mens_P2 * precio_P2_descuento
    total_pago_P3_energia= cons_mens_P3 * precio_P3_descuento

    sumatorio_total_pago_energia = total_pago_P1_energia + total_pago_P2_energia + total_pago_P3_energia
    return sumatorio_total_pago_energia

def calcular_potencia_mens_index(potencia_contratada_P1,potencia_contratada_P2,dias,precio_potencia_dia_P1,precio_potencia_dia_P2,dto_p):
    total_pago_P1_potencia= dias * precio_potencia_dia_P1 * potencia_contratada_P1 * (1-dto_p)
    total_pago_P2_potencia= dias * precio_potencia_dia_P2 * potencia_contratada_P2 * (1-dto_p)
    sumatorio_total_pago_potencia = total_pago_P1_potencia + total_pago_P2_potencia
    return sumatorio_total_pago_potencia
    
def calcular_total_factura_mens_index(sumatorio_total_pago_energia,sumatorio_total_pago_potencia,impuesto_electrico,otros,alquiler_equipo,IVA):
    bi_IVA= (sumatorio_total_pago_energia + sumatorio_total_pago_potencia
        +impuesto_electrico + otros + alquiler_equipo)
    importe_total_factura_mens= bi_IVA * (1+IVA)
    return importe_total_factura_mens

def encontrar_opcion_mas_barata_mens_index(endpoint:int,df_energia,df_potencia,cons_mens_P1,cons_mens_P2,cons_mens_P3,precio_mens_P1,precio_mens_P2,precio_mens_P3,potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2, descuento, dto_p,impuesto_electrico, otros, alquiler_equipo, IVA):
    opciones = []

    df_combinado = pd.merge(df_energia, df_potencia, on='cia',suffixes=["_e","_p"])
    df_combinado.dropna(axis=0,inplace=True)

    sumatorio_total_pago_energia = calcular_energia_mens_index(cons_mens_P1, cons_mens_P2, cons_mens_P3, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento)
    sumatorio_total_pago_potencia = calcular_potencia_mens_index(potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2,dto_p)
    importe_total_factura_mens_actual = round(calcular_total_factura_mens_index(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico, otros,alquiler_equipo, IVA),2)
    min_cost_dict = {}

    for index,row in df_combinado.iterrows():
 
        precio_mens_P1, precio_mens_P2, precio_mens_P3 = row['p1_e'], row['p2_e'], row['p3_e']
        precio_potencia_dia_P1, precio_potencia_dia_P2 = row['p1_p'], row['p2_p']
        
        sumatorio_total_pago_energia = calcular_energia_mens_index(cons_mens_P1, cons_mens_P2, cons_mens_P3, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento)
        sumatorio_total_pago_potencia = calcular_potencia_mens_index(potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2,dto_p)
        importe_total_factura_mens = round(calcular_total_factura_mens_index(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico, otros,alquiler_equipo, IVA),2)

        if row['cia'] not in min_cost_dict or importe_total_factura_mens < min_cost_dict[row['cia']]:
            min_cost_dict[row['cia']] = importe_total_factura_mens
            p1e_barata=precio_mens_P1
            p2e_barata=precio_mens_P2
            p3e_barata=precio_mens_P3
            p1p_barata=precio_potencia_dia_P1
            p2p_barata=precio_potencia_dia_P2

    opciones = [{
        'CIA': cia,
        'FEE': df_combinado.loc[df_combinado['cia'] == cia, 'fee'].values[0], #PINTA MAL
        'PRODUCTO_CIA': df_combinado.loc[df_combinado['cia'] == cia, 'producto_cia'].values[0],
        'CostoTotal': min_cost,
        'Ahorro': round(importe_total_factura_mens_actual - min_cost, 2),
        'PorcentajeAhorro': round(((importe_total_factura_mens_actual - min_cost) / importe_total_factura_mens_actual) * 100, 2)
    } for cia, min_cost in min_cost_dict.items()]

    # Opción más barata para cada compañía
    df_opciones = pd.DataFrame(opciones)
    idx_opcion_mas_barata = df_opciones['CostoTotal'].idxmin()

    opcion_barata=df_opciones.iloc[idx_opcion_mas_barata]

    opciones_mas_baratas = df_opciones.nsmallest(5, 'CostoTotal')
    ahorro_euros=round(importe_total_factura_mens_actual-opcion_barata['CostoTotal'],2)
    porcentaje_ahorro= round((ahorro_euros/importe_total_factura_mens_actual)*100,2)
    if endpoint == 2:

        dict1={
            'Precio actual': importe_total_factura_mens_actual,
            'Ahorro': ahorro_euros,
            'Porcentaje de ahorro': f"{porcentaje_ahorro:.1f}%",
        } 
        dict2=opcion_barata.to_dict()
        dict3={'p1e':p1e_barata,'p2e':p2e_barata,'p3e':p3e_barata,
            'p1p':p1p_barata, 'p2p':p2p_barata}
        dict1.update(dict2)
        dict1.update(dict3)
        return dict1

    elif endpoint == 3:
        resultados_df = pd.DataFrame([{
            'Precio actual': importe_total_factura_mens_actual,
            'Opciones más baratas': opciones_mas_baratas
        }])

        resultados = resultados_df.to_json(orient='records', force_ascii=False)

        return jsonify(resultados),opciones_mas_baratas

#------------------------------------------------------------ANUAL FIJO-----------------------------------------------------------------
# funciones de cálculo importes

def calcular_energia_anual_fijo(cons_anual_P1,cons_anual_P2,cons_anual_P3, precio_mens_P1,precio_mens_P2,precio_mens_P3,descuento):
    # sumatorio_cons_mens=cons_mens_P1+cons_mens_P2+cons_mens_P3
    # cons_anual_P1,cons_anual_P2,cons_anual_P3 ==========>TIENEN QUE VENIR DEL SCRAPPING DE CANDELA POR EL CUPS
    precio_P1_descuento= precio_mens_P1 * (1-descuento) #€
    precio_P2_descuento= precio_mens_P2 * (1-descuento)
    precio_P3_descuento= precio_mens_P3 * (1-descuento)

    total_pago_P1_energia= cons_anual_P1 * precio_P1_descuento #€
    total_pago_P2_energia= cons_anual_P2 * precio_P2_descuento
    total_pago_P3_energia= cons_anual_P3 * precio_P3_descuento

    sumatorio_total_pago_energia = total_pago_P1_energia + total_pago_P2_energia + total_pago_P3_energia
    return sumatorio_total_pago_energia

def calcular_potencia_anual_fijo(potencia_contratada_P1,potencia_contratada_P2,precio_potencia_dia_P1,precio_potencia_dia_P2,dto_p):
    
    # OJO HAY Q SCRAPEAR LAS POTENCIA_CONTRATADA
    total_pago_P1_potencia= 365 * precio_potencia_dia_P1 * potencia_contratada_P1 * (1-dto_p)
    total_pago_P2_potencia= 365 * precio_potencia_dia_P2 * potencia_contratada_P2 * (1-dto_p)
    sumatorio_total_pago_potencia = total_pago_P1_potencia + total_pago_P2_potencia
    return sumatorio_total_pago_potencia

def calcular_total_factura_anual_fijo(sumatorio_total_pago_energia,sumatorio_total_pago_potencia,impuesto_electrico,otros,alquiler_equipo,IVA):
    bi_IVA= (sumatorio_total_pago_energia + sumatorio_total_pago_potencia
         +impuesto_electrico*12 + + alquiler_equipo*12 + otros*12)
    importe_total_factura_anual= bi_IVA * (1+IVA)
    return importe_total_factura_anual
#cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap, precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_anual_P1_scrap,potencia_contratada_anual_P2_scrap,precio_potencia_dia_P1_form,precio_potencia_dia_P2_form,descuento_form, descuento_potencia_form, impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form
def encontrar_opcion_mas_barata_anual_fijo(endpoint:int,df,cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap, precio_P1_form,precio_P2_form,precio_P3_form,potencia_contratada_P1_scrap,potencia_contratada_P2_scrap,precio_potencia_dia_P1_form,precio_potencia_dia_P2_form,descuento_form,dto_p_form, impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form):

    opciones = []
    sumatorio_total_pago_energia = calcular_energia_anual_fijo(cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap, precio_P1_form,precio_P2_form,precio_P3_form, descuento_form)
    sumatorio_total_pago_potencia = calcular_potencia_anual_fijo(potencia_contratada_P1_scrap, potencia_contratada_P2_scrap, precio_potencia_dia_P1_form, precio_potencia_dia_P2_form,dto_p_form)
    #impuesto_electrico, otros, alquiler_equipo, IVA = 0.33, 1.27, 0.88, 0.05  # CAMBIAR A INPUT DE LA FACTURA

    # print(sumatorio_total_pago_energia,sumatorio_total_pago_potencia)

    importe_total_factura_anual_actual = round(calcular_total_factura_anual_fijo(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico_form, otros_form,alquiler_equipo_form, IVA_form),2)
    min_cost_dict = {}

    for index,row in df.iterrows():

        precio_mens_P1, precio_mens_P2, precio_mens_P3 = row['p1_e'], row['p2_e'], row['p3_e']
        precio_potencia_dia_P1, precio_potencia_dia_P2 = row['p1_p'], row['p2_p']
        
        sumatorio_total_pago_energia = calcular_energia_anual_fijo(cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento_form)
        sumatorio_total_pago_potencia = calcular_potencia_anual_fijo(potencia_contratada_P1_scrap, potencia_contratada_P2_scrap, precio_potencia_dia_P1, precio_potencia_dia_P2,dto_p_form)
        # impuesto_electrico, otros,alquiler_equipo, IVA = impuesto_electrico, otros,alquiler_equipo, IVA  # CAMBIAR A INPUT FORMULARIO

        importe_total_factura_anual = round(calcular_total_factura_anual_fijo(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico_form, otros_form, alquiler_equipo_form,IVA_form),2)
        # Update the minimum cost for each 'CIA'
        if row['cia'] not in min_cost_dict or importe_total_factura_anual < min_cost_dict[row['cia']]:
            min_cost_dict[row['cia']] = importe_total_factura_anual
            p1e_barata=precio_mens_P1
            p2e_barata=precio_mens_P2
            p3e_barata=precio_mens_P3
            p1p_barata=precio_potencia_dia_P1
            p2p_barata=precio_potencia_dia_P2

 
    opciones = [{
        'CIA': cia,
        'FEE': df.loc[df['cia'] == cia, 'fee'].values[0],
        'PRODUCTO_CIA': df.loc[df['cia'] == cia, 'producto_cia'].values[0],
        'CostoTotal': min_cost,
        'Ahorro': round(importe_total_factura_anual_actual - min_cost, 2),
        'PorcentajeAhorro': round(((importe_total_factura_anual_actual - min_cost) / importe_total_factura_anual_actual) * 100, 2)
    } for cia, min_cost in min_cost_dict.items()]

    # Opción más barata para cada compañía
    df_opciones = pd.DataFrame(opciones)
    idx_opcion_mas_barata = df_opciones['CostoTotal'].idxmin()
    
    opcion_barata=df_opciones.iloc[idx_opcion_mas_barata]

    opciones_mas_baratas = df_opciones.nsmallest(5, 'CostoTotal')
    ahorro_euros=round(importe_total_factura_anual_actual-opcion_barata['CostoTotal'],2)
    porcentaje_ahorro= round((ahorro_euros/importe_total_factura_anual_actual)*100,2)

    if endpoint == 2: #CHECK
        dict1={
                'Precio actual': importe_total_factura_anual_actual,
                'Ahorro': ahorro_euros,
                'Porcentaje de ahorro': f"{porcentaje_ahorro:.1f}%",
            } 
        dict2=opcion_barata.to_dict()
        dict3={'p1e':p1e_barata,'p2e':p2e_barata,'p3e':p3e_barata,
            'p1p':p1p_barata, 'p2p':p2p_barata}
        dict1.update(dict2)
        dict1.update(dict3)
        return dict1

    elif endpoint == 3:
        resultado_df = pd.DataFrame([{
            'Precio actual': importe_total_factura_anual_actual,
            'Opciones más baratas': opciones_mas_baratas
        }])
        
        resultados = resultado_df.to_json(orient='records', force_ascii=False)
        return jsonify(resultados), opciones_mas_baratas

#-------------------------------------------------------ANUAL INDEXADO----------------------------------------------------

def calcular_energia_anual_index(cons_anual_P1,cons_anual_P2,cons_anual_P3, P1M_E,P2M_E,P3M_E,descuento):
    # sumatorio_cons_mens=cons_mens_P1+cons_mens_P2+cons_mens_P3
    precio_P1_descuento= P1M_E * (1-descuento) #€
    precio_P2_descuento= P2M_E * (1-descuento)
    precio_P3_descuento= P3M_E * (1-descuento)
    
    #añadir P4,P5,P6 como None/0/1

    total_pago_P1_energia= cons_anual_P1 * precio_P1_descuento #€
    total_pago_P2_energia= cons_anual_P2 * precio_P2_descuento
    total_pago_P3_energia= cons_anual_P3 * precio_P3_descuento

    sumatorio_total_pago_energia = total_pago_P1_energia + total_pago_P2_energia + total_pago_P3_energia
    return sumatorio_total_pago_energia

def calcular_potencia_anual_index(potencia_contratada_P1,potencia_contratada_P2,precio_potencia_dia_P1,precio_potencia_dia_P2,dto_p):
    total_pago_P1_potencia= 365 * precio_potencia_dia_P1 * potencia_contratada_P1 * (1-dto_p)
    total_pago_P2_potencia= 365 * precio_potencia_dia_P2 * potencia_contratada_P2 * (1-dto_p)
    sumatorio_total_pago_potencia = total_pago_P1_potencia + total_pago_P2_potencia
    return sumatorio_total_pago_potencia
    
def calcular_total_factura_anual_index(sumatorio_total_pago_energia,sumatorio_total_pago_potencia,impuesto_electrico,otros,alquiler_equipo,IVA):
    bi_IVA= (sumatorio_total_pago_energia + sumatorio_total_pago_potencia
         +impuesto_electrico*12 + otros*12 + alquiler_equipo*12)
    importe_total_factura_anual= bi_IVA * (1+IVA)
    return importe_total_factura_anual

def encontrar_opcion_mas_barata_anual_index(endpoint:int,df_energia, df_potencia,cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap, precio_P1_form, precio_P2_form, precio_P3_form,potencia_contratada_P1_scrap,potencia_contratada_P2_scrap,precio_potencia_dia_P1_form,precio_potencia_dia_P2_form,descuento_form,dto_p_form, impuesto_electrico_form, otros_form, alquiler_equipo_form, IVA_form):
    opciones = []

    df_combinado = pd.merge(df_energia, df_potencia, on='cia',suffixes=["_e","_p"])
    df_combinado.dropna(axis=0,inplace=True)
    #precio_media_P1, precio_media_P2, precio_media_P3 vienen del form
    sumatorio_total_pago_energia = calcular_energia_anual_index(cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap, precio_P1_form, precio_P2_form, precio_P3_form, descuento_form)
    sumatorio_total_pago_potencia = calcular_potencia_anual_index(potencia_contratada_P1_scrap, potencia_contratada_P2_scrap, precio_potencia_dia_P1_form, precio_potencia_dia_P2_form,dto_p_form)
    #impuesto_electrico, otros, alquiler_equipo, IVA = 0.33, 1.27, 0.88,0.05  # CAMBIAR A INPUT DE LA FACTURA

    importe_total_factura_anual_actual = round(calcular_total_factura_anual_index(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico_form, otros_form,alquiler_equipo_form, IVA_form),2)
    min_cost_dict = {}


    for index,row in df_combinado.iterrows():

        precio_mens_P1, precio_mens_P2, precio_mens_P3 = row['p1_e'], row['p2_e'], row['p3_e']
        precio_potencia_dia_P1, precio_potencia_dia_P2 = row['p1_p'], row['p2_p']
        
        sumatorio_total_pago_energia = calcular_energia_anual_index(cons_anual_P1_scrap,cons_anual_P2_scrap,cons_anual_P3_scrap, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento_form)
        sumatorio_total_pago_potencia = calcular_potencia_anual_index(potencia_contratada_P1_scrap, potencia_contratada_P2_scrap, precio_potencia_dia_P1, precio_potencia_dia_P2,dto_p_form)
        importe_total_factura_anual_ppta = round(calcular_total_factura_anual_index(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico_form, otros_form,alquiler_equipo_form, IVA_form),2)
        
       # Update the minimum cost for each 'CIA'
        if row['cia'] not in min_cost_dict or importe_total_factura_anual_ppta < min_cost_dict[row['cia']]:
            min_cost_dict[row['cia']] = importe_total_factura_anual_ppta
            p1e_barata=precio_mens_P1
            p2e_barata=precio_mens_P2
            p3e_barata=precio_mens_P3
            p1p_barata=precio_potencia_dia_P1
            p2p_barata=precio_potencia_dia_P2
    
    # Create a list with the minimum cost entries for each 'CIA' and calculate savings for each option
    opciones = [{
        'CIA': cia,
        'FEE': df_combinado.loc[df_combinado['cia'] == cia, 'fee'].values[0],
        'PRODUCTO_CIA': df_combinado.loc[df_combinado['cia'] == cia, 'producto_cia'].values[0],
        'CostoTotal': min_cost,
        'Ahorro': round(importe_total_factura_anual_actual - min_cost, 2),
        'PorcentajeAhorro': round(((importe_total_factura_anual_actual - min_cost) / importe_total_factura_anual_actual) * 100, 2)
    } for cia, min_cost in min_cost_dict.items()]

    # Opción más barata para cada compañía
    df_opciones = pd.DataFrame(opciones)
    idx_opcion_mas_barata = df_opciones['CostoTotal'].idxmin()
    
    opcion_barata=df_opciones.iloc[idx_opcion_mas_barata]

    opciones_mas_baratas = df_opciones.nsmallest(5, 'CostoTotal')
    ahorro_euros=round(importe_total_factura_anual_actual-opcion_barata['CostoTotal'],2)
    porcentaje_ahorro= round((ahorro_euros/importe_total_factura_anual_actual)*100,2)

    if endpoint == 2:
            dict1={
                    'Precio actual': importe_total_factura_anual_actual,
                    'Ahorro': ahorro_euros,
                    'Porcentaje de ahorro': f"{porcentaje_ahorro:.1f}%",
                } 
            dict2=opcion_barata.to_dict()
            dict3={'p1e':p1e_barata,'p2e':p2e_barata,'p3e':p3e_barata,
                'p1p':p1p_barata, 'p2p':p2p_barata}
            dict1.update(dict2)
            dict1.update(dict3)
            return dict1


    elif endpoint == 3:
        response_data = pd.DataFrame([{
            'Precio actual': importe_total_factura_anual_actual,
            'Opciones más baratas': opciones_mas_baratas
        }])

        resultados = response_data.to_json(orient='records', force_ascii=False)
        return jsonify(resultados)
    
    #----------------------------------------------------FUNCIÓN WEBSCRAPING-------------------------------------------------------------------------------------------------------------------------------

def webscraping(CUPS_input):
    # CUPS_input=request.args.get('CUPS_input')
    
    dir_path = os.path.dirname(os.path.realpath(__file__))

    service = Service(executable_path=(os.path.join(dir_path, ".", "chromedriver.exe")))
    options = webdriver.ChromeOptions()

    driver = webdriver.Chrome(service=service, options=options)
    driver.get("http://www.google.es")
    loadMore = driver.find_element(By.XPATH, '/html/body/div[2]/div[3]/div[3]/span/div/div/div/div[3]/div[1]/button[1]/div')
    loadMore.click()
    url = 'https://agentes.candelaenergia.es/#/login'
    driver.get(url)
    time.sleep(1)
    caja_seleccion = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div/div[1]/div/form/div[1]/div[1]/md-select')))
    caja_seleccion.click()
    time.sleep(1)
    opciones = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/md-select-menu/md-content/md-option[1]/div[1]')))
    
    opciones[0].click()
    time.sleep(1)
    campo_usuario = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[1]/div/form/div[1]/div[2]/input')
    campo_contraseña = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[1]/div/form/div[1]/div[3]/input')

    campo_usuario.send_keys(usuario)
    campo_contraseña.send_keys(contrasena)

    time.sleep(1)
    formulario = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[1]/div/form/button')
    formulario.click()

    time.sleep(5)
    sips = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[1]/ul/li[3]/a')
    sips.click()

    time.sleep(2)
    CUPS = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-card/div/form/div[1]/md-input-container[1]/input')
    time.sleep(1)
    CUPS.send_keys(CUPS_input) #aqui iba el cups de kino: ES0031104629924014ZJ0F

    inspeccionar_CUPS = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-card/div/form/div[4]/button')
    inspeccionar_CUPS.click()
    time.sleep(5)
    tabla_CUPS = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[3]/input')
    
    placeholder_CUPS = tabla_CUPS.get_attribute('placeholder')

    tabla_municipio = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[5]/input')
    placeholder_municipio = tabla_municipio.get_attribute('placeholder')

    tabla_Provincia = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[6]/input')
    placeholder_Provincia = tabla_Provincia.get_attribute('placeholder')

    tabla_postal = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[7]/input')
    placeholder_postal = tabla_postal.get_attribute('placeholder')

    tabla_tarifa = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[8]/input')
    placeholder_tarifa = tabla_tarifa.get_attribute('placeholder')

    tabla_consumo_anual = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[10]/input')
    placeholder_consumo_anual = tabla_consumo_anual.get_attribute('placeholder')

    tabla_consumo_anual_P1 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[11]/input')
    placeholder_consumo_anual_P1 = tabla_consumo_anual_P1.get_attribute('placeholder')

    tabla_consumo_anual_P2 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[12]/input')
    placeholder_consumo_anual_P2 = tabla_consumo_anual_P2.get_attribute('placeholder')

    tabla_consumo_anual_P3 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[13]/input')
    placeholder_consumo_anual_P3 = tabla_consumo_anual_P3.get_attribute('placeholder')

    tabla_consumo_anual_P4 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[14]/input')
    placeholder_consumo_anual_P4 = tabla_consumo_anual_P4.get_attribute('placeholder')

    tabla_consumo_anual_P5 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[15]/input')
    placeholder_consumo_anual_P5 = tabla_consumo_anual_P5.get_attribute('placeholder')

    tabla_consumo_anual_P6 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[16]/input')
    placeholder_consumo_anual_P6 = tabla_consumo_anual_P6.get_attribute('placeholder')

    tabla_P1 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[19]/input')
    placeholder_P1 = tabla_P1.get_attribute('placeholder')

    tabla_P2 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[20]/input')
    placeholder_P2 = tabla_P2.get_attribute('placeholder')

    tabla_P3 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[21]/input')
    placeholder_P3 = tabla_P3.get_attribute('placeholder')

    tabla_P4 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[22]/input')
    placeholder_P4 = tabla_P4.get_attribute('placeholder')

    tabla_P5 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[23]/input')
    placeholder_P5 = tabla_P5.get_attribute('placeholder')

    tabla_P6 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[24]/input')
    placeholder_P6 = tabla_P6.get_attribute('placeholder')

    tabla_distribuidora = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[26]/input')
    placeholder_distribuidora = tabla_distribuidora.get_attribute('placeholder')

    tabla_cambio_comercial = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[1]/td[28]/input')
    placeholder_cambio_comercial = tabla_cambio_comercial.get_attribute('placeholder')

    tabla_ultimo_cambio_BIE = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr/td[29]/input')
    placeholder_ultimo_cambio_BIE = tabla_ultimo_cambio_BIE.get_attribute('placeholder')

    tabla_tension = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr/td[30]/input')
    placeholder_tension = tabla_tension.get_attribute('placeholder')

    tabla_distribuidora_Contrato = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr/td[34]/input')
    placeholder_distribuidora_Contrato = tabla_distribuidora_Contrato.get_attribute('placeholder')

    
    placeholder_CUPS = placeholder_CUPS.strip()
    placeholder_municipio = placeholder_municipio.strip()
    placeholder_Provincia = placeholder_Provincia.strip()
    placeholder_postal = placeholder_postal.strip()
    placeholder_tarifa = placeholder_tarifa.strip()
    placeholder_consumo_anual = placeholder_consumo_anual.strip()
    placeholder_consumo_anual_P1 = placeholder_consumo_anual_P1.strip()
    placeholder_consumo_anual_P2 = placeholder_consumo_anual_P2.strip()
    placeholder_consumo_anual_P3 = placeholder_consumo_anual_P3.strip()
    placeholder_consumo_anual_P4 = placeholder_consumo_anual_P4.strip()
    placeholder_consumo_anual_P5 = placeholder_consumo_anual_P5.strip()
    placeholder_consumo_anual_P6 = placeholder_consumo_anual_P6.strip()
    placeholder_P1 = placeholder_P1.strip()
    placeholder_P2 = placeholder_P2.strip()
    placeholder_P3 = placeholder_P3.strip()
    placeholder_P4 = placeholder_P4.strip()
    placeholder_P5 = placeholder_P5.strip()
    placeholder_P6 = placeholder_P6.strip()
    placeholder_distribuidora = placeholder_distribuidora.strip()
    placeholder_cambio_comercial = placeholder_cambio_comercial.strip()
    placeholder_ultimo_cambio_BIE = placeholder_ultimo_cambio_BIE.strip()
    placeholder_tension = placeholder_tension.strip()
    placeholder_distribuidora_Contrato = placeholder_distribuidora_Contrato.strip()
    time.sleep(1)
    valor_CUPS = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[3]')
    valor_placeholder_CUPS = valor_CUPS.text #valor del cups

    valor_municipio = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[6]')
    valor_placeholder_municipio = valor_municipio.text

    valor_Provincia = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[7]')
    valor_placeholder_Provincia = valor_Provincia.text

    valor_postal = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[8]')
    valor_placeholder_postal = valor_postal.text

    valor_tarifa = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[9]/any/any')
    valor_placeholder_tarifa = valor_tarifa.text

    valor_consumo_anual = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[11]')
    valor_placeholder_consumo_anual = valor_consumo_anual.text

    valor_consumo_anual_P1 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[13]')
    valor_placeholder_consumo_anual_P1 = valor_consumo_anual_P1.text

    valor_consumo_anual_P2 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[14]')
    valor_placeholder_consumo_anual_P2 = valor_consumo_anual_P2.text

    valor_consumo_anual_P3 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[15]')
    valor_placeholder_consumo_anual_P3 = valor_consumo_anual_P3.text

    valor_consumo_anual_P4 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[16]')
    valor_placeholder_consumo_anual_P4 = valor_consumo_anual_P4.text

    valor_consumo_anual_P5 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[17]')
    valor_placeholder_consumo_anual_P5 = valor_consumo_anual_P5.text

    valor_consumo_anual_P6 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[18]')
    valor_placeholder_consumo_anual_P6 = valor_consumo_anual_P6.text

    valor_P1 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[21]')
    valor_placeholder_P1 = valor_P1.text

    valor_P2 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[22]')
    valor_placeholder_P2 = valor_P2.text

    valor_P3 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[23]')
    valor_placeholder_P3 = valor_P3.text

    valor_P4 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[24]')
    valor_placeholder_P4 = valor_P4.text

    valor_P5 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[25]')
    valor_placeholder_P5 = valor_P5.text

    valor_P6 = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[26]')
    valor_placeholder_P6 = valor_P6.text

    valor_distribuidora = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[28]')
    valor_placeholder_distribuidora = valor_distribuidora.text

    valor_cambio_comercial = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[30]')
    valor_placeholder_cambio_comercial = valor_cambio_comercial.text

    valor_ultimo_cambio_BIE = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[31]')
    valor_placeholder_ultimo_cambio_BIE = valor_ultimo_cambio_BIE.text

    valor_tension = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[32]/any/any')
    valor_placeholder_tension = valor_tension.text

    valor_distribuidora_Contrato = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-content/md-card/md-table-container/table/tbody/tr[2]/td[37]')
    valor_placeholder_distribuidora_Contrato = valor_distribuidora_Contrato.text

    valor_placeholder_CUPS = valor_placeholder_CUPS.strip()
    valor_placeholder_municipio = valor_placeholder_municipio.strip()
    valor_placeholder_Provincia = valor_placeholder_Provincia.strip()
    valor_placeholder_postal = valor_placeholder_postal.strip()
    valor_placeholder_tarifa = valor_placeholder_tarifa.strip()
    valor_placeholder_consumo_anual = valor_placeholder_consumo_anual.strip()
    valor_placeholder_consumo_anual_P1 = valor_placeholder_consumo_anual_P1.strip()
    valor_placeholder_consumo_anual_P2 = valor_placeholder_consumo_anual_P2.strip()
    valor_placeholder_consumo_anual_P3 = valor_placeholder_consumo_anual_P3.strip()
    valor_placeholder_consumo_anual_P4 = valor_placeholder_consumo_anual_P4.strip()
    valor_placeholder_consumo_anual_P5 = valor_placeholder_consumo_anual_P5.strip()
    valor_placeholder_consumo_anual_P6 = valor_placeholder_consumo_anual_P6.strip()
    valor_placeholder_P1 = valor_placeholder_P1.strip()
    valor_placeholder_P2 = valor_placeholder_P2.strip()
    valor_placeholder_P3 = valor_placeholder_P3.strip()
    valor_placeholder_P4 = valor_placeholder_P4.strip()
    valor_placeholder_P5 = valor_placeholder_P5.strip()
    valor_placeholder_P6 = valor_placeholder_P6.strip()
    valor_placeholder_distribuidora = valor_placeholder_distribuidora.strip()
    valor_placeholder_cambio_comercial = valor_placeholder_cambio_comercial.strip()
    valor_placeholder_ultimo_cambio_BIE = valor_placeholder_ultimo_cambio_BIE.strip()
    valor_placeholder_tension = valor_placeholder_tension.strip()
    valor_placeholder_distribuidora_Contrato = valor_placeholder_distribuidora_Contrato.strip()

    dicc = {placeholder_CUPS:valor_placeholder_CUPS, 
        placeholder_municipio:valor_placeholder_municipio,
        placeholder_Provincia:valor_placeholder_Provincia,
        placeholder_postal:valor_placeholder_postal,
        placeholder_tarifa:valor_placeholder_tarifa,
        placeholder_consumo_anual:valor_placeholder_consumo_anual,
        placeholder_consumo_anual_P1:valor_placeholder_consumo_anual_P1,
        placeholder_consumo_anual_P2:valor_placeholder_consumo_anual_P2,
        placeholder_consumo_anual_P3:valor_placeholder_consumo_anual_P3,
        placeholder_consumo_anual_P4:valor_placeholder_consumo_anual_P4,
        placeholder_consumo_anual_P5:valor_placeholder_consumo_anual_P5,
        placeholder_consumo_anual_P6:valor_placeholder_consumo_anual_P6,
        placeholder_P1:valor_placeholder_P1,
        placeholder_P2:valor_placeholder_P2,
        placeholder_P3:valor_placeholder_P3,
        placeholder_P4:valor_placeholder_P4,
        placeholder_P5:valor_placeholder_P5,
        placeholder_P6:valor_placeholder_P6,
        placeholder_distribuidora:valor_placeholder_distribuidora,
        placeholder_cambio_comercial:valor_placeholder_cambio_comercial,
        placeholder_ultimo_cambio_BIE:valor_placeholder_ultimo_cambio_BIE,
        valor_placeholder_tension:placeholder_tension,
        placeholder_distribuidora_Contrato:valor_placeholder_distribuidora_Contrato}

    placeholder_CUPS = placeholder_CUPS.strip()
    placeholder_municipio = placeholder_municipio.strip()
    placeholder_Provincia = placeholder_Provincia.strip()
    placeholder_postal = placeholder_postal.strip()
    placeholder_tarifa = placeholder_tarifa.strip()
    placeholder_consumo_anual = placeholder_consumo_anual.strip()
    placeholder_consumo_anual_P1 = placeholder_consumo_anual_P1.strip()
    placeholder_consumo_anual_P2 = placeholder_consumo_anual_P2.strip()
    placeholder_consumo_anual_P3 = placeholder_consumo_anual_P3.strip()
    placeholder_consumo_anual_P4 = placeholder_consumo_anual_P4.strip()
    placeholder_consumo_anual_P5 = placeholder_consumo_anual_P5.strip()
    placeholder_consumo_anual_P6 = placeholder_consumo_anual_P6.strip()
    placeholder_P1 = placeholder_P1.strip()
    placeholder_P2 = placeholder_P2.strip()
    placeholder_P3 = placeholder_P3.strip()
    placeholder_P4 = placeholder_P4.strip()
    placeholder_P5 = placeholder_P5.strip()
    placeholder_P6 = placeholder_P6.strip()
    placeholder_distribuidora = placeholder_distribuidora.strip()
    placeholder_cambio_comercial = placeholder_cambio_comercial.strip()
    placeholder_ultimo_cambio_BIE = placeholder_ultimo_cambio_BIE.strip()
    placeholder_tension = placeholder_tension.strip()
    placeholder_distribuidora_Contrato = placeholder_distribuidora_Contrato.strip()

    df = pd.DataFrame([dicc])
    df["P1"] = df["P1"].str.replace(",",".")
    df["P2"] = df["P2"].str.replace(",",".")
    columnas_numericas = ["Código Postal", "P1", "P2"]
    df[columnas_numericas] = df[columnas_numericas].apply(pd.to_numeric, errors='coerce')
    columnas_fecha = ["Cambio Comercializadora", "Cambio BIE", "Cambio Contrato"]
    df[columnas_fecha] = df[columnas_fecha].apply(pd.to_datetime, errors='coerce')

    df['Consumo anual'] = df['Consumo anual'].str.split().str[0]
    df['Consumo anual P1'] = df['Consumo anual P1'].str.split().str[0]
    df['Consumo anual P2'] = df['Consumo anual P2'].str.split().str[0]
    df['Consumo anual P3'] = df['Consumo anual P3'].str.split().str[0]

    df[["Consumo anual","Consumo anual P1","Consumo anual P2","Consumo anual P3"]] = df[["Consumo anual","Consumo anual P1","Consumo anual P2","Consumo anual P3"]].astype(float)
    resultados_anuales= df.to_json(orient='records', lines=True,force_ascii=False,)

    return resultados_anuales