import pandas as pd
df = pd.read_csv('data/processed/indexed_price.csv')
index_power = pd.read_csv('data/processed/indexed_price_power.csv')

from datetime import datetime

fecha_actual = datetime.now()
df['diferencia'] = (fecha_actual - df['MES']).abs() # diferencia entre cada fecha 'MES' y la fecha actual


condicion = (df['SISTEMA'] == 'PENINSULA') & (df['TARIFA'] == '2.0TD') # filtrar para obtener las filas más cercanas por CIA y con SISTEMA y TARIFA específicos
filas_mas_cercanas = df[condicion].groupby(['SISTEMA', 'TARIFA', 'CIA']).apply(lambda x: x[x['diferencia'] == x['diferencia'].min()])

filas_mas_cercanas = filas_mas_cercanas.drop('diferencia', axis=1).reset_index(drop=True)
filas_mas_cercanas['FEE'] = filas_mas_cercanas['FEE'].str.upper()
filas_mas_cercanas.dropna(axis=0,inplace=True)

# condiciones para filtrar (sería con el desplegable)
condiciones_sistema_tarifa = (index_power['SISTEMA'] == 'PENINSULA') & (index_power['TARIFA'] == '2.0TD') & (index_power['PRODUCTO'] == 'INDEXADO')

condiciones_cias = index_power['CIA'].isin(['ACCIONA', 'AEQ', 'CANDELA', 'FACTOR', 'IGNIS', 'MAX'])

index_power_filtrado = index_power[condiciones_sistema_tarifa & condiciones_cias] # aplicar el filtro

# funciones de cálculo importes
def calcular_energia(cons_mens_P1,cons_mens_P2,cons_mens_P3, precio_mens_P1,precio_mens_P2,precio_mens_P3,descuento):
    # sumatorio_cons_mens=cons_mens_P1+cons_mens_P2+cons_mens_P3
    precio_P1_descuento= precio_mens_P1 * (1-descuento) #€
    precio_P2_descuento= precio_mens_P2 * (1-descuento)
    precio_P3_descuento= precio_mens_P3 * (1-descuento)

    total_pago_P1_energia= cons_mens_P1 * precio_P1_descuento #€
    total_pago_P2_energia= cons_mens_P2 * precio_P2_descuento
    total_pago_P3_energia= cons_mens_P3 * precio_P3_descuento

    sumatorio_total_pago_energia = total_pago_P1_energia + total_pago_P2_energia + total_pago_P3_energia
    return sumatorio_total_pago_energia

def calcular_potencia(potencia_contratada_P1,potencia_contratada_P2,dias,precio_potencia_dia_P1,precio_potencia_dia_P2):
    total_pago_P1_potencia= dias * precio_potencia_dia_P1 * potencia_contratada_P1
    total_pago_P2_potencia= dias * precio_potencia_dia_P2 * potencia_contratada_P2
    sumatorio_total_pago_potencia = total_pago_P1_potencia + total_pago_P2_potencia
    return sumatorio_total_pago_potencia

def calcular_total_factura(sumatorio_total_pago_energia,sumatorio_total_pago_potencia,impuesto_electrico,otros,IVA):
    bi_IVA= (sumatorio_total_pago_energia + sumatorio_total_pago_potencia
         +impuesto_electrico + otros)
    importe_total_factura_mens= bi_IVA * (1+IVA)
    return importe_total_factura_mens

def encontrar_opcion_mas_barata(df_energia, df_potencia):
    opciones = []

    df_combinado = pd.merge(df_energia, df_potencia, on='CIA',suffixes=["_E","_P"])

    for index,row in df_combinado.iterrows():
        cons_mens_P1, cons_mens_P2, cons_mens_P3 = 74, 83, 168 #CAMBIAR A INPUT DE LA FACTURA
        potencia_contratada_P1, potencia_contratada_P2 = 3.45, 3.45 #CAMBIAR A INPUT DE LA FACTURA
        precio_mens_P1, precio_mens_P2, precio_mens_P3 = row['P1_E'], row['P2_E'], row['P3_E']
        precio_potencia_dia_P1, precio_potencia_dia_P2 = row['P1_P'], row['P2_P']
        descuento = 0.02  # CAMBIAR A INPUT DE LA FACTURA
        dias = 33 # CAMBIAR A INPUT DE LA FACTURA
        
        sumatorio_total_pago_energia = calcular_energia(cons_mens_P1, cons_mens_P2, cons_mens_P3, precio_mens_P1, precio_mens_P2, precio_mens_P3, descuento)
        sumatorio_total_pago_potencia = calcular_potencia(potencia_contratada_P1, potencia_contratada_P2, dias, precio_potencia_dia_P1, precio_potencia_dia_P2)
        impuesto_electrico, otros, IVA = 5, 2, 0.21  # CAMBIAR A INPUT DE LA FACTURA

        importe_total_factura_mens = calcular_total_factura(sumatorio_total_pago_energia, sumatorio_total_pago_potencia, impuesto_electrico, otros, IVA)

        opciones.append({
            'CIA': row['CIA'],
            'FEE': row['FEE'],
            'PRODUCTO_CIA': row['PRODUCTO_CIA'],
            'CostoTotal': importe_total_factura_mens
        })

    # Opción más barata para cada compañía
    df_opciones = pd.DataFrame(opciones)
    idx_opcion_mas_barata = df_opciones['CostoTotal'].idxmin()
    
    opcion_barata=df_opciones.iloc[idx_opcion_mas_barata]

    opciones_mas_baratas = df_opciones.nsmallest(5, 'CostoTotal')
    
    return 'Opción más barata:',opcion_barata, "Opciones más baratas:", opciones_mas_baratas
    
encontrar_opcion_mas_barata(filas_mas_cercanas,index_power_filtrado)