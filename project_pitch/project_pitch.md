# **Project Pitch [C3]: HCAI – Hydrological Climate Analysis & Insights**  

## **Project Overview**   

Our goal is to provide researchers and decision-makers with a **dashboard** for data comparison and an **AI-powered approach** to reveal hidden patterns in hydrological data.

---

### **1. Interactive Dashboard for Model Comparison**  
The dashboard provides an intuitive interface for exploring hydrological model data with multiple visualization modes:  

- **Heatmaps of HRU values** across different points in time (where applicable).  
- **Heatmaps of changes in values** over time intervals, helping to identify trends.  
- **Comparative heatmaps** showing differences between two hydrological models (**CH-RUN vs. PRAVAH**).  
- **Customizable visualization settings**, including:  
  - Selection of **target data** (e.g., precipitation, runoff, soil moisture).  
  - **Mode selection**: Absolute values, absolute change, relative change.  
  - **Target time selection** (specific timestep or time interval).

---

### **2. Advanced Data Analysis & Machine Learning**  
Beyond visualization, we want to provide **data-driven insights** through AI and statistical techniques:  

- **Regression-based analysis:**  
  - A simple regression network will be trained to **identify key data relationships**.  
  - Open questions: **Which input variables to use? What model architecture is fit for the task?**  

- **Input sensitivity analysis:**  
  - Identifying how different input variables impact hydrological outputs on average.  
  - Helps gauging **the relative importence of input parameters**.  

- **Comparative Latent Space Analysis:**  
  - Projecting high-dimensional hydrological data into a **lower-dimensional space** while preserving key patterns.  
  - Comparing **how data points move in this space over time relative to each other**, offering insights into real world dynamics through the lense of an abstract space.  
  - **Dashboard integration**: Users can visually track data movement in the latent space.