# Background
Renewable solar photovoltaic energy generation has been widely utilized to support electricity supply nowadays. The rapid change of solar photovoltaic energy generation causes challenges to manage the solar photovoltaic energy generation systems. Estimating and forecasting solar irradiance can be referenced to understand performance of renewable solar photovoltaic energy generation in advance and resolve some of the challenges to manage the system.

# Algorithm Description
As a method to estimate solar irradiance, we utilized cloud cover estimation using a machine learning model called U-Net [1]. The application estimates solar irradiance from a calculated cloud cover ratio and outputs the percentage of solar irradiance in Watt per square meter.

# Using the code
Output: solar irradiance (W/m2)  
Input: cloud cover ratio (0-1)  
Image resolution: N/A  
Inference (calculation) time:  
Model loading time: N/A  

# Arguments
   '-debug': Debug flag  
   '-node-latitude': Latitude of the node location (default = 36.691959)  
   '-node-longitude': Longitude of the node location (default = -97.565965)  

# Ontology:
The code publishes measurements with toptic ‘env.solar.irradiance’

### Reference
[1] Seongha Park, Yongho Kim, Nicola J. Ferrier, Scott M. Collis, Rajesh Sankaran and Pete H. Beckman “Prediction of Solar Irradiance and Photovoltaic Solar Energy Product Based on Cloud Coverage Estimation Using Machine Learning Methods”, 2020, Atmosphere, Volume 12, Issue 3, pages 395.
