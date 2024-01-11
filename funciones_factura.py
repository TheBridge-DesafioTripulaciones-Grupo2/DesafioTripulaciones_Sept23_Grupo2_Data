import pandas as pd
import datetime
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

df=pd.read_csv('data/processed/indexed_price.csv')
def filtrar_df(): #cargar el df antes de llamar a la función
    # df=df
    df['MES'] = pd.to_datetime(df['MES'])

    fecha_actual = datetime.now()

    df['diferencia'] = (fecha_actual - df['MES']).abs()

    condicion = (df['SISTEMA'] == 'PENINSULA') & (df['TARIFA'] == '2.0TD')
    filas_mas_cercanas = df[condicion].groupby(['SISTEMA', 'TARIFA', 'CIA']).apply(lambda x: x[x['diferencia'] == x['diferencia'].min()])

    filas_mas_cercanas = filas_mas_cercanas.drop('diferencia', axis=1).reset_index(drop=True)
    return filas_mas_cercanas