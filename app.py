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
from key import usuario,contrasena
import psycopg2
# from datos_dummy import bd



app = Flask(__name__)
app.config["DEBUG"] = True

#------------------------------------------------------------Conectamos y sacamos los datos de la database---------------------------------------------------------

db_params = {
    'host': '34.78.249.103',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'cristian99'
}

conn = psycopg2.connect(**db_params)
cursor = conn.cursor()


consulta_fixed = "SELECT * FROM fixed_price"
consulta_indexed = "SELECT * FROM indexed_price"
consulta_power = "SELECT * FROM indexed_price_power"

df_database = pd.read_sql_query(consulta_fixed, conn)
index_price = pd.read_sql_query(consulta_indexed, conn)
index_power = pd.read_sql_query(consulta_power, conn)

cursor.close()
conn.close()

#-------------------------------------------------------------

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

def calcular_potencia_mens_fijo(potencia_contratada_P1,potencia_contratada_P2,dias,precio_potencia_dia_P1,precio_potencia_dia_P2):
    total_pago_P1_potencia= dias * precio_potencia_dia_P1 * potencia_contratada_P1
    total_pago_P2_potencia= dias * precio_potencia_dia_P2 * potencia_contratada_P2
    sumatorio_total_pago_potencia = total_pago_P1_potencia + total_pago_P2_potencia
    return sumatorio_total_pago_potencia

def calcular_total_factura_mens_fijo(sumatorio_total_pago_energia,sumatorio_total_pago_potencia,impuesto_electrico,otros,alquiler_equipo,IVA):
    bi_IVA= (sumatorio_total_pago_energia + sumatorio_total_pago_potencia
        +impuesto_electrico + + alquiler_equipo + otros)
    importe_total_factura_mens= bi_IVA * (1+IVA)
    return importe_total_factura_mens

def encontrar_opcion_mas_barata_mens_fijo(df,cons_mens_P1,cons_mens_P2,cons_mens_P3,precio_mens_P1,precio_mens_P2,precio_mens_P3,potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2, descuento, impuesto_electrico, otros, alquiler_equipo, IVA): #df_filtrado
    opciones = []

   
    sumatorio_total_pago_energia = calcular_energia_mens_fijo(cons_mens_P1, cons_mens_P2, cons_mens_P3, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento)
    sumatorio_total_pago_potencia = calcular_potencia_mens_fijo(potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2)
    # print(sumatorio_total_pago_energia,sumatorio_total_pago_potencia)
    importe_total_factura_mens_actual = round(calcular_total_factura_mens_fijo(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico, otros,alquiler_equipo, IVA),2)

    for index,row in df.iterrows():

        sumatorio_total_pago_energia = calcular_energia_mens_fijo(cons_mens_P1, cons_mens_P2, cons_mens_P3, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento)
        sumatorio_total_pago_potencia = calcular_potencia_mens_fijo(potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2)
        importe_total_factura_mens = round(calcular_total_factura_mens_fijo(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico, otros, alquiler_equipo,IVA),2)

        opciones.append({
            'CIA': row['cia'],
            'FEE': row['fee'],
            'PRODUCTO_CIA': row['producto_cia'],
            'CostoTotal': importe_total_factura_mens
        })

    # Opción más barata para cada compañía
    df_opciones = pd.DataFrame(opciones)
    idx_opcion_mas_barata = df_opciones['CostoTotal'].idxmin()
    
    opcion_barata=df_opciones.iloc[idx_opcion_mas_barata]

    opciones_mas_baratas = df_opciones.nsmallest(5, 'CostoTotal')
    ahorro_euros=round(importe_total_factura_mens_actual-opcion_barata['CostoTotal'],2)
    porcentaje_ahorro= round((ahorro_euros/importe_total_factura_mens_actual)*100,2)

    return ('Precio actual:',importe_total_factura_mens_actual,'Opción más barata:',opcion_barata,
            'Ahorro:',ahorro_euros, 'Porcentaje de ahorro:',f"{porcentaje_ahorro:.1f}%","Opciones más baratas:", opciones_mas_baratas)

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

def calcular_potencia_mens_index(potencia_contratada_P1,potencia_contratada_P2,dias,precio_potencia_dia_P1,precio_potencia_dia_P2):
    total_pago_P1_potencia= dias * precio_potencia_dia_P1 * potencia_contratada_P1
    total_pago_P2_potencia= dias * precio_potencia_dia_P2 * potencia_contratada_P2
    sumatorio_total_pago_potencia = total_pago_P1_potencia + total_pago_P2_potencia
    return sumatorio_total_pago_potencia
    
def calcular_total_factura_mens_index(sumatorio_total_pago_energia,sumatorio_total_pago_potencia,impuesto_electrico,otros,alquiler_equipo,IVA):
    bi_IVA= (sumatorio_total_pago_energia + sumatorio_total_pago_potencia
        +impuesto_electrico + otros + alquiler_equipo)
    importe_total_factura_mens= bi_IVA * (1+IVA)
    return importe_total_factura_mens


def encontrar_opcion_mas_barata_mens_index(df_energia,df_potencia,cons_mens_P1,cons_mens_P2,cons_mens_P3,precio_mens_P1,precio_mens_P2,precio_mens_P3,potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2, descuento, impuesto_electrico, otros, alquiler_equipo, IVA):
    opciones = []

    df_combinado = pd.merge(df_energia, df_potencia, on='cia',suffixes=["_e","_p"])
    df_combinado.dropna(axis=0,inplace=True)

    #sumatorio_total_pago_energia = calcular_energia_mens_index(cons_mens_P1, cons_mens_P2, cons_mens_P3, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento)
    #sumatorio_total_pago_potencia = calcular_potencia_mens_index(potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2)


    # print(sumatorio_total_pago_energia,sumatorio_total_pago_potencia)

    importe_total_factura_mens_actual = round(calcular_total_factura_mens_index(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico, otros,alquiler_equipo, IVA),2)


    for index,row in df_combinado.iterrows():
 
        # print(sumatorio_total_pago_energia,sumatorio_total_pago_potencia)

        sumatorio_total_pago_energia = calcular_energia_mens_index(cons_mens_P1, cons_mens_P2, cons_mens_P3, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento)
        sumatorio_total_pago_potencia = calcular_potencia_mens_index(potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2)

        importe_total_factura_mens = round(calcular_total_factura_mens_index(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico, otros,alquiler_equipo, IVA),2)

        opciones.append({
            'CIA': row['cia'],
            'FEE': row['fee'],
            'PRODUCTO_CIA': row['producto_cia'],
            'CostoTotal': importe_total_factura_mens
        })

    # Opción más barata para cada compañía
    df_opciones = pd.DataFrame(opciones)
    idx_opcion_mas_barata = df_opciones['CostoTotal'].idxmin()

    opcion_barata=df_opciones.iloc[idx_opcion_mas_barata]

    opciones_mas_baratas = df_opciones.nsmallest(5, 'CostoTotal')
    ahorro_euros=round(importe_total_factura_mens_actual-opcion_barata['CostoTotal'],2)
    porcentaje_ahorro= round((ahorro_euros/importe_total_factura_mens_actual)*100,2)

    return ('Precio actual:',importe_total_factura_mens_actual,'Opción más barata:',opcion_barata,
            'Ahorro:',ahorro_euros, 'Porcentaje de ahorro:',f"{porcentaje_ahorro:.1f}%","Opciones más baratas:", opciones_mas_baratas)

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

def calcular_potencia_anual_fijo(potencia_contratada_P1,potencia_contratada_P2,precio_potencia_dia_P1,precio_potencia_dia_P2):
    
    # OJO HAY Q SCRAPEAR LAS POTENCIA_CONTRATADA
    total_pago_P1_potencia= 365 * precio_potencia_dia_P1 * potencia_contratada_P1
    total_pago_P2_potencia= 365 * precio_potencia_dia_P2 * potencia_contratada_P2
    sumatorio_total_pago_potencia = total_pago_P1_potencia + total_pago_P2_potencia
    return sumatorio_total_pago_potencia

def calcular_total_factura_anual_fijo(sumatorio_total_pago_energia,sumatorio_total_pago_potencia,impuesto_electrico,otros,alquiler_equipo,IVA):
    bi_IVA= (sumatorio_total_pago_energia + sumatorio_total_pago_potencia
         +impuesto_electrico*12 + + alquiler_equipo*12 + otros*12)
    importe_total_factura_anual= bi_IVA * (1+IVA)
    return importe_total_factura_anual

def encontrar_opcion_mas_barata_anual_fijo(df): #df_filtrado
    opciones = []

    sumatorio_total_pago_energia = calcular_energia_anual_fijo(cons_anual_P1, cons_anual_P2, cons_anual_P3, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento)
    sumatorio_total_pago_potencia = calcular_potencia_anual_fijo(potencia_contratada_P1, potencia_contratada_P2, precio_potencia_dia_P1, precio_potencia_dia_P2)
    impuesto_electrico, otros, alquiler_equipo, IVA = 0.33, 1.27, 0.88,0.05  # CAMBIAR A INPUT DE LA FACTURA

    # print(sumatorio_total_pago_energia,sumatorio_total_pago_potencia)

    importe_total_factura_anual_actual = round(calcular_total_factura_anual_fijo(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico, otros,alquiler_equipo, IVA),2)


    for index,row in df.iterrows():

        precio_mens_P1, precio_mens_P2, precio_mens_P3 = row['p1_e'], row['p2_e'], row['p3_e']
        precio_potencia_dia_P1, precio_potencia_dia_P2 = row['p1_p'], row['p2_p']


        
        sumatorio_total_pago_energia = calcular_energia_anual_fijo(cons_anual_P1, cons_anual_P2, cons_anual_P3, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento)
        sumatorio_total_pago_potencia = calcular_potencia_anual_fijo(potencia_contratada_P1, potencia_contratada_P2, precio_potencia_dia_P1, precio_potencia_dia_P2)
        impuesto_electrico, otros,alquiler_equipo, IVA = 0.33, 1.27,0.88, 0.05  # CAMBIAR A INPUT DE LA FACTURA

        importe_total_factura_anual = round(calcular_total_factura_anual_fijo(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico, otros, alquiler_equipo,IVA),2)

        opciones.append({
            'CIA': row['cia'],
            'FEE': row['fee'],
            'PRODUCTO_CIA': row['producto_cia'],
            'CostoTotal': importe_total_factura_anual
        })

    # Opción más barata para cada compañía
    df_opciones = pd.DataFrame(opciones)
    idx_opcion_mas_barata = df_opciones['CostoTotal'].idxmin()
    
    opcion_barata=df_opciones.iloc[idx_opcion_mas_barata]

    opciones_mas_baratas = df_opciones.nsmallest(5, 'CostoTotal')
    ahorro_euros=round(importe_total_factura_anual_actual-opcion_barata['CostoTotal'],2)
    porcentaje_ahorro= round((ahorro_euros/importe_total_factura_anual_actual)*100,2)

    return ('Precio actual:',importe_total_factura_anual_actual,'Opción más barata:',opcion_barata,
            'Ahorro:',ahorro_euros, 'Porcentaje de ahorro:',f"{porcentaje_ahorro:.1f}%","Opciones más baratas:", opciones_mas_baratas)

#-------------------------------------------------------CREAMOS APP----------------------------------------------------


@app.route('/', methods=['GET'])
def home():
    return "<h1>Desafío de tripulaciones, grupo 2 (API Data homepage)</p>"


#---------------------------------------------------------PRIMER ENDPOINT------------------------------------------------


# 1./anualdata: recibe un CUPS, realiza el webscraping y devuelve los datos anuales
@app.route('/anualdata/<string:CUPS_input>', methods=['GET'])
def anual_data(CUPS_input):
    # CUPS_input=request.args.get('CUPS_input')
    service = Service(executable_path='chromedriver.exe')
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

    time.sleep(3)
    sips = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[1]/ul/li[3]/a')
    sips.click()

    time.sleep(2)
    CUPS = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-card/div/form/div[1]/md-input-container[1]/input')
    time.sleep(1)
    CUPS.send_keys(CUPS_input) #aqui iba el cups de kino: ES0031104629924014ZJ0F

    inspeccionar_CUPS = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/md-tabs/md-tabs-content-wrapper/md-tab-content/div/md-card/div/form/div[4]/button')
    inspeccionar_CUPS.click()

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
    columnas_numericas = ["Código Postal", "P1", "P2"]
    df[columnas_numericas] = df[columnas_numericas].apply(pd.to_numeric, errors='coerce')
    columnas_fecha = ["Cambio Comercializadora", "Cambio BIE", "Cambio Contrato"]
    df[columnas_fecha] = df[columnas_fecha].apply(pd.to_datetime, errors='coerce')
    resultados_anuales= df.to_json(orient='records', lines=True,force_ascii=False,)

    return resultados_anuales
    #tildes no las lee
   

#----------------------------------------------------------SEGUNDO ENDPOINT----------------------------------------------------------

# 2./proposal: recibe los datos de factura, datos anuales, la compañía, modelo, etc, realiza los cálculos y devuelve todos los datos de la propuesta en concreto
@app.route('/proposal/<string:Tipo_consumo>/<string:Metodo>/<float:cons_P1>/,<float:cons_P2>/<float:cons_P3>/<float:precio_P1>/<float:precio_P2>/<float:precio_P3>/<float:descuento>/<float:potencia_contratada_P1>/<float:potencia_contratada_P2>/<float:dias>/<float:precio_potencia_dia_P1>/<float:precio_potencia_dia_P1>/<float:precio_potencia_dia_P2>/<float:impuesto_electrico>/<float:alquiler_equipo>/<float:otros>/<string:Tipo_sistema>/<string:Tipo_tarifa>/<string:CIA>/<string:producto_CIA>/<timestamp:mes_facturacion>/<string:FEE>/<int:IVA>' methods=['GET'])
def proposal(Tipo_consumo,Metodo,cons_P1,cons_P2,cons_P3,precio_P1,precio_P2,precio_P3,descuento,potencia_contratada_P1,
              potencia_contratada_P2,dias,precio_potencia_dia_P1,precio_potencia_dia_P2,impuesto_electrico,alquiler_equipo,otros,Tipo_sistema,Tipo_tarifa,
              CIA,producto_CIA,mes_facturacion,FEE,IVA): #tipo_consumo: mensual o anual; metodo: fijo o indexado
    #mensual utiliza la fixed price, la filtramos para peninsula y 2.0
    df_filtrado = (df_database['sistema'] == 'PENINSULA') & (df_database['tarifa'] == '2.0TD')

    #indexed price filtros
    fecha_actual = datetime.now()
    index_price['diferencia'] = (fecha_actual - index_price['mes']).abs() # diferencia entre cada fecha 'MES' y la fecha actual
    condicion = (index_price['sistema'] == 'PENINSULA') & (index_price['tarifa'] == '2.0TD') # filtrar para obtener las filas más cercanas por CIA y con SISTEMA y TARIFA específicos
    filas_mas_cercanas = index_price[condicion].groupby(['sistema', 'tarifa', 'cia']).apply(lambda x: x[x['diferencia'] == x['diferencia'].min()])
    filas_mas_cercanas = filas_mas_cercanas.drop('diferencia', axis=1).reset_index(drop=True)

    #indexed price power filtros
    condiciones_sistema_tarifa = (index_power['sistema'] == 'PENINSULA') & (index_power['tarifa'] == '2.0TD') & (index_power['producto'] == 'INDEXADO')
    condiciones_cias = index_power['cia'].isin(['ACCIONA', 'AEQ', 'CANDELA', 'FACTOR', 'IGNIS', 'MAX'])
    index_power_filtrado = index_power[condiciones_sistema_tarifa & condiciones_cias]


    #cons_mens_P1, cons_mens_P2, cons_mens_P3 = 74, 83, 168 #CAMBIAR A INPUT DE LA FACTURA
    #potencia_contratada_P1, potencia_contratada_P2 = 3.45, 3.45 #CAMBIAR A INPUT DE LA FACTURA
    #precio_mens_P1, precio_mens_P2, precio_mens_P3 = 0.128515, 0.128515, 0.128515
    #precio_potencia_dia_P1, precio_potencia_dia_P2 = 0.09968, 0.033816
    #descuento = 0.02  # CAMBIAR A INPUT DE LA FACTURA
    #dias = 33 # CAMBIAR A INPUT DE LA FACTURA
    #impuesto_electrico, otros, alquiler_equipo, IVA = 0.33, 1.27, 0.88,0.05  # CAMBIAR A INPUT DE LA FACTURA

    #----------------------------------------Calculadora de consumo mensual----------------------------------------------
    if Tipo_consumo=='Consumo mensual':
        #------------------------------------------Mensual Fijo-------------------------------------------------------
        if Metodo=='Fijo':
            # funciones de cálculo importes
            opcion_barata_mens_fijo = encontrar_opcion_mas_barata_mens_fijo(df_filtrado,cons_P1,cons_P2,cons_P3,precio_P1,precio_P2,precio_P3,potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2, descuento, impuesto_electrico, otros, alquiler_equipo, IVA)
            #return jsonify(opcion_barata)
          
         #------------------------------------------Mensual Indexado--------------------------------------------------
        elif Metodo=='Indexado':
            opcion_barata_mens_index = encontrar_opcion_mas_barata_mens_index(index_power_filtrado,cons_P1,cons_P2,cons_P3,precio_P1,precio_P2,precio_P3,potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2, descuento, impuesto_electrico, otros, alquiler_equipo, IVA)

#-------------------------------------------------Calculadora Consumo Anual--------------------------------------------------------------
    elif Tipo_consumo=='Consumo anual':
        #---------------------------------------------------------Anual Fijo----------------------------------------------------------------
        if Metodo=='Fijo':
            sumatorio_total_pago_energia = calcular_energia_anual_fijo(cons_P1,cons_P2,cons_P3, precio_P1,precio_P2,precio_P3,descuento)
            sumatorio_total_pago_potencia = calcular_potencia_anual_fijo(potencia_contratada_P1,potencia_contratada_P2,precio_potencia_dia_P1,precio_potencia_dia_P2)
            
        #--------------------------------------------------------Anual indexado-------------------------------------------------------------
        elif Metodo=='Indexado':
            x

    
#     results = [book for book in books if book["id"]==id]
#     return results


# # 3.Ruta para obtener un libro concreto mediante su título como parámetro en la llamada de otra forma
# @app.route('/v0/book/<string:title>', methods=["GET"])
# def book_title(title):
#     results = [book for book in books if book["title"].lower()==title.lower()]
#     return results


# # 4.Ruta para obtener un libro concreto mediante su titulo dentro del cuerpo de la llamada  
# @app.route('/v1/book', methods=["GET"])
# def book_title_body():
#     title = request.get_json().get('title', None)
#     if not title:
#         return "Not a valid title in the request", 400
#     else:
#         results = [book for book in books if book["title"].lower()==title.lower()]
#         if results == []:
#             return "Book not found" , 400
#         else:
#             return results

# # 5.Ruta para añadir un libro mediante un json en la llamada
# @app.route('/v1/add_book', methods=["POST"])
# def post_books():
#     data = request.get_json()
#     books.append(data)
#     return books


# # 6.Ruta para añadir un libro mediante parámetros
# @app.route('/v2/add_book', methods=["POST"])
# def post_books_v2():
#     book = {}
#     book['id'] = int(request.args['id'])
#     book['title'] = request.args['title']
#     book['author'] = request.args['author']
#     book['first_sentence'] = request.args['first_sentence']
#     book['published'] = request.args['published']
#     books.append(book)
#     return books

# app.run()



# """def home():
#     return render_template('index.html')"""

# """@app.route('/ingest', methods=['POST'])
# def ingest():
#     data = request.get_json()
#     new_data = data.get('data', None)
#     if not new_data:
#         return {"error":"No se proporcionaron datso para agregar a la bbdd"}, 400

#     try:
#         connection = sqlite3.connect('data/advertising.db')
#         cursor = connection.cursor()
#         query = "INSERT INTO campañas VALUES (?,?,?,?)"
#         for valor in new_data:
#             cursor.execute(query, valor)
#         connection.commit()
#         connection.close()
#         return {'message': 'Datos ingresados correctamente'}, 200
#     except Exception as e:
#         return {'error':str(e)}, 500"""

# """@app.route('/retrain', methods=['POST'])
# def retrain():
#     try:
#         connection = sqlite3.connect('data/advertising.db')
#         cursor = connection.cursor()
#         query = '''SELECT * FROM campañas'''
#         result = cursor.execute(query).fetchall()
#         df = pd.DataFrame(result)
#         model.fit(df.iloc[:,:-1], df.iloc[:,-1])
#         with open('data/new_advertising_model.pkl', 'wb') as file:
#             pickle.dump(model, file)
#         return {'message': 'Modelo reentrenado correctamente.'}, 200
#     except Exception as e:
#         return {'error':str(e)}, 500"""

# from flask import Flask, request, jsonify
# import os
# import pickle
# import pandas as pd
# import sqlite3

# # os.chdir(os.path.dirname(__file__)) # da error en terminal
# app = Flask(__name__)
# # app.config['DEBUG'] = True
# script_dir = os.path.dirname(os.path.abspath(__file__))
# os.chdir(script_dir)

# @app.route("/", methods=['GET'])
# def hello():
#     return "Bienvenid@ a nuestra app de Several Energy"

# # 1

# @app.route('/predict', methods=['GET'])
# def predict_list():
#     model = pickle.load(open('data/advertising_model','rb'))
#     data = request.get_json()   #{"data": [[100, 100, 200]]}

#     input_values = data['data'][0]
#     tv, radio, newspaper = map(int, input_values)

#     prediction = model.predict([[tv, radio, newspaper]])
#     return jsonify({'prediction': round(prediction[0], 2)})


# #2

# @app.route('/ingest', methods=['POST'])
# def add_data():
#     data = request.get_json()

#     for row in data.get('data', []):
#         tv, radio, newspaper, sales = row
#         query = "INSERT INTO Advertising (tv, radio, newspaper, sales) VALUES (?, ?, ?, ?)"
#         connection = sqlite3.connect('data/Advertising.db')
#         crsr = connection.cursor()
#         crsr.execute(query, (tv, radio, newspaper, sales))
#         connection.commit()
#         connection.close()

#     return jsonify({'message': 'Datos ingresados correctamente'})

# #3

# @app.route('/retrain', methods=['POST'])
# def retrain():
#     conn = sqlite3.connect('data/Advertising.db')
#     crsr = conn.cursor()
#     query = "SELECT * FROM Advertising;"
#     crsr.execute(query)
#     ans = crsr.fetchall()
#     conn.close()
#     names = [description[0] for description in crsr.description]
#     df = pd.DataFrame(ans, columns=names)
#     model = pickle.load(open('data/advertising_model', 'rb'))
#     X = df[["TV", "newspaper", "radio"]]
#     y = df["sales"]
#     model.fit(X, y)
#     pickle.dump(model, open('data/advertising_model', 'wb'))

#     return jsonify({'message': 'Modelo reentrenado correctamente.'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
