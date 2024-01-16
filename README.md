
# Proyecto de Data Science para Several Energy
## Descripción
Este proyecto tiene como objetivo mejorar los procesos de Several Energy mediante la implementación de diversas técnicas y herramientas de ciencia de datos. Los logros clave de este proyecto incluyen web scraping con Selenium para obtener datos anuales de los clientes según su CUPS, el desarrollo de cuatro calculadoras de precios de la luz para diferentes compañías y sus planes, la creación de una API versátil con varios puntos finales para la ingesta de datos, generación de propuestas y visualizaciones dinámicas, así como un breve Análisis Exploratorio de Datos (EDA) y la estructura de una base de datos SQL para conectar la API.
El proyecto ha sido desarrollado por Adrián Nieto, Joaquín Gálvez, Daniel Manso y Águeda González.

## Componentes del proyecto
#### 1. Web scraping
Implementamos web scraping con la librería Selenium de Python para obtener datos anuales de los clientes mediante sus CUPS (Código Universal del Punto de Suministro). Este proceso nos permite recopilar información relevante de manera eficiente y automatizada en cuanto el asesor accede a la pestaña de datos anuales.

El web scraping se realiza desde el archivo [app.py](scripts/app.py), en la carpeta notebooks, esta el proceso paso a paso.

Nota: Es necesario usuario y contraseña en candela para poder realizar la consulta mediante web scrapping, para la realización del proyecto, se ha utilizado git.ignore para no compartir las credenciales.

#### 2. Calculadoras de precios de la luz
Desarrollamos diferentes calculadoras para determinar los planes de electricidad más rentables para los clientes según si introducen los datos de su consumo anual o mensual y si desea ver precios fijos o indexados. Las calculadoras consideran factores como las horas consumidas en cada franja horaria para garantizar que los clientes reciban recomendaciones personalizadas alineadas con sus patrones de consumo de energía.

Las calculadoras estan todas en la carpeta notebooks, se puede revisar ahi el proceso de prueba.

#### 3. API con múltiples *endpoints*
La API tiene varios *endpoints* para facilitar diferentes funcionalidades:

- Ingesta de datos
Introduce datos mensuales de los clientes a partir de sus facturas, proporcionando una forma sencilla de actualizar los registros de los clientes.
- Generación de propuestas
Genera la mejor propuesta para el plan de electricidad más económico según las preferencias del usuario, patrones de consumo y características del plan.
- Visualizaciones dinámicas
Proporciona gráficos interactivos que se actualizan dinámicamente al pasar el cursor, permitiendo a los usuarios visualizar tarifas actuales y compararlas entre diferentes compañías.
Se puede revisar el codigo que genera las graficas en este [notebook](visualizations/plots.ipynb)
- Top 5 de tarifas más baratas
Recupera y presenta las 5 tarifas más baratas de cada compañía, teniendo en cuenta las necesidades y preferencias del cliente y las necesidades y comisiones del asesor.
#### 4. Análisis Exploratorio de Datos (EDA)
Realizamos un breve EDA para comprender mejor los datos y los patrones de consumo. Este análisis proporciona información y visualizaciones valiosas para ajustar y mejorar las calculadoras y la generación de propuestas.

#### 5. Estructura de base de datos SQL
Creamos la estructura inicial de una base de datos SQL para almacenar y gestionar de forma eficiente los datos recopilados. La base de datos facilita la conexión de la API y garantiza una gestión ordenada y escalable de la información.
#### 6. Pruebas de *machine learning*
Hicimos varias pruebas con diferentes modelos de regresión, series temporales y redes neuronales, pero los datos facilitados por la empresa no fueron suficientes para sacar predicciones fiables, dado que solo disponíamos de datos de 24 meses. Uno de los siguientes pasos del proyecto sería obtener más datos, no solo de los precios de la luz a nivel nacional, sino de las distintas empresas y planes.

Las pruebas con machine learning se pueden revisar en estos archivos [Redes Neuronales](notebooks/05_ML_RRNN_dffiltrados.ipynb) y [Regression](notebooks/05_ML_Regressiones.ipynb)
