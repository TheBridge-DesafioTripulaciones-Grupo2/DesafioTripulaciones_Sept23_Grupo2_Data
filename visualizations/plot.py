import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Dataframe creado con datos ficticios
df = pd.DataFrame({
    'CIA': ['Iberdrola', 'Endesa', 'Acciona', 'Naturgy', 'Candela', 'Compañía Actual'],
    'Ahorro_Mensual': np.random.uniform(10, 20, size=6),
    'Ahorro_Anual': np.random.uniform(10, 20, size=6),
    'FEE': ['-'] * 6,
    'PRODUCTO_CIA': ['RESIDENCIAL NOCHE LUZ', 'RESIDENCIAL POR USO LUZ LOYAL', 'RESIDENCIAL POR USO LUZ', 'TEMPO LIBRE', 'PEH/API 2.0<10kW PLAN ESTABLE', 'Producto_cia_actual'],
    'Porcentaje de ahorro': ['13%', '14%', '5%', '3%', '4%', '-'],
    'Ahorro en euros': [10, 12, 9, 11, 10, 10],
    'Anual': [17.76, 20.56, 19.63, 18.69, 21.50, 1.87],
    'Mensual': [16.13, 19.35, 14.52, 17.74, 16.13, 16.13],
    'Porcentaje_Mensual_Comparacion': [100.0, 120.0, 90.0, 110.0, 100.0, 100.0],
    'Porcentaje_Anual_Comparacion': [950.0, 1100.0, 1050.0, 1000.0, 1150.0, 100.0]
})

# Creamos un dataframe para cada barra a representar, en este caso mensual y anual
customdata_mensual = df[['FEE', 'PRODUCTO_CIA', 'Porcentaje_Mensual_Comparacion', 'Ahorro_Mensual']]
customdata_anual = df[['FEE', 'PRODUCTO_CIA', 'Porcentaje_Anual_Comparacion', 'Ahorro_Anual']]

# Creación de barras por separado
bar_mensual = px.bar(
    data_frame=df,
    x='CIA', 
    y='Ahorro_Mensual',
    title='Porcentajes de ahorro Mensual por Empresa',
    labels={'value': 'Porcentaje de Ahorro', 'CIA':'Compañía'},
    hover_data={
        'CIA': True, 
        'FEE': True,
        'Porcentaje de ahorro': True,
        'PRODUCTO_CIA': True,
        'Ahorro en euros': True
    },
    custom_data=customdata_mensual,
)

bar_anual = px.bar(
    data_frame=df,
    x='CIA', 
    y='Ahorro_Anual',
    title='Porcentajes de ahorro Anual por Empresa',
    labels={'value': 'Porcentaje de Ahorro', 'CIA':'Compañía'},
    hover_data={
        'CIA': True, 
        'FEE': True,
        'Porcentaje de ahorro': True,
        'PRODUCTO_CIA': True,
        'Ahorro en euros': True
    },
    custom_data=customdata_anual,
)

# Actualizar el color de las barras
bar_mensual.update_traces(marker_color='#1F1D1C', name='Mensual')
bar_anual.update_traces(marker_color='#FF8523', name='Anual')

# Crear figura combinando las dos barras
fig = go.Figure(data=bar_mensual.data + bar_anual.data)

# Actualizar el diseño del gráfico
fig.update_layout(
    barmode='group',
    width=800,
    legend=dict(title='', orientation='h', y=-0.12, x=0, traceorder='grouped'),
    hoverlabel=dict(bgcolor='#FAFAFA')
)

fig.update_traces(
    hovertemplate='<b style="color:#1F1D1C; font-size:16px">FEE: %{customdata[0]}</b><br>'
                  '<b style="color:#1F1D1C;">PRODUCTO_CIA:</b> %{customdata[1]}<br>'
                  '<b style="color:#1F1D1C;">Ahorro en euros:</b> %{customdata[2]:,.2f}'
                  '<b style="color:#1F1D1C;">Porcentaje de ahorro:</b> %{customdata[3]}<br>', 
    hoverlabel=dict(bgcolor='#FAFAFA'),
)
fig.update_layout(
    legend=dict(title='', orientation='h', y=-0.12, x=0, traceorder='grouped'),
    yaxis=dict(range=[0, 50], tickvals=[10, 20, 30, 40, 50], ticktext=['10%', '20%', '30%', '40%', '50%'],showgrid=True),  # Ampliar el eje y al 50% y especificar los valores deseados
    margin=dict(l=50, r=150, b=50, t=50),  # Ajustar los márgenes
    xaxis=dict(showgrid=True), 
    grid=dict(xside='top', yside='right'), 
    plot_bgcolor="#FAFAFA"  # Color de fondo del gráfico
)
fig.update_xaxes(categoryorder='array', categoryarray=['Mensual', 'Anual'])  # Personalizar el orden de las barras
fig.update_layout(bargap=0.45)  # Ajustar espacio entre las barras

fig.show()
